
import java.util.ArrayList;

public class EmployeeList extends ArrayList<Employee> {

    public String getNameById(int id) {
        for (Employee e : this) {
            if (e.getId() == id) {
                return e.getName();
            }
        }
        return "Not found";
    }

    public Employee getEmployeeWithMaxSalary() {
        if (this.isEmpty()) {
            return null;
        }

        Employee maxEmp = this.get(0);
        for (Employee e : this) {
            if (e.getSalary() > maxEmp.getSalary()) {
                maxEmp = e;
            }
        }
        return maxEmp;
    }
}
