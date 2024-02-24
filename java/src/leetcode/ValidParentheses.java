package leetcode;

import java.util.*;

public class ValidParentheses {


    // My initial thought was to assign positive numbers for opening and
    // negative for closing parenthesis. Then add up the values and check if
    // the sum is zero. This does not work. Assuming we assign `(` the value
    // 1, and `}` the value -3, then "(((}" would be a valid string.


    public static void main(String[] args) {
        System.out.println(isValid("()(())({})[]{}"));
    }


    public static boolean isValid(String parenString) {
        if (parenString.length() == 1) {
            // Because just one paranthesis is invalid
            return false;
        } else if (parenString.length() == 0) {
            return true;
        }

        char[] parans = parenString.toCharArray();
        Deque<Character> stack = new ArrayDeque<>();
        Map<Character, Character> paranMap = new HashMap<>();
        paranMap.put(')', '(');
        paranMap.put('}', '{');
        paranMap.put(']', '[');

        for (char paran : parans) {
            Character mappedParan = paranMap.get(paran);

            if (mappedParan == null) {
                stack.push(paran);
            } else if (stack.isEmpty() || stack.pop() != mappedParan) {
                return false;
            }
        }
        return 0 == stack.size();
    }
}
