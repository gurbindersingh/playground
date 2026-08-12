package fiddles;

public class AdjacencyMatrixGenerator {

  public static void main(String[] args) {
    int n = 400;
    for (int i = 0; i < n; i++) {
      long count = 0;
      System.out.print("{ ");

      for (int j = 0; j < n; j++) {
        long adj = Math.round(Math.random());
        count += adj;
        System.out.print(adj + (j + 1 >= n ? " }," : ", "));
      }
      System.out.println();
    }
  }
}
