#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

// COMPILE USING THE FOLLOWING SYNTAX: gcc INFILE -fopenmp -o OUTFILE

void printarray(int *array, int n)
{
  printf("[ ");
  for (int i = 0; i < n; i++)
  {
    printf("%4d", array[i]);
    if (i + 1 < n)
      printf(" | ");
  }
  printf(" ]\n");
}

int main()
{
  printf("\n=========================================================\n");
  printf("=== Exercise 1.4: Reduction for associative operation ===\n");
  printf("=========================================================\n");
  int arr[] = {2, 3, 5, 7, 11, 13, 17, 19, 23 /*, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97 */};
  int n = (sizeof arr) / (sizeof arr[0]);
  int nn = n;
  int k = 1;
  int sum = 0;

  for (int i = 0; i < n; i++)
  {
    sum += arr[i];
  }
  printf("sum: %d\n\n", sum);

  printf("nn: %d\n", nn);
  printarray(arr, n);
  while (nn > 1)
  {
    int p = (nn >> 1) + (nn & 1); // REMINDER: the `&` is the AND bit operator

#pragma omp parallel num_threads(n / 2)
    {
      int i = omp_get_thread_num();
      int ki2 = 2 * k * i;
      if ((ki2 + k) < n)
      {
        arr[ki2] = arr[ki2] + arr[ki2 + k];
        // arr[ki2 + k] = 0;
      }
    }
    k = 2 * k;
    nn = p;
    printarray(arr, n);
  }

  printf("\n");
  return 0;
}
