# U-505 exterior model: stern gear. Twin screws, shafts and brackets, twin balanced spade
# rudders, stern planes, propeller guards, deadwood skeg and stern tube doors.
# From 2G-9C: rudders are 975 mm off the centreline and 225 mm inboard of the propeller
# centres, plane area 3.111 m2 each; the propeller guards run outboard forward of the
# rudders, then aft to the stern-plane axis, which supports them. Propeller diameter,
# pitch and blade count are estimated.

PROP = dict(x=1.2, y=-34.55, z=1.45, R=0.93, hub=0.2, pitch=1.75, blades=3)
RUDDER = dict(x=0.975, y_stock=-35.62, chord=1.06, fwd=0.26, z0=0.32, z1=3.25)
SPLANE = dict(y_axis=-36.95, z=1.45, chord=0.98, x0=0.12, x1=2.62)


def foil(chord, thick, n=14):
    """Symmetric NACA-ish section points (u along chord from leading edge, v half-thickness)."""
    out = []
    for i in range(n + 1):
        b = math.pi * i / n
        u = 0.5 * (1 - math.cos(b))
        v = 5 * thick * (0.2969 * math.sqrt(u) - 0.126 * u - 0.3516 * u ** 2 + 0.2843 * u ** 3 - 0.1036 * u ** 4)
        out.append((u * chord, v * chord))
    return out


def foil_ring(chord, thick, n=14):
    pts = foil(chord, thick, n)
    upper = pts
    lower = [(u, -v) for (u, v) in reversed(pts[1:-1])]
    return upper + lower


def add_blade_set(bm, P, side):
    """Propeller blades with twist from pitch; right-hand screw on starboard, left on port."""
    cx, cy, cz = P['x'] * side, P['y'], P['z']
    R, rh = P['R'], P['hub']
    hand = side
    nr, nc = 12, 12
    for b in range(P['blades']):
        phase = 2 * math.pi * b / P['blades'] + (0.4 if side > 0 else 1.1)
        top, bot = [], []
        for i in range(nr + 1):
            r = rh * 0.9 + (R - rh * 0.9) * i / nr
            rr = max(0.0, (r - rh) / (R - rh))
            # chord: wide elliptic blade with rounded tip; skew back toward the tip
            chord = 0.74 * math.sqrt(max(0.0, 1 - max(0.0, rr) ** 2.2)) * (0.75 + 0.5 * rr) + 0.02
            skew = 0.35 * rr ** 1.6
            pitch_ang = math.atan(P['pitch'] / (2 * math.pi * r))
            th = 0.09 * (1 - rr) + 0.012
            rowt, rowb = [], []
            for j in range(nc + 1):
                u = j / nc
                s_ = (u - 0.5) * chord          # along chord, centred
                tthk = th * 0.5 * math.sin(math.pi * u) ** 0.7
                # chord line in the (circumferential, axial) plane rotated by pitch angle
                circ = s_ * math.cos(pitch_ang)
                axial = s_ * math.sin(pitch_ang)
                ang = phase + (circ / r) * hand + skew * hand
                for sgn, row in ((1, rowt), (-1, rowb)):
                    ax = axial + sgn * tthk * math.cos(pitch_ang)
                    ci = -sgn * tthk * math.sin(pitch_ang)
                    a2 = ang + (ci / r) * hand
                    row.append(Vector((cx + r * math.cos(a2), cy - ax, cz + r * math.sin(a2))))
            top.append(rowt); bot.append(rowb)
        vt = [[bm.verts.new(p) for p in row] for row in top]
        vb = [[bm.verts.new(p) for p in row] for row in bot]
        for i in range(nr):
            for j in range(nc):
                f = bm.faces.new((vt[i][j], vt[i][j + 1], vt[i + 1][j + 1], vt[i + 1][j])); f.smooth = True
                f = bm.faces.new((vb[i][j], vb[i + 1][j], vb[i + 1][j + 1], vb[i][j + 1])); f.smooth = True
        for i in range(nr):
            for row_t, row_b, jj in ((vt, vb, 0), (vt, vb, nc)):
                if jj == 0:
                    f = bm.faces.new((row_t[i][0], row_t[i + 1][0], row_b[i + 1][0], row_b[i][0]))
                else:
                    f = bm.faces.new((row_t[i][nc], row_b[i][nc], row_b[i + 1][nc], row_t[i + 1][nc]))
                f.smooth = True
        for j in range(nc):
            f = bm.faces.new((vt[nr][j], vt[nr][j + 1], vb[nr][j + 1], vb[nr][j])); f.smooth = True


def add_hub(bm, P, side):
    cx, cy, cz = P['x'] * side, P['y'], P['z']
    rings = []
    prof = [(0.38, 0.0), (0.3, 0.17), (0.2, 0.215), (0.0, 0.225), (-0.25, 0.215), (-0.42, 0.17),
            (-0.55, 0.11), (-0.62, 0.05), (-0.64, 0.005)]
    for (dy, r) in prof:
        rings.append([(cx + r * math.cos(2 * math.pi * k / 24), cy + dy, cz + r * math.sin(2 * math.pi * k / 24)) for k in range(24)])
    add_loft_bm(bm, rings, closed=True, cap_start=True, cap_end=True)


def add_foil_surface(bm, root_c, tip_c, root_le, tip_le, axis, chord_dir, thick=0.12, n=14, tip_round=True):
    """Loft a foil from root to tip. *_le are leading-edge points; chord_dir points aft;
    axis is the span direction (unused beyond orientation)."""
    root_le, tip_le = Vector(root_le), Vector(tip_le)
    cd = Vector(chord_dir).normalized()
    span = (tip_le - root_le).normalized()
    tn = cd.cross(span).normalized()
    rings = []
    steps = 8
    for i in range(steps + 1):
        t = i / steps
        le = root_le.lerp(tip_le, t)
        ch = lerp(root_c, tip_c, t)
        ring = [le + cd * u + tn * v for (u, v) in foil_ring(ch, thick, n)]
        rings.append(ring)
    if tip_round:
        le = tip_le + span * 0.04
        rings.append([le + cd * (u * 0.9 + tip_c * 0.05) + tn * v * 0.45 for (u, v) in foil_ring(tip_c, thick, n)])
    add_loft_bm(bm, rings, closed=True, cap_start=True, cap_end=True)


def build_stern():
    c = reset_coll('Stern', ROOT)
    P, Rd, S = PROP, RUDDER, SPLANE
    bm_b = bmesh.new()      # bronze propellers
    bm_s = bmesh.new()      # painted steel
    for side in (1, -1):
        add_blade_set(bm_b, P, side)
        add_hub(bm_b, P, side)
        # shaft from hull exit to the hub
        px, py, pz = P['x'] * side, P['y'], P['z']
        exit_pt, _ = side_point(-30.6, 1.0, side)
        sx = exit_pt.x * 0.92
        add_cyl(bm_s, (sx, -30.6, pz + 0.05), (px, py + 0.4, pz), 0.11, seg=16)
        # shaft fairing (bossing) where the shaft leaves the hull
        add_cyl(bm_s, (sx * 0.8, -29.9, pz + 0.07), (sx * 1.02, -31.4, pz + 0.04), 0.3, r1=0.17, seg=20)
        # A-bracket struts just forward of the propeller
        sy = py + 0.75
        # A-bracket: one leg up into the counter, one leg in to the deadwood skeg
        zc_up = (hull_z_under(sy, px - side * 0.2) or pz + 1.2) + 0.12
        legs = [((px - side * 0.2, zc_up), (px, pz)), ((side * 0.12, pz - 0.55), (px, pz))]
        for (rx_, rz_), (tx_, tz_) in legs:
            add_foil_surface(bm_s, 0.34, 0.3, (rx_, sy + 0.17, rz_), (tx_, sy + 0.17, tz_), None, (0, -1, 0), thick=0.22)
        add_cyl(bm_s, (px, sy + 0.25, pz), (px, sy - 0.25, pz), 0.17, seg=18)
        # rudder: balanced spade hung from the counter; 3.111 m2 (2G-9C)
        rx = Rd['x'] * side
        z_top = (hull_z_under(Rd['y_stock'], rx) or 3.0) + 0.06
        span = 3.111 / (Rd['chord'] * 0.94)
        z_bot = z_top - span
        le_y = Rd['y_stock'] + Rd['fwd'] * Rd['chord']
        add_foil_surface(bm_s, Rd['chord'] * 0.9, Rd['chord'], (rx, le_y - 0.04, z_bot), (rx, le_y, z_top + 0.1),
                         None, (0, -1, 0), thick=0.16)
        # rudder stock collar where it enters the hull
        add_cyl(bm_s, (rx, Rd['y_stock'], z_top - 0.05), (rx, Rd['y_stock'], z_top + 0.25), 0.12, seg=14)
        # stern plane (outboard of the skeg, aft of the rudders)
        le_y = S['y_axis'] + 0.3 * S['chord']
        add_foil_surface(bm_s, S['chord'], S['chord'] * 0.9, (side * S['x0'], le_y, S['z']), (side * S['x1'], le_y - 0.06, S['z']),
                         None, (0, -1, 0), thick=0.13)
        add_cyl(bm_s, (0, S['y_axis'], S['z']), (side * (S['x1'] + 0.08), S['y_axis'], S['z']), 0.06, seg=12)
        # propeller guard: from the hull forward of the screw, outboard past the tip,
        # then straight aft to the outer end of the stern-plane axis
        g_out = P['x'] + P['R'] + 0.32
        gz = S['z'] + 0.02
        root, _ = side_point(-31.2, gz, side)
        pts = [(root.x * 0.95, -31.2, gz), (side * (abs(root.x) + 0.5), -31.9, gz),
               (side * (g_out - 0.15), -32.9, gz), (side * g_out, -33.7, gz),
               (side * g_out, -35.4, gz), (side * (S['x1'] - 0.02), S['y_axis'] + 0.05, gz)]
        add_tube_path(bm_s, pts, 0.09, seg=14)
        # guard stay down to the keel line
        add_tube_path(bm_s, [(side * g_out, -33.9, gz), (side * 0.45, -33.4, 0.45)], 0.05, seg=10)
    # deadwood skeg: thin centre fin carrying the plane axis and rudder supports
    rings = []
    for y in stations(-32.6, -37.25, 18, end_density=1.0):
        t = (y + 32.6) / (-37.25 + 32.6)
        zb = lerp(0.62, S['z'] - 0.25, t ** 1.3)
        zt_ = hull_params(y)['zk'] + 0.3
        hw = lerp(0.2, 0.07, t)
        rings.append([(hw, y, zb + 0.05), (hw * 0.4, y, zb), (-hw * 0.4, y, zb), (-hw, y, zb + 0.05), (-hw, y, zt_), (hw, y, zt_)])
    add_loft_bm(bm_s, rings, closed=True, cap_start=True, cap_end=True, smooth=False)
    # rudder heel supports (skeg shoes) under each rudder
    bm_to_obj(bm_b, 'Stern_Propellers', c, mats=['M_Bronze'], smooth=True)
    bm_to_obj(bm_s, 'Stern_Gear', c, mats=['M_HullPaint'], smooth=True)

    # stern torpedo tube shutters (two), as flush panels with dark outlines
    bm_h = bmesh.new()
    bm_r = bmesh.new()
    for side in (1, -1):
        pt, n = side_point(-36.0, 3.7, side)
        add_groove(bm_h, pt, n, (0, -0.2, 1), 0.92, 0.72, t=0.05)
        add_shutter_rim(bm_r, -36.0, 3.7, 0.8, 0.6, side)
    ob = bm_to_obj(bm_h, 'Stern_TubeDoors', c, mats=['M_Hole'], recalc=False)
    shrinkwrap(ob, 'Hull_Outer')
    bm_to_obj(bm_r, 'Stern_ShutterRims', c, mats=['M_HullPaint'], smooth=True)
