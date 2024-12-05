/**
 * Instead of creating a Promise by passing a callback to it,
 * we can also have the callback simply return the already
 * resolved or rejected Promises, thereby eliminating the
 * need for having a method signature that has to accept
 * a reject() and resolve() callback.
 */

function returnPromise() {
  const num = Math.random() * 100;
  console.log(num);
  if (num < 50) return Promise.reject("Number smaller than 50");
  else {
    return Promise.resolve("Number greater than 50");
  }
}

returnPromise()
  .then((value) => {
    console.log(value);
  })
  .catch((value) => {
    console.log(value);
  });
