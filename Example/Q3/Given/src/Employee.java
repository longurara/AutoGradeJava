
public class Employee {

    private int id;
    private String name;
    private double salary;

    public Employee() {
    }

    public Employee(int id, String name, double salary) {
        this.id = id;
        this.name = name;
        this.salary = salary;
    }

    public int getId() {
        return id;
    }

    public String getName() {
        return name.toUpperCase();
    }

    public void setName(String value) {
        this.name = value;
    }

    public double getSalary() {
        return salary;
    }

    public void setSalary(double value) {
        this.salary = value;
    }

    @Override
    public String toString() {
        return String.format("%d,%s,%.2f", id, getName(), salary);
    }
}
