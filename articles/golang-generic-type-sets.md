---
title: "Golang: Did you know about generic type sets?"
date: 2025-11-26
description: "Did you know about generic type sets? If you want safer and more optimized generics in Golang, you must understand generic type sets."
og_image: "/images/golang-generic-typesets.webp"
---

![Golang Generic Typesets](/images/golang-generic-typesets.webp)

## Introduction

Did you know about generic type sets? If you want safer and more
optimized generics in Golang, you must understand generic type sets.

## What is monomorphization in a nutshell?

Monomorphization is the process where the compiler generates
specialized machine code for each concrete type used in a generic
function.

In languages that fully monomorphize, calling a generic function with
`int64` and later with `float64` produces two distinct, highly optimized
versions of that function, highly optimizing the execution.

However, Go uses partial monomorphization (via GCShape), it can
generate specialized code for many cases, but it also groups
instantiations based on compatible underlying representations to reduce
code size and compile time. The result is a middle ground between
efficiency and performance.

## The problem

To understand why this works, it’s important to remember that Go uses
interfaces in two different ways:

```go
// Traditional usage of interfaces -> dynamic dispatch
type Writer interface {
    Write([]byte) (int, error)
}

// Generic constraints (type sets)
type Number interface {
    ~int64 | ~float64  // use "~" to allow any type whose underlying type is this
}

type Any interface{} // Anything implements
```

Even though `Any` accepts any type, it gives the compiler
zero information about what the value actually is. With
`Any`, the compiler cannot monomorphize at all.

Without any clues, everything is left in our hands, we need to apply
type inference (assertion) and check for type safety.

For example, `AnyAdd` won't work without type inference, but
`NumberAdd` doesn't need type inference because of type
constraints, and also runs faster than `AnyAdd`:

```go
// [T x] stands for "T can be of any type that implements x"

// Using Any
// needs type handling
func AnyAdd[T Any](a, b T) Any {
    ai := Any(a) // needs conversion for assertion
    bi := Any(b)

    switch av := ai.(type) {
    case int64:
        bv, ok := bi.(int64)
        if !ok {
            panic("b is not int64")
        }
        return av + bv
    case float64:
        bv, ok := bi.(float64)
        if !ok {
            panic("b is not float64")
        }
        return av + bv
    default:
        panic(fmt.Sprintf("unsupported type: %T", a))
    }
}

// Using a type set -> partially monomorphized
func NumberAdd[T Number](a, b T) T {
    return a + b
}
```

See the difference.

## Important notes

When using untyped constants, the compiler cannot infer a type if the
constant can fit into ambiguous types, see:

```go
var a int64 = 1
var b int64 = 2

NumberAdd(a, b)          // Ok

NumberAdd(3, 4)          // ERROR! Ambiguous -> 3 and 4 could be int64 or int or int32... compilation error
NumberAdd[int64](3, 4)   // Ok: type explicitly chosen
```

## Conclusion

If you don’t know the type in advance, like with a dynamic JSON
response, use empty interfaces (like `any`) with runtime type checks. This
provides flexibility, but at the cost of safety and performance.

If the set of possible types is known, using type sets allows the
compiler to apply GCShape (Go monomorphization) to your code, giving
safety and optimized execution.
