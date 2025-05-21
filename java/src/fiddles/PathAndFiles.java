package fiddles;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class PathAndFiles {

    public static void main(String[] args) throws IOException {
       fileSystemTraversal();
    }

    public static void fileSystemTraversal() throws IOException {
        Files.walk(Paths.get("/app")).forEach(path -> System.out.println(path));
    }

    public static void resolvePaths() throws IOException {
        System.out.println(Files.list(Paths.get("/data").resolve("local").resolve("devdata"))
                                .map(path -> path.toString())
                                .toList());

    }
}
