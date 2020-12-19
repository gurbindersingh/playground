function sumSquareDifference(n) {
  let sum = 0;
  let squareSum = 0;
  
  for (let i = 1; i <= n; i++) {
    sum += i;
    squareSum += i * i;
  }
  
  return squareSum - sum * sum;
}

sumSquareDifference(100);
