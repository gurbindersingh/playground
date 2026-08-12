package leetcode;

import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static java.util.stream.Collectors.toList;

public class RomanToInteger {

    static int romanToInt(String s) {
        Map<Character, Integer> mapping = new HashMap<>();
        mapping.put('I', 1);
        mapping.put('V', 5);
        mapping.put('X', 10);
        mapping.put('L', 50);
        mapping.put('C', 100);
        mapping.put('D', 500);
        mapping.put('M', 1000);
        int result = 0;

        for (int i = 0; i < s.length(); ) {
            int numLeft = mapping.get(s.charAt(i));
            int numRight = (i + 1) < s.length() ? mapping.get(s.charAt(i + 1)) : 0;

            if (numLeft < numRight) {
                result += numRight - numLeft;
                i += 2;
            } else {
                result += numLeft;
                i++;
            }
        }
        return result;
    }
}
