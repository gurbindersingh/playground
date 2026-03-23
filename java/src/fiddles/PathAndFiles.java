package fiddles;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class PathAndFiles {

    public static void main(String[] args) throws IOException {
        pathValidation();
        emptyPath();
    }


    public static void fileSystemTraversal() throws IOException {
        Files.walk(Paths.get("/app")).forEach(path -> System.out.println(path));
    }


    public static void resolvePaths() throws IOException {
        System.out.println(Files.list(Paths.get("/data").resolve("local").resolve("devdata"))
                                .map(path -> path.toString())
                                .toList());

    }


    public static void pathValidation() {
        Path dataDirectory = Paths.get("/tmp/data").toAbsolutePath().normalize();
        Path tenantRoot = dataDirectory.resolve("tenants").resolve("1");

        String[] paths = {
            // Normal paths
            "documents/2026/03/18/doc-abc/file.pdf",
            "assets/logo",
            "llm-messages/case-42",
            // Traversal: escape tenant dir into another tenant
            "../../2/documents/stolen/secret.pdf",
            // Traversal: escape data directory entirely
            "../../../../etc/passwd",
            // Sneaky: goes up then back down
            "../1/documents/legit/file.pdf",
            // Traversal in filename component
            "documents/2026/03/18/doc-abc/../../../../../../etc/passwd",
            };

        for (String p : paths) {
            Path resolved = tenantRoot.resolve(p).toAbsolutePath().normalize();
            boolean withinTenant = resolved.startsWith(tenantRoot);
            boolean withinDataDir = resolved.startsWith(dataDirectory);
            System.out.printf(
                "%-65s tenant=%-5s dataDir=%-5s -> %s%n",
                p, withinTenant, withinDataDir, resolved
            );
        }
    }


    public static void emptyPath() {
        System.out.println("Empty path: '" + Paths.get("") + "'");
    }
}
