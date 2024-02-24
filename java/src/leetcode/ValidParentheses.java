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
            // Because just one parenthesis is invalid
            return false;
        } else if (parenString.isEmpty()) {
            return true;
        }

        char[] parentheses = parenString.toCharArray();
        Deque<Character> stack = new ArrayDeque<>();
        Map<Character, Character> parenMap = new HashMap<>();
        parenMap.put(')', '(');
        parenMap.put('}', '{');
        parenMap.put(']', '[');

        for (char parenthesis : parentheses) {
            Character matchingParenthesis = parenMap.get(parenthesis);
            boolean isOpeningParenthesis = matchingParenthesis == null;

            if (isOpeningParenthesis) {
                stack.push(parenthesis);
            } else if (stack.isEmpty() || !stack.pop().equals(matchingParenthesis)) {
                return false;
            }
        }
        return stack.isEmpty();
    }
}
