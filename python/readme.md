# Notes

## Variable scopes in Python

Python variables are scoped to the innermost function, class, or module in which they're assigned, unless modified by a `global` or `nonlocal` keyword. 

Control blocks like `if`, loops, `with` and `try/catch` blocks *don't* create a new scope, so a variable assigned inside them is still scoped to a function, class, or module.