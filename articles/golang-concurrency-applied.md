---
title: "Golang: Go concurrency applied in back-ends"
date: 2025-11-13
description: "A practical introduction to Go concurrency in back-end development using goroutines, channels, sync, atomic, and context."
og_image: "/images/go-concurrency-article.webp"
---

![Go concurrency applied in back-ends](/images/go-concurrency-article.webp)

## Introduction

After a long story, I decided to make an article about Go
concurrency. Before that, I wanted to do another article about Go
back-ends, but I decided to cover both subjects, applying Go concurrency
in back-ends.

## Concurrency in a Nutshell

First of all, we need to recall what concurrency is, an essential
concept for building efficient and high-performance applications.

Concurrency in computing allows tasks to progress by interleaved
execution, improving performance and resource usage of tasks such as I/O
operations, daemons, back-ends and more. It's essential, especially in
applications that demand fast returns and support multiple users.

## Goroutines and Channels

Go concurrency is built around goroutines and channels, two features
that walk together in Go concurrency.

### Goroutine

Goroutines are lightweight threads managed by the Go runtime. They
are lighter than traditional threads, goroutines start with a stack size
of ~2KB, which grows dynamically based on its memory usage.

Also, goroutines are managed in the user-space by the Go runtime, they
are multiplexed by the Go scheduler onto a smaller number of kernel
threads, managed by the OS. The Go scheduler allows spawning a high number of
goroutines with minimal overhead, making it efficient for concurrent
programming, especially in applications with high demand for
concurrency.

Here is an example:

```go
package main

import (
	"fmt"
	"time"
)

func iterateUntil(num int) {
	for i := 0; i < num; i++ {
		time.Sleep(500 * time.Millisecond)
		fmt.Println(i)
	}
}

func main() {
	num := 10
	go iterateUntil(num)
	// You can use goroutines on lambda functions too
	go func(msg string) {
		for i := 0; i < num; i++ {
			time.Sleep(500 * time.Millisecond)
			fmt.Println(msg)
		}
	}("im reading fugu.cafe")

	fmt.Println("ops")
	time.Sleep(6 * time.Second)
}
```

Look at the output:

```sh
$ go run main.go
ops
im reading fugu.cafe
0
1
im reading fugu.cafe
im reading fugu.cafe
2
3
im reading fugu.cafe
im reading fugu.cafe
4
5
im reading fugu.cafe
im reading fugu.cafe
6
7
im reading fugu.cafe
im reading fugu.cafe
8
im reading fugu.cafe
9
```

Notice how the goroutines make progress together, although they
aren't synchronized. This is concurrency.

### Channels

Channels are typed pipes used to send and receive values between
goroutines. While a value isn't received, the sending goroutine blocks
until the other goroutine receives it and vice-versa.

This built-in blocking behavior makes channels a natural way to
synchronize execution between goroutines. Depending on the use case, you
can use channels to coordinate task completion, pass data safely, or
control the timing of concurrent tasks.

A brief example:

```go
package main

import (
	"fmt"
)

func iterateUntil(
	num int,
	myTurn <-chan struct{}, // For receive-only, use <- prefix, otherwise, <- suffix
	yourTurn chan<- struct{},
	done chan<- string,
	id string,
) {
	for i := 0; i < num; i++ {
		<-myTurn
		if id == "i" {
			fmt.Println(i)
		} else {
			fmt.Println("im reading fugu.cafe")
		}
		yourTurn <- struct{}{}
	}
	done <- "OK!"
}

func main() {
	num := 10

	// For signals that don't need to carry data, use a channel of empty structs
	chanX := make(chan struct{})
	chanY := make(chan struct{})
	done := make(chan string, 2) // we can define the length of a channel

	go iterateUntil(num, chanX, chanY, done, "i")
	go iterateUntil(num, chanY, chanX, done, "msg")

	fmt.Println("there is")

	chanX <- struct{}{} // init

	fmt.Println(<-done)
	_ = <-chanX // throw away the last turn signal
	fmt.Println(<-done)

	fmt.Println("all done")
}
```

Look at the output:

```sh
$ go run main.go
there is
0
im reading fugu.cafe
1
im reading fugu.cafe
2
im reading fugu.cafe
3
im reading fugu.cafe
4
im reading fugu.cafe
5
im reading fugu.cafe
6
im reading fugu.cafe
7
im reading fugu.cafe
8
im reading fugu.cafe
9
OK!
im reading fugu.cafe
OK!
all done
```

Notice how it's synchronized, but there are some problems. It can be
difficult to organize the synchrony between different or large quantities
of functions.

### `sync` package

While channels are the idiomatic way to communicate and synchronize
between goroutines, sometimes you need more direct control or a simpler
way to manage synchrony between goroutines without worrying too much about
deadlocking or data racing. The `sync` package offers that, check
[`sync`](https://pkg.go.dev/sync) for more options.

Here is the same example as before, but utilizing `Mutex`, `WaitGroup`
and `Cond`:

```go
package main

import (
	"fmt"
	"sync"
)

func iterateUntil(
	num int,
	mu *sync.Mutex,
	cond *sync.Cond,
	wg *sync.WaitGroup,
	turn *string,
	id string,
) {
	defer wg.Done()

	for i := 0; i < num; i++ {
		// acquire lock
		mu.Lock()
		// unlock to receive turn
		for *turn != id {
			cond.Wait()
		}
		if id == "i" {
			fmt.Println(i)
			*turn = "msg"
		} else {
			fmt.Println("im reading fugu.cafe")
			*turn = "i"
		}
		// For more than 2 goroutines being used, use Broadcast()!!!
		cond.Signal()
		// Unlock
		mu.Unlock()
	}
}

func main() {
	var wg sync.WaitGroup
	var mu sync.Mutex
	cond := sync.NewCond(&mu)

	wg.Add(2) // 2 is the number of goroutines for WaitGroup

	fmt.Println("there is")

	turn := "i" // start

	go iterateUntil(10, &mu, cond, &wg, &turn, "i")
	go iterateUntil(10, &mu, cond, &wg, &turn, "msg")

	wg.Wait() // Wait until all goroutines finish
	fmt.Println("both OK!")
	fmt.Println("all done")
}
```

Look at the output:

```sh
$ go run main.go
there is
0
im reading fugu.cafe
1
im reading fugu.cafe
2
im reading fugu.cafe
3
im reading fugu.cafe
4
im reading fugu.cafe
5
im reading fugu.cafe
6
im reading fugu.cafe
7
im reading fugu.cafe
8
im reading fugu.cafe
9
im reading fugu.cafe
both OK!
all done
```

Notice how the `sync` package makes concurrency easier to manage,
although channels are often enough for many cases.

Not only that, `sync` provides the subpackage `atomic`, which is useful
for performing atomic operations and avoiding data races in shared
memory access and mutation.

A brief example of the `sync/atomic` package, check
[`sync/atomic`](https://pkg.go.dev/sync/atomic) for more options:

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	var counter int64
	var wg sync.WaitGroup
	workers := 5
	increments := 1000

	wg.Add(workers)

	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < increments; j++ {
				// prevents data races between goroutines
				atomic.AddInt64(&counter, 1)
			}
		}()
	}

	wg.Wait()
	fmt.Println("final value:", counter)
}
```

Look at the output:

```sh
$ go run main.go
final value: 5000
```

## Go concurrency applied in back-ends

Concurrency shines in back-end development. It allows you to process
multiple tasks and background jobs efficiently without blocking the flow
and without high overhead. There are a lot of situations where it is useful,
such as:

- Financial operations, where atomic updates ensure safe and
  consistent exchanges.
- Heavy data processing, where heavy data can be split into chunks
  and processed concurrently.
- Scheduled or cycled jobs, which can run independently in the
  background.
- Calling multiple services or APIs for faster processing.

### `context` package

In back-end applications, you often need a way to cancel operations,
set deadlines or timeouts, or pass request-scoped data, and that’s
where the `context` package shines.

Here is an example using `net/http` with a request-scoped
context and timeout:

```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

func handleRequest(w http.ResponseWriter, r *http.Request) {
	// get the request-scoped context from the request
	ctx := r.Context()

	// attribute to the context a 2-second timeout
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	// schedule the context closure in the end
	defer cancel()

	done := make(chan string)

	go func() {
		time.Sleep(3 * time.Second) // longer than timeout
		done <- "task completed"
	}()

	select {
	case res := <-done:
		fmt.Fprintf(w, "Success: %s\n", res)
	case <-ctx.Done():
		// ctx.Err() returns reason for cancellation
		http.Error(w, fmt.Sprintf("Request canceled: %v", ctx.Err()), http.StatusRequestTimeout)
	}
}

func main() {
	http.HandleFunc("/task", handleRequest)
	fmt.Println("Server running at http://localhost:8080")
	http.ListenAndServe(":8080", nil)
}
```

Look at the output:

```sh
$ curl http://localhost:8080/task
Request canceled: context deadline exceeded
```

Notice how `context` is essential for controlling request lifetimes,
allowing your back-end to cancel unnecessary work, and provide fast,
reliable responses to clients.

## Conclusion

If everything is set up correctly, your Go back-end can now
efficiently handle multiple tasks concurrently, using goroutines for
lightweight concurrency, channels and sync primitives for safe
operations, and the `context` package for managing request lifetimes.
It’s a simple, robust, and responsive setup.
