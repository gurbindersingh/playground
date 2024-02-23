# Notes

## Table of content

- [Table of content](#table-of-content)
- [Variable scopes in Python](#variable-scopes-in-python)
- [Asynchronous code](#asynchronous-code)


## Variable scopes in Python

Python variables are scoped to the innermost function, class, or module in which they're assigned, unless modified by a `global` or `nonlocal` keyword. 

Control blocks like `if`, loops, `with` and `try/catch` blocks *don't* create a new scope, so a variable assigned inside them is still scoped to a function, class, or module.

## Asynchronous code

> This is a summary of the [Original Documentation](https://docs.python.org/3/library/asyncio-task.html).

There are three kinds of awaitable objects:

- Coroutines is simply a function defined using the async keyword.
- Tasks are used to run coroutines *concurrently*.
  - We can also use Task Groups to wait for a number of tasks to finish.
- Futures are low-level objects representing an eventual result of an asynchronous operation. These are rarely required in application level code.

> **NOTE:** Tasks and Futures are *not* thread-safe.


