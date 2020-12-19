package leetcode;

public class ReverseInteger {

    public static int reverse(int x) {
        boolean wasNegative = x < 0;
        int xCopy = Math.abs(x);
        long reversed = 0;

        while (xCopy != 0) {
            reversed = reversed * 10 + xCopy % 10;
            xCopy /= 10;
        }
        reversed = reversed < Integer.MIN_VALUE || reversed > Integer.MAX_VALUE ? 0 : reversed;
        reversed = wasNegative ? (-1) * reversed : reversed;

        return (int) reversed;
    }
}
