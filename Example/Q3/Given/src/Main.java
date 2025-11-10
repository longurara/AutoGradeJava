

import java.util.Scanner;

/**
 *
 * @author Kiem Ho
 */
public class Main {

    public static EmployeeList createEmployeeList() {
        EmployeeList employeeList = new EmployeeList();
        employeeList.add(new Employee(100, "Hoang An", 50));
        employeeList.add(new Employee(101, "Quang Khanh", 70));
        employeeList.add(new Employee(102, "Thanh Tien", 60));
        employeeList.add(new Employee(103, "Quoc Thuan", 80));
        employeeList.add(new Employee(104, "Minh Thanh", 90));
        employeeList.add(new Employee(105, "Dang Khoa", 100));
        return employeeList;
    }
    //--------------------------------------------------------------
    public static void printEmployeeList(EmployeeList employeeList) {
        for (Employee e : employeeList) {
            System.out.println(e);
        }
    }
    //--------------------------------------------------------------
    public static void main(String[] args) {
        int tc, id;
        double salary;
        String name;
        Scanner sc = new Scanner(System.in);
        EmployeeList employeeList = createEmployeeList();
        System.out.println("The employees have been added:");
        printEmployeeList(employeeList);
        System.out.println("Add a new Employees:");        
        System.out.print("Enter id:");
        id = Integer.parseInt(sc.nextLine());
        System.out.print("Enter name:");
        name = sc.nextLine();
        System.out.print("Enter salary:");
        salary = Double.parseDouble(sc.nextLine());
        Employee item = new Employee(id, name, salary);
        employeeList.add(item);
        System.out.println("1.Test getNameById()");
        System.out.println("2.Test getEmployeeWithMaxSalary()");
        System.out.print("Enter TC(1/2):");
        tc = Integer.parseInt(sc.nextLine());
        if (tc == 1) {
            System.out.print("Enter id:");
            id = Integer.parseInt(sc.nextLine());
            System.out.println("OUTPUT:");
            System.out.format("%s\n", employeeList.getNameById(id));
        } else if (tc == 2) {
            System.out.println("OUTPUT:");
            System.out.println(employeeList.getEmployeeWithMaxSalary());
        }
    }
}
