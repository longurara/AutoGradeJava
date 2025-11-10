
import java.util.Scanner;

/**
 *
 * @author Kiem Ho
 */
public class Main {        
    public static void main(String[] args) {
        int tc;              
        String value = "";
        MyUtilities obj = new MyUtilities();  
        System.out.println("1.Test checkIntegerNumber");   
        System.out.println("2.Test sumNumber");
        System.out.print("Enter Test Case No.(1/2):");
        Scanner sc = new Scanner(System.in);
        tc = Integer.parseInt(sc.nextLine());          
        if (tc == 1) {                    
            System.out.print("Enter a string:");            
            value = sc.nextLine();   
            System.out.println("OUTPUT:");
            System.out.format("%d\n",obj.checkNumber(value));       
        }else if (tc == 2) {       
            value = sc.nextLine();            
            System.out.println("OUTPUT:");
           System.out.format("%d\n",obj.sumNumber(value));  
            
            
        } 
        sc.close();
    }
}
