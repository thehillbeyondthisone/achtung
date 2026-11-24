# U-505 exterior model: weather deck. Slatted timber over the casing (Encl G 505, 517),
# with staggered drain openings, steel margin strips and cross straps, the four deck
# hatches 2G-9C lists (two torpedo-loading, galley, engine room; 600 mm clear, torpedo
# hatches 660 mm), retractable bitts, the forward windlass capstan and the aft capstan,
# guard rails beside the tower and pressure-tight canisters. Positions are estimated.

HATCHES = [  # (name, y, clear radius, slant deg)
    ('TorpedoFwd', 22.5, 0.33, 12),
    ('Galley', 9.6, 0.30, 0),
    ('EngineRoom', -10.6, 0.30, 0),
    ('TorpedoAft', -24.8, 0.33, -12),
]
PLANK_W, PLANK_GAP, PLANK_T = 0.105, 0.028, 0.045
CANISTER_X, CANISTER_Y = 1.2, -7.75
DECK_Y0, DECK_Y1 = -35.6, 34.6
MARGIN = 0.15
DECK_HARDWARE_MATS = ('M_Gunmetal', 'M_Galv', 'M_Iron')
DECK_DARK_STEEL, DECK_BARE_STEEL, DECK_IRON = range(len(DECK_HARDWARE_MATS))


def deck_z(x, y):
    p = hull_params(y)
    w = p['w']
    camber = 0.06 * min(1.0, w / 1.6)
    return p['zt'] + camber * (1 - min(1.0, (x / max(w, 1e-3))) ** 2)


def tower_excl():
    """Half-width of the tower footprint (plus clearance) as a function of y."""
    T = TW
    outl = offset_outline(egg(T['body_W'], T['body_yf'], T['body_yb'], T['body_ym'], n=96, ef=1.55, eb=2.4), 0.3)
    outl += offset_outline(egg(T['aft_W'], T['aft_yf'], T['aft_yb'], T['aft_ym'], n=72, ef=2.4, eb=1.9), 0.28)
    # compass hood
    outl += [(0.5, 4.2 + 0.1 * k) for k in range(15)]

    def f(y):
        xs = [abs(p[0]) for p in outl if abs(p[1] - y) < 0.07]
        return max(xs) if xs else -1.0
    return f


def add_deck_box(bm, x0, x1, y0, y1, t, lift=0.0, mat_index=0):
    """Box lying on the cambered, sheered deck between x0..x1, y0..y1."""
    vs = []
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        z = deck_z(x, y) + lift
        vs.append((x, y, z))
    bot = [bm.verts.new(v) for v in vs]
    top = [bm.verts.new((v[0], v[1], v[2] + t)) for v in vs]
    for f in ((0, 3, 2, 1),):
        bm.faces.new([bot[i] for i in f]).material_index = mat_index
    bm.faces.new(top).material_index = mat_index
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((bot[i], bot[j], top[j], top[i])).material_index = mat_index


def deck_fastener(bm, x, y, z, radius=0.021, height=0.012, material=DECK_DARK_STEEL):
    """A shallow hex head set into the mounting surface."""
    add_cyl(bm, (x, y, z - 0.004), (x, y, z + height), radius, seg=6,
            mat_index=material, smooth=False)


def deck_hatch_hardware(bm, y, z, outer_radius, slant):
    # Pin and seam follow the lid angle. Fasteners around the base sit on the flat hatch plate.
    frame = Matrix.Translation((0, y, z)) @ Matrix.Rotation(math.radians(slant), 4, 'X')
    pin_y = -(outer_radius + 0.06)
    for side in (-1, 1):
        add_cyl(bm, frame @ Vector((side * 0.148, pin_y, 0.185)),
                frame @ Vector((side * 0.193, pin_y, 0.185)), 0.044, seg=10,
                mat_index=DECK_BARE_STEEL)
    rings = []
    for radius, level in ((outer_radius + 0.006, 0.132), (outer_radius + 0.033, 0.144),
                          (outer_radius + 0.033, 0.156)):
        rings.append([frame @ Vector((radius * math.cos(a), radius * math.sin(a), level))
                      for a in (math.tau * i / 24 for i in range(24))])
    add_loft_bm(bm, rings, mat_index=DECK_DARK_STEEL)
    for offset in (-0.62, 0.0, 0.62):
        plate_z = lerp(deck_z(0.68, y - 0.76), deck_z(0.68, y + 0.76), (offset + 0.76) / 1.52)
        for x in (-0.60, 0.60):
            deck_fastener(bm, x, y + offset, plate_z + PLANK_T + 0.008, radius=0.025)


def build_deck():
    c = reset_coll('Deck', ROOT)
    ex = tower_excl()
    hatch_zone = [(h[1], 0.78) for h in HATCHES]
    hardware = bmesh.new()
    bm = bmesh.new()
    pitch = PLANK_W + PLANK_GAP
    n_side = int((1.78 - MARGIN) / pitch)
    seg_len, gap = 1.32, 0.15
    for i in range(-n_side, n_side + 1):
        xc = i * pitch
        xa, xb = xc - PLANK_W / 2, xc + PLANK_W / 2
        phase = ((i * 7) % 5) / 5.0 * (seg_len + gap)
        y = DECK_Y0 - phase
        while y < DECK_Y1:
            y0, y1 = y, y + seg_len
            y += seg_len + gap
            # clip to where the plank lies inside the deck margin and outside the tower / hatches
            ok_pts = []
            for k in range(9):
                yy = lerp(y0, y1, k / 8)
                if yy < DECK_Y0 or yy > DECK_Y1:
                    ok_pts.append(False); continue
                w = hull_params(yy)['w']
                inside = (abs(xc) + PLANK_W / 2) < (w - MARGIN)
                if ex(yy) > 0 and abs(xc) < ex(yy):
                    inside = False
                for hy, hr in hatch_zone:
                    if abs(yy - hy) < hr and abs(xc) < 0.7:
                        inside = False
                ok_pts.append(inside)
            # keep the longest run of valid samples
            best, cur, start, bs = 0, 0, 0, 0
            for k, ok in enumerate(ok_pts):
                if ok:
                    if cur == 0:
                        start = k
                    cur += 1
                    if cur > best:
                        best, bs = cur, start
                else:
                    cur = 0
            if best >= 2:
                ya = lerp(y0, y1, bs / 8)
                yb = lerp(y0, y1, (bs + best - 1) / 8)
                if yb - ya > 0.12:
                    add_deck_box(bm, xa, xb, ya, yb, PLANK_T)
    bm_to_obj(bm, 'Deck_Planks', c, mats=['M_DeckWood'])

    # steel: margin strips, cross straps, hatch plates
    bm = bmesh.new()
    ys = [DECK_Y0 - 1.6 + 0.4 * k for k in range(int((DECK_Y1 - DECK_Y0 + 4.2) / 0.4))]
    for s in (1, -1):
        rings = []
        for yy in ys:
            p = hull_params(yy)
            w = p['w']
            if w < 0.2:
                continue
            xo = s * (w - 0.005)
            xi = s * max(0.05, w - MARGIN - 0.01)
            zo, zi = deck_z(abs(xo), yy), deck_z(abs(xi), yy)
            rings.append([(xi, yy, zi), (xo, yy, zo), (xo, yy, zo + 0.03), (xi, yy, zi + 0.03)])
        add_loft_bm(bm, rings, closed=True, cap_start=True, cap_end=True, smooth=False)
        spacing = 1.45
        for station in range(int((DECK_Y1 - DECK_Y0) / spacing)):
            yy = DECK_Y0 + (station + 0.5) * spacing
            x = s * (hull_params(yy)['w'] - 0.082)
            deck_fastener(hardware, x, yy, deck_z(x, yy) + 0.03, radius=0.019, height=0.006)
    yy = DECK_Y0 + 1.0
    while yy < DECK_Y1 - 0.5:
        if ex(yy) < 0 and all(abs(yy - h[1]) > 0.9 for h in HATCHES):
            w = hull_params(yy)['w'] - MARGIN
            sections = []
            for fraction in (-1, -0.5, 0, 0.5, 1):
                x = w * fraction
                aft, fwd = yy - 0.03, yy + 0.03
                za, zf = deck_z(x, aft) + PLANK_T, deck_z(x, fwd) + PLANK_T
                sections.append([(x, aft, za), (x, fwd, zf), (x, fwd, zf + 0.012), (x, aft, za + 0.012)])
                if abs(fraction) < 1:
                    deck_fastener(hardware, x, yy, (za + zf) * 0.5 + 0.012,
                                  radius=0.019, height=0.006)
            add_loft_bm(bm, sections, cap_start=True, cap_end=True, smooth=False)
        yy += 3.6
    for (nm, hy, hr, sl) in HATCHES:
        add_deck_box(bm, -0.68, 0.68, hy - 0.76, hy + 0.76, PLANK_T + 0.008)
    bm_to_obj(bm, 'Deck_Steel', c, mats=['M_HullPaint'])

    # hatches: coaming, domed lid, hinge, central handwheel and dogs
    bm = bmesh.new()
    for (nm, hy, hr, sl) in HATCHES:
        z0 = deck_z(0, hy) + PLANK_T + 0.008
        ro = hr + 0.06
        deck_hatch_hardware(hardware, hy, z0, ro, sl)
        hb = bmesh.new()
        add_cyl(hb, (0, 0, -0.05), (0, 0, 0.13), ro, seg=40)
        rings = []
        for k in range(7):
            a = (math.pi / 2) * k / 6
            r = (ro + 0.03) * math.cos(a)
            z = 0.13 + 0.03 + 0.12 * math.sin(a)
            rings.append([(r * math.cos(2 * math.pi * j / 40), r * math.sin(2 * math.pi * j / 40), z) for j in range(40)])
        rings[-1] = [(0.001 * math.cos(2 * math.pi * j / 40), 0.001 * math.sin(2 * math.pi * j / 40), rings[-1][0][2]) for j in range(40)]
        add_loft_bm(hb, [[(p[0], p[1], 0.13) for p in rings[0]]] + rings, closed=True)
        add_box(hb, (0, -(ro + 0.06), 0.17), (0.34, 0.14, 0.12))                  # hinge
        add_cyl(hb, (0, 0, 0.29), (0, 0, 0.36), 0.03, seg=10)                      # spindle
        for j in range(6):                                                          # handwheel rim + spokes
            a = 2 * math.pi * j / 6
            add_cyl(hb, (0, 0, 0.36), (0.16 * math.cos(a), 0.16 * math.sin(a), 0.36), 0.012, seg=6)
        pts = [(0.17 * math.cos(2 * math.pi * j / 24), 0.17 * math.sin(2 * math.pi * j / 24), 0.36) for j in range(25)]
        add_tube_path(hb, pts, 0.016, seg=6, cap=False)
        for j in range(8):                                                          # dogs
            a = 2 * math.pi * (j + 0.5) / 8
            add_box(hb, ((ro + 0.02) * math.cos(a), (ro + 0.02) * math.sin(a), 0.1), (0.07, 0.07, 0.1),
                    rot=Matrix.Rotation(a, 4, 'Z'))
        bmesh.ops.rotate(hb, verts=hb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(sl), 3, 'X'))
        bmesh.ops.translate(hb, verts=hb.verts, vec=(0, hy, z0))
        tmp = bpy.data.meshes.new('_tmp'); hb.to_mesh(tmp); hb.free(); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)

    # bitts (pairs of short posts on a plate), both sides
    for by in (31.2, 17.5, -15.5, -31.0):
        w = hull_params(by)['w']
        for s in (1, -1):
            x = s * (w - 0.42)
            z = deck_z(abs(x), by) + PLANK_T
            add_box(bm, (x, by, z + 0.015), (0.3, 0.72, 0.03))
            for dx in (-0.105, 0.105):
                for dy in (-0.29, 0.29):
                    deck_fastener(hardware, x + dx, by + dy, z + 0.03)
            for dy in (-0.2, 0.2):
                add_cyl(bm, (x, by + dy, z), (x, by + dy, z + 0.3), 0.075, seg=16)
                add_cyl(bm, (x, by + dy, z + 0.3), (x, by + dy, z + 0.34), 0.095, seg=16)
                add_cyl(hardware, (x, by + dy, z + 0.026), (x, by + dy, z + 0.074),
                        0.091, seg=12, mat_index=DECK_IRON)
    # capstans: windlass head forward, capstan aft
    for cy in (30.0, -29.6):
        z = deck_z(0, cy) + PLANK_T
        add_cyl(bm, (0, cy, z - 0.02), (0, cy, z + 0.06), 0.36, seg=32)
        add_cyl(bm, (0, cy, z + 0.06), (0, cy, z + 0.36), 0.22, r1=0.2, seg=32)
        add_cyl(bm, (0, cy, z + 0.36), (0, cy, z + 0.42), 0.26, seg=32)
        for j in range(8):
            a = 2 * math.pi * j / 8
            add_box(bm, (0.215 * math.cos(a), cy + 0.215 * math.sin(a), z + 0.21), (0.05, 0.05, 0.28),
                    rot=Matrix.Rotation(a, 4, 'Z'))
            deck_fastener(hardware, 0.315 * math.cos(a), cy + 0.315 * math.sin(a), z + 0.06, radius=0.024)
        for j in range(6):
            a = 2 * math.pi * j / 6
            add_cyl(bm, (0.13 * math.cos(a), cy + 0.13 * math.sin(a), z + 0.42), (0.13 * math.cos(a), cy + 0.13 * math.sin(a), z + 0.44), 0.035, seg=8)
    # pressure-tight canisters: Encl G 507 is captioned "Flask as in rack aft of conning tower".
    # Placed just aft of the aft fairing so the walkways beside the tower stay clear.
    for s in (1, -1):
        x, y = s * CANISTER_X, CANISTER_Y
        z = deck_z(abs(x), y) + PLANK_T
        add_cyl(bm, (x, y, z), (x, y, z + 1.05), 0.17, seg=24)
        add_cyl(bm, (x, y, z + 1.05), (x, y, z + 1.12), 0.19, seg=24)
        for zz in (0.25, 0.8):
            # Strap and buckle remain inside the existing cap outline.
            add_cyl(hardware, (x, y, z + zz), (x, y, z + zz + 0.04), 0.185, seg=24,
                    mat_index=DECK_DARK_STEEL)
            add_box(hardware, (x, y + 0.170, z + zz + 0.022), (0.082, 0.036, 0.046),
                    mat_index=DECK_BARE_STEEL)
        add_cyl(hardware, (x, y, z + 0.001), (x, y, z + 0.044), 0.190, seg=18,
                mat_index=DECK_IRON)
    bm_to_obj(bm, 'Deck_Fittings', c, mats=['M_HullPaint'], smooth=True)

    # guard rails: stanchions with two wire runs, alongside the tower
    bm_r = bmesh.new()
    for s in (1, -1):
        for (ya, yb) in ((-16.5, -8.0), (5.5, 12.5)):
            n = int((yb - ya) / 1.5) + 1
            tops, mids = [], []
            for k in range(n):
                yy = lerp(ya, yb, k / (n - 1))
                w = hull_params(yy)['w']
                x = s * (w - 0.07)
                z = deck_z(abs(x), yy)
                add_cyl(bm_r, (x, yy, z), (x, yy, z + 0.9), 0.02, seg=8)
                add_cyl(bm_r, (x, yy, z), (x, yy, z + 0.06), 0.04, seg=8)
                add_deck_box(hardware, x - 0.061, x + 0.061, yy - 0.09, yy + 0.09,
                             0.018, lift=0.03, mat_index=DECK_IRON)
                for fore_aft in (-0.058, 0.058):
                    bolt_y = yy + fore_aft
                    deck_fastener(hardware, x, bolt_y, deck_z(x, bolt_y) + 0.048,
                                  radius=0.015, height=0.011, material=DECK_BARE_STEEL)
                tops.append((x, yy, z + 0.9)); mids.append((x, yy, z + 0.48))
            for run in (tops, mids):
                pts = []
                for k in range(len(run) - 1):
                    a, b = Vector(run[k]), Vector(run[k + 1])
                    for m in range(6):
                        t = m / 6
                        p = a.lerp(b, t)
                        p.z -= 0.025 * math.sin(math.pi * t)
                        pts.append(p)
                pts.append(Vector(run[-1]))
                add_tube_path(bm_r, pts, 0.007, seg=5)
    bm_to_obj(bm_r, 'Deck_Rails', c, mats=['M_Galv'], smooth=True)
    bm_to_obj(hardware, 'Deck_Hardware', c, mats=DECK_HARDWARE_MATS)
