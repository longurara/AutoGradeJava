
public class Bike {

    private int id;
    private String name;
    private double price;

    public Bike() {
    }

    public Bike(int id, String name, double price) {
        this.id = id;
        this.name = name;
        this.price = price;
    }

    public String getName() {
        return name.toUpperCase();
    }

    public int getId() {
        return id;
    }

    public double getPrice() {
        return price;
    }

    public double getSalePrice() {
        return price + price * 0.1;
    }

    @Override
    public String toString() {
        return id + "," + name.toUpperCase() + "," + String.format("%.2f", price);
    }

}
