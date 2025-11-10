
public class MyUtilities implements IUtilities {

    @Override
    public int checkNumber(String value) {
        try {
            int num = Integer.parseInt(value);
            return num * num;
        } catch (NumberFormatException e) {
            return value.length();
        }
    }

    @Override
    public int sumNumber(String value) {
        int sum = 0;
        for (char ch : value.toCharArray()) {
            if (Character.isDigit(ch)) {
                sum += Character.getNumericValue(ch);
            }
        }
        return sum;
    }

    public int checkIntegerNumber(String value, int min, int max) {
        try {
            int num = Integer.parseInt(value);
            if (num >= min && num <= max) {
                return num * num;
            } else {
                return -1;
            }
        } catch (NumberFormatException e) {
            return value.length();
        }
    }
}
