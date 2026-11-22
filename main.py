"""A single ripe strawberry, extreme macro close-up.

Procedural render, Python 3.13 standard library only. Deterministic:
one fixed seed drives every random choice, no time or OS randomness.
Writes one 1024x1024 PNG to $ENTRY_OUTPUT_DIR/entry.png
(default /output/entry.png).
"""

import math
import os
import random
import struct
import zlib

W = H = 1024
SEED = 20261122


def clamp255(v):
    if v < 0:
        return 0
    if v > 255:
        return 255
    return v


def lerp(a, b, t):
    return a + (b - a) * t


def body_half_width(y):
    """Half width of the strawberry body at row y (0 outside the body)."""
    if y < 285 or y > 935:
        return 0.0
    t = (y - 285) / 650.0
    return 312.0 * (1.0 - t ** 2.3) ** 0.55


def render():
    rng = random.Random(SEED)

    # Small tiled grain, values in [-2, 2], reused across the frame.
    noise = [[rng.randint(-2, 2) for _ in range(128)] for _ in range(128)]

    # Warm out-of-focus background circles: (cx, cy, r, rgb, strength).
    bokeh = []
    for _ in range(18):
        bokeh.append((
            rng.uniform(-40, 1064),
            rng.uniform(-40, 1064),
            rng.uniform(34, 120),
            (rng.randint(238, 255), rng.randint(186, 218),
             rng.randint(118, 168)),
            rng.uniform(0.10, 0.26),
        ))

    # ---- background: warm creamy vertical gradient -------------------
    top = (250, 226, 190)
    bottom = (219, 174, 134)
    rows = []
    for y in range(H):
        t = y / (H - 1)
        r = int(lerp(top[0], bottom[0], t))
        g = int(lerp(top[1], bottom[1], t))
        b = int(lerp(top[2], bottom[2], t))
        rows.append(bytearray(bytes((r, g, b)) * W))

    # ---- bokeh circles, soft radial falloff --------------------------
    for (cx, cy, rad, col, strength) in bokeh:
        y0 = max(0, int(cy - rad))
        y1 = min(H - 1, int(cy + rad) + 1)
        for y in range(y0, y1):
            dy = (y - cy) / rad
            chord = math.sqrt(max(0.0, 1.0 - dy * dy)) * rad
            x0 = max(0, int(cx - chord))
            x1 = min(W - 1, int(cx + chord) + 1)
            row = rows[y]
            for x in range(x0, x1):
                d = math.hypot((x - cx) / rad, dy)
                if d >= 1.0:
                    continue
                a = strength * (1.0 - d * d)
                i = x * 3
                row[i] = clamp255(int(row[i] + (col[0] - row[i]) * a))
                row[i + 1] = clamp255(int(row[i + 1] + (col[1] - row[i + 1]) * a))
                row[i + 2] = clamp255(int(row[i + 2] + (col[2] - row[i + 2]) * a))

    # ---- calyx leaves (drawn first; the berry body covers their base)
    leaf_base_x, leaf_base_y = 512, 312
    leaf_angles = (-168, -138, -108, -90, -72, -42, -12)
    for k, ang_deg in enumerate(leaf_angles):
        ang = math.radians(ang_deg)
        dx = math.cos(ang)
        dy = math.sin(ang)
        # Perpendicular direction.
        px, py = -dy, dx
        length = 150.0 + 26.0 * math.sin(k * 2.3 + 1.0) + (18.0 if k in (2, 4) else 0.0)
        max_w = 15.0 + 4.0 * math.sin(k * 1.7)
        steps = int(length)
        for s in range(steps):
            f = s / steps
            # Slight outward curve as the leaf grows.
            bend = 14.0 * f * f * (1 if k % 2 == 0 else -1)
            cx = leaf_base_x + dx * s + px * bend
            cy = leaf_base_y + dy * s + py * bend
            half = max_w * math.sin(math.pi * (f ** 0.75)) * (1.0 - 0.25 * f)
            if half < 0.6:
                continue
            # Leaf colour: deep green at the base, brighter toward the tip.
            gr = int(lerp(34, 74, f))
            gg = int(lerp(96, 152, f))
            gb = int(lerp(38, 62, f))
            iy = int(round(cy))
            if iy < 0 or iy >= H:
                continue
            row = rows[iy]
            x0 = max(0, int(cx - half))
            x1 = min(W - 1, int(cx + half) + 1)
            for x in range(x0, x1):
                # Vein: a lighter stripe down the middle of the leaf.
                vein = 1.0 if abs(x - cx) < 1.6 else 0.0
                i = x * 3
                row[i] = clamp255(gr + (52 if vein else 0))
                row[i + 1] = clamp255(gg + (58 if vein else 0))
                row[i + 2] = clamp255(gb + (30 if vein else 0))

    # Short stem rising from the calyx.
    for s in range(64):
        cx = 512 + int(10.0 * math.sin(s / 22.0))
        cy = 312 - s
        if cy < 0:
            break
        row = rows[cy]
        for x in range(cx - 7, cx + 8):
            if 0 <= x < W:
                i = x * 3
                row[i] = 74
                row[i + 1] = 122
                row[i + 2] = 58

    # ---- strawberry body ---------------------------------------------
    # Vertical colour stops: bright sunlit red at the shoulder, deep
    # ruby in the middle, dark wine red toward the tip.
    stops = (
        (0.00, (242, 52, 44)),
        (0.35, (220, 26, 34)),
        (0.70, (194, 16, 30)),
        (1.00, (138, 10, 24)),
    )

    def body_colour(t):
        for j in range(len(stops) - 1):
            t0, c0 = stops[j]
            t1, c1 = stops[j + 1]
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0)
                return (lerp(c0[0], c1[0], f),
                        lerp(c0[1], c1[1], f),
                        lerp(c0[2], c1[2], f))
        return stops[-1][1]

    for y in range(285, 936):
        hw = body_half_width(y)
        if hw <= 0.0:
            continue
        t = (y - 285) / 650.0
        base_r, base_g, base_b = body_colour(t)
        row = rows[y]
        x0 = max(0, int(512 - hw))
        x1 = min(W - 1, int(512 + hw) + 1)
        vv = (y - 560) / 360.0
        for x in range(x0, x1):
            dx = (x - 512) / hw
            ax = abs(dx)
            if ax >= 1.0:
                continue
            # Soft edge anti-aliasing over the last few pixels.
            edge = 1.0
            if ax > 0.965:
                edge = (1.0 - ax) / 0.035
                edge = edge * edge * (3.0 - 2.0 * edge)
            # Light from the upper left: shade across the curved body.
            shade = 0.70 + 0.38 * (-dx * 0.72 - vv * 0.55)
            if shade < 0.36:
                shade = 0.36
            elif shade > 1.16:
                shade = 1.16
            # Soft shadow tucked under the calyx at the top of the body.
            shade *= 1.0 - 0.34 * math.exp(-(((y - 318) / 46.0) ** 2))
            # Broad glossy sheen slightly left of centre.
            sheen = 0.14 * math.exp(-((dx + 0.28) ** 2) / 0.055)
            # Two soft specular highlights, plus one tight hot spot.
            h1 = 132.0 * math.exp(-(((x - 408) / 150.0) ** 2
                                    + ((y - 428) / 150.0) ** 2) * 2.1)
            h2 = 64.0 * math.exp(-(((x - 622) / 105.0) ** 2
                                   + ((y - 648) / 105.0) ** 2) * 2.0)
            h3 = 95.0 * math.exp(-(((x - 452) / 46.0) ** 2
                                   + ((y - 392) / 46.0) ** 2) * 2.4)
            r = base_r * (shade + sheen) + h1 + h2 + h3
            g = base_g * (shade + sheen) + h1 * 0.92 + h2 * 0.9 + h3 * 0.9
            b = base_b * (shade + sheen) + h1 * 0.85 + h2 * 0.85 + h3 * 0.82
            i = x * 3
            if edge >= 1.0:
                row[i] = clamp255(int(r))
                row[i + 1] = clamp255(int(g))
                row[i + 2] = clamp255(int(b))
            else:
                row[i] = clamp255(int(row[i] + (r - row[i]) * edge))
                row[i + 1] = clamp255(int(row[i + 1] + (g - row[i + 1]) * edge))
                row[i + 2] = clamp255(int(row[i + 2] + (b - row[i + 2]) * edge))

    # ---- achenes (pale seeds) set in shallow dimples -----------------
    seed_rng = random.Random(SEED + 7)
    seeds = []
    y = 350
    band = 0
    while y < 890:
        hw = body_half_width(y)
        if hw > 40:
            n = max(3, int(hw / 62))
            for j in range(n):
                frac = (j + 0.5) / n
                jitter = seed_rng.uniform(-0.16, 0.16)
                sx = 512 + (frac * 2.0 - 1.0 + jitter) * hw * 0.86
                sy = y + seed_rng.uniform(-14, 14)
                seeds.append((sx, sy, seed_rng.uniform(8.0, 11.0),
                              seed_rng.uniform(13.0, 17.0)))
        y += 46 + (band % 2) * 22
        band += 1
    for (sx, sy, rx, ry) in seeds:
        # Dimple: a darker halo slightly larger than the seed.
        for (rrx, rry, mul) in ((rx + 5.0, ry + 6.0, 0.58), (rx, ry, None)):
            iy0 = max(0, int(sy - rry))
            iy1 = min(H - 1, int(sy + rry) + 1)
            for iy in range(iy0, iy1):
                ddy = (iy - sy) / rry
                chord = math.sqrt(max(0.0, 1.0 - ddy * ddy)) * rrx
                ix0 = max(0, int(sx - chord))
                ix1 = min(W - 1, int(sx + chord) + 1)
                row = rows[iy]
                for ix in range(ix0, ix1):
                    i = ix * 3
                    if mul is None:
                        # Pale cream seed, lit from the upper left.
                        lit = 1.0 + 0.10 * (1.0 - (iy - sy) / max(ry, 1.0))
                        row[i] = clamp255(int(246 * lit))
                        row[i + 1] = clamp255(int(231 * lit))
                        row[i + 2] = clamp255(int(176 * lit))
                    else:
                        row[i] = int(row[i] * mul)
                        row[i + 1] = int(row[i + 1] * mul)
                        row[i + 2] = int(row[i + 2] * mul)

    # ---- water droplets catching the light ---------------------------
    drop_rng = random.Random(SEED + 21)
    for _ in range(30):
        dy_ = drop_rng.uniform(330, 880)
        hw = body_half_width(int(dy_))
        if hw < 60:
            continue
        dx_ = drop_rng.uniform(-0.8, 0.8) * hw
        cx = 512 + dx_
        cy = dy_
        rad = drop_rng.uniform(4.0, 12.0)
        iy0 = max(0, int(cy - rad))
        iy1 = min(H - 1, int(cy + rad) + 1)
        for iy in range(iy0, iy1):
            ddy = (iy - cy) / rad
            chord = math.sqrt(max(0.0, 1.0 - ddy * ddy)) * rad
            ix0 = max(0, int(cx - chord))
            ix1 = min(W - 1, int(cx + chord) + 1)
            row = rows[iy]
            for ix in range(ix0, ix1):
                d = math.hypot((ix - cx) / rad, ddy)
                if d >= 1.0:
                    continue
                # Lift toward white in the middle, bright sparkle top-left.
                lift = 0.38 * (1.0 - d * d)
                spark = 0.85 * math.exp(-(((ix - (cx - rad * 0.35)) / 2.2) ** 2
                                         + ((iy - (cy - rad * 0.35)) / 2.2) ** 2))
                i = ix * 3
                row[i] = clamp255(int(row[i] + (255 - row[i]) * lift + 255 * spark))
                row[i + 1] = clamp255(int(row[i + 1] + (255 - row[i + 1]) * lift + 255 * spark))
                row[i + 2] = clamp255(int(row[i + 2] + (255 - row[i + 2]) * lift + 255 * spark))

    # ---- vignette + grain, one final pass ----------------------------
    fx = [1.0 - 0.16 * ((x - 512) / 512.0) ** 2 for x in range(W)]
    fy = [1.0 - 0.16 * ((y - 512) / 512.0) ** 2 for y in range(H)]
    for y in range(H):
        row = rows[y]
        fyy = fy[y]
        nrow = noise[y & 127]
        for x in range(W):
            f = fx[x] * fyy
            n = nrow[x & 127]
            i = x * 3
            row[i] = clamp255(int(row[i] * f) + n)
            row[i + 1] = clamp255(int(row[i + 1] * f) + n)
            row[i + 2] = clamp255(int(row[i + 2] * f) + n)

    return rows


def png_bytes(rows):
    # Filter 2 (Up): each byte stored as the difference from the byte
    # directly above it. The image is mostly smooth vertical gradients,
    # so Up residuals are small and compress far better than raw rows.
    raw = bytearray()
    prev = bytes(W * 3)
    for row in rows:
        raw.append(2)
        cur = bytes(row)
        raw.extend((c - p) & 0xFF for c, p in zip(cur, prev))
        prev = cur
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", compressed) + chunk(b"IEND", b""))


def main():
    rows = render()
    data = png_bytes(rows)
    out_dir = os.environ.get("ENTRY_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
