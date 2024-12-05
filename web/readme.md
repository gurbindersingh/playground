# Typescript (and Javascript) Playground

## Gotchas

### ERR_MODULE_NOT_FOUND

At the end it will say

> Did you mean to import xyz.js?

Check if your import is missing the file-type extension, that is the most likely error. By default ECMAScript requires you to add the file extension. If you want to omit it, you need to call node with the `--experimental-specifier-resolution=node` flag.

### ReferenceError: require is not defined

Check if your `package.json` includes `"type": "module"`, this specifies the files as ES6 modules, which don't use the require-syntax.
