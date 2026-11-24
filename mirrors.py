import math, struct, sys, time, zlib

def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def mul(a, k): return (a[0]*k, a[1]*k, a[2]*k)
def dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def norm(a): return mul(a, 1 / math.sqrt(dot(a, a)))

SPHERES = [
    ((-2.05, 1.0, 5.6), 1.0, (1.0, 0.35, 0.3), 0.9),
    (( 0.0, 1.4, 6.3), 1.4, (0.95, 0.95, 0.95), 0.95),
    (( 2.05, 1.0, 5.6), 1.0, (0.35, 0.55, 1.0), 0.9),
    ((-0.95, 0.55, 3.9), 0.55, (1.0, 0.8, 0.25), 0.9),
    (( 0.95, 0.55, 3.9), 0.55, (0.35, 1.0, 0.5), 0.9),
    (( 0.0, 0.35, 3.1), 0.35, (0.85, 0.45, 1.0), 0.9),
]
LIGHT = norm((-0.6, 1.0, -0.5))
SKY = (0.55, 0.7, 0.95)
AMBIENT = 0.15
EPS = 1e-4
rays = 0

def hit_sphere(o, d, c, r):
    oc = sub(o, c)
    b = dot(oc, d)
    disc = b*b - (dot(oc, oc) - r*r)
    if disc < 0: return None
    t = -b - math.sqrt(disc)
    return t if t > EPS else None

def trace(o, d):
    global rays
    rays += 1
    best = None
    for s in SPHERES:
        t = hit_sphere(o, d, s[0], s[1])
        if t and (best is None or t < best[0]):
            p = add(o, mul(d, t))
            best = (t, p, norm(sub(p, s[0])), s[2], s[3])
    if d[1] < 0:
        t = -o[1] / d[1]
        if t > EPS and (best is None or t < best[0]):
            p = add(o, mul(d, t))
            check = (math.floor(p[0]) + math.floor(p[2])) % 2
            best = (t, p, (0, 1, 0), (0.85, 0.85, 0.85) if check else (0.12, 0.12, 0.14), 0.0)
    return best

def shade(o, d, depth=0):
    hit = trace(o, d)
    if hit is None:
        k = max(0.0, d[1])
        return (0.08 + 0.25 * k, 0.1 + 0.35 * k, 0.2 + 0.6 * k)
    _, p, n, color, refl = hit
    light = AMBIENT
    if trace(p, LIGHT) is None:
        light += max(0.0, dot(n, LIGHT))
    c = mul(color, light)
    if refl > 0 and depth < 10:
        r = sub(d, mul(n, 2 * dot(d, n)))
        rc = shade(p, r, depth + 1)
        c = add(mul(c, 1 - refl), tuple(color[i] * rc[i] * refl for i in range(3)))
    return c

def render(w, h):
    cam, fov = (0.0, 1.6, -1.0), math.tan(math.radians(30))
    rows = []
    for y in range(h):
        row = bytearray(b'\x00')
        for x in range(w):
            px = (2 * (x + 0.5) / w - 1) * fov * w / h
            py = (1 - 2 * (y + 0.5) / h) * fov
            c = shade(cam, norm((px, py - 0.15, 1.0)))
            row += bytes(min(255, int(255 * math.sqrt(max(0.0, v)))) for v in c)
        rows.append(bytes(row))
    return rows

def write_png(path, w, h, rows):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(b''.join(rows), 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)

if __name__ == '__main__':
    w, h = int(sys.argv[1]), int(sys.argv[2])
    start = time.perf_counter()
    rows = render(w, h)
    write_png(sys.argv[3], w, h, rows)
    print(f'{w}x{h} pixels={w*h} rays={rays} seconds={time.perf_counter() - start:.1f}')
