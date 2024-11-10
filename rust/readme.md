# Notes

- [Scoping](#scoping)

## Scoping

- Variables in Rust don't just hold data but also own resources.
  - Whenever a variable goes out of scope, its destructor is called to free the 
    owned resources.
  - We can implement the `Drop` trait for custom logic.
- Resources can only have one owner.
  - Whenever data is reassigned or passed as a value, the ownership is 
    transferred to the new owner, called a *move*.
    - The previous owner cannot be used after this.
    - Partial moves are also possible, e.g. when destructuring.
  - Whenever ownership is transferred, we can change the data's mutability.
  - To use object without transferring their ownership, we can pass them as 
    references (`&T`) to *borrow* them. This ensures that the object is not
    destroyed after it leaves the scope. Alternatively we can also use the 
    `ref` keyword.
    - Mutable data can also be borrowed mutably by using a mutable reference 
      (`&mut T`). Otherwise the object will only borrowed immutably.
      - Only one mutable borrow is allowed at a time. An object can only be
        mutably borrowed again after the previous reference has been used for 
        the last time.
- There are explicit lifetime annotations