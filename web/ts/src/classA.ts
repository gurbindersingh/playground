export class ClassA {
  private privateField: number;
  nonPrivateField: string;

  constructor(a: number, b: string) {
    this.privateField = a;
    this.nonPrivateField = b;
  }

  print() {
    console.log(
      "ClassA(privateField=",
      this.privateField,
      ", nonPrivateField=",
      this.nonPrivateField,
      ")"
    );
  }

  private className() {
    return Class
  }
}
