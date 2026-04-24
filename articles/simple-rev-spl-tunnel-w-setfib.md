---
title: "FreeBSD: Simple reverse split tunneling with setfib(1)"
date: 2026-04-11
description: "A simple way to do reverse split tunneling on FreeBSD using setfib(1) and multiple FIBs."
og_image: "/images/spl-rev-split-tunnel-on-fbsd-w-setfib.webp"
---

![Simple rev split tunneling on FBSD w setfib](/images/spl-rev-split-tunnel-on-fbsd-w-setfib.webp)

## Introduction

A common split tunneling setup keeps the normal network as the default path and sends only seleted traffic through the VPN.

Reverse split tunneling is the opposite.

In this model, the system is effectively VPN-first for ordinary traffic, while only selected applications are allowed to escape through the normal network.

On FreeBSD, one of the simplest ways to do this is with multiple FIB and `setfib(1)`.

A FIB is basically a routing table. By keeping the VPN-oriented routing in the default FIB and preserving the normal gateway in another one, I can choose which processes bypass the tunnel simply by starting them with `setfib`.

Ths gives a clean and simple form of reverse split tunneling:

- Regular system traffic goes through the VPN
- Selected applications bass the VPN
- ROuting stays simple and explicit

##  What `setfib(1)` does?

`setfib(1)` runs a command with a different default routing table. In practice, this means sockets opened by that process will use the selected FIB instead of the default one.

For example, if my non-VPN routes live in FIB 1:

```sh
$ setfib 1 chromium
```

Starts `chromium` without the VPN tunnel.

## How it works?

Your real routing layout does not look like this:


```text
FIB 0: default -> wg0
FIB 1: default -> clearnet

```

That would be an oversimplification.

A more accurate reverse split setup on FreeBSD with WireGuard often looks like this instead:

```text
FIB 0:
  default                -> normal gateway
  VPN endpoint host route-> normal gateway
  0.0.0.0/1              -> wg0
  128.0.0.0/1            -> wg0
FIB 1:
  default                -> normal gateway

```

In other words, the main routing table keeps just enough normal routing for the tunnel itself to stay reachable, while almost all ordinary traffic is catured by two half-deault routes through `wg0`.

That is exactly what reverse split tunneling needs:

- Ordinary traffic uses the VPN in the default routing view
- the WireGuard peer remains reachable outside the tunnel
- Selected applications can bypass the VPn by running under another FIB

In my case, the tables looked like this:

```text
FIB 0:
  0.0.0.0/1      -> wg0
  128.0.0.0/1    -> wg0
  default        -> 10.0.0.1 via wifibox0
  <vpn-ip>       -> 10.0.0.1 via wifibox0
FIB 1:
  default        -> 10.0.0.1 via wifibox0
```

So even though FIB 0 still had a normal default route, the two `/1` routes were more specific and therefore won for almost all IPv4 traffic. The hos routet for the VPN endpoint stayed outside the tunnel, which prevented the tunnel from trying to route itself through itself.

## Enabling multiple FIBs

FreeBSD needs to know in advance how many routing tables it should provide. For a simple setup, two FIBs are enough: one for the VPN view and one for the normal network view.

Add this to `/boot/loader.conf`:

```text
net.fibs="2"
```

Then reboot the system.

After rebooting, confirm it.

```sh
$ sysctl net.fibs
```

## Preparing the idea before changing routes

Before moving the default system traffic into the VPN, identify your current normal gateway.

For example:

```sh
$ netstat -rn
```

You should note your regular default route, something like:

```text
default 192.168.15.1
```
