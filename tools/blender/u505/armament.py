# U-505 exterior model: anti-aircraft guns. The TG 22.3 photographs show a 20 mm mount
# (Encl G 506: a twin cradle on a pedestal, wire netting round the platform) and refer to
# a 37 mm mount. Here: two twin 20 mm mounts on the upper Wintergarten platform and one
# 37 mm on the lower platform, a common 1944 Type IXC fit. Counts and details are
# estimated; no deck gun forward (none appears in Encl G 499/517).


def _merge(bm, sub, M):
    bmesh.ops.transform(sub, verts=sub.verts, matrix=M)
    tmp = bpy.data.meshes.new('_tmp')
    sub.to_mesh(tmp); sub.free()
    bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)


def twin20(bm, base, yaw_deg, elev_deg):
    # pedestal (fixed)
    p = bmesh.new()
    add_cyl(p, (0, 0, 0), (0, 0, 0.05), 0.26, seg=24)
    add_cyl(p, (0, 0, 0.05), (0, 0, 0.62), 0.11, r1=0.09, seg=20)
    for j in range(8):
        a = 2 * math.pi * j / 8
        add_cyl(p, (0.21 * math.cos(a), 0.21 * math.sin(a), 0.05), (0.21 * math.cos(a), 0.21 * math.sin(a), 0.075), 0.022, seg=6)
    _merge(bm, p, Matrix.Translation(base))
    # traversing carriage
    t = bmesh.new()
    add_cyl(t, (0, 0, 0.62), (0, 0, 0.72), 0.15, seg=20)
    for s in (1, -1):  # side arms of the cradle
        add_box(t, (s * 0.3, -0.02, 0.86), (0.06, 0.34, 0.32))
        add_box(t, (s * 0.17, -0.02, 0.74), (0.3, 0.12, 0.05))
        # shoulder rests / gunner's arms
        add_tube_path(t, [(s * 0.2, -0.05, 0.8), (s * 0.28, -0.42, 0.95), (s * 0.24, -0.62, 1.0)], 0.018, seg=6)
        add_box(t, (s * 0.24, -0.66, 1.0), (0.12, 0.05, 0.16))
    # handwheel / foot rest frame
    add_tube_path(t, [(-0.32, -0.3, 0.68), (0, -0.48, 0.66), (0.32, -0.3, 0.68)], 0.016, seg=6)
    # elevating mass: two guns, spaced on the cradle, pointing +Y before rotation
    e = bmesh.new()
    for s in (1, -1):
        gx = s * 0.17
        add_box(e, (gx, 0.0, 0.0), (0.11, 0.62, 0.15))                       # receiver
        add_box(e, (gx, -0.36, -0.02), (0.07, 0.16, 0.1))                     # rear plate
        add_cyl(e, (gx, 0.31, 0.0), (gx, 0.62, 0.0), 0.04, seg=14)            # recoil sleeve
        add_cyl(e, (gx, 0.62, 0.0), (gx, 1.32, 0.0), 0.021, seg=12)           # barrel
        add_cyl(e, (gx, 1.32, 0.0), (gx, 1.44, 0.0), 0.03, r1=0.036, seg=12)  # flash hider
        # 20-round box magazine on the outboard side, curved
        for k in range(5):
            add_box(e, (gx + s * 0.1, 0.05 - 0.035 * k, 0.03 + 0.045 * k), (0.06, 0.13, 0.05),
                    rot=Matrix.Rotation(math.radians(-8 * k), 4, 'X'))
    add_box(e, (0, 0.05, 0.0), (0.24, 0.08, 0.06))                            # cradle bridge
    # ring sight on a post
    add_cyl(e, (0, 0.2, 0.08), (0, 0.2, 0.26), 0.01, seg=6)
    pts = [(0.11 * math.cos(2 * math.pi * k / 24), 0.2, 0.33 + 0.11 * math.sin(2 * math.pi * k / 24)) for k in range(25)]
    add_tube_path(e, pts, 0.006, seg=5, cap=False)
    add_tube_path(e, [(-0.11, 0.2, 0.33), (0.11, 0.2, 0.33)], 0.004, seg=4)
    add_tube_path(e, [(0, 0.2, 0.22), (0, 0.2, 0.44)], 0.004, seg=4)
    _merge(t, e, Matrix.Translation((0, 0, 0.9)) @ Matrix.Rotation(math.radians(elev_deg), 4, 'X'))
    _merge(bm, t, Matrix.Translation(base) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z'))


def flak37(bm, base, yaw_deg, elev_deg):
    p = bmesh.new()
    add_cyl(p, (0, 0, 0), (0, 0, 0.06), 0.4, seg=28)
    add_cyl(p, (0, 0, 0.06), (0, 0, 0.55), 0.17, r1=0.14, seg=24)
    for j in range(10):
        a = 2 * math.pi * j / 10
        add_cyl(p, (0.34 * math.cos(a), 0.34 * math.sin(a), 0.06), (0.34 * math.cos(a), 0.34 * math.sin(a), 0.09), 0.025, seg=6)
    _merge(bm, p, Matrix.Translation(base))
    t = bmesh.new()
    add_cyl(t, (0, 0, 0.55), (0, 0, 0.66), 0.24, seg=24)
    for s in (1, -1):
        add_box(t, (s * 0.24, 0.0, 0.95), (0.07, 0.42, 0.6))                  # trunnion cheeks
        # layer / trainer seats with backrests
        add_tube_path(t, [(s * 0.2, -0.1, 0.66), (s * 0.55, -0.35, 0.62)], 0.022, seg=6)
        add_box(t, (s * 0.6, -0.4, 0.62), (0.26, 0.24, 0.05))
        add_box(t, (s * 0.6, -0.53, 0.78), (0.24, 0.04, 0.26))
        # handwheels
        pts = [(s * 0.32, 0.1 + 0.11 * math.cos(2 * math.pi * k / 20), 0.88 + 0.11 * math.sin(2 * math.pi * k / 20)) for k in range(21)]
        add_tube_path(t, pts, 0.012, seg=5, cap=False)
    e = bmesh.new()
    add_box(e, (0, -0.1, 0.0), (0.22, 0.95, 0.26))                           # receiver
    add_box(e, (0, -0.62, 0.02), (0.18, 0.12, 0.2))                          # breech end
    add_cyl(e, (0, 0.38, 0.0), (0, 0.95, 0.0), 0.075, seg=18)                 # recoil housing
    for s in (1, -1):
        add_cyl(e, (s * 0.09, 0.35, -0.09), (s * 0.09, 0.8, -0.09), 0.028, seg=10)  # recuperators
    add_cyl(e, (0, 0.95, 0.0), (0, 2.45, 0.0), 0.045, seg=16)                 # barrel
    add_cyl(e, (0, 2.45, 0.0), (0, 2.68, 0.0), 0.06, r1=0.075, seg=16)        # flash hider
    # 8-round clip feeding from the left
    for k in range(8):
        add_cyl(e, (-0.17 - 0.02 * k, -0.05, 0.13 + 0.07 * k), (-0.17 - 0.02 * k, 0.32, 0.13 + 0.07 * k), 0.03, seg=10)
    add_box(e, (-0.2, 0.12, 0.38), (0.03, 0.45, 0.6))
    # sights
    add_cyl(e, (0.2, 0.0, 0.18), (0.2, 0.0, 0.32), 0.012, seg=6)
    pts = [(0.2 + 0.13 * math.cos(2 * math.pi * k / 24), 0.0, 0.42 + 0.13 * math.sin(2 * math.pi * k / 24)) for k in range(25)]
    add_tube_path(e, pts, 0.006, seg=5, cap=False)
    _merge(t, e, Matrix.Translation((0, 0, 0.98)) @ Matrix.Rotation(math.radians(elev_deg), 4, 'X'))
    _merge(bm, t, Matrix.Translation(base) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z'))


def build_armament():
    c = reset_coll('Armament', ROOT)
    T = TW
    bm = bmesh.new()
    zup = T['ledge_top'] + 0.08
    twin20(bm, Vector((0.68, -2.95, zup)), yaw_deg=-150, elev_deg=22)
    twin20(bm, Vector((-0.68, -2.95, zup)), yaw_deg=160, elev_deg=8)
    flak37(bm, Vector((0, -5.55, T['low_plat_z'] + 0.12)), yaw_deg=180, elev_deg=12)
    # ready-use ammunition lockers on the platforms
    for (x, y, z) in ((1.05, -1.95, zup), (-1.05, -1.95, zup)):
        add_box(bm, (x, y, z + 0.22), (0.3, 0.55, 0.44))
        add_box(bm, (x, y, z + 0.455), (0.33, 0.58, 0.03))
    bm_to_obj(bm, 'Armament_Guns', c, mats=['M_Gunmetal'], smooth=True)


def build_rigging():
    c = reset_coll('Rigging', ROOT)
    bm = bmesh.new()
    bm_i = bmesh.new()
    bt = TW['bul_top']
    fwd = [Vector((0, Y_BOW - 0.35, zt_at(Y_BOW) + 0.25)), Vector((0, TW['bul_yf'] + 0.08, bt + 0.06))]
    # aft jumping wire: from a post on the lower-platform rail to a stern post
    stern_post = Vector((0, -36.9, zt_at(-36.9) + 0.75))
    add_cyl(bm, (0, -36.9, zt_at(-36.9)), (0, -36.9, zt_at(-36.9) + 0.8), 0.045, seg=10)
    aft_post_base = Vector((0, TW['aft_yb'] - 0.12, TW['low_plat_z'] + 0.1))
    add_cyl(bm, aft_post_base, aft_post_base + Vector((0, -0.05, 1.45)), 0.04, seg=10)
    aft = [aft_post_base + Vector((0, -0.05, 1.4)), stern_post]
    # bridge fitting for the forward wire
    add_box(bm, fwd[1] + Vector((0, -0.04, -0.08)), (0.07, 0.22, 0.18))
    for (a, b) in (fwd, aft):
        pts = []
        for k in range(41):
            t = k / 40
            p = a.lerp(b, t)
            p.z -= 0.12 * math.sin(math.pi * t)
            pts.append(p)
        add_tube_path(bm, pts, 0.011, seg=6)
        # strain insulators near both ends
        d = (b - a).normalized()
        for t in (0.07, 0.11, 0.9):
            p = a.lerp(b, t)
            p.z -= 0.12 * math.sin(math.pi * t)
            add_cyl(bm_i, p - d * 0.11, p + d * 0.11, 0.045, seg=12)
            add_cyl(bm_i, p - d * 0.16, p - d * 0.11, 0.03, r1=0.045, seg=12)
            add_cyl(bm_i, p + d * 0.11, p + d * 0.16, 0.045, r1=0.03, seg=12)
    bm_to_obj(bm, 'Rigging_JumpingWires', c, mats=['M_Galv'], smooth=True)
    bm_to_obj(bm_i, 'Rigging_Insulators', c, mats=['M_Porcelain'], smooth=True)
