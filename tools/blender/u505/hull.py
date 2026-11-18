# U-505 exterior model: outer hull, casing, saddle tanks and keel.
# Requires common.py in the same exec namespace.
#
# The outer hull is lofted from parametric sections. Each half-section runs from the
# keel centre up to the deck centre:
#   lower body  superellipse quadrant (0, zk) -> (B, zc), exponent n
#   shoulder    ellipse quadrant (B, zc) -> (cw, zj)
#   casing side straight line (cw, zj) -> (w, zt), small rounded deck edge
#   deck top    slight camber to the centreline
# Saddle tanks are separate lofted blisters that intersect the hull.
# Section shapes are an artistic reconstruction from the capture photographs
# (Encl G 470/499/505/517) and the 2G-9C principal dimensions, not lines plans.

Y_BOW = 39.0
Y_STERN = -37.8
PH_R = 2.225          # pressure hull radius (14'7" diameter)
WL_Z = 4.30           # normal surfaced waterline above PH bottom (estimated)

T_ZK_STERN = [(-37.8, 4.75), (-37.35, 4.15), (-36.8, 3.0), (-36.0, 1.75), (-35.0, 1.05),
              (-33.5, 0.62), (-31.5, 0.32), (-29.0, 0.1), (-26.0, 0.0)]
T_W = [(-37.8, 0.30), (-37.3, 0.85), (-36.2, 1.25), (-34.0, 1.52), (-30.0, 1.68),
       (-24.0, 1.78), (18.0, 1.78), (23.0, 1.62), (27.0, 1.36), (31.0, 1.0),
       (34.5, 0.62), (37.0, 0.32), (38.4, 0.12), (39.0, 0.03)]
T_B = [(-37.8, 0.34), (-37.3, 0.95), (-36.2, 1.38), (-34.0, 1.66), (-31.0, 1.92),
       (-27.5, 2.2), (-23.0, 2.33), (21.0, 2.33), (25.0, 2.18), (28.5, 1.88),
       (31.5, 1.45), (34.5, 0.98), (36.8, 0.56), (38.2, 0.26), (39.0, 0.04)]
T_ZC = [(-37.8, 3.9), (-36.6, 3.05), (-35.0, 2.82), (-32.5, 2.68), (-30.0, 2.45), (-27.5, 2.3),
        (-24.0, 2.225), (22.0, 2.225), (27.0, 2.55), (31.0, 3.3), (34.5, 4.05),
        (37.0, 4.7), (39.0, 5.6)]
T_N = [(-37.8, 0.8), (-36.5, 0.55), (-34.0, 0.5), (-32.0, 0.72), (-30.0, 1.25), (-28.0, 1.7),
       (-25.0, 2.0), (23.0, 2.0), (27.0, 1.75), (31.0, 1.4), (35.0, 1.2), (39.0, 1.1)]
T_KZ = [(-37.8, 0.45), (-30.0, 0.45), (-25.0, 0.32), (23.0, 0.32), (28.0, 0.45), (39.0, 0.45)]
T_KX = [(-37.8, 0.6), (-30.0, 0.55), (-25.0, 0.42), (23.0, 0.42), (28.0, 0.55), (39.0, 0.6)]


def zk_at(y):
    if y > 28.5:
        return 6.75 * ((y - 28.5) / (Y_BOW - 28.5)) ** 3
    if y < -26.0:
        return pchip(T_ZK_STERN, y)
    return 0.0


def zt_at(y):
    z = 5.9
    z += 0.85 * ss(20.0, Y_BOW, y) ** 1.6
    z -= 0.2 * ss(-26.0, Y_STERN, y)
    return z


def hull_params(y):
    zk = zk_at(y)
    zt = zt_at(y)
    w = pchip(T_W, y)
    B = max(pchip(T_B, y), w + 0.01)
    zc = pchip(T_ZC, y)
    n = pchip(T_N, y)
    kz = pchip(T_KZ, y)
    kx = pchip(T_KX, y)
    zc = clamp(zc, zk + 0.03, zt - 0.25)
    zj = zc + kz * (zt - zc)
    cw = w + kx * (B - w)
    return dict(zk=zk, zt=zt, w=w, B=B, zc=zc, n=n, zj=zj, cw=cw)


N_LOW, N_SHO, N_SIDE, N_DECK = 22, 8, 5, 6
CREASE_IDX = N_LOW + N_SHO          # index of (cw, zj): crease between shoulder and casing side
DECK_EDGE_IDX = CREASE_IDX + N_SIDE + 2


def half_section(y):
    """List of (x, z) from the keel centre to the deck centre (x >= 0)."""
    p = hull_params(y)
    zk, zt, w, B, zc, n, zj, cw = (p[k] for k in ('zk', 'zt', 'w', 'B', 'zc', 'n', 'zj', 'cw'))
    pts = []
    # lower body: theta from pi/2 (keel) to 0 (max breadth)
    for i in range(N_LOW):
        th = (math.pi / 2) * (1 - i / N_LOW)
        x = B * se_pow(math.cos(th), 2 / n)
        z = zc - (zc - zk) * se_pow(math.sin(th), 2 / n)
        pts.append((x, z))
    # shoulder: (B, zc) -> (cw, zj)
    for i in range(N_SHO):
        ph = (math.pi / 2) * i / N_SHO
        x = cw + (B - cw) * math.cos(ph)
        z = zc + (zj - zc) * math.sin(ph)
        pts.append((x, z))
    # casing side (cw, zj) -> (w, zt - r)
    r = min(0.07, 0.5 * w)
    for i in range(N_SIDE):
        t = i / N_SIDE
        pts.append((lerp(cw, w, t), lerp(zj, zt - r, t)))
    # rounded deck edge
    pts.append((w, zt - r))
    pts.append((w - r * 0.3, zt - r * 0.3))
    # deck top with camber
    camber = 0.06 * min(1.0, w / 1.6)
    for i in range(N_DECK + 1):
        x = (w - r) * (1 - i / N_DECK)
        z = zt + camber * (1 - (x / max(w, 1e-3)) ** 2)
        pts.append((x, z))
    return pts


def hull_z_under(y, x):
    """Height of the hull underside at |x| (lower body only). None if outside."""
    hs = half_section(y)
    x = abs(x)
    for i in range(CREASE_IDX):
        x0, z0 = hs[i]
        x1, z1 = hs[i + 1]
        if (x0 - x) * (x1 - x) <= 0 and x1 != x0:
            return lerp(z0, z1, (x - x0) / (x1 - x0))
    return None


def full_ring(y):
    hs = half_section(y)
    # starboard side keel->deck centre, then port side deck centre->keel (skip duplicate centre points)
    right = [(x, y, z) for (x, z) in hs]
    left = [(-x, y, z) for (x, z) in reversed(hs[1:-1])]
    return right + left


def build_main_hull(coll):
    ys = stations(Y_STERN, Y_BOW, 300, end_density=3.0)
    rings = [full_ring(y) for y in ys]
    verts, faces = loft(rings, closed=True)
    n = len(rings[0])
    nh = len(half_section(0.0))
    # stern cap and bow cap (fans to a centre vertex)
    for idx, ring_i in ((0, 0), (1, len(rings) - 1)):
        r = rings[ring_i]
        c = (sum(p[0] for p in r) / n, r[0][1] + (-0.02 if idx == 0 else 0.02), sum(p[2] for p in r) / n)
        ci = len(verts)
        verts.append(c)
        base = ring_i * n
        for j in range(n):
            j2 = (j + 1) % n
            if idx == 0:
                faces.append((base + j2, base + j, ci))
            else:
                faces.append((base + j, base + j2, ci))
    # material index: 0 hull paint, 1 deck void (top surface under the slats)
    deck_lo = DECK_EDGE_IDX
    deck_hi = nh - 1  # centre
    left_start = nh
    mat_idx = []
    for i in range(len(rings) - 1):
        for j in range(n):
            # profile index along half-section for this column
            if j < nh:
                k = j
            else:
                k = nh - 2 - (j - left_start)
            mat_idx.append(1 if k >= deck_lo else 0)
    mat_idx += [0] * (len(faces) - len(mat_idx))
    # sharp edges along the creases (both sides)
    sharp = []
    cols = [CREASE_IDX, DECK_EDGE_IDX - 1]
    cols_all = []
    for k in cols:
        cols_all.append(k)
        cols_all.append(left_start + (nh - 2 - k))
    for i in range(len(rings) - 1):
        for k in cols_all:
            sharp.append((i * n + k, (i + 1) * n + k))
    ob = mesh_obj('Hull_Outer', verts, faces, coll, mats=['M_HullPaint', 'M_DeckVoid'],
                  smooth=True, mat_idx=mat_idx, sharp_edges=sharp)
    # the degenerate end fans can fool recalc; make sure the side faces point outboard
    me = ob.data
    probe = [p for p in me.polygons if abs(p.center.y) < 1.0 and p.center.x > 1.5 and 4.5 < p.center.z < 5.8]
    if probe and probe[0].normal.x < 0:
        me.flip_normals()
    return ob

# ---------------------------------------------------------------- saddle tanks

ST_Y0, ST_Y1 = -20.5, 21.5     # tank extent (estimated)


def tank_section(y, side, nseg=40):
    L = (ST_Y1 - ST_Y0) / 2
    ym = (ST_Y0 + ST_Y1) / 2
    u = (y - ym) / L
    # plan envelope: full over most of the length, fairing in at the ends (bow end finer)
    p = 3.2 if u > 0 else 2.6
    f = max(0.0, 1 - abs(u) ** p) ** (1 / p)
    f = f ** 0.8
    a = 1.53 * f + 0.02
    xc = 1.90 - 0.75 * (1 - f)
    zc = 2.42 + 0.25 * (1 - f)
    b = 2.06 * (0.55 + 0.45 * f)
    e = 2.5
    pts = []
    for i in range(nseg):
        t = 2 * math.pi * i / nseg
        x = xc + a * se_pow(math.cos(t), 2 / e)
        z = zc + b * se_pow(math.sin(t), 2 / e)
        pts.append((side * x, y, z))
    if side < 0:
        pts.reverse()
    return pts


def build_saddle_tanks(coll):
    obs = []
    for side, nm in ((1, 'SaddleTank_S'), (-1, 'SaddleTank_P')):
        ys = stations(ST_Y0, ST_Y1, 120, end_density=3.0)
        rings = [tank_section(y, side) for y in ys]
        verts, faces = loft(rings, closed=True, cap_start=True, cap_end=True)
        ob = mesh_obj(nm, verts, faces, coll, mats=['M_HullPaint'], smooth=True)
        obs.append(ob)
    return obs

# ---------------------------------------------------------------- keel

def build_keel(coll):
    bm = bmesh.new()
    rings = []
    y0, y1 = -27.5, 26.5
    for y in stations(y0, y1, 60, end_density=4.0):
        u = (y - (y0 + y1) / 2) / ((y1 - y0) / 2)
        f = max(0.0, 1 - abs(u) ** 6) ** (1 / 6)
        hw = 0.05 + 0.42 * f
        zb = 0.15 - 0.5 * f
        top = 0.35
        rings.append([(hw, y, top), (hw, y, zb + 0.06), (hw - 0.06, y, zb), (-hw + 0.06, y, zb),
                      (-hw, y, zb + 0.06), (-hw, y, top)])
    add_loft_bm(bm, rings, closed=True, cap_start=True, cap_end=True, smooth=False)
    return bm_to_obj(bm, 'Keel_Ballast', coll, mats=['M_HullDark'])


def build_hull():
    get_coll(ROOT)
    c = reset_coll('Hull', ROOT)
    h = build_main_hull(c)
    tanks = build_saddle_tanks(c)
    k = build_keel(c)
    return h
