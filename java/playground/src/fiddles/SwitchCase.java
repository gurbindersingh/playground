package fiddles;

public class SwitchCase {

  public static void main(String[] args) {
    int a = 2;

    switch (a) {
      case 0 -> System.out.println("Zero");
      case 1 -> System.out.println("One");
    }
  }
}
