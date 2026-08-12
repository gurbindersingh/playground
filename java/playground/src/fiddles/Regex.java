package fiddles;

import java.util.List;

public class Regex {

    public static void main(String[] args) {
        matchURL();
    }


    public static void matchURL() {
        final String url = "https://example.com/some/path";
        final String[] splitUrl = url.split("//")[1].split("/")[0].split("\\.");
        System.out.println(List.of(splitUrl));
    }
}
