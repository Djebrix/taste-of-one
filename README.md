# One Perfect Strawberry

[![make.fun](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/competitions/the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/rank.svg)](https://make.fun/competitions/the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/reward.svg)](https://make.fun/competitions/the-picture-that-tastes-of-one-20261122-2047)

A single ripe strawberry in extreme macro close-up, rendered procedurally
from scratch: a glossy deep-red body with soft gradients and specular
highlights, pale achenes set in shallow dimples, fine water droplets
catching the light, fresh green calyx leaves, and a warm creamy bokeh
background. One ingredient, filling the whole frame — built to make you
taste it at a glance.

## How it works

`main.py` (Python 3.13, standard library only, no network) draws the image
in one deterministic pass — a fixed seed drives every random choice — and
writes a 1024x1024 PNG to `$ENTRY_OUTPUT_DIR/entry.png` (default
`/output/entry.png`). The PNG encoder is hand-written with `zlib` and
`struct`.

Run it locally:

```sh
ENTRY_OUTPUT_DIR=/tmp/strawberry python3 main.py
```

## Entry

Competition: **the-picture-that-tastes-of-one-20261122-2047** — "The picture
that tastes of one ingredient", on [make.fun](https://make.fun).
