#!/usr/bin/env python3
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import webbrowser
import difflib
import os
import json
import csv
import shutil
import tempfile
import zipfile

from grade_core import grade_all

class GraderUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PE Java Autograder — UI")
        self.geometry("1200x760")

        self.root_var = tk.StringVar(value="")
        self.java_home_var = tk.StringVar(value=os.environ.get("JAVA_HOME", ""))
        self.status_var = tk.StringVar(value="Chọn thư mục gốc chứa Q1..Q4 rồi bấm 'Chấm bài'")
        self.total_var = tk.StringVar(value="")
        # Defaults / overrides
        self.strict_var = tk.BooleanVar(value=False)
        self.ignore_trailing_var = tk.BooleanVar(value=False)
        self.default_rs = tk.StringVar(value="default")  # default/yes/no
        self.default_cs = tk.StringVar(value="default")  # default/yes/no
        self.timeout_ms_var = tk.StringVar(value="")     # optional

        self._build_widgets()

    def _build_widgets(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Thư mục gốc (Root):").grid(row=0, column=0, sticky="w")
        e_root = ttk.Entry(top, textvariable=self.root_var, width=80)
        e_root.grid(row=0, column=1, padx=6, sticky="we")
        ttk.Button(top, text="Chọn...", command=self.choose_root).grid(row=0, column=2)
        ttk.Button(top, text="Chọn ZIP...", command=self.choose_zip).grid(row=0, column=3, padx=(4,0))

        ttk.Label(top, text="JAVA_HOME (tuỳ chọn):").grid(row=1, column=0, sticky="w")
        e_java = ttk.Entry(top, textvariable=self.java_home_var, width=80)
        e_java.grid(row=1, column=1, padx=6, sticky="we")
        ttk.Button(top, text="Chấm bài", command=self.run_grade).grid(row=1, column=2)

        top.columnconfigure(1, weight=1)

        actions = ttk.Frame(self, padding=(10, 0))
        actions.pack(fill="x")
        ttk.Button(actions, text="Tạo testcase...", command=self.open_testcase_dialog).pack(side="left")
        ttk.Button(actions, text="Chấm hàng loạt...", command=self.run_batch_grade).pack(side="left", padx=6)
        ttk.Button(actions, text="Chấm nhiều ZIP...", command=self.run_multi_zip_grade).pack(side="left")

        # Settings
        settings = ttk.Labelframe(self, text="Thiết lập so sánh (mặc định nếu testcase không chỉ rõ)", padding=10)
        settings.pack(fill="x", padx=10)

        ttk.Checkbutton(settings, text="Strict compare (không chuẩn hoá gì)", variable=self.strict_var).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(settings, text="Bỏ khoảng trắng cuối dòng (ignore trailing spaces per line)", variable=self.ignore_trailing_var).grid(row=0, column=1, sticky="w", padx=10)

        ttk.Label(settings, text="Default REMOVE_SPACES:").grid(row=1, column=0, sticky="w", pady=6)
        cb_rs = ttk.Combobox(settings, textvariable=self.default_rs, values=["default","yes","no"], width=10, state="readonly")
        cb_rs.grid(row=1, column=1, sticky="w")
        cb_rs.current(0)

        ttk.Label(settings, text="Default CASE_SENSITIVE:").grid(row=1, column=2, sticky="w", pady=6)
        cb_cs = ttk.Combobox(settings, textvariable=self.default_cs, values=["default","yes","no"], width=10, state="readonly")
        cb_cs.grid(row=1, column=3, sticky="w")
        cb_cs.current(0)

        ttk.Label(settings, text="TIMEOUT_MS (mặc định):").grid(row=1, column=4, sticky="w")
        ttk.Entry(settings, textvariable=self.timeout_ms_var, width=12).grid(row=1, column=5, sticky="w")

        # Results tables (single + batch)
        mid = ttk.Frame(self, padding=10)
        mid.pack(fill="both", expand=True)

        notebook = ttk.Notebook(mid)
        notebook.pack(fill="both", expand=True)

        single_tab = ttk.Frame(notebook)
        notebook.add(single_tab, text="Kết quả đơn lẻ")

        cols = ("Question","TestCase","Passed","Mark","Rules","Runtime")
        self.tree = ttk.Treeview(single_tab, columns=cols, show="headings", selectmode="browse")
        heads = {
            "Question":"Question","TestCase":"TestCase","Passed":"Passed",
            "Mark":"Mark","Rules":"Rules","Runtime":"Runtime"
        }
        widths = {"Question":100,"TestCase":160,"Passed":90,"Mark":80,"Rules":500,"Runtime":180}
        for c in cols:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width=widths[c], anchor="center" if c in ("Passed","Mark") else "w")
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<Double-1>", self.on_open_detail)
        vsb = ttk.Scrollbar(single_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        batch_tab = ttk.Frame(notebook)
        notebook.add(batch_tab, text="Batch ZIP")
        batch_cols = ("StudentID","FullName","Progress","Score","Q1","Q2","Q3","Q4")
        self.batch_tree = ttk.Treeview(batch_tab, columns=batch_cols, show="headings", selectmode="browse")
        batch_heads = {
            "StudentID":"MSSV","FullName":"Họ và tên","Progress":"Tiến độ",
            "Score":"Điểm","Q1":"Q1","Q2":"Q2","Q3":"Q3","Q4":"Q4"
        }
        batch_widths = {"StudentID":140,"FullName":220,"Progress":140,"Score":110,"Q1":60,"Q2":60,"Q3":60,"Q4":60}
        for c in batch_cols:
            self.batch_tree.heading(c, text=batch_heads[c])
            anchor = "center" if c.startswith("Q") or c in ("Progress","Score","StudentID") else "w"
            self.batch_tree.column(c, width=batch_widths[c], anchor=anchor)
        self.batch_tree.pack(fill="both", expand=True, side="left")
        batch_vsb = ttk.Scrollbar(batch_tab, orient="vertical", command=self.batch_tree.yview)
        self.batch_tree.configure(yscrollcommand=batch_vsb.set)
        batch_vsb.pack(side="right", fill="y")
        self.batch_tree.tag_configure("pass", background="#e8ffe8")
        self.batch_tree.tag_configure("fail", background="#ffe8e8")

        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Mở thư mục kết quả", command=self.open_out_dir).pack(side="left")
        ttk.Button(bottom, text="Xem tổng kết", command=self.open_summary).pack(side="left", padx=6)

        ttk.Label(bottom, textvariable=self.total_var, font=("Segoe UI", 10, "bold")).pack(side="right", padx=10)
        ttk.Label(bottom, textvariable=self.status_var).pack(side="right")

        style = ttk.Style(self)
        style.map("Treeview", background=[("selected", "#3a7afe")], foreground=[("selected", "white")])

        self.out_dir = None
        self.detail_cache = {}
        self.batch_items = {}

    def choose_root(self):
        d = filedialog.askdirectory(title="Chọn thư mục gốc chứa Q1..Q4")
        if d:
            self.root_var.set(d)

    def choose_zip(self):
        f = filedialog.askopenfilename(title="Chọn file ZIP chứa Q1..Q4", filetypes=[("ZIP", "*.zip")])
        if f:
            self.root_var.set(f)

    def list_questions(self, base_path: Path | None = None):
        base = base_path or Path(self.root_var.get().strip())
        if not base.exists() or not base.is_dir():
            return []
        questions = [p.name for p in base.iterdir() if p.is_dir() and p.name.upper().startswith("Q")]
        return sorted(questions, key=lambda s: (len(s), s))

    def _defaults(self):
        def parse_opt(x):
            x = (x or "").strip().lower()
            if x in ("yes","no"):
                return (x == "yes")
            return None
        timeout_ms = self.timeout_ms_var.get().strip()
        try:
            timeout_ms = int(timeout_ms) if timeout_ms else None
        except Exception:
            timeout_ms = None
        return {
            "Strict": bool(self.strict_var.get()),
            "IgnoreTrailingPerLine": bool(self.ignore_trailing_var.get()),
            "RemoveSpaces": parse_opt(self.default_rs.get()),
            "CaseSensitive": parse_opt(self.default_cs.get()),
            "TimeoutMs": timeout_ms,
        }

    def _looks_like_question_root(self, folder: Path) -> bool:
        try:
            return any(p.is_dir() and p.name.upper().startswith("Q") for p in folder.iterdir())
        except Exception:
            return False

    def _guess_root_in_dir(self, base: Path) -> Path | None:
        if self._looks_like_question_root(base):
            return base
        for child in base.iterdir():
            if child.is_dir() and self._looks_like_question_root(child):
                return child
        return None

    def _prepare_root_path(self, root_value: str):
        path = Path(root_value)
        if path.is_dir():
            return {"root": path, "cleanup": None, "zip_source": None}
        if path.is_file() and path.suffix.lower() == ".zip":
            temp_base = Path(tempfile.mkdtemp(prefix="autograde_zip_"))
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(temp_base)
            except Exception as ex:
                shutil.rmtree(temp_base, ignore_errors=True)
                raise RuntimeError(f"Giải nén ZIP thất bại: {ex}")
            guessed = self._guess_root_in_dir(temp_base) or temp_base
            return {"root": guessed, "cleanup": temp_base, "zip_source": path}
        raise FileNotFoundError("Không tìm thấy thư mục hoặc ZIP hợp lệ.")

    def _relocate_zip_results(self, zip_source: Path, data: dict):
        out_dir = data.get("out_dir")
        if not out_dir:
            return None
        src = Path(out_dir)
        dest = zip_source.with_name(f"{zip_source.stem}_grading_out")
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        shutil.move(str(src), dest)
        new_path = str(dest)
        prefix = str(src)
        for r in data.get("results", []):
            for key in ("ExpectedPath","StudentPath"):
                val = r.get(key)
                if isinstance(val, str) and val.startswith(prefix):
                    r[key] = new_path + val[len(prefix):]
        data["out_dir"] = new_path
        return new_path

    def _parse_zip_name(self, stem: str):
        parts = stem.split("_", 1)
        student_id = parts[0].strip()
        full_name = parts[1].replace("_", " ").strip() if len(parts) > 1 else ""
        return student_id, full_name

    def _extract_question_passes(self, summaries):
        res = {}
        lookup = { (s.get("Question") or "").upper(): s for s in (summaries or []) }
        for idx in range(1, 5):
            key = f"Q{idx}"
            summ = lookup.get(key.upper())
            if not summ or summ.get("MaxScore", 0.0) == 0:
                res[key] = ""
                continue
            res[key] = bool(abs(summ.get("Score", 0.0) - summ.get("MaxScore", 0.0)) < 1e-6)
        return res

    def _format_bool(self, value):
        if value is True:
            return "TRUE"
        if value is False:
            return "FALSE"
        return ""

    def run_grade(self):
        root_value = self.root_var.get().strip()
        if not root_value:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn thư mục gốc chứa Q1..Q4 hoặc file ZIP")
            return
        try:
            prep = self._prepare_root_path(root_value)
        except Exception as exc:
            messagebox.showerror("Lỗi", str(exc))
            return

        self.status_var.set("Đang chấm...")
        self.tree.delete(*self.tree.get_children())
        self.detail_cache.clear()
        self.out_dir = None
        self.total_var.set("")

        def worker():
            cleanup_root = prep.get("cleanup")
            zip_source = prep.get("zip_source")
            try:
                data = grade_all(prep["root"], self.java_home_var.get().strip(), defaults=self._defaults())
                if zip_source:
                    self._relocate_zip_results(zip_source, data)
                self.out_dir = data.get("out_dir")
                results = data.get("results", [])
                for r in results:
                    rules = f"RS={'YES' if r['RemoveSpaces'] else 'NO' if r['RemoveSpaces'] is not None else 'default'}; "                             f"CS={'YES' if r['CaseSensitive'] else 'NO' if r['CaseSensitive'] is not None else 'default'}; "                             f"Strict={self.strict_var.get()}; IgnoreTrail={self.ignore_trailing_var.get()}"
                    runtime = f"Exit={r['ExitCode']}; Error={r['RuntimeError']}; Empty={r['EmptyOutput']}; Timeout={r['Timeout']}"
                    values = (r["Question"], r["TestCase"], "PASS" if r["Passed"] else "FAIL", f"{r['Mark']}", rules, runtime)
                    item_id = self.tree.insert("", "end", values=values)
                    self.tree.item(item_id, tags=("pass",) if r["Passed"] else ("fail",))
                    self.detail_cache[(r["Question"], r["TestCase"])] = r

                self.tree.tag_configure("pass", background="#e8ffe8")
                self.tree.tag_configure("fail", background="#ffe8e8")

                total_score = data.get("total_score", 0.0)
                total_max   = data.get("total_max", 0.0)
                self.total_var.set(f"Tổng điểm: {total_score} / {total_max}")
                self.status_var.set(f"Hoàn tất. Kết quả tại: {self.out_dir}")
            except Exception as e:
                self.status_var.set("Có lỗi khi chấm.")
                messagebox.showerror("Lỗi", str(e))
            finally:
                if cleanup_root:
                    shutil.rmtree(cleanup_root, ignore_errors=True)

        threading.Thread(target=worker, daemon=True).start()

    def open_testcase_dialog(self):
        root = self.root_var.get().strip()
        if not root:
            messagebox.showwarning("Thiếu thông tin", "Hãy chọn thư mục gốc trước khi tạo testcase.")
            return
        root_path = Path(root)
        if not root_path.exists() or not root_path.is_dir():
            messagebox.showwarning("Không hỗ trợ", "Chỉ tạo testcase trên thư mục, không phải file ZIP.")
            return
        questions = self.list_questions(root_path)
        if not questions:
            messagebox.showwarning("Không tìm thấy", "Thư mục gốc không có cấu trúc Q1..Qn.")
            return
        TestcaseDialog(self, root_path, questions)

    def run_batch_grade(self):
        parent = filedialog.askdirectory(title="Chọn thư mục chứa nhiều bài cần chấm")
        if not parent:
            return
        parent_path = Path(parent)
        child_dirs = [p for p in parent_path.iterdir() if p.is_dir() and not p.name.startswith("_")]
        if not child_dirs:
            messagebox.showwarning("Không tìm thấy", "Thư mục này không chứa bài nộp con.")
            return
        java_home = self.java_home_var.get().strip()
        defaults_template = self._defaults()
        self.status_var.set(f"Đang chấm hàng loạt trong {parent_path} ...")

        def worker():
            rows = []
            for folder in sorted(child_dirs, key=lambda p: p.name):
                entry = {"Student": folder.name, "Score": "", "Max": "", "Percent": "", "OutDir": "", "Error": ""}
                try:
                    q_dirs = [c for c in folder.iterdir() if c.is_dir() and c.name.upper().startswith("Q")]
                    if not q_dirs:
                        raise RuntimeError("Không tìm thấy thư mục Q* trong bài nộp này.")
                    data = grade_all(folder, java_home, defaults=defaults_template.copy())
                    score = data.get("total_score", 0.0)
                    max_score = data.get("total_max", 0.0)
                    percent = round(100.0 * score / max_score, 2) if max_score else 0.0
                    entry.update({
                        "Score": score,
                        "Max": max_score,
                        "Percent": percent,
                        "OutDir": data.get("out_dir", ""),
                        "Error": ""
                    })
                except Exception as ex:
                    entry["Error"] = str(ex)
                rows.append(entry)
            summary_path = parent_path / "_batch_summary.csv"
            with open(summary_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Student","Score","Max","Percent","OutDir","Error"])
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
            self.after(0, lambda: self._after_batch(summary_path, rows))

        threading.Thread(target=worker, daemon=True).start()

    def _after_batch(self, summary_path, rows):
        ok = sum(1 for r in rows if not r["Error"])
        fail = len(rows) - ok
        self.status_var.set(f"Chấm hàng loạt xong: {ok} OK, {fail} lỗi. Kết quả: {summary_path}")
        messagebox.showinfo("Hoàn tất", f"Đã tạo file tổng hợp: {summary_path}\nThành công: {ok}  Lỗi: {fail}")

    def run_multi_zip_grade(self):
        files = filedialog.askopenfilenames(title="Chọn nhiều file ZIP", filetypes=[("ZIP","*.zip")])
        if not files:
            return
        java_home = self.java_home_var.get().strip()
        defaults = self._defaults()
        self.status_var.set(f"Đang chấm {len(files)} ZIP...")

        self.batch_tree.delete(*self.batch_tree.get_children())
        self.batch_items = {}
        paths = [Path(f) for f in files]
        for zip_path in paths:
            student_id, full_name = self._parse_zip_name(zip_path.stem)
            iid = self.batch_tree.insert("", "end", values=(student_id, full_name, "Chờ", "", "", "", "", ""))
            self.batch_items[str(zip_path)] = iid

        def worker():
            rows = []
            for zip_path in paths:
                student_id, full_name = self._parse_zip_name(zip_path.stem)
                entry = {
                    "StudentID": student_id,
                    "FullName": full_name,
                    "Q1": "",
                    "Q2": "",
                    "Q3": "",
                    "Q4": "",
                    "Score": "",
                    "Max": "",
                    "Error": "",
                }
                try:
                    self.after(0, self._update_batch_row, str(zip_path), {"Progress":"Đang chấm"})
                    prep = self._prepare_root_path(str(zip_path))
                    try:
                        data = grade_all(prep["root"], java_home, defaults=defaults.copy())
                        if prep["zip_source"]:
                            self._relocate_zip_results(prep["zip_source"], data)
                        entry["Score"] = data.get("total_score", 0.0)
                        entry["Max"] = data.get("total_max", 0.0)
                        entry.update(self._extract_question_passes(data.get("summaries")))
                        entry["Progress"] = "Hoàn tất"
                    finally:
                        cleanup = prep.get("cleanup")
                        if cleanup:
                            shutil.rmtree(cleanup, ignore_errors=True)
                except Exception as ex:
                    entry["Error"] = str(ex)
                    entry["Progress"] = "Lỗi"
                rows.append(entry)
                self.after(0, self._update_batch_row, str(zip_path), entry)

            summary_path = paths[0].parent / "_KetQua.csv"
            fields = ["StudentID","FullName","Q1","Q2","Q3","Q4","Score","Max","Error"]
            with open(summary_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for row in rows:
                    row_out = {k: row.get(k, "") for k in fields}
                    for key in ("Q1","Q2","Q3","Q4"):
                        row_out[key] = self._format_bool(row_out[key])
                    writer.writerow(row_out)
            self.after(0, lambda: self._after_multi_zip(summary_path, rows))

        threading.Thread(target=worker, daemon=True).start()

    def _after_multi_zip(self, summary_path, rows):
        ok = sum(1 for r in rows if not r["Error"])
        fail = len(rows) - ok
        self.status_var.set(f"Chấm ZIP xong: {ok} OK, {fail} lỗi. File: {summary_path}")
        messagebox.showinfo("Hoàn tất", f"Đã xuất: {summary_path}\nThành công: {ok}  Lỗi: {fail}")

    def _update_batch_row(self, zip_key, entry):
        iid = self.batch_items.get(zip_key)
        if not iid:
            return
        values = list(self.batch_tree.item(iid, "values"))
        if "Progress" in entry:
            values[2] = entry["Progress"]
        if "Score" in entry and entry["Score"] != "":
            max_score = entry.get("Max")
            score_val = entry.get("Score", "")
            values[3] = f"{score_val} / {max_score}" if max_score not in (None, "") else str(score_val)
        for idx, key in enumerate(("Q1","Q2","Q3","Q4"), start=4):
            if key in entry:
                values[idx] = self._format_bool(entry[key])
        self.batch_tree.item(iid, values=values)
        if entry.get("Error"):
            self.batch_tree.item(iid, tags=("fail",))
        elif entry.get("Progress") == "Hoàn tất":
            self.batch_tree.item(iid, tags=("pass",))

    def on_open_detail(self, event):
        sel = self.tree.focus()
        if not sel:
            return
        values = self.tree.item(sel, "values")
        if not values:
            return
        q, tc, *_ = values
        key = (q, tc)
        if key not in self.detail_cache:
            return
        r = self.detail_cache[key]
        DetailWindow(self, r)

    def open_out_dir(self):
        if self.out_dir and os.path.isdir(self.out_dir):
            if os.name == "nt":
                os.startfile(self.out_dir)
            else:
                webbrowser.open(f"file://{self.out_dir}")
        else:
            messagebox.showinfo("Thông tin", "Chưa có kết quả để mở. Hãy chấm trước.")

    def open_summary(self):
        if not self.out_dir:
            messagebox.showinfo("Thông tin", "Chưa có kết quả để mở. Hãy chấm trước.")
            return
        summary = Path(self.out_dir)/"summary.csv"
        if summary.exists():
            if os.name == "nt":
                os.startfile(str(summary))
            else:
                webbrowser.open(f"file://{summary}")
        else:
            messagebox.showinfo("Thông tin", "Chưa tìm thấy summary.csv")

class DetailWindow(tk.Toplevel):
    def __init__(self, master, r):
        super().__init__(master)
        self.title(f"Chi tiết — {r['Question']} / {r['TestCase']}")
        self.geometry("1200x850")

        info = ttk.Frame(self, padding=8)
        info.pack(fill="x")
        ttk.Label(info, text=f"Compiled: {'YES' if r['Compiled'] else 'NO'} — MainClass: {r['MainClass']} — Mark: {r['Mark']}").pack(side="left")

        runtime_line = f"ExitCode={r['ExitCode']}  RuntimeError={r['RuntimeError']}  EmptyOutput={r['EmptyOutput']}  Timeout={r['Timeout']}"
        ttk.Label(self, text=runtime_line, foreground="#555").pack(anchor="w", padx=10)

        btns = ttk.Frame(self, padding=8)
        btns.pack(fill="x")
        ttk.Button(btns, text="Mở Expected", command=lambda: self.open_path(r["ExpectedPath"])).pack(side="left")
        ttk.Button(btns, text="Mở Student", command=lambda: self.open_path(r["StudentPath"])).pack(side="left", padx=6)
        if not r["Compiled"] and r["CompileLog"]:
            ttk.Button(btns, text="Xem Compile Log", command=lambda: self.show_text("Compile Log", r["CompileLog"])).pack(side="left", padx=6)
        if r["Stderr"]:
            ttk.Button(btns, text="Xem Stderr", command=lambda: self.show_text("Stderr", r["Stderr"])).pack(side="left", padx=6)

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(paned)
        ttk.Label(left, text="Expected").pack(anchor="w")
        self.txt_expected = tk.Text(left, wrap="word")
        self.txt_expected.pack(fill="both", expand=True)
        self.txt_expected.insert("1.0", r["Expected"] or "")
        paned.add(left, weight=1)

        right = ttk.Frame(paned)
        ttk.Label(right, text="Got (Student)").pack(anchor="w")
        self.txt_got = tk.Text(right, wrap="word")
        self.txt_got.pack(fill="both", expand=True)
        self.txt_got.insert("1.0", r["Got"] or "")
        paned.add(right, weight=1)

        diff_frame = ttk.Frame(self, padding=8)
        diff_frame.pack(fill="both", expand=True)
        ttk.Label(diff_frame, text="Diff:").pack(anchor="w")
        self.txt_diff = tk.Text(diff_frame, wrap="none", height=16)
        self.txt_diff.pack(fill="both", expand=True)
        self.show_colored_diff(r["Expected"] or "", r["Got"] or "")

    def show_colored_diff(self, expected, got):
        # Colored character-level diff
        sm = difflib.SequenceMatcher(None, expected, got)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            s1 = expected[i1:i2]
            s2 = got[j1:j2]
            if tag == "equal":
                self.txt_diff.insert("end", s1)
            elif tag == "delete":
                self.txt_diff.insert("end", s1, ("del",))
            elif tag == "insert":
                self.txt_diff.insert("end", s2, ("ins",))
            elif tag == "replace":
                self.txt_diff.insert("end", s1, ("del",))
                self.txt_diff.insert("end", s2, ("ins",))
        # Tag styles
        self.txt_diff.tag_configure("del", background="#ffe0e0")
        self.txt_diff.tag_configure("ins", background="#e0ffe0")

    def open_path(self, p):
        if not p: return
        if os.name == "nt":
            os.startfile(p)
        else:
            webbrowser.open(f"file://{p}")

    def show_text(self, title, content):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("900x600")
        txt = tk.Text(win, wrap="word")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", content)

class TestcaseDialog(tk.Toplevel):
    def __init__(self, master, root_path: Path, questions):
        super().__init__(master)
        self.title("Tạo testcase mới")
        self.geometry("700x650")
        self.root_path = root_path
        self.questions = questions

        form = ttk.Frame(self, padding=10)
        form.pack(fill="both", expand=True)

        ttk.Label(form, text="Question:").grid(row=0, column=0, sticky="w")
        self.q_var = tk.StringVar(value=questions[0])
        ttk.Combobox(form, textvariable=self.q_var, values=questions, state="readonly", width=10).grid(row=0, column=1, sticky="w")

        ttk.Label(form, text="Tên file (vd: tc4)").grid(row=1, column=0, sticky="w", pady=6)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=20).grid(row=1, column=1, sticky="w")

        ttk.Label(form, text="INPUT").grid(row=2, column=0, sticky="w")
        self.txt_input = tk.Text(form, height=8, width=60)
        self.txt_input.grid(row=2, column=1, columnspan=3, pady=4, sticky="nsew")

        ttk.Label(form, text="OUTPUT").grid(row=3, column=0, sticky="w")
        self.txt_output = tk.Text(form, height=6, width=60)
        self.txt_output.grid(row=3, column=1, columnspan=3, pady=4, sticky="nsew")

        ttk.Label(form, text="REMOVE_SPACES").grid(row=4, column=0, sticky="w", pady=4)
        self.rs_var = tk.StringVar(value="default")
        ttk.Combobox(form, textvariable=self.rs_var, values=["default","yes","no"], state="readonly", width=10).grid(row=4, column=1, sticky="w")

        ttk.Label(form, text="CASE_SENSITIVE").grid(row=4, column=2, sticky="w")
        self.cs_var = tk.StringVar(value="default")
        ttk.Combobox(form, textvariable=self.cs_var, values=["default","yes","no"], state="readonly", width=10).grid(row=4, column=3, sticky="w")

        ttk.Label(form, text="MARK").grid(row=5, column=0, sticky="w", pady=4)
        self.mark_var = tk.StringVar(value="1.0")
        ttk.Entry(form, textvariable=self.mark_var, width=10).grid(row=5, column=1, sticky="w")

        ttk.Label(form, text="TIMEOUT_MS").grid(row=5, column=2, sticky="w")
        self.timeout_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.timeout_var, width=10).grid(row=5, column=3, sticky="w")

        btns = ttk.Frame(form, padding=10)
        btns.grid(row=6, column=0, columnspan=4, sticky="e")
        ttk.Button(btns, text="Lưu", command=self.save).pack(side="right")
        ttk.Button(btns, text="Hủy", command=self.destroy).pack(side="right", padx=6)

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

    def save(self):
        q = self.q_var.get()
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Thiếu thông tin", "Nhập tên file testcase.")
            return
        if not name.lower().endswith(".txt"):
            name += ".txt"
        input_text = self.txt_input.get("1.0", "end").strip("\n")
        output_text = self.txt_output.get("1.0", "end").strip("\n")
        if not input_text or not output_text:
            messagebox.showwarning("Thiếu thông tin", "INPUT và OUTPUT không được để trống.")
            return
        mark = self.mark_var.get().strip() or "1.0"
        timeout = self.timeout_var.get().strip()
        sections = []
        sections.append(f"INPUT:\n{input_text}")
        sections.append(f"OUTPUT:\n{output_text}")
        if self.rs_var.get() != "default":
            sections.append(f"REMOVE_SPACES:\n{self.rs_var.get().upper()}")
        if self.cs_var.get() != "default":
            sections.append(f"CASE_SENSITIVE:\n{self.cs_var.get().upper()}")
        sections.append(f"MARK:\n{mark}")
        if timeout:
            sections.append(f"TIMEOUT_MS:\n{timeout}")
        content = "\n".join(sections).rstrip() + "\n"

        target = self.root_path / q / "TestCases" / name
        if target.exists():
            if not messagebox.askyesno("Ghi đè", f"{target} đã tồn tại. Ghi đè?"):
                return
        target.write_text(content, encoding="utf-8")
        messagebox.showinfo("Thành công", f"Đã tạo testcase: {target}")
        self.destroy()


if __name__ == "__main__":
    app = GraderUI()
    app.mainloop()
