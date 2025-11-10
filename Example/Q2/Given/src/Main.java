
import java.util.Scanner;


/**
 *
 * @author Kiem Ho
 */
public class Main {
    public static void main(String[] args) {
        int tc;       
        double radius;
        Scanner sc = new Scanner(System.in);       
        System.out.print("Enter radius:");
        radius = Double.parseDouble(sc.nextLine());             
        System.out.println("1.Test calculatePerimeter()");
        System.out.println("2.Test calculateArea()");
        System.out.println("3.Test toString()");
        System.out.print("Enter TC(1/2/3):");
        tc = sc.nextInt();     
        Circle c= new Circle(radius);
        System.out.println("OUTPUT:");
        if(tc == 1){            
             c.calculatePerimeter();
             System.out.format("%.2f\n",c.getPerimeter());
        }
        else if(tc == 2){              
             c.calculateArea();
             System.out.format("%.2f\n",c.getArea());
        }
        else if(tc==3){                      
            System.out.println(c);
        }
    }
}
