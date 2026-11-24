# U-505 exterior model: conning-tower fairwater, bridge and Wintergarten platforms.
# Shape follows the capture photographs (Encl G 470, 499, 506, 517): a lower fairwater
# with a pronounced flared ledge at bridge-deck level, a bridge bulwark topped by an
# outward spray lip, an open upper platform aft of the bridge and a lower platform
# further aft. Dimensions are estimated from the photographs.

DECK_Z = 5.9
TW = dict(
    body_W=1.12, body_yf=4.30, body_yb=-4.30, body_ym=0.9,
    ledge_z=8.0, ledge_top=8.07, ledge_off=0.34,
    bul_W=1.30, bul_yf=4.45, bul_yb=-1.75, bul_ym=1.5, bul_top=9.42,
    aft_yf=-2.8, aft_yb=-7.05, aft_W=1.05, aft_ym=-4.0, low_plat_z=7.02,
)


HATCH_Y = -0.9      # upper conning-tower hatch, matching the game's hull.hatch.x_m
HATCH_RADIUS = 0.301
LADDER_X = 0.78     # lower -> upper platform ladders, each side
RUNG_Y = -5.6       # deck -> lower platform rungs on the aft fairing sides
# Gameplay fitting, not from the photographs: a ladder hung off each side of the upper platform down
# to the walkway beside the fairwater. With the boat 21-23 degrees stern-down in the game's Act 3 and
# 7 June scenes the aft rungs land in the sea, so this keeps the dry forward deck reachable.
SIDE_LADDER_Y, SIDE_LADDER_X = -2.5, 1.36
# Gameplay fitting, not from the photographs: rungs up each side of the fairwater and over the bridge
# bulwark, forward of the bridge fittings. As the 7 June boat settles stern-down the side ladders flood
# first; this route back to the hatch from the forward deck stays dry about 2 m longer.
FWD_RUNG_Y, FWD_RUNG_X = 2.6, 1.42


def split_runs(path, keep):
    """Split a polyline into contiguous runs of points that pass keep()."""
    runs, cur = [], []
    for p in path:
        if keep(p):
            cur.append(p)
        elif cur:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
    if len(cur) > 1:
        runs.append(cur)
    return runs


def upper_edge_y(x):
    """Aft edge (railing line) of the upper platform at |x|."""
    T = TW
    upl = egg(T['body_W'] + T['ledge_off'] - 0.05, T['body_yf'], T['body_yb'] - 0.02, T['body_ym'],
              n=400, ef=1.55, eb=2.4)
    aft = [p for p in upl if p[1] < T['body_ym']]
    return min(aft, key=lambda p: abs(abs(p[0]) - abs(x)))[1]


def egg(W, yf, yb, ym, n=72, es=2.6, ef=1.7, eb=2.1, a0=0.0, a1=2 * math.pi, closed=True):
    """Plan outline (x, y) with a rounded bow-ward end and fuller aft end.
    alpha = 0 starboard, pi/2 forward, pi port, 3pi/2 aft."""
    pts = []
    cnt = n if closed else n + 1
    for i in range(cnt):
        a = a0 + (a1 - a0) * i / n
        c, s = math.cos(a), math.sin(a)
        x = W * se_pow(c, 2 / es)
        if s >= 0:
            y = ym + (yf - ym) * abs(s) ** (2 / ef)
        else:
            y = ym - (ym - yb) * abs(s) ** (2 / eb)
        pts.append((x, y))
    return pts


def plan_normals(pts, closed=True):
    out = []
    n = len(pts)
    for i in range(n):
        if closed:
            p0, p1 = pts[i - 1], pts[(i + 1) % n]
        else:
            p0 = pts[max(i - 1, 0)]
            p1 = pts[min(i + 1, n - 1)]
        tx, ty = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(tx, ty) or 1.0
        # outward for CCW (alpha increasing) curves: rotate tangent clockwise
        out.append((ty / L, -tx / L))
    return out


def sweep(bm, plan, profile, closed=True, cap_top=None, cap_bottom=None, mat_index=0, smooth=True):
    """Sweep a (offset, z) profile along a plan outline. cap_top: z for a fan cap at the
    last profile point (uses its offset outline)."""
    nrm = plan_normals(plan, closed)
    rings = []
    for (off, z) in profile:
        rings.append([(p[0] + n[0] * off, p[1] + n[1] * off, z) for p, n in zip(plan, nrm)])
    vr = add_loft_bm(bm, rings, closed=closed, mat_index=mat_index, smooth=smooth)
    if cap_top is not None and closed:
        ring = vr[-1]
        cx = sum(v.co.x for v in ring) / len(ring)
        cy = sum(v.co.y for v in ring) / len(ring)
        c = bm.verts.new((cx, cy, ring[0].co.z))
        for i in range(len(ring)):
            f = bm.faces.new((ring[i], ring[(i + 1) % len(ring)], c))
            f.material_index = mat_index
    if cap_bottom is not None and closed:
        ring = vr[0]
        cx = sum(v.co.x for v in ring) / len(ring)
        cy = sum(v.co.y for v in ring) / len(ring)
        c = bm.verts.new((cx, cy, ring[0].co.z))
        for i in range(len(ring)):
            f = bm.faces.new((ring[(i + 1) % len(ring)], ring[i], c))
            f.material_index = mat_index
    return vr


def offset_outline(plan, off, closed=True):
    nrm = plan_normals(plan, closed)
    return [(p[0] + n[0] * off, p[1] + n[1] * off) for p, n in zip(plan, nrm)]


def add_plate_outline(bm, outline, z, thick, mat_index=0):
    """Flat plate with the given outline (convex), thickness downward."""
    n = len(outline)
    top = [bm.verts.new((x, y, z)) for x, y in outline]
    bot = [bm.verts.new((x, y, z - thick)) for x, y in outline]
    f = bm.faces.new(top); f.material_index = mat_index
    f = bm.faces.new(list(reversed(bot))); f.material_index = mat_index
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((bot[i], bot[j], top[j], top[i]))
        f.material_index = mat_index


def railing(bm_pipe, bm_net, path, z0, height=1.0, spacing=0.55, r=0.021, mid=True, net=True):
    """Pipe railing along a plan polyline at deck height z0."""
    pts = [Vector((p[0], p[1], 0)) for p in path]
    # resample stanchion positions
    seglens = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seglens)
    nst = max(2, int(total / spacing) + 1)

    def at(d):
        for i, L in enumerate(seglens):
            if d <= L or i == len(seglens) - 1:
                t = d / L if L > 0 else 0
                return pts[i].lerp(pts[i + 1], min(t, 1.0))
            d -= L
        return pts[-1]
    for k in range(nst):
        p = at(total * k / (nst - 1))
        add_cyl(bm_pipe, (p.x, p.y, z0), (p.x, p.y, z0 + height), r, seg=8)
        add_cyl(bm_pipe, (p.x, p.y, z0), (p.x, p.y, z0 + 0.03), r * 2.2, seg=8)
        for dx, dy in ((r, r), (-r, -r)):
            add_cyl(bm_pipe, (p.x + dx, p.y + dy, z0 + 0.028),
                    (p.x + dx, p.y + dy, z0 + 0.037), 0.009, seg=6)
        if mid:
            z = z0 + height * 0.5
            add_cyl(bm_pipe, (p.x, p.y, z - 0.02), (p.x, p.y, z + 0.02), r * 1.28, seg=8)
    top = [(p[0], p[1], z0 + height) for p in path]
    add_tube_path(bm_pipe, top, r * 1.15, seg=8)
    if mid:
        add_tube_path(bm_pipe, [(p[0], p[1], z0 + height * 0.5) for p in path], r * 0.9, seg=8)
    if net and bm_net is not None:
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            vs = [bm_net.verts.new((a[0], a[1], z0 + 0.04)), bm_net.verts.new((b[0], b[1], z0 + 0.04)),
                  bm_net.verts.new((b[0], b[1], z0 + height - 0.03)), bm_net.verts.new((a[0], a[1], z0 + height - 0.03))]
            bm_net.faces.new(vs)


def add_hole(bm, center, normal, up, w, h, mat_index=0, depth=0.012, round_=0.5, seg=6):
    """Dark rounded-rect inset that reads as an opening (slot, porthole)."""
    c = Vector(center); n = Vector(normal).normalized(); u = Vector(up).normalized()
    r = n.cross(u).normalized(); u = r.cross(n).normalized()
    rad = min(w, h) * 0.5 * round_
    pts = []
    for cx, cy, a0 in ((w / 2 - rad, h / 2 - rad, 0), (-w / 2 + rad, h / 2 - rad, 90),
                       (-w / 2 + rad, -h / 2 + rad, 180), (w / 2 - rad, -h / 2 + rad, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    ring = [bm.verts.new(c + n * depth + r * px + u * py) for px, py in pts]
    f = bm.faces.new(ring)
    f.material_index = mat_index


def tower_ring(bm, x, y, profile, mat_index=0, seg=28):
    """Turn a closed (radius, height) section around a vertical axis."""
    directions = [(math.cos(2 * math.pi * k / seg), math.sin(2 * math.pi * k / seg)) for k in range(seg)]
    rings = [[(x + r * a, y + r * b, z) for a, b in directions] for r, z in profile]
    verts = add_loft_bm(bm, rings, mat_index=mat_index)
    for k in range(seg):
        j = (k + 1) % seg
        face = bm.faces.new((verts[-1][k], verts[-1][j], verts[0][j], verts[0][k]))
        face.material_index = mat_index


def add_bridge_hatch(bm, floor):
    """Open coaming and lid, with a recessed dark throat above the fairwater cap."""
    y = HATCH_Y
    tower_ring(bm, 0, y, [(0.36, floor - 0.02), (0.36, floor + 0.13),
                           (0.352, floor + 0.15), (0.317, floor + 0.15),
                           (HATCH_RADIUS, floor + 0.128), (HATCH_RADIUS, floor - 0.047)])
    tower_ring(bm, 0, y, [(0.352, floor + 0.15), (0.35, floor + 0.16),
                           (0.32, floor + 0.16), (0.317, floor + 0.15)], mat_index=1)
    tower_ring(bm, 0, y, [(HATCH_RADIUS, floor + 0.097), (HATCH_RADIUS, floor + 0.118),
                           (0.292, floor + 0.118), (0.292, floor + 0.097)], mat_index=4)
    add_cyl(bm, (0, y, floor - 0.059), (0, y, floor - 0.043), 0.302, seg=36, mat_index=2)
    # Show the top rung and rounded sides of the ladder beneath the coaming.
    for x in (-0.156, 0.156):
        add_tube_path(bm, [(x, y + 0.234, floor - 0.04), (x, y + 0.234, floor + 0.045),
                           (x, y + 0.216, floor + 0.085)], 0.016, seg=8)
    add_cyl(bm, (-0.155, y + 0.23, floor + 0.018), (0.155, y + 0.23, floor + 0.018),
            0.016, seg=8, mat_index=1)
    # Hinge cheeks, cross pin, and the lid's original retaining stay.
    for x in (-0.115, 0.115):
        add_box(bm, (x, y - 0.341, floor + 0.14), (0.068, 0.073, 0.10))
    add_cyl(bm, (-0.145, y - 0.372, floor + 0.181), (0.145, y - 0.372, floor + 0.181), 0.033, seg=12)
    for x in (-0.153, 0.153):
        a, b = x - 0.008, x + 0.008
        add_cyl(bm, (a, y - 0.372, floor + 0.181), (b, y - 0.372, floor + 0.181), 0.026, seg=8, mat_index=1)
    add_cyl(bm, (0, y - 0.36, floor + 0.18), (0, y - 0.41, floor + 0.9), 0.04, seg=8)

    # Build the lid flat, then place it at the established angle and offset.
    existing = set(bm.verts)
    add_cyl(bm, (0, 0, 0), (0, 0, 0.081), 0.37, seg=28)
    add_cyl(bm, (0, 0, 0.08), (0, 0, 0.106), 0.335, r1=0.235, seg=28)
    tower_ring(bm, 0, 0, [(0.345, -0.014), (0.345, 0.003),
                           (0.322, 0.003), (0.322, -0.014)], mat_index=4)
    add_box(bm, (0, 0, 0.10), (0.12, 0.50, 0.05))
    add_box(bm, (0, 0, -0.019), (0.105, 0.43, 0.03))
    for x in (-0.115, 0.115):
        add_box(bm, (x, -0.337, -0.01), (0.058, 0.13, 0.045))
    add_cyl(bm, (0, 0, -0.063), (0, 0, -0.014), 0.044, seg=12, mat_index=1)
    wheel = [(0.115 * math.cos(k * math.tau / 24), 0.115 * math.sin(k * math.tau / 24), -0.066) for k in range(25)]
    add_tube_path(bm, wheel, 0.011, seg=7, cap=False)
    for k in range(4):
        a = k * math.tau / 4
        add_cyl(bm, (0, 0, -0.066), (0.115 * math.cos(a), 0.115 * math.sin(a), -0.066), 0.009, seg=6)
    added = [v for v in bm.verts if v not in existing]
    bmesh.ops.rotate(bm, verts=added, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(80), 3, 'X'))
    bmesh.ops.translate(bm, verts=added, vec=(0, y - 0.36, floor + 0.57))


def add_bridge_details(bm, bulwark, floor, lip):
    """Interior face of the bulwark and the close-range bridge instrument fittings."""
    normals = plan_normals(bulwark, closed=False)
    inset = offset_outline(bulwark, -0.063, closed=False)
    # Bodies of the ribs sit against the inner wall. Keep the ladder exit clear.
    for side in (-1, 1):
        indices = [k for k, (x, _) in enumerate(inset) if x * side > 0]
        for along in (-0.65, 0.32, 1.19, 2.99, 3.58):
            k = min(indices, key=lambda i: abs(inset[i][1] - along))
            x, y = inset[k]
            nx, ny = normals[k]
            rot = Matrix.Rotation(math.atan2(ny, nx), 4, 'Z')
            add_box(bm, (x, y, (floor + lip) / 2), (0.041, 0.063, lip - floor - 0.12), rot=rot)
            add_box(bm, (x - nx * 0.009, y - ny * 0.009, floor + 0.025), (0.065, 0.096, 0.05), rot=rot)
            for z in (floor + 0.19, floor + 0.52, lip - 0.18):
                a = (x - nx * 0.020, y - ny * 0.020, z)
                b = (x - nx * 0.027, y - ny * 0.027, z)
                add_cyl(bm, a, b, 0.012, seg=6, mat_index=1)
    add_tube_path(bm, [(x, y, lip - 0.043) for x, y in inset], 0.009, seg=6, mat_index=1)

    # Repeater compass face, rim, index and pointer.
    cx, cy, cz = 0.45, 3.1, floor + 1.051
    add_cyl(bm, (cx, cy, cz - 0.001), (cx, cy, cz + 0.003), 0.112, seg=24, mat_index=2)
    tower_ring(bm, cx, cy, [(0.123, cz - 0.003), (0.12, cz + 0.015),
                            (0.108, cz + 0.015), (0.108, cz - 0.003)], mat_index=1)
    for k in range(16):
        a = k * math.tau / 16
        r = 0.086 if k % 4 == 0 else 0.094
        add_box(bm, (cx + r * math.cos(a), cy + r * math.sin(a), cz + 0.004),
                (0.026 if k % 4 == 0 else 0.012, 0.0035, 0.003),
                rot=Matrix.Rotation(a, 4, 'Z'), mat_index=3)
    add_box(bm, (cx + 0.024, cy, cz + 0.008), (0.095, 0.008, 0.004),
            rot=Matrix.Rotation(0.38, 4, 'Z'), mat_index=3)

    # The rudder indicator faces aft. Ticks and needle sit above its backing plate.
    add_box(bm, (-0.75, 2.848, floor + 0.75), (0.148, 0.013, 0.174), mat_index=1)
    add_box(bm, (-0.75, 2.84, floor + 0.75), (0.124, 0.006, 0.145), mat_index=2)
    for k in range(-3, 4):
        a = k * 0.26
        x = -0.75 + 0.058 * math.sin(a)
        z = floor + 0.72 + 0.064 * math.cos(a)
        add_box(bm, (x, 2.835, z), (0.004, 0.004, 0.012),
                rot=Matrix.Rotation(a, 4, 'Y'), mat_index=3)
    add_box(bm, (-0.755, 2.834, floor + 0.752), (0.004, 0.004, 0.063),
            rot=Matrix.Rotation(-0.15, 4, 'Y'), mat_index=3)
    add_tube_path(bm, [(-0.75, 2.90, floor + 0.64), (-0.75, 2.90, floor + 0.32),
                       (-0.79, 2.93, floor + 0.25), (-0.87, 2.96, floor + 0.2),
                       (-0.88, 2.96, floor + 0.01)], 0.009, seg=8, mat_index=4)

    # Signal-lamp bezel and lens, and two fasteners on its foot.
    add_cyl(bm, (0.9, 1.45, floor + 0.95), (0.9, 1.439, floor + 0.95), 0.095, seg=20, mat_index=1)
    add_cyl(bm, (0.9, 1.438, floor + 0.95), (0.9, 1.433, floor + 0.95), 0.073, seg=20, mat_index=3)
    add_cyl(bm, (0.9, 1.5, floor - 0.005), (0.9, 1.5, floor + 0.022), 0.047, seg=12)
    for y in (1.47, 1.53):
        add_cyl(bm, (0.9, y, floor + 0.022), (0.9, y, floor + 0.031), 0.009, seg=6, mat_index=1)


def build_tower():
    c = reset_coll('Tower', ROOT)
    T = TW
    # ---------------------------------------------------------------- fairwater body
    bm = bmesh.new()
    body = egg(T['body_W'], T['body_yf'], T['body_yb'], T['body_ym'], n=96, ef=1.55, eb=2.4)
    lz, lt, lo = T['ledge_z'], T['ledge_top'], T['ledge_off']
    prof = [(0.22, DECK_Z - 0.12), (0.17, DECK_Z), (0.09, DECK_Z + 0.08), (0.03, DECK_Z + 0.2),
            (0.0, DECK_Z + 0.45), (0.0, lz - 0.38), (0.015, lz - 0.26), (0.06, lz - 0.16),
            (0.14, lz - 0.08), (0.25, lz - 0.025), (lo, lz), (lo + 0.01, lz + 0.02),
            (lo + 0.01, lt - 0.02), (lo - 0.01, lt)]
    sweep(bm, body, prof, cap_top=lt)
    bm_to_obj(bm, 'Tower_Fairwater', c, mats=['M_HullPaint'], smooth=True)

    # ---------------------------------------------------------------- aft fairing (lower platform)
    bm = bmesh.new()
    aft = egg(T['aft_W'], T['aft_yf'], T['aft_yb'], T['aft_ym'], n=72, ef=2.4, eb=1.9)
    pz = T['low_plat_z']
    prof = [(0.2, DECK_Z - 0.12), (0.15, DECK_Z), (0.07, DECK_Z + 0.1), (0.0, DECK_Z + 0.35),
            (0.0, pz - 0.3), (0.03, pz - 0.15), (0.12, pz - 0.05), (0.2, pz), (0.2, pz + 0.05)]
    sweep(bm, aft, prof, cap_top=pz + 0.05)
    bm_to_obj(bm, 'Tower_AftFairing', c, mats=['M_HullPaint'], smooth=True)

    # ---------------------------------------------------------------- bridge bulwark (open aft)
    bm = bmesh.new()
    gap = math.radians(38)  # opening aft, each side of the centreline
    a0 = -math.pi / 2 + gap
    a1 = 3 * math.pi / 2 - gap
    bul = egg(T['bul_W'], T['bul_yf'], T['bul_yb'], T['bul_ym'], n=110, ef=1.5, eb=2.2,
              a0=a0, a1=a1, closed=False)
    bt = T['bul_top']
    prof = [(-0.05, lt - 0.01), (0.0, lt - 0.01), (0.0, lt + 0.05), (0.01, bt - 0.2), (0.03, bt - 0.1),
            (0.09, bt - 0.04), (0.15, bt - 0.015), (0.16, bt), (0.12, bt + 0.015), (-0.04, bt + 0.015),
            (-0.05, bt), (-0.05, lt - 0.01)]
    vr = sweep(bm, bul, prof, closed=False)
    # end caps of the wall
    for ring_idx in (0, -1):
        col = [r[ring_idx] for r in vr[:-1]]
        f = bm.faces.new(col if ring_idx == 0 else list(reversed(col)))
    bm_to_obj(bm, 'Tower_Bulwark', c, mats=['M_HullPaint'], smooth=True)

    # ---------------------------------------------------------------- compass hood at the base front
    bm = bmesh.new()
    rings = []
    for i in range(14):
        t = i / 13
        y = 4.15 + 1.35 * t
        k = math.sqrt(max(0.0, 1 - t ** 2.2))
        hw, hh = 0.42 * k + 0.01, 0.78 * k + 0.01
        ring = []
        for j in range(25):
            a = math.pi * j / 24
            ring.append((hw * math.cos(a), y, DECK_Z - 0.05 + hh * math.sin(a)))
        rings.append(ring)
    add_loft_bm(bm, rings, closed=False, cap_end=False)
    bm_to_obj(bm, 'Tower_CompassHood', c, mats=['M_HullPaint'], smooth=True)

    # ---------------------------------------------------------------- floors
    bm = bmesh.new()
    inner = offset_outline(egg(T['bul_W'], T['bul_yf'], T['bul_yb'], T['bul_ym'], n=96, ef=1.5, eb=2.2), -0.06)
    # bridge floor grating: slats running athwartships
    ylo = min(p[1] for p in inner); yhi = max(p[1] for p in inner)
    yy = ylo + 0.05
    while yy < yhi - 0.05:
        # find half-width at this y from the inner outline
        xs = [abs(p[0]) for p in inner if abs(p[1] - yy) < 0.12]
        if xs:
            hw = max(xs) - 0.03
            edge = max(0, abs(yy - HATCH_Y) - 0.035)
            if edge < HATCH_RADIUS:
                cut = math.sqrt(HATCH_RADIUS ** 2 - edge ** 2)
                if cut < hw:
                    for side in (-1, 1):
                        add_box(bm, (side * (hw + cut) / 2, yy, lt + 0.035), (hw - cut, 0.07, 0.05))
            else:
                add_box(bm, (0, yy, lt + 0.035), (2 * hw, 0.07, 0.05))
        yy += 0.105
    # upper platform grating (aft of bridge)
    up = offset_outline(egg(T['body_W'], T['body_yf'], T['body_yb'], T['body_ym'], n=96, ef=1.55, eb=2.4), lo - 0.08)
    yy = T['body_yb'] + lo - 0.02
    while yy < T['bul_yb'] + 0.2:
        xs = [abs(p[0]) for p in up if abs(p[1] - yy) < 0.12]
        if xs:
            hw = max(xs) - 0.03
            add_box(bm, (0, yy, lt + 0.035), (2 * hw, 0.07, 0.05))
        yy += 0.105
    # lower platform grating
    lp = offset_outline(aft, 0.12)
    yy = T['aft_yb'] + 0.1
    while yy < T['body_yb'] + 0.25:
        xs = [abs(p[0]) for p in lp if abs(p[1] - yy) < 0.12]
        if xs:
            hw = max(xs) - 0.03
            add_box(bm, (0, yy, pz + 0.085), (2 * hw, 0.07, 0.05))
        yy += 0.105
    bm_to_obj(bm, 'Tower_Gratings', c, mats=['M_GratingWood'])

    # ---------------------------------------------------------------- railings and netting
    bm_p = bmesh.new(); bm_n = bmesh.new()
    # upper platform: from the starboard bulwark end, round the aft end, to the port end
    upl = egg(T['body_W'] + lo - 0.05, T['body_yf'], T['body_yb'] - 0.02, T['body_ym'], n=96, ef=1.55, eb=2.4)
    # outline order runs starboard -> forward -> port -> aft, so the aft run is contiguous.
    # Gaps are left where the ladders from the lower platform arrive (|x| around LADDER_X).
    path = [p for p in upl if p[1] < T['bul_yb'] + 0.45]
    keep = lambda p: (not (LADDER_X - 0.26 < abs(p[0]) < LADDER_X + 0.26)
                      and not (abs(p[1] - SIDE_LADDER_Y) < 0.3 and abs(p[0]) > 0.9))
    for run in split_runs(path, keep):
        railing(bm_p, bm_n, run, lt + 0.05, height=1.0, spacing=0.6)
    # forward rungs up the fairwater and over the bulwark, with a foot step inside (gameplay fitting)
    for s in (1, -1):
        zb, ztop = DECK_Z + 0.05, T['bul_top'] + 0.05
        for dy in (-0.18, 0.18):
            add_tube_path(bm_p, [(s * FWD_RUNG_X, FWD_RUNG_Y + dy, zb), (s * FWD_RUNG_X, FWD_RUNG_Y + dy, ztop - 0.02)], 0.02, seg=8)
            add_box(bm_p, (s * FWD_RUNG_X, FWD_RUNG_Y + dy, zb + 0.012), (0.075, 0.083, 0.024))
            # handhold arching over the bulwark lip
            add_tube_path(bm_p, [(s * FWD_RUNG_X, FWD_RUNG_Y + dy, ztop - 0.02), (s * 1.35, FWD_RUNG_Y + dy, ztop + 0.18),
                                 (s * 1.12, FWD_RUNG_Y + dy, ztop + 0.12), (s * 1.08, FWD_RUNG_Y + dy, ztop - 0.25)], 0.02, seg=8)
        for k in range(1, 12):
            z = lerp(zb, ztop, k / 12)
            add_cyl(bm_p, (s * FWD_RUNG_X, FWD_RUNG_Y - 0.18, z), (s * FWD_RUNG_X, FWD_RUNG_Y + 0.18, z), 0.017, seg=6)
        add_box(bm_p, (s * 1.0, FWD_RUNG_Y, lt + 0.62), (0.16, 0.36, 0.04))   # inside step
    # side ladders from the upper platform edge down to the deck walkway (gameplay fitting)
    for s in (1, -1):
        zb, zt_ = DECK_Z + 0.05, lt + 0.06
        for dy in (-0.2, 0.2):
            add_tube_path(bm_p, [(s * SIDE_LADDER_X, SIDE_LADDER_Y + dy, zb),
                                 (s * SIDE_LADDER_X, SIDE_LADDER_Y + dy, zt_ + 0.9)], 0.022, seg=8)
            add_box(bm_p, (s * SIDE_LADDER_X, SIDE_LADDER_Y + dy, zb + 0.012), (0.075, 0.083, 0.024))
            add_cyl(bm_p, (s * (SIDE_LADDER_X - 0.08), SIDE_LADDER_Y + dy, zt_ - 0.038),
                    (s * SIDE_LADDER_X, SIDE_LADDER_Y + dy, zt_ - 0.038), 0.027, seg=8)
        for k in range(1, 8):
            z = lerp(zb, zt_, k / 7)
            add_cyl(bm_p, (s * SIDE_LADDER_X, SIDE_LADDER_Y - 0.2, z), (s * SIDE_LADDER_X, SIDE_LADDER_Y + 0.2, z), 0.018, seg=6)
    # lower platform: around the aft end only, open at the side rungs from the deck
    lpl = offset_outline(aft, 0.17)
    path2 = [p for p in lpl if p[1] < T['body_yb'] + 0.1]
    for run in split_runs(path2, lambda p: abs(p[1] - RUNG_Y) > 0.36):
        railing(bm_p, bm_n, run, pz + 0.1, height=1.0, spacing=0.6)
    # steep ladders from the lower platform up to the upper platform, one each side
    for s in (1, -1):
        yt = upper_edge_y(LADDER_X) - 0.03
        yb = yt - 0.42
        zb, zt_ = pz + 0.11, lt + 0.06
        for dx in (-0.2, 0.2):
            add_tube_path(bm_p, [(s * LADDER_X + dx, yb, zb), (s * LADDER_X + dx, yt, zt_ + 0.75)], 0.022, seg=8)
            add_box(bm_p, (s * LADDER_X + dx, yb, zb + 0.012), (0.075, 0.083, 0.024))
        for k in range(1, 5):
            t = k / 5
            add_cyl(bm_p, (s * LADDER_X - 0.2, lerp(yb, yt, t), lerp(zb, zt_, t)),
                    (s * LADDER_X + 0.2, lerp(yb, yt, t), lerp(zb, zt_, t)), 0.018, seg=6)
    bm_to_obj(bm_p, 'Tower_Railings', c, mats=['M_Galv'], smooth=True)
    bm_to_obj(bm_n, 'Tower_Netting', c, mats=['M_Netting'], recalc=False)

    # ---------------------------------------------------------------- bridge equipment
    bm = bmesh.new()
    details = bmesh.new()
    fz = lt + 0.06
    # periscope standards (sky periscope forward, attack periscope aft), streamlined
    for (py, top, rb, rt) in ((1.55, bt + 0.95, 0.30, 0.17), (0.35, bt + 0.55, 0.26, 0.14)):
        rings = []
        for i in range(10):
            t = i / 9
            z = fz + (top - fz) * t
            rx = lerp(rb, rt, t ** 0.8)
            ry = rx * 1.55
            rings.append([(rx * math.cos(2 * math.pi * k / 24), py - ry * 0.3 + ry * math.sin(2 * math.pi * k / 24) * (1.0 if math.sin(2 * math.pi * k / 24) > 0 else 0.8), z) for k in range(24)])
        add_loft_bm(bm, rings, closed=True, cap_end=True)
        add_cyl(bm, (0, py, top), (0, py, top + 0.05), rt * 1.25, seg=20)
        # Low flanges and bolts sit inside the area occupied by each standard.
        flange = [(x * 1.115, py + (y - py) * 1.115) for x, y, _ in rings[0]]
        add_plate_outline(details, flange, fz + 0.03, 0.035)
        for x, y, _ in rings[0][::3]:
            x, y = x * 1.057, py + (y - py) * 1.057
            add_cyl(details, (x, y, fz + 0.029), (x, y, fz + 0.043), 0.011, seg=6, mat_index=1)
    # sky periscope raised, with head and lifting collar
    add_cyl(bm, (0, 1.55, bt + 0.95), (0, 1.55, bt + 3.6), 0.095, seg=20)
    add_cyl(bm, (0, 1.55, bt + 2.2), (0, 1.55, bt + 2.26), 0.16, seg=20)
    add_cyl(bm, (0, 1.55, bt + 3.6), (0, 1.55, bt + 4.15), 0.095, r1=0.06, seg=20)
    add_box(bm, (0, 1.62, bt + 3.98), (0.11, 0.08, 0.13))
    # attack periscope head (retracted) just above its standard
    add_cyl(bm, (0, 0.35, bt + 0.55), (0, 0.35, bt + 0.9), 0.07, r1=0.035, seg=16)
    # UZO pedestal at the bridge front
    add_cyl(bm, (0, 3.75, fz), (0, 3.75, fz + 1.05), 0.085, seg=16)
    add_cyl(bm, (0, 3.75, fz + 1.05), (0, 3.75, fz + 1.15), 0.14, seg=16)
    add_box(bm, (0, 3.8, fz + 1.22), (0.22, 0.12, 0.1))
    add_cyl(bm, (-0.07, 3.85, fz + 1.22), (-0.07, 3.95, fz + 1.24), 0.03, seg=10)
    add_cyl(bm, (0.07, 3.85, fz + 1.22), (0.07, 3.95, fz + 1.24), 0.03, seg=10)
    # compass repeater binnacle
    add_cyl(bm, (0.45, 3.1, fz), (0.45, 3.1, fz + 0.95), 0.08, seg=14)
    add_cyl(bm, (0.45, 3.1, fz + 0.95), (0.45, 3.1, fz + 1.05), 0.15, r1=0.13, seg=18)
    # voice pipe and bridge rudder indicator
    add_tube_path(bm, [(-0.55, 3.2, fz), (-0.55, 3.2, fz + 0.8), (-0.52, 3.35, fz + 0.95)], 0.035, seg=10)
    add_cyl(bm, (-0.52, 3.35, fz + 0.95), (-0.5, 3.45, fz + 1.0), 0.06, r1=0.075, seg=12)
    add_box(bm, (-0.75, 2.9, fz + 0.75), (0.18, 0.1, 0.22))
    # retractable rod antenna housing (port side of the bridge)
    add_cyl(bm, (-0.95, 0.8, fz), (-0.95, 0.8, bt + 0.25), 0.07, seg=14)
    add_cyl(bm, (-0.95, 0.8, bt + 0.25), (-0.95, 0.8, bt + 2.3), 0.018, seg=8)
    # signal lamp bracket and lamp
    add_cyl(bm, (0.9, 1.5, fz), (0.9, 1.5, fz + 0.9), 0.03, seg=8)
    add_cyl(bm, (0.9, 1.45, fz + 0.95), (0.9, 1.65, fz + 0.95), 0.1, seg=16)
    bm_to_obj(bm, 'Tower_BridgeGear', c, mats=['M_Gunmetal'], smooth=True)
    add_bridge_hatch(details, fz)
    add_bridge_details(details, bul, fz, bt)
    bm_to_obj(details, 'Tower_BridgeDetails', c,
              mats=['M_Gunmetal', 'M_Galv', 'M_Hole', 'M_Porcelain', 'M_Iron'])

    # ---------------------------------------------------------------- side lights, rungs, openings
    bm = bmesh.new()
    bm_h = bmesh.new()
    bm_h2 = bmesh.new()
    for s in (1, -1):
        # navigation light boxes on the bulwark sides
        add_box(bm, (s * (T['bul_W'] + 0.05), 2.4, bt - 0.45), (0.12, 0.42, 0.22))
        add_box(bm, (s * (T['bul_W'] + 0.03), 2.6, bt - 0.45), (0.07, 0.04, 0.2))
        # rungs on the aft fairing side (deck to lower platform)
        for k in range(4):
            z = DECK_Z + 0.25 + 0.27 * k
            yR = RUNG_Y
            xo = T['aft_W'] + 0.05
            add_tube_path(bm, [(s * (xo - 0.02), yR - 0.18, z), (s * (xo + 0.09), yR - 0.18, z), (s * (xo + 0.09), yR + 0.18, z), (s * (xo - 0.02), yR + 0.18, z)], 0.014, seg=6)
        # grab rails on the fairwater sides
        add_tube_path(bm, [(s * (T['body_W'] - 0.01), -3.0, 7.0), (s * (T['body_W'] + 0.07), -3.0, 7.0), (s * (T['body_W'] + 0.07), -1.2, 7.0), (s * (T['body_W'] - 0.01), -1.2, 7.0)], 0.016, seg=6)
        # round openings below the ledge, forward
        yh = 3.55
        xh = None
        for p in body:
            if p[0] * s > 0 and abs(p[1] - yh) < 0.15:
                xh = p[0]
        if xh is not None:
            add_hole(bm_h, (xh, yh, lz - 0.55), (s * 0.9, 0.45, 0), (0, 0, 1), 0.2, 0.2, round_=1.0, seg=8)
        # free-flooding slots along the fairwater base
        for k in range(10):
            yy = -3.4 + 0.6 * k
            xs = [p[0] for p in body if p[0] * s > 0 and abs(p[1] - yy) < 0.1]
            if xs:
                xh = max(xs, key=abs)
                add_hole(bm_h, (xh, yy, DECK_Z + 0.42), (s, 0, 0), (0, 0, 1), 0.38, 0.09, round_=1.0, seg=4)
        for k in range(6):
            yy = -6.6 + 0.55 * k
            xs = [p[0] for p in aft if p[0] * s > 0 and abs(p[1] - yy) < 0.1]
            if xs:
                xh = max(xs, key=abs)
                add_hole(bm_h2, (xh, yy, DECK_Z + 0.4), (s, 0, 0), (0, 0, 1), 0.34, 0.09, round_=1.0, seg=4)
    bm_to_obj(bm, 'Tower_Fittings', c, mats=['M_HullPaint'], smooth=True)
    ob = bm_to_obj(bm_h, 'Tower_Openings', c, mats=['M_Hole'], recalc=False)
    shrinkwrap(ob, 'Tower_Fairwater')
    ob = bm_to_obj(bm_h2, 'Tower_AftOpenings', c, mats=['M_Hole'], recalc=False)
    shrinkwrap(ob, 'Tower_AftFairing')
