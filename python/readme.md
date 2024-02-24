# Notes

## Table of content

- [Table of content](#table-of-content)
- [Variable scopes in Python](#variable-scopes-in-python)
- [Writing asynchronous code using asyncio](#writing-asynchronous-code-using-asyncio)
  - [How asyncio works](#how-asyncio-works)
  - [Asynchronous tasks in Python](#asynchronous-tasks-in-python)
    - [Tasks](#tasks)
    - [Futures](#futures)
  - [Bootstrapping an asynchronous application](#bootstrapping-an-asynchronous-application)
  - [Interrupting a running task](#interrupting-a-running-task)
  - [Pitfalls](#pitfalls)
    - [Concurrency](#concurrency)
    - [Calling blocking functions](#calling-blocking-functions)
  - [Asynchronous programming vs. multi-threading/processing](#asynchronous-programming-vs-multi-threadingprocessing)

## Variable scopes in Python

Python variables are scoped to the innermost function, class, or module in
which they're assigned, unless modified by a `global` or `nonlocal` keyword.

Control blocks like `if`, loops, `with` and `try/catch` blocks _don't_ create a 
new scope, so a variable assigned inside them is still scoped to a function, 
class, or module.

## Writing asynchronous code using asyncio

> **Some useful resources**:
>
> - https://bbc.github.io/cloudfit-public-docs/
> - https://faculty.ai/tech-blog/a-guide-to-using-asyncio/
> - https://blog.apify.com/python-asyncio-tutorial/
> - https://blog.devgenius.io/mastering-asynchronous-programming-in-python-a-comprehensive-guide-ef1e8e5b35db
> - https://datarodeo.io/python/optimizing-python-workflows-with-asyncio-for-asynchronous-programming/
> - https://medium.com/@tushar_aggarwal/master-the-power-of-asyncio-a-step-by-step-guide-ac0c46719811
> - https://superfastpython.com/python-asyncio/
> - https://docs.python.org/3/library/asyncio-task.html
>
> The official documentation is good for quickly looking things up but it 
> doesn't explain things properly.

### How asyncio works

The asyncio library allows us to write more efficient code by making use of an 
event-loop. This allows us to write non-blocking code, e.g. when performing IO 
bound operations. Whenever a task would cause the CPU to idle, the event-loop 
will pause it and instead execute another task.

### Asynchronous tasks in Python

In Python tasks that can be paused and resumed are called coroutines. They are 
simply functions that are defined using the `async` keyword. The point at which 
a coroutine may be paused by the event-loop is marked using the `await` 
keyword.

When we define a coroutine like 

```python
async def foo():
  # so something
```

and then call it like so `foo()`, it isn't actually executed. Instead Python 
creates an object of the class `Coroutine`. To actually call it we have to use 
`await` keyword first, like so: `await foo()`. In case `foo()` returns any 
values, then it will also unwrap and return those. 

> **NOTE:**  We can only use the `await` keyword in an `async` function. For 
> how to execute a Python script see [Bootstrapping an asynchronous application](#bootstrapping-an-asynchronous-application).

Coroutines are one of three awaitable objects:

- Coroutines
- Tasks
- Futures

#### Tasks

The event-loop cannot schedule coroutines directly, instead they have to be 
wrapped in a `Task` object. 

Tasks are used to run coroutines _concurrently_. That means that when we 
schedule two tasks they will be executed at the "same" time (with the 
event-loop switching back and forth between them whenever one calls `await`). 
An example for this can be found in the [how-to](how-to/async-await.py) 
directory.

We can also use `asyncio.gather()` or 
[Task Groups](https://docs.python.org/3/library/asyncio-task.html#task-groups) 
to schedule a number of tasks and wait for them to finish.

#### Futures

Futures are low-level objects representing an result of an asynchronous 
operation that will be available sometime in the future. They also hold the 
state of the Future.

These are rarely required in application level code unless you are writing  
your own asynchronous library.

> **NOTE:** Tasks and Futures are _not_ thread-safe.

### Bootstrapping an asynchronous application

If we can only `await` a coroutine in another coroutine, then how do we start 
the script in the first place? For that we use `asyncio.run()`. It's used to 
execute the entry-point function.

### Interrupting a running task

There is no explicit method to interrupt a running tasks. Instead we can call `asyncio.sleep(0)` as a workaround. According to the first article listed above, this is efficiently implemented.

### Pitfalls

#### Concurrency

If you execute coroutines like this

```py
await foo()
await bar()
```

you might notice that they are *not* executed concurrently but sequentially. 
This seems counterintuitive in the beginning. But lets recall what `await` 
does: it simply tells the event-loop that this operation might block, if this 
is the case, pause the current task and execute another one. It does not 
implicitly create a new task. These coroutines are still being executed in the context of the *current* `Task`.

To run code concurrently we can explicitly create a task for each and `await` their completion

```py
task1 = asyncio.create_task(bar())
task2 = asyncio.create_task(foo())

await task1
await task2
```

or simply use the `asyncio.gather()` function. We can also use 
[Task Groups](https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup) 
for this.

#### Calling blocking functions

If we have a I/O-bound functions (not defined using `async`), calling them 
inside a coroutine will block the entire event-loop. This may be the case if 
you are using function from a library or some old code. This can greatly reduce 
the performance. To circumvent this issue, we can use the `asyncio.to_thread()` 
function. This will create a coroutine that can we awaited and execute it in a 
separate thread.

### Asynchronous programming vs. multi-threading/processing

For I/O-bound tasks use asynchronous programming. For CPU-bound tasks use multi-threading or multi-processing.
