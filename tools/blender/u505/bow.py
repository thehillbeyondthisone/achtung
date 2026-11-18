# U-505 exterior model: bow fittings. Bow planes (2G-9C: permanently rigged out, 1500 mm
# above the pressure-hull bottom, just forward of the pressure hull), their streamlined
# guard horns, four bow-tube shutters, the starboard hawse pipe with a stockless anchor
# stowed flush (2G-9C), and the stem bar. Sizes are estimated.

BOWPLANE = dict(y_axis=30.2, z=1.5, root_c=1.35, tip_c=1.05, span=1.85)


def add_groove(bm, center, normal, up, w, h, t=0.035, seg=10, depth=0.004):
    """Elliptical dark outline (a shutter or plate seam) on a surface."""
    c = Vector(center); n = Vector(normal).normalized(); u = Vector(up).normalized()
    r = n.cross(u).normalized(); u = r.cross(n).normalized()
    N = seg * 4
    outer, inner = [], []
    for k in range(N):
        a = 2 * math.pi * k / N
        outer.append(bm.verts.new(c + n * depth + r * (w / 2) * math.cos(a) + u * (h / 2) * math.sin(a)))
        inner.append(bm.verts.new(c + n * depth + r * (w / 2 - t) * math.cos(a) + u * (h / 2 - t) * math.sin(a)))
    for k in range(N):
        k2 = (k + 1) % N
        bm.faces.new((outer[k], outer[k2], inner[k2], inner[k]))


def add_shutter_rim(bm, yc, zc, w, h, side, r=0.022, lift=0.012, n=40):
    """Raised rim round a tube shutter, following the hull surface point by point."""
    pts = []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        y = yc + (w / 2) * math.cos(a)
        z = zc + (h / 2) * math.sin(a)
        p, nrm = side_point(y, z, side)
        pts.append(p + nrm * lift)
    add_tube_path(bm, pts, r, seg=8, cap=False)


def build_bow():
    c = reset_coll('Bow', ROOT)
    B = BOWPLANE
    bm = bmesh.new()
    for side in (1, -1):
        root, _ = side_point(B['y_axis'], B['z'], side)
        rx = abs(root.x) - 0.12
        le_root = B['y_axis'] + 0.35 * B['root_c']
        le_tip = B['y_axis'] + 0.35 * B['tip_c'] - 0.12
        add_foil_surface(bm, B['root_c'], B['tip_c'], (side * rx, le_root, B['z']),
                         (side * (rx + B['span']), le_tip, B['z'] - 0.05), None, (0, -1, 0), thick=0.13)
        # plane shaft boss
        add_cyl(bm, (side * (rx - 0.1), B['y_axis'], B['z']), (side * (rx + 0.22), B['y_axis'], B['z']), 0.13, seg=16)
        # guard horn: from the hull forward of the plane, out and aft to just outboard of the tip
        gz = B['z'] + 0.02
        y0 = B['y_axis'] + 1.75
        r0, _ = side_point(y0, gz, side)
        tip_x = rx + B['span'] + 0.16
        pts = []
        for k in range(10):
            t = k / 9
            x = lerp(abs(r0.x) - 0.08, tip_x, math.sin(t * math.pi / 2) ** 0.8)
            y = lerp(y0, B['y_axis'] + 0.05, t ** 1.4)
            pts.append((side * x, y, gz))
        # tapered horn: sweep rings of decreasing radius
        rings = []
        for k, p in enumerate(pts):
            rr = lerp(0.16, 0.07, k / (len(pts) - 1))
            p = Vector(p)
            if k < len(pts) - 1:
                tdir = (Vector(pts[k + 1]) - p).normalized()
            else:
                tdir = (p - Vector(pts[k - 1])).normalized()
            nrm = Vector((0, 0, 1))
            bi = tdir.cross(nrm).normalized()
            rings.append([p + nrm * rr * 0.55 * math.sin(2 * math.pi * j / 16) + bi * rr * math.cos(2 * math.pi * j / 16) for j in range(16)])
        add_loft_bm(bm, rings, closed=True, cap_start=True, cap_end=True)
    # stem bar along the leading edge
    pts = []
    for k in range(40):
        y = 28.8 + (Y_BOW - 0.05 - 28.8) * k / 39
        pts.append((0, y + 0.03, zk_at(y) - 0.02))
    add_tube_path(bm, pts, 0.045, seg=8)
    # jumping-wire stem fitting at the deck tip
    add_box(bm, (0, Y_BOW - 0.45, zt_at(Y_BOW - 0.45) + 0.18), (0.08, 0.5, 0.36))
    add_cyl(bm, (-0.06, Y_BOW - 0.35, zt_at(Y_BOW) + 0.25), (0.06, Y_BOW - 0.35, zt_at(Y_BOW) + 0.25), 0.07, seg=12)
    bm_to_obj(bm, 'Bow_PlanesGuards', c, mats=['M_HullPaint'], smooth=True)

    # bow tube shutters and seam outlines
    bm_h = bmesh.new()
    bm_r = bmesh.new()
    for side in (1, -1):
        for zz, yy in ((1.85, 33.4), (3.15, 33.9)):
            pt, n = side_point(yy, zz, side)
            add_groove(bm_h, pt, n, (0, 0.25, 1), 0.96, 0.74, t=0.05)
            add_shutter_rim(bm_r, yy, zz, 0.84, 0.62, side)
            add_hole(bm_h, pt + Vector((0, -0.28, 0.12)), n, (0, 0, 1), 0.07, 0.07, round_=1.0, seg=4)
    # hawse pipe recess (starboard)
    pt, n = side_point(35.0, 5.35, 1)
    add_hole(bm_h, pt, n, (0, 0.5, 1), 0.62, 0.5, round_=1.0, seg=6)
    ob = bm_to_obj(bm_h, 'Bow_Outlines', c, mats=['M_Hole'], recalc=False)
    shrinkwrap(ob, 'Hull_Outer')
    bm_to_obj(bm_r, 'Bow_ShutterRims', c, mats=['M_HullPaint'], smooth=True)

    # stockless (Hall) anchor stowed in the hawse: crown and two flukes visible
    bm_a = bmesh.new()
    M = Matrix.Rotation(math.atan2(n.y, n.x), 3, 'Z')
    base = pt + n * 0.06
    add_box(bm_a, base, (0.12, 0.36, 0.26), rot=Matrix.Rotation(math.atan2(n.y, n.x), 4, 'Z'))
    for s in (1, -1):
        fl = base + Vector((0, s * 0.17, -0.05))
        add_box(bm_a, fl + n * 0.03, (0.07, 0.22, 0.34), rot=Matrix.Rotation(math.atan2(n.y, n.x), 4, 'Z') @ Matrix.Rotation(s * 0.35, 4, 'X'))
    bm_to_obj(bm_a, 'Bow_Anchor', c, mats=['M_Iron'], smooth=False)
