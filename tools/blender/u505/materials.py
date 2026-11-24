# U-505 exterior model: procedural Cycles materials (no image textures, no photo
# projection). Weathering follows the capture photographs: light grey topsides heavily
# peeled to a dark undercoat, rust runs, salt bloom and growth at the waterline, dark grey
# below the boot-top, a slatted timber deck weathered silver-grey.
# All parts sit at the origin with identity transforms, so Object coordinates = boat
# coordinates (metres, +Y bow, Z from the pressure-hull bottom).

WL = 4.30


class NB:
    """Small node-building helper."""

    def __init__(self, m):
        m.use_nodes = True
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0

    def n(self, kind, **props):
        node = self.t.nodes.new(kind)
        for k, v in props.items():
            try:
                setattr(node, k, v)
            except Exception:
                pass
        node.location = (self.x, 0)
        self.x += 60
        return node

    def link(self, a, b):
        self.t.links.new(a, b)

    def math(self, op, a, b=None, clamp=False):
        m = self.n('ShaderNodeMath', operation=op, use_clamp=clamp)
        self._feed(m.inputs[0], a)
        if b is not None:
            self._feed(m.inputs[1], b)
        return m.outputs[0]

    def _feed(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v
        else:
            self.link(v, sock)

    def maprange(self, v, a, b, c=0.0, d=1.0, interp='LINEAR'):
        m = self.n('ShaderNodeMapRange', interpolation_type=interp, clamp=True)
        self._feed(m.inputs['Value'], v)
        m.inputs['From Min'].default_value = a
        m.inputs['From Max'].default_value = b
        m.inputs['To Min'].default_value = c
        m.inputs['To Max'].default_value = d
        return m.outputs['Result']

    def mix(self, fac, a, b):
        m = self.n('ShaderNodeMix', data_type='RGBA', blend_type='MIX', clamp_factor=True)
        fi = next(s for s in m.inputs if s.identifier == 'Factor_Float')
        ai = next(s for s in m.inputs if s.identifier == 'A_Color')
        bi = next(s for s in m.inputs if s.identifier == 'B_Color')
        self._feed(fi, fac)
        self._feed(ai, a if not (isinstance(a, tuple) and len(a) == 3) else (*a, 1.0))
        self._feed(bi, b if not (isinstance(b, tuple) and len(b) == 3) else (*b, 1.0))
        return next(s for s in m.outputs if s.identifier == 'Result_Color')

    def mixf(self, fac, a, b):
        m = self.n('ShaderNodeMix', data_type='FLOAT', clamp_factor=True)
        fi = next(s for s in m.inputs if s.identifier == 'Factor_Float')
        ai = next(s for s in m.inputs if s.identifier == 'A_Float')
        bi = next(s for s in m.inputs if s.identifier == 'B_Float')
        self._feed(fi, fac); self._feed(ai, a); self._feed(bi, b)
        return next(s for s in m.outputs if s.identifier == 'Result_Float')

    def noise(self, vec, scale, detail=6.0, rough=0.55, dist=0.0, dims='3D'):
        m = self.n('ShaderNodeTexNoise', noise_dimensions=dims)
        self._feed(m.inputs['Vector'], vec)
        m.inputs['Scale'].default_value = scale
        m.inputs['Detail'].default_value = detail
        m.inputs['Roughness'].default_value = rough
        if 'Distortion' in m.inputs:
            m.inputs['Distortion'].default_value = dist
        return m.outputs['Fac']

    def mapping(self, vec, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0)):
        m = self.n('ShaderNodeMapping')
        self._feed(m.inputs['Vector'], vec)
        m.inputs['Scale'].default_value = scale
        m.inputs['Location'].default_value = loc
        m.inputs['Rotation'].default_value = rot
        return m.outputs['Vector']

    def principled(self, out_node=True):
        p = self.n('ShaderNodeBsdfPrincipled')
        if out_node:
            o = self.n('ShaderNodeOutputMaterial')
            self.link(p.outputs[0], o.inputs['Surface'])
        return p

    def bump(self, h, strength=0.3, dist=0.01, normal=None):
        b = self.n('ShaderNodeBump')
        b.inputs['Strength'].default_value = strength
        b.inputs['Distance'].default_value = dist
        self._feed(b.inputs['Height'], h)
        if normal is not None:
            self.link(normal, b.inputs['Normal'])
        return b.outputs['Normal']


def P(p, name):
    """Principled input by name, tolerating renamed sockets."""
    alts = {'Specular': ['Specular IOR Level', 'Specular'], 'Coat': ['Coat Weight', 'Coat']}
    for nm in alts.get(name, [name]):
        if nm in p.inputs:
            return p.inputs[nm]
    raise KeyError(name)


def fresh(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return m, NB(m)


def lin(c):
    """sRGB 0..1 tuple to linear."""
    def f(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return tuple(f(u) for u in c)


def seam_lines(B, pos_axis, period, width):
    """1 on thin lines across an axis (weld beads every `period` metres)."""
    v = B.math('DIVIDE', pos_axis, period)
    v = B.math('ADD', v, 0.5)
    v = B.math('FRACT', v)
    v = B.math('SUBTRACT', v, 0.5)
    v = B.math('ABSOLUTE', v)
    v = B.math('MULTIPLY', v, period)
    return B.maprange(v, 0.0, width, 1.0, 0.0, interp='SMOOTHSTEP')


def mat_hull_paint():
    m, B = fresh('M_HullPaint')
    tc = B.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    sep = B.n('ShaderNodeSeparateXYZ'); B.link(obj, sep.inputs[0])
    X, Y, Z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    geo = B.n('ShaderNodeNewGeometry')

    # ---- base paint zones: dark grey below the boot-top, light grey above
    wl_wobble = B.math('MULTIPLY', B.noise(obj, 0.6, detail=2), 0.12)
    zrel = B.math('SUBTRACT', Z, B.math('ADD', wl_wobble, WL + 0.12))
    upper = B.maprange(zrel, -0.03, 0.03)
    c_low = lin((0.20, 0.205, 0.21))
    c_up = lin((0.60, 0.61, 0.60))
    # subtle panel-to-panel tone shifts
    tone = B.noise(B.mapping(obj, (0.25, 0.08, 0.4)), 1.0, detail=1)
    c_up2 = B.mix(B.maprange(tone, 0.3, 0.7), lin((0.47, 0.48, 0.48)), lin((0.56, 0.56, 0.55)))
    base = B.mix(upper, c_low, c_up2)

    # ---- peeled patches revealing dark undercoat (strong on the tower, per the photos)
    peel_n = B.noise(obj, 2.4, detail=14, rough=0.68, dist=0.9)
    peel_fine = B.noise(obj, 16.0, detail=6, rough=0.7)
    peel_v = B.math('ADD', peel_n, B.math('MULTIPLY', B.math('SUBTRACT', peel_fine, 0.5), 0.32))
    # sparse small chips everywhere
    chips = B.maprange(B.noise(obj, 26.0, detail=3, dist=0.4), 0.69, 0.72)
    tower_boost = B.maprange(Z, 6.2, 8.8, 0.0, 0.05)
    thr = B.math('SUBTRACT', 0.585, tower_boost)
    peel = B.maprange(B.math('SUBTRACT', peel_v, thr), 0.0, 0.02)
    peel = B.math('MAXIMUM', peel, chips)
    peel = B.math('MULTIPLY', peel, upper)
    c_under = lin((0.24, 0.24, 0.235))
    col = B.mix(peel, base, c_under)
    # rust at the heart of the bigger peels
    rust_core = B.maprange(B.math('SUBTRACT', peel_v, B.math('ADD', thr, 0.09)), 0.0, 0.04)
    col = B.mix(B.math('MULTIPLY', rust_core, 0.85), col, lin((0.33, 0.16, 0.08)))

    # ---- edge wear via pointiness
    edge = B.maprange(geo.outputs['Pointiness'], 0.52, 0.6)
    edge = B.math('MULTIPLY', edge, B.maprange(B.noise(obj, 14.0, detail=3), 0.45, 0.6))
    col = B.mix(B.math('MULTIPLY', edge, 0.7), col, lin((0.24, 0.2, 0.17)))

    # ---- rust runs: vertical streaks, strongest just below the deck edge and slots
    streak_v = B.mapping(obj, (5.5, 5.5, 0.35))
    streak = B.noise(streak_v, 3.0, detail=5, rough=0.5)
    streak = B.maprange(streak, 0.56, 0.72)
    region = B.noise(obj, 0.35, detail=2)
    region = B.maprange(region, 0.45, 0.62)
    below_deck = B.maprange(Z, 6.1, 5.0)
    above_wl = B.maprange(Z, WL - 0.3, WL + 0.4)
    runs = B.math('MULTIPLY', streak, region)
    runs = B.math('MULTIPLY', runs, B.math('MULTIPLY', below_deck, above_wl))
    col = B.mix(B.math('MULTIPLY', runs, 0.7), col, lin((0.36, 0.2, 0.11)))

    # ---- general grime streaks running down every vertical surface
    grime = B.noise(B.mapping(obj, (9.0, 9.0, 0.5)), 2.0, detail=6, rough=0.6)
    grime = B.math('MULTIPLY', B.maprange(grime, 0.45, 0.75), B.maprange(B.noise(obj, 0.5, detail=2), 0.35, 0.65))
    col = B.mix(B.math('MULTIPLY', B.math('MULTIPLY', grime, upper), 0.55), col, lin((0.22, 0.21, 0.19)))

    # ---- salt bloom and waterline growth
    salt = B.math('MULTIPLY', B.maprange(B.noise(B.mapping(obj, (2, 2, 6)), 2.0, detail=6), 0.5, 0.7),
                  B.math('MULTIPLY', B.maprange(Z, WL + 0.1, WL + 0.5), B.maprange(Z, WL + 1.5, WL + 0.6)))
    col = B.mix(B.math('MULTIPLY', salt, 0.45), col, lin((0.78, 0.78, 0.74)))
    growth = B.math('MULTIPLY', B.maprange(Z, WL - 0.9, WL - 0.05),
                    B.maprange(Z, WL + 0.12, WL - 0.02))
    growth = B.math('MULTIPLY', growth, B.maprange(B.noise(obj, 3.5, detail=8), 0.38, 0.62))
    col = B.mix(growth, col, lin((0.17, 0.2, 0.11)))

    # ---- weld seams (raised beads) and plate texture
    seams_y = seam_lines(B, Y, 2.4, 0.012)
    seams_z = seam_lines(B, Z, 1.15, 0.012)
    seams = B.math('MAXIMUM', seams_y, seams_z)
    h = B.math('MULTIPLY', seams, 0.6)
    h = B.math('ADD', h, B.math('MULTIPLY', B.noise(obj, 40.0, detail=4), 0.15))
    h = B.math('ADD', h, B.math('MULTIPLY', peel, -0.5))
    nrm = B.bump(h, strength=0.35, dist=0.004)
    dent = B.noise(obj, 0.9, detail=3)
    nrm = B.bump(dent, strength=0.06, dist=0.05, normal=nrm)

    rough = B.mixf(peel, 0.62, 0.78)
    rough = B.mixf(B.math('MULTIPLY', runs, 0.8), rough, 0.9)
    rough = B.mixf(B.math('MULTIPLY', B.math('SUBTRACT', 1.0, upper), 1.0), rough, 0.55)
    rough = B.mixf(growth, rough, 0.95)
    p = B.principled()
    B.link(col, P(p, 'Base Color'))
    B.link(rough, P(p, 'Roughness'))
    B.link(nrm, P(p, 'Normal'))
    P(p, 'Specular').default_value = 0.45
    return m


def simple(name, color, rough=0.6, metal=0.0, spec=0.5, bump_scale=None, bump_str=0.1):
    m, B = fresh(name)
    p = B.principled()
    P(p, 'Base Color').default_value = (*color, 1.0)
    P(p, 'Roughness').default_value = rough
    P(p, 'Metallic').default_value = metal
    P(p, 'Specular').default_value = spec
    if bump_scale:
        tc = B.n('ShaderNodeTexCoord')
        n = B.noise(tc.outputs['Object'], bump_scale, detail=6)
        B.link(B.bump(n, strength=bump_str, dist=0.01), P(p, 'Normal'))
    return m


def mat_gunmetal():
    m, B = fresh('M_Gunmetal')
    tc = B.n('ShaderNodeTexCoord'); obj = tc.outputs['Object']
    geo = B.n('ShaderNodeNewGeometry')
    edge = B.maprange(geo.outputs['Pointiness'], 0.51, 0.58)
    edge = B.math('MULTIPLY', edge, B.maprange(B.noise(obj, 25.0, detail=3), 0.4, 0.6))
    grime = B.maprange(B.noise(obj, 4.0, detail=8), 0.4, 0.7)
    col = B.mix(grime, lin((0.34, 0.35, 0.35)), lin((0.2, 0.2, 0.2)))
    col = B.mix(B.math('MULTIPLY', B.maprange(B.noise(obj, 7.0, detail=6), 0.62, 0.7), 0.8), col, lin((0.32, 0.17, 0.08)))
    col = B.mix(edge, col, lin((0.55, 0.55, 0.56)))
    p = B.principled()
    B.link(col, P(p, 'Base Color'))
    B.link(B.mixf(edge, 0.15, 0.9), P(p, 'Metallic'))
    B.link(B.mixf(edge, 0.55, 0.3), P(p, 'Roughness'))
    B.link(B.bump(B.noise(obj, 60.0, detail=3), strength=0.08, dist=0.002), P(p, 'Normal'))
    return m


def mat_deck_wood(across=False):
    m, B = fresh('M_GratingWood' if across else 'M_DeckWood')
    tc = B.n('ShaderNodeTexCoord'); obj = tc.outputs['Object']
    if across:
        # Bridge and Wintergarten slats run athwartships.
        obj = B.mapping(obj, rot=(0, 0, math.pi / 2))
    sep = B.n('ShaderNodeSeparateXYZ'); B.link(obj, sep.inputs[0])
    X, Y, Z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    # per-plank id from floor(x / pitch), floor(y / segment)
    px = B.math('FLOOR', B.math('ADD', B.math('DIVIDE', X, 0.105 if across else 0.133), 0.5))
    py = 0 if across else B.math('FLOOR', B.math('DIVIDE', Y, 1.47))
    comb = B.n('ShaderNodeCombineXYZ')
    B.link(px, comb.inputs[0]); B._feed(comb.inputs[1], py)
    wn = B.n('ShaderNodeTexWhiteNoise', noise_dimensions='3D')
    B.link(comb.outputs[0], wn.inputs['Vector'])
    rnd = wn.outputs['Value']
    # grain stretched along the plank (Y)
    grain_v = B.mapping(obj, (28.0, 1.2, 28.0), loc=(0, 0, 0))
    grain = B.noise(grain_v, 4.0, detail=10, rough=0.6, dist=0.6)
    rings_ = B.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X')
    B.link(B.mapping(obj, (1.0, 0.04, 1.0)), rings_.inputs['Vector'])
    rings_.inputs['Scale'].default_value = 18.0
    rings_.inputs['Distortion'].default_value = 6.0
    rings_.inputs['Detail'].default_value = 3.0
    g = B.math('ADD', B.math('MULTIPLY', grain, 0.7), B.math('MULTIPLY', rings_.outputs['Fac'], 0.3))
    weathered = lin((0.40, 0.395, 0.375))
    dark = lin((0.2, 0.185, 0.165))
    col = B.mix(B.maprange(g, 0.35, 0.75), weathered, dark)
    col = B.mix(B.math('MULTIPLY', rnd, 0.6), col, lin((0.3, 0.27, 0.23)))
    # wet/dirty patches and rust stains near fittings
    dirt = B.maprange(B.noise(obj, 0.8, detail=6), 0.5, 0.75)
    col = B.mix(B.math('MULTIPLY', dirt, 0.6), col, lin((0.16, 0.14, 0.11)))
    p = B.principled()
    B.link(col, P(p, 'Base Color'))
    B.link(B.mixf(dirt, 0.82, 0.7), P(p, 'Roughness'))
    P(p, 'Specular').default_value = 0.35
    B.link(B.bump(g, strength=0.25, dist=0.003), P(p, 'Normal'))
    return m


def mat_bronze():
    m, B = fresh('M_Bronze')
    tc = B.n('ShaderNodeTexCoord'); obj = tc.outputs['Object']
    pat = B.maprange(B.noise(obj, 5.0, detail=8), 0.5, 0.68)
    col = B.mix(pat, lin((0.72, 0.5, 0.3)), lin((0.25, 0.33, 0.24)))
    p = B.principled()
    B.link(col, P(p, 'Base Color'))
    B.link(B.mixf(pat, 1.0, 0.2), P(p, 'Metallic'))
    B.link(B.mixf(pat, 0.32, 0.8), P(p, 'Roughness'))
    B.link(B.bump(B.noise(obj, 30, detail=4), strength=0.08, dist=0.003), P(p, 'Normal'))
    return m


def mat_netting():
    m, B = fresh('M_Netting')
    tc = B.n('ShaderNodeTexCoord'); obj = tc.outputs['Object']
    sep = B.n('ShaderNodeSeparateXYZ'); B.link(obj, sep.inputs[0])
    X, Y, Z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    hz = B.math('ADD', X, Y)
    a = B.math('ADD', hz, Z)
    b = B.math('SUBTRACT', hz, Z)
    la = seam_lines(B, a, 0.075, 0.011)
    lb = seam_lines(B, b, 0.075, 0.011)
    wire = B.math('MAXIMUM', la, lb)
    p = B.principled(out_node=False)
    P(p, 'Base Color').default_value = (*lin((0.42, 0.42, 0.4)), 1.0)
    P(p, 'Metallic').default_value = 0.6
    P(p, 'Roughness').default_value = 0.55
    tr = B.n('ShaderNodeBsdfTransparent')
    ms = B.n('ShaderNodeMixShader')
    B.link(wire, ms.inputs[0])
    B.link(tr.outputs[0], ms.inputs[1])
    B.link(p.outputs[0], ms.inputs[2])
    o = B.n('ShaderNodeOutputMaterial')
    B.link(ms.outputs[0], o.inputs['Surface'])
    m.use_backface_culling = False
    return m


def mat_galv():
    m, B = fresh('M_Galv')
    tc = B.n('ShaderNodeTexCoord'); obj = tc.outputs['Object']
    r = B.maprange(B.noise(obj, 6.0, detail=8), 0.58, 0.7)
    col = B.mix(r, lin((0.5, 0.5, 0.49)), lin((0.3, 0.16, 0.08)))
    p = B.principled()
    B.link(col, P(p, 'Base Color'))
    B.link(B.mixf(r, 0.45, 0.1), P(p, 'Metallic'))
    B.link(B.mixf(r, 0.45, 0.85), P(p, 'Roughness'))
    return m


def build_materials():
    mat_hull_paint()
    mat_gunmetal()
    mat_deck_wood()
    mat_deck_wood(across=True)
    mat_bronze()
    mat_netting()
    mat_galv()
    simple('M_HullDark', lin((0.16, 0.165, 0.17)), rough=0.7, bump_scale=3.0, bump_str=0.05)
    simple('M_DeckVoid', lin((0.03, 0.03, 0.03)), rough=0.95)
    simple('M_Hole', (0.002, 0.002, 0.002), rough=1.0, spec=0.0)
    simple('M_Iron', lin((0.18, 0.12, 0.08)), rough=0.8, metal=0.4, bump_scale=20, bump_str=0.2)
    simple('M_Porcelain', lin((0.62, 0.55, 0.45)), rough=0.18, spec=0.6)
    # the keel is under water and painted like the hull bottom
    k = bpy.data.objects.get('Keel_Ballast')
    if k:
        k.data.materials.clear(); k.data.materials.append(bpy.data.materials['M_HullPaint'])
