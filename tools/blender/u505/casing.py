# U-505 exterior model: hull-surface details. Free-flooding slots in the casing and
# saddle tanks, tank vent housings, deck-edge strake, plate seams and weld beads.
# Slot rows and counts are artistic, guided by Encl G 505/517.


def side_point(y, z, s=1):
    """Point and outward normal on the main hull (outer casing) at height z, side s."""
    hs = half_section(y)
    top = DECK_EDGE_IDX
    for i in range(top):
        x0, z0 = hs[i]
        x1, z1 = hs[i + 1]
        if (z0 - z) * (z1 - z) <= 0 and z1 != z0:
            t = (z - z0) / (z1 - z0)
            x = lerp(x0, x1, t)
            tx, tz = x1 - x0, z1 - z0
            L = math.hypot(tx, tz) or 1
            n = Vector((s * tz / L, 0, -tx / L))
            # make sure it points outward
            if n.x * s < 0:
                n = -n
            return Vector((s * x, y, z)), n.normalized()
    x, zz = hs[top]
    return Vector((s * x, y, zz)), Vector((s, 0, 0))


def tank_point(y, ang, s=1):
    """Point and normal on the saddle tank surface; ang in radians from the outboard
    extreme (0) toward the bottom (-pi/2) or top (+pi/2)."""
    nseg = 160
    ring = tank_section(y, 1, nseg=nseg)
    i = int(round((ang % (2 * math.pi)) / (2 * math.pi) * nseg)) % nseg
    p = Vector(ring[i])
    q0 = Vector(ring[i - 1]); q1 = Vector(ring[(i + 1) % nseg])
    t = (q1 - q0)
    n = Vector((t.z, 0, -t.x)).normalized()
    if n.x < 0 and abs(n.x) > abs(n.z):
        n = -n
    return Vector((s * p.x, p.y, p.z)), Vector((s * n.x, 0, n.z)).normalized()


def build_casing():
    c = reset_coll('Casing', ROOT)
    bm_h = bmesh.new()      # openings (dark)
    bm_s = bmesh.new()      # painted steel fittings
    tower_zone = (-7.3, 4.8)

    # ---- upper casing free-flooding slots: one long row each side, a second row forward
    y = -35.2
    k = 0
    while y < 33.5:
        p = hull_params(y)
        zrow = p['zt'] - 0.34
        if p['w'] > 0.5 and not (tower_zone[0] < y < tower_zone[1]):
            for s in (1, -1):
                pt, n = side_point(y, zrow, s)
                add_hole(bm_h, pt, n, (0, 0, 1), 0.30, 0.085, round_=1.0, seg=4, depth=0.006)
                if y > 16.0 or y < -27.0:
                    pt2, n2 = side_point(y + 0.26, zrow - 0.24, s)
                    add_hole(bm_h, pt2, n2, (0, 0, 1), 0.30, 0.085, round_=1.0, seg=4, depth=0.006)
        y += 0.52
        k += 1

    # ---- saddle-tank flooding slots near the bottom of each tank, in groups
    tank_holes = {}
    for s in (1, -1):
        bm_t = tank_holes[s] = bmesh.new()
        y = ST_Y0 + 2.2
        while y < ST_Y1 - 2.0:
            for row, ang in enumerate((-1.05, -1.25)):
                pt, n = tank_point(y + row * 0.22, ang if s > 0 else ang, s)
                add_hole(bm_t, pt, n, (0, 1, 0), 0.62, 0.11, round_=1.0, seg=4, depth=0.006)
            y += 1.05
    # ---- tank vent housings (Entlüftung) on top of the saddle tanks
    for s in (1, -1):
        for yv in (-16.5, -9.0, 7.5, 15.5):
            pt, n = tank_point(yv, 1.25, s)
            add_cyl(bm_s, pt - n * 0.05, pt + n * 0.16, 0.16, seg=16)
            add_cyl(bm_s, pt + n * 0.16, pt + n * 0.2, 0.19, seg=16)
            for b in range(8):
                a = 2 * math.pi * b / 8
                off = Vector((0, math.cos(a) * 0.165, 0)) + Vector((-n.z * s, 0, n.x * s)) * math.sin(a) * 0.165
                add_cyl(bm_s, pt + n * 0.2 + off, pt + n * 0.235 + off, 0.018, seg=6)
    # ---- weld seam beads on the saddle tanks (horizontal strakes and vertical butts)
    bm_w = bmesh.new()
    for s in (1, -1):
        for ang in (0.55, 0.0, -0.6):
            pts = []
            for yy in [ST_Y0 + 1.5 + i * 0.5 for i in range(int((ST_Y1 - ST_Y0 - 3) / 0.5) + 1)]:
                pt, n = tank_point(yy, ang, s)
                pts.append(pt + n * 0.002)
            add_tube_path(bm_w, pts, 0.0065, seg=6)
        yy = ST_Y0 + 3.0
        while yy < ST_Y1 - 2.5:
            pts = []
            for a in [-1.2 + i * 0.12 for i in range(21)]:
                pt, n = tank_point(yy, a, s)
                pts.append(pt + n * 0.002)
            add_tube_path(bm_w, pts, 0.006, seg=6)
            yy += 2.4
    # ---- vertical seams along the casing sides (frame butts) and a rubbing strake
    for s in (1, -1):
        yy = -34.0
        while yy < 33.0:
            if not (tower_zone[0] < yy < tower_zone[1]):
                p = hull_params(yy)
                z0 = max(p['zj'], 4.55 if ST_Y0 + 2 < yy < ST_Y1 - 2 else p['zj']) + 0.05
                pts = []
                for z in [z0 + (p['zt'] - 0.1 - z0) * i / 5 for i in range(6)]:
                    pt, n = side_point(yy, z, s)
                    pts.append(pt + n * 0.002)
                add_tube_path(bm_w, pts, 0.006, seg=5)
            yy += 2.4
        pts = []
        for yy in [-35.8 + i * 0.4 for i in range(int(70.0 / 0.4))]:
            p = hull_params(yy)
            pt, n = side_point(yy, p['zt'] - 0.12, s)
            pts.append(pt + n * 0.015)
        add_tube_path(bm_w, pts, 0.025, seg=6)
    ob = bm_to_obj(bm_h, 'Casing_Openings', c, mats=['M_Hole'], recalc=False)
    shrinkwrap(ob, 'Hull_Outer')
    for s, nm in ((1, 'S'), (-1, 'P')):
        ob = bm_to_obj(tank_holes[s], 'Casing_TankSlots_' + nm, c, mats=['M_Hole'], recalc=False)
        shrinkwrap(ob, 'SaddleTank_' + nm)
    bm_to_obj(bm_s, 'Casing_Vents', c, mats=['M_HullPaint'], smooth=True)
    bm_to_obj(bm_w, 'Casing_Seams', c, mats=['M_HullPaint'], smooth=True)
