#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

int main(int argc, char *argv[])
{
  MPI_Init(&argc, &argv);

  // Get the size of the communicator
  int size = 0;
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  if (size != 6)
  {
    printf("This application is meant to be run with 6 MPI processes.\n");
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  // Get my rank
  int my_rank;
  MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);

  int R[] = {-1, -1, -1, 1, -1, -1};
  // int I[] = {0, 2, 4, 6, 8, 10};
  // int I[] = {1, 2, 3, 4, 5, 6};
  // int I[] = {-1, -2, -3, -4, -5, 0};
  int I[] = {100, 5, 5, 5, 5, 5};

  MPI_Reduce_scatter_block(I, R, 1, MPI_INT, MPI_MAX, MPI_COMM_WORLD);

  printf("(thread %d) R[0]=%2d, R[%d]=%2d\n", my_rank, R[0], my_rank, R[my_rank]);

  MPI_Finalize();

  for (int i = 0; i < size; i++)
  {
    printf("%d, ", R[i]);
  }
  printf("\n");

  return EXIT_SUCCESS;
}
