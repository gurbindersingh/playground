# Notes

## Table of content

- [Table of content](#table-of-content)
- [Variable scopes in Python](#variable-scopes-in-python)
- [Writing asynchronous code using asyncio](#writing-asynchronous-code-using-asyncio)
  - [What is asyncio?](#what-is-asyncio)
  - [Bootstrapping an asynchronous application](#bootstrapping-an-asynchronous-application)
  - [Interrupting a running task](#interrupting-a-running-task)
  - [Gotchas](#gotchas)
    - [Concurrency](#concurrency)

## Variable scopes in Python

Python variables are scoped to the innermost function, class, or module in
which they're assigned, unless modified by a `global` or `nonlocal` keyword.

Control blocks like `if`, loops, `with` and `try/catch` blocks _don't_ create a new scope, so a variable assigned inside them is still scoped to a function, class, or module.

## Writing asynchronous code using asyncio

### What is asyncio?

> This is a summary of the following resources:
>
> - https://bbc.github.io/cloudfit-public-docs/
> - https://docs.python.org/3/library/asyncio-task.html
>
> The official documentation is good for quickly looking things up but it doesn't explain things properly.

This library allows us to write more efficient code by switching betweens tasks when the CPU is idle, e.g. due to IO bound tasks. It does this by using an event-loop.

In Python such tasks are called coroutines. They are one of three awaitable objects:

- Coroutines is simply a function defined using the `async` keyword.
- Tasks are used to run coroutines _concurrently_.
  - We can also use Task Groups to wait for a number of tasks to finish.
- Futures are low-level objects representing an eventual result of an asynchronous operation. 
  - These are rarely required in application level code unless you are writing your own asynchronous library.

> **NOTE:** Tasks and Futures are _not_ thread-safe.

Calling a function that is defined using the `async` keyword does not actually 
execute it, instead Python implicitly creates an object of class `Coroutine`. 
To get the value we must unwrap it using the `await` keyword, which can only be 
used in asynchronous code blocks. Whenever a `Coroutine` object is awaited, the execution of the current task may be paused, but this is not guaranteed.

### Bootstrapping an asynchronous application

One problem we have with `async` functions is that we can't call them outside 
of asynchronous code. So to bootstrap an application we can use the 
`asyncio.run()` function to run an asynchronous function from an synchronous 
one.

### Interrupting a running task

There is no explicit method to interrupt a running tasks. Instead we can call `asyncio.sleep(0)` as a workaround. According to the first article listed above, this is efficiently implemented.

### Gotchas

#### Concurrency

The following code

```py
await foo()
await bar()
```

does *not* execute concurrently but sequentially. It will simply ensure that if 
there are already other tasks in the event-loop, they might get a turn if 
`foo()` blocks.

To run code concurrently either do

```py
task1 = asyncio.create_task(bar())
task2 = asyncio.create_task(foo())

await task1
await task2
```

or simply use the `asyncio.gather()` function. We can also use 
[Task Groups](https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup) 
for this.
