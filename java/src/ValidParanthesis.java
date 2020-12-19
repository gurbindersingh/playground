package leetcode;

import java.util.*;

public class ValidParanthesis {

    public static boolean isValid(String s) {
        if (s.length() == 1) {
            // Because just one paranthesis is invalid
            return false;
        } else if (s.length() == 0) {
            return true;
        }

        char[] parans = s.toCharArray();
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
