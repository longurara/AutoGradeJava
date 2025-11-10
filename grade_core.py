#!/usr/bin/env python3
import os, subprocess, shutil, csv, re, sys
from pathlib import Path

def parse_testcase_text(text: str):
    """
    Supports sections:
    INPUT:, OUTPUT:, REMOVE_SPACES:, CASE_SENSITIVE:, MARK:, TIMEOUT_MS:
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    headers = ["INPUT","OUTPUT","REMOVE_SPACES","CASE_SENSITIVE","MARK","TIMEOUT_MS"]
    pattern = re.compile(r'^(INPUT|OUTPUT|REMOVE_SPACES|CASE_SENSITIVE|MARK|TIMEOUT_MS):\s*$', re.MULTILINE | re.IGNORECASE)
    matches = list(pattern.finditer(text))
    data = {h: None for h in headers}
    if not matches:
        data["INPUT"] = text.strip("\n")
        return data
    indices = [ (m.group(1).upper(), m.end(), m.start()) for m in matches ]
    indices.append(("__END__", len(text), len(text)))
    for i in range(len(indices)-1):
        key, content_start, _ = indices[i]
        _, __, next_start = indices[i+1]
        content = text[content_start:next_start]
        content = content.lstrip("\n")
        if key in ("REMOVE_SPACES","CASE_SENSITIVE","MARK","TIMEOUT_MS"):
            data[key] = content.strip()
        else:
            data[key] = content.rstrip("\n")
    return data

def to_bool(val, default=None):
    if val is None or val == "":
        return default
    v = val.strip().lower()
    if v in ("yes","y","true","1"):
        return True
    if v in ("no","n","false","0"):
        return False
    return default

def to_float(val, default=1.0):
    try:
        return float(val.strip())
    except Exception:
        return default

def to_int(val, default=None):
    try:
        return int(val.strip())
    except Exception:
        return default

def apply_compare_rules(expected: str, got: str, remove_spaces=None, case_sensitive=None, whitespace_norm=False, strict=False, ignore_trailing_per_line=False):
    e = expected or ""
    g = got or ""

    if strict:
        # No normalization at all
        pass
    else:
        if whitespace_norm:
            e = re.sub(r"\s+", " ", e).strip()
            g = re.sub(r"\s+", " ", g).strip()

        if remove_spaces is True:
            e = re.sub(r"\s+", "", e)
            g = re.sub(r"\s+", "", g)

        if ignore_trailing_per_line:
            e = "\n".join([ln.rstrip() for ln in e.splitlines()])
            g = "\n".join([ln.rstrip() for ln in g.splitlines()])

        if case_sensitive is False:  # NOT case sensitive
            e = e.casefold()
            g = g.casefold()

    return e == g

def find_java_tools(java_home=None):
    javac = "javac"
    java = "java"
    if java_home:
        bin_dir = Path(java_home) / "bin"
        javac = str(bin_dir / ("javac.exe" if os.name=="nt" else "javac"))
        java  = str(bin_dir / ("java.exe"  if os.name=="nt" else "java"))
    return javac, java

def detect_main_class(src_dir: Path):
    main_candidate = src_dir/"Main.java"
    if main_candidate.exists():
        return "Main"
    for p in src_dir.rglob("*.java"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"public\s+static\s+void\s+main\s*\(", txt):
                return p.stem
        except Exception:
            pass
    return "Main"

def run_cmd(cmd, input_text=None, cwd=None, timeout_ms=None):
    try:
        res = subprocess.run(cmd, input=input_text, capture_output=True, text=True, cwd=cwd, timeout=None if timeout_ms is None else timeout_ms/1000.0)
        return res.returncode, res.stdout, res.stderr, False  # not timeout
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ""
        err = (e.stderr or "") + "\n[TIMEOUT]"
        return 124, out, err, True
    except FileNotFoundError as e:
        return 127, "", str(e), False

def grade_question(root: Path, qname: str, javac: str, java: str, out_dir: Path, defaults: dict):
    q_dir = root/qname
    given = q_dir/"Given"
    src   = given/"src"
    run   = given/"run"
    jar   = run/f"{qname}.jar"
    has_jar = jar.exists()
    tcdir = q_dir/"TestCases"

    results = []
    summary = {"Question": qname, "Passed": 0, "Total": 0, "Percent": 0.0,
               "Compiled": False, "MainClass": "Main", "Score": 0.0, "MaxScore": 0.0}

    if not q_dir.exists():
        return results, summary, "Question folder does not exist."

    classes_dir = out_dir/f"{qname}-classes"
    if classes_dir.exists():
        shutil.rmtree(classes_dir)
    classes_dir.mkdir(parents=True, exist_ok=True)

    java_files = [str(p) for p in src.rglob("*.java")] if src.exists() else []
    compile_log = ""
    compiled_ok = False
    if java_files:
        rc, out, err, _ = run_cmd([javac, "-d", str(classes_dir)] + java_files)
        compiled_ok = (rc == 0)
        compile_log = (out or "") + (("\n" + err) if err else "")
    elif has_jar:
        compile_log = "Skipped compilation: using existing run/*.jar"
    else:
        return results, summary, "No .java files in Given/src/ and no run/JAR found."

    summary["Compiled"] = compiled_ok

    main_class = detect_main_class(src)
    summary["MainClass"] = main_class
    student_from_jar = False
    if compiled_ok:
        student_cmd = [java, "-cp", str(classes_dir), main_class]
    elif has_jar:
        student_cmd = [java, "-jar", str(jar)]
        student_from_jar = True
    else:
        return results, summary, "Compilation failed and no run/JAR available."

    tcs = sorted(tcdir.glob("*.txt")) if tcdir.exists() else []
    summary["Total"] = len(tcs)

    for tc in tcs:
        case_name = tc.stem
        exp_path = out_dir/f"{qname}-{case_name}-expected.txt"
        stu_path = out_dir/f"{qname}-{case_name}-student.txt"
        meta_path = out_dir/f"{qname}-{case_name}-meta.json"

        ttext = tc.read_text(encoding="utf-8", errors="ignore")
        tdata = parse_testcase_text(ttext)
        input_text = tdata.get("INPUT") if tdata.get("INPUT") is not None else ttext
        explicit_output = tdata.get("OUTPUT")
        remove_spaces = to_bool(tdata.get("REMOVE_SPACES"), default=defaults.get("RemoveSpaces"))
        case_sensitive = to_bool(tdata.get("CASE_SENSITIVE"), default=defaults.get("CaseSensitive"))
        mark = to_float(tdata.get("MARK"), default=1.0)
        timeout_ms = to_int(tdata.get("TIMEOUT_MS"), default=defaults.get("TimeoutMs"))

        # Expected: prioritize run/Q*.jar when available so prompts match exactly
        expected_from_jar = jar.exists()
        if expected_from_jar:
            rc1, out1, err1, to1 = run_cmd([java, "-jar", str(jar)], input_text=input_text, timeout_ms=timeout_ms)
            exp = out1
        elif explicit_output is not None:
            exp = explicit_output
        else:
            exp = ""
        exp_path.write_text(exp, encoding="utf-8", errors="ignore")

        # Student
        rc2, out2, err2, to2 = run_cmd(student_cmd, input_text=input_text, timeout_ms=timeout_ms)
        stu_path.write_text(out2, encoding="utf-8", errors="ignore")

        empty_out = (out2.strip() == "")
        runtime_error = (rc2 != 0) or (err2.strip() != "")

        passed = apply_compare_rules(
            exp, out2,
            remove_spaces=remove_spaces,
            case_sensitive=case_sensitive,
            whitespace_norm=(remove_spaces is None and case_sensitive is None and not defaults.get("Strict")),
            strict=defaults.get("Strict", False),
            ignore_trailing_per_line=defaults.get("IgnoreTrailingPerLine", False),
        )

        summary["MaxScore"] += mark
        if passed:
            summary["Score"] += mark
            summary["Passed"] += 1

        meta = {
            "ExitCode": rc2,
            "Stderr": err2,
            "Timeout": to2,
            "EmptyOutput": empty_out,
            "RuntimeError": runtime_error,
            "AppliedRules": {
                "RemoveSpaces": remove_spaces,
                "CaseSensitive": case_sensitive,
                "Strict": defaults.get("Strict", False),
                "IgnoreTrailingPerLine": defaults.get("IgnoreTrailingPerLine", False)
            }
        }
        meta_path.write_text(__import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        results.append({
            "Question": qname,
            "TestCase": tc.name,
            "Passed": passed,
            "Mark": mark,
            "ExpectedPath": str(exp_path),
            "StudentPath": str(stu_path),
            "Expected": exp,
            "Got": out2,
            "Compiled": compiled_ok,
            "MainClass": main_class,
            "CompileLog": compile_log,
            "RemoveSpaces": remove_spaces,
            "CaseSensitive": case_sensitive,
            "ExitCode": rc2,
            "Stderr": err2,
            "Timeout": to2,
            "EmptyOutput": empty_out,
            "RuntimeError": runtime_error,
            "ExpectedFromJar": expected_from_jar,
            "StudentFromJar": student_from_jar,
        })

    if summary["MaxScore"] > 0:
        summary["Percent"] = round(100.0 * summary["Score"] / summary["MaxScore"], 2)

    return results, summary, compile_log

def grade_all(root: Path, java_home: str = "", defaults: dict | None = None):
    defaults = defaults or {"Strict": False, "IgnoreTrailingPerLine": False, "RemoveSpaces": None, "CaseSensitive": None, "TimeoutMs": None}
    root = Path(root).resolve()
    out_dir = root/"_grading_out"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    javac, java = find_java_tools(java_home or None)
    questions = [d.name for d in (root).iterdir() if d.is_dir() and d.name.upper().startswith("Q")]
    questions = sorted(questions, key=lambda s: (len(s), s))

    all_results = []
    summaries = []
    messages = []

    for q in questions:
        r, s, msg = grade_question(root, q, javac, java, out_dir, defaults)
        all_results.extend(r)
        summaries.append(s)
        if msg:
            messages.append(f"{q}: {msg}")

    # Write per-question CSV
    for q in set(s["Question"] for s in summaries):
        rows = [r for r in all_results if r["Question"] == q]
        if rows:
            csv_path = out_dir/f"{q}-results.csv"
            with open(csv_path, "w", newline='', encoding="utf-8") as f:
                import csv as _csv
                w = _csv.DictWriter(f, fieldnames=["Question","TestCase","Passed","Mark","ExpectedPath","StudentPath","ExitCode","RuntimeError","EmptyOutput"])
                w.writeheader()
                for row in rows:
                    w.writerow({
                        "Question": row["Question"],
                        "TestCase": row["TestCase"],
                        "Passed": row["Passed"],
                        "Mark": row["Mark"],
                        "ExpectedPath": row["ExpectedPath"],
                        "StudentPath": row["StudentPath"],
                        "ExitCode": row["ExitCode"],
                        "RuntimeError": row["RuntimeError"],
                        "EmptyOutput": row["EmptyOutput"],
                    })

    # Write summary
    with open(out_dir/"summary.csv", "w", newline='', encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Question","Passed","Total","Percent","Compiled","MainClass","Score","MaxScore"])
        w.writeheader()
        for s in summaries:
            w.writerow(s)

    total_score = sum(s["Score"] for s in summaries)
    total_max   = sum(s["MaxScore"] for s in summaries)
    with open(out_dir/"overall.txt", "w", encoding="utf-8") as f:
        f.write(f"Total Score: {total_score} / {total_max}\n")

    return {
        "results": all_results,
        "summaries": summaries,
        "messages": messages,
        "out_dir": str(out_dir),
        "total_score": total_score,
        "total_max": total_max,
    }
