
public class Circle extends Shape {

    private double radius;

    public Circle() {
    }

    public Circle(double radius) {
        this.radius = radius;
        calculateArea();
        calculatePerimeter();
    }

    public void calculateArea() {
        double area = Math.PI * radius * radius;
        setArea(area);
    }

    public void calculatePerimeter() {
        double perimeter = 2 * Math.PI * radius;
        setPerimeter(perimeter);
    }

    @Override
    public String toString() {
        return String.format("%.2f,%.2f", getPerimeter(), getArea());
    }

}
