#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

int main(int argc, char *argv[])
{
  int threads = 1,
      chunksize = 4;
  int a = 0;

#pragma omp parallel num_threads(threads)
  {
    int id1 = omp_get_thread_num();

#pragma omp parallel for schedule(static, chunksize)
    for (int i = 0; i < 4; i++)
    {
      int id2 = omp_get_thread_num();
      a++;
      printf("thread %d/%d: %d\n", id1, id2, a);
    }
  }

  printf("\n");
  a = 0;
  chunksize = 2;
#pragma omp parallel num_threads(threads)
  {
    int id1 = omp_get_thread_num();
#pragma omp parallel for schedule(static, chunksize)
    for (int i = 0; i < 4; i++)
    {
      int id2 = omp_get_thread_num();
      a++;
      printf("thread %d/%d: %d\n", id1, id2, a);
    }
  }

  return 0;
}