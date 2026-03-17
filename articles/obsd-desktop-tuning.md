---
title: "OpenBSD: Desktop Tuning Guide"
date: 2025-10-18
description: "A practical guide to tuning an OpenBSD desktop with sysctl, login.conf, fstab, and mfs for responsiveness and better resource usage."
og_image: "/images/obsd-tuning-dsk-article.webp"
---

![OpenBSD desktop tuning](/images/obsd-tuning-dsk-article.webp)

## Introduction

While tuning my X260 ThinkPad with OpenBSD and my W541 ThinkPad with
FreeBSD, I realized the importance of understanding what each important
system parameter for tuning does and how it affects performance.

This guide aims to clarify the purpose of each parameter and their
relevance for optimizing a BSD desktop experience. This guide is for
OpenBSD, I will write a separate one for FreeBSD. Check
[OpenBSD man pages](https://man.openbsd.org) for detailed information
and more options.

## /etc/sysctl.conf

### A quick brief on `sysctl(8)`

The `sysctl(8)` utility displays kernel state variables and allows
processes with appropriate privilege to modify kernel state
variables. The state to be retrieved or set is described using a
Management Information Base (MIB) style name, using a dotted set of
parameters, for example:

```sh
$ sysctl hw.audio.record
kern.audio.record=0
$ doas sysctl kern.audio.record=1
kern.audio.record: 0 -> 1 # activates mic
```

### `/etc/sysctl.conf`

`sysctl.conf(5)` is the `sysctl(8)` configuration file used to set
sysctl variables at system startup. Here is an example with tuning and a
quick explanation for each parameter:

```text
# i recommend researching and testing with `sysctl(8)` before doing anything here for safety, there are tons of parameters to explore.

# shared memory is a method of sharing a common memory space for inter-process communication (IPC)
# modern browsers, multimedia apps, databases, games, containers, vms

kern.shminfo.shmall=1966080 # total number of pages, 1 page per 4096 bytes. ill put 1966080 pages for my 8gb tp ((8GB-512M)/4096)
kern.shminfo.shmmax=536870912  # cap for each shm segment, for safety, ill set it dividing my memory by 16. 512mb is enough (db shared_buffer, browser cache).
kern.shminfo.shmmni=2048 # max number of segments in a system (enough space for multitasks, containers, vms)
kern.shminfo.shmseg=2048 # max number of segments a single process can attach to (allows browsers/multimedia with many tabs/processes use multiple segments)

# IPC semaphores (sync between processes)
kern.seminfo.semmns=4096 # total semaphores
kern.seminfo.semmni=1024 # total sets of semaphores, 1024 x average semaphores per set should equal to SEMMNS

# Max processes and open file descriptors (enough for me. browsers, compiling, multitasking)
kern.maxproc=8192
kern.maxfiles=16384

# Vnode is a kernel abstraction of a file system, it represents a file system object (good for caching)
kern.maxvnodes=100000 # max tracked filesystem objects by the kernel (open files, dirs, sockets, etc.)

# Network tuning
kern.somaxconn=1024 # max number of pending TCP connections in listen queue (useful on p2p, modern browsers open tons of connections), 1024 feels enough for me
net.inet.udp.recvspace=262144 # UDP receive and send buffers, useful for streaming and calls
net.inet.udp.sendspace=262144
net.inet.tcp.mssdflt=1460 # max segment size to ethernet MTU
net.inet.tcp.keepidle=300 # reduce idle keepalive time to detect dead connections faster
net.inet.ip.ifq.maxlen=4096 # increase interface queue max length for better burst handling
net.inet6.ip6.ifq.maxlen=4096 # for ipv6

hw.smt=1 # enable hyperthreading, check https://www.openbsd.org/faq/faq10.html before
```

## /etc/login.conf

`login.conf(5)` is the configuration file that describes
various attributes of a login class. A login class determines what styles
of authentication are available, along with its session resource limits and
environment. I'll modify the `staff` attributes and add my user to the `staff`
class. Here is an example:

```text
# Staff have fewer restrictions and can login even when nologins are set.
# cur - initial limit
# max - max limit
# use 'infinity' for unlimited restriction
# for datasize, ill set max = (shmall - 256M), cur = shmall/2
# for maxproc, ill set max = maxproc/4, cur = maxproc/8, my user doesnt need too many processes
# for openfiles, ill set max = (maxfiles - 1024), cur = maxfiles/2
# for stacksize, ill set max = 32M, cur = 16M
staff:\
	:datasize-cur=4096M:\
	:datasize-max=7936M:\
	:maxproc-cur=1024:\
	:maxproc-max=2048:\
	:openfiles-cur=8192:\
	:openfiles-max=15360:\
	:stacksize-cur=16M:\
    :stacksize-max=32M:\
	:ignorenologin:\
	:requirehome@:\
	:tc=default:\
	:lang=en_US.UTF-8:
```

Adding my user to the `staff` class:

```sh
$ doas usermod -L staff splattedbrain
```

You can build `/etc/login.conf.db` if your
`login.conf(5)` is large for performance improvement:

```sh
$ doas cap_mkdb /etc/login.conf
```

## /etc/fstab

The `fstab(5)` file contains static information about the
filesystems and their mount configurations. There are mount options that
improve read and write performance, like `noatime`, which
prevents the system from updating the access time of a file unless it's
modified or the status change time is also being updated. It reduces
write operations.

```text
# if you need, you can disable swap partition with swapctl(8) '-d' parameter
f0c02cfb168f7d3e.b none swap sw
f0c02cfb168f7d3e.a / ffs rw,noatime,wxallowed 1 1
```

## mfs on /tmp or ~/.cache

If you have enough memory and can use a part of it for caching
temporary files, you should mount an `mfs` filesystem on
`/tmp` or `~/.cache`. `mfs` (memory filesystem) allows creating a virtual disk
using RAM, being useful for frequently accessed files, but all data is lost when the system is
powered off. For example, in `fstab(5)`:

```text
# -s for the size
swap /tmp mfs rw,nosuid,nodev,-s=512M 0 0
```

You should change `/tmp` permissions:

```sh
$ doas chmod 1777 /tmp
$ doas mount /tmp
```

See
["Use ramdisk on /tmp on OpenBSD (2018-05-08)"](https://dataswamp.org/~solene/2018-05-08-mfs-tmp.html)
for detailed information.

## Conclusion

This guide focuses on safe, desktop-appropriate tuning for OpenBSD.
Most of these settings help improve responsiveness, concurrency, and
memory utilization without sacrificing stability.
