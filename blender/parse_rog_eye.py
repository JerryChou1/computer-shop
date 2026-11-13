import re, json, sys

SRC = "/Users/jjmac_studio/.hermes/cache/scratch/rog_eye.svg"
OUT = "/Users/jjmac_studio/.hermes/cache/scratch/rog_eye_polys.json"
svg = open(SRC).read()

# collect path d attributes (skip clipPath rects: they are plain L-only boxes)
ds = re.findall(r'<path[^>]*\sd="([^"]+)"', svg)
# dedupe keeping first occurrence, drop rectangle-ish (no curves & 4 pts)
def parse_path(d):
    # tokenize
    toks = re.findall(r'([MLCQZzmclqz])([^MLCQZzmclqz]*)', d)
    polys = []          # list of polygons (each starts after each M)
    cur = []
    x = y = 0.0
    sx = sy = 0.0
    for cmd, arg in toks:
        nums = [float(n) for n in re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', arg)]
        if cmd in ('M', 'm'):
            if len(cur) > 2: polys.append(cur)
            x, y = nums[0], nums[1]
            if cmd == 'm': x += sx; y += sy
            sx, sy = x, y; cur = [(x, y)]
        elif cmd in ('L', 'l'):
            it = iter(nums)
            for a, b in zip(it, it):
                x += a if cmd == 'l' else 0; y += b if cmd == 'l' else 0
                if cmd == 'L': x, y = a, b
                cur.append((x, y))
        elif cmd in ('C', 'c'):
            for i in range(0, len(nums), 6):
                x1, y1, x2, y2, x3, y3 = nums[i:i+6]
                if cmd == 'c':
                    x1 += x; y1 += y; x2 += x; y2 += y; x3 += x; y3 += y
                px, py = x, y
                for t in [i/12 for i in range(1, 13)]:
                    mt = 1 - t
                    bx = mt**3*px + 3*mt*mt*t*x1 + 3*mt*t*t*x2 + t**3*x3
                    by = mt**3*py + 3*mt*mt*t*y1 + 3*mt*t*t*y2 + t**3*y3
                    cur.append((bx, by))
                x, y = x3, y3
        elif cmd in ('Z', 'z'):
            if len(cur) > 2: polys.append(cur)
            cur = [(sx, sy)]
    if len(cur) > 2: polys.append(cur)
    return polys

seen = set()
out_polys = []
for d in ds:
    key = d[:80]
    if key in seen: continue
    seen.add(key)
    polys = parse_path(d)
    # reject rectangles (only L, 4 pts) and tiny fragments
    bad = False
    for p in polys:
        xs = [v[0] for v in p]; ys = [v[1] for v in p]
        w = max(xs)-min(xs); h = max(ys)-min(ys)
        if len(p) <= 5 and abs(w-h*0) > 0 and (w > 200 and h > 120 and w*h > 200*120*0.9):
            bad = True
    if bad: continue
    # flatten (assume single contour per path)
    main = max(polys, key=len)
    if len(main) < 8: continue
    xs = [v[0] for v in main]; ys = [v[1] for v in main]
    w = max(xs)-min(xs); h = max(ys)-min(ys)
    if w < 5 or h < 5: continue
    out_polys.append([[round(a,3), round(b,3)] for a,b in main])

# normalize into a single coordinate space (viewBox 375x375)
json.dump(out_polys, open(OUT, "w"))
print("contours:", len(out_polys), "pts each:", [len(p) for p in out_polys])
