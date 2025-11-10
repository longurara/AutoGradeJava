


import java.util.Scanner;


public class Main {

    
    public static void main(String[] args) {
        int id, tc;
        String name;     
        double price;
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter id:");
        id = Integer.parseInt(sc.nextLine());
        System.out.print("Enter name:");
        name = sc.nextLine();
        System.out.print("Enter price:");
        price = Double.parseDouble(sc.nextLine());         
        Bike p = new Bike(id, name, price);
        System.out.println("1.Test getSalePrice()");
        System.out.println("2.Test getName");
        System.out.println("3.Test toString()");
        System.out.print("Enter TC(1/2/3):");
        tc = sc.nextInt();       
        if(tc == 1){
             System.out.println("OUTPUT:");
             System.out.format("%.2f\n",p.getSalePrice());
        }
        else if(tc == 2){                 
             System.out.println("OUTPUT:");            
             System.out.println(p.getName());
        }
        else if(tc == 3){             
             System.out.println("OUTPUT:");
             System.out.format("%s\n",p.toString());
        }

    }
    
}
