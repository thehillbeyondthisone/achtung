# U-505 exterior model: presentation sets, cameras and render helper.
#   use_set('sea')     Atlantic: Ocean modifier sea at the surfaced waterline, physical sky, sun
#   use_set('studio')  Display: hull on keel blocks over a cyclorama, area lights
#   shoot('Cam_Hero', path, samples=256, res=(1920, 1080))
# The boat sits at normal surfaced trim (estimated waterline WL = 4.30 m above the
# pressure-hull bottom), not at the damaged, low attitude seen in the capture photographs.

SETS = ('Set_Sea', 'Set_Studio')

CAMERAS = {
    # name: (target, direction from target to camera, distance, lens, set)
    'Cam_Hero':        ((0, 3.0, 5.6), (1.0, 0.72, 0.11), 92, 42, 'sea'),
    'Cam_SeaBroadside': ((0, 0.5, 5.6), (1.0, 0.05, 0.06), 128, 50, 'sea'),
    'Cam_Tower':       ((0, -1.0, 7.9), (0.95, 0.55, 0.42), 13.5, 35, 'sea'),
    'Cam_Wintergarten': ((0, -4.2, 8.3), (0.55, -0.95, 0.5), 7.5, 28, 'sea'),
    'Cam_DeckFwd':     ((0, 14.0, 6.3), (0.18, 1.0, 0.16), 15, 24, 'sea'),
    'Cam_StudioBow':   ((0, 8.0, 3.2), (0.72, 1.0, 0.1), 74, 40, 'studio'),
    'Cam_StudioStern': ((0, -32.5, 1.9), (0.9, -0.7, -0.08), 12.5, 30, 'studio'),
    'Cam_StudioSide':  ((0, 0.6, 3.6), (1.0, 0.0, 0.02), 108, 40, 'studio'),
    'Cam_StudioBowPlanes': ((1.2, 32.0, 2.3), (0.75, 0.75, -0.42), 10.0, 28, 'studio'),
}


def _aim(cam, target, direction, dist, lens):
    t = Vector(target); d = Vector(direction).normalized()
    cam.location = t + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_start = 0.1
    cam.data.clip_end = 5000


def _world(name, sky=True):
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
    if sky:
        s = nt.nodes.new('ShaderNodeTexSky')
        for t in ('MULTIPLE_SCATTERING', 'SINGLE_SCATTERING', 'NISHITA', 'HOSEK_WILKIE'):
            try:
                s.sky_type = t; break
            except Exception:
                pass
        for k, v in (('sun_elevation', math.radians(24)), ('sun_rotation', math.radians(205)),
                     ('altitude', 30.0), ('air_density', 1.0), ('aerosol_density', 0.8), ('ozone_density', 1.0),
                     ('sun_intensity', 0.7), ('sun_size', math.radians(0.6))):
            try:
                setattr(s, k, v)
            except Exception:
                pass
        nt.links.new(s.outputs[0], bg.inputs['Color'])
        bg.inputs['Strength'].default_value = 0.09
    else:
        grad = nt.nodes.new('ShaderNodeTexGradient')
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Rotation'].default_value = (0, -math.pi / 2, 0)
        nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
        nt.links.new(mp.outputs[0], grad.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (0.012, 0.013, 0.015, 1)
        ramp.color_ramp.elements[1].color = (0.05, 0.055, 0.06, 1)
        nt.links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
        bg.inputs['Strength'].default_value = 1.0
    return w


def _water_mat():
    m, B = fresh('M_Sea')
    attr = B.n('ShaderNodeAttribute', attribute_name='foam')
    tc = B.n('ShaderNodeTexCoord')
    foam_break = B.noise(tc.outputs['Object'], 1.8, detail=8)
    foam = B.math('MULTIPLY', B.maprange(attr.outputs['Fac'], 0.25, 0.9), B.maprange(foam_break, 0.45, 0.7))
    col = B.mix(foam, lin((0.005, 0.035, 0.06)), lin((0.75, 0.78, 0.78)))
    p = B.principled()
    B.link(col, P(p, 'Base Color'))
    B.link(B.mixf(foam, 0.07, 0.7), P(p, 'Roughness'))
    # wind ripples on top of the swell
    rip = B.noise(B.mapping(tc.outputs['Object'], (1.0, 2.2, 1.0)), 2.2, detail=10, rough=0.6)
    B.link(B.bump(rip, strength=0.22, dist=0.08), P(p, 'Normal'))
    P(p, 'IOR').default_value = 1.333
    P(p, 'Specular').default_value = 0.5
    try:
        P(p, 'Subsurface Weight').default_value = 0.0
    except KeyError:
        pass
    return m


def build_scene():
    sc = bpy.context.scene
    # ---------------------------------------------------------------- sea set
    c = reset_coll('Set_Sea', None)
    me = bpy.data.meshes.new('Sea')
    sea = bpy.data.objects.new('Sea', me)
    c.objects.link(sea)
    SS, REP = 160, 5
    sea.location = (-SS * REP / 2, -SS * REP / 2, WL)
    o = sea.modifiers.new('Ocean', 'OCEAN')
    for k, v in (('geometry_mode', 'GENERATE'), ('resolution', 18), ('viewport_resolution', 8),
                 ('spatial_size', SS), ('repeat_x', REP), ('repeat_y', REP), ('size', 1.0),
                 ('wave_scale', 1.9), ('choppiness', 1.15), ('wind_velocity', 11.0),
                 ('wave_alignment', 0.35), ('wave_direction', math.radians(35)), ('damping', 0.5),
                 ('use_normals', True), ('use_foam', True), ('foam_layer_name', 'foam'),
                 ('foam_coverage', 0.35), ('random_seed', 7), ('time', 3.0)):
        try:
            setattr(o, k, v)
        except Exception as e:
            print('ocean', k, e)
    me.materials.append(_water_mat())
    me.shade_smooth()
    # far-sea skirt out to the horizon (a ring with a hole where the ocean patch is)
    bm = bmesh.new()
    inner = SS * REP / 2 - 6
    outer = 9000.0
    N = 64
    zf = WL - 1.1   # below the patch's troughs where they overlap
    ri = [bm.verts.new((inner * 0.9 * math.cos(2 * math.pi * k / N), inner * 0.9 * math.sin(2 * math.pi * k / N), zf)) for k in range(N)]
    ro = [bm.verts.new((outer * math.cos(2 * math.pi * k / N), outer * math.sin(2 * math.pi * k / N), zf)) for k in range(N)]
    for k in range(N):
        k2 = (k + 1) % N
        bm.faces.new((ri[k], ri[k2], ro[k2], ro[k]))
    bm_to_obj(bm, 'Sea_Far', c, mats=['M_Sea'], smooth=True)
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 2.6
    sun.angle = math.radians(1.2)
    sun.color = (1.0, 0.95, 0.88)
    so = bpy.data.objects.new('Sun', sun)
    so.rotation_euler = (math.radians(66), 0, math.radians(205 - 180))
    c.objects.link(so)
    # ---------------------------------------------------------------- studio set
    c2 = reset_coll('Set_Studio', None)
    bm = bmesh.new()
    floor_z = -1.45
    # cyclorama: floor sweeping up behind the boat (behind = -X, cameras sit to starboard)
    rings = []
    for k in range(25):
        a = (math.pi / 2) * k / 24
        r = 30.0
        x = -30.0 - r * math.sin(a)
        z = floor_z + r - r * math.cos(a)
        rings.append([(x, -1500.0, z), (x, 1500.0, z)])
    rings.insert(0, [(1500.0, -1500.0, floor_z), (1500.0, 1500.0, floor_z)])
    vs = [[bm.verts.new(p) for p in r] for r in rings]
    for i in range(len(vs) - 1):
        bm.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))
    ext = [(vs[-1][0].co.x, -1500.0, vs[-1][0].co.z + 400.0), (vs[-1][0].co.x, 1500.0, vs[-1][0].co.z + 400.0)]
    e0, e1 = bm.verts.new(ext[0]), bm.verts.new(ext[1])
    bm.faces.new((vs[-1][0], vs[-1][1], e1, e0))
    cyc = bm_to_obj(bm, 'Studio_Cyc', c2, mats=[simple('M_Studio', lin((0.2, 0.205, 0.21)), rough=0.85)], smooth=True)
    # keel blocks and side shores (timber)
    bm = bmesh.new()
    kz = -0.35
    for yy in range(-24, 26, 4):
        for lvl in range(3):
            h = (kz - floor_z) / 3
            z0 = floor_z + lvl * h
            rot = Matrix.Rotation(math.radians(90 if lvl % 2 else 0), 4, 'Z')
            add_box(bm, (0, yy, z0 + h / 2), (1.5, 0.45, h * 0.96), rot=rot if lvl % 2 else None)
    for yy in (-14.0, -6.0, 6.0, 14.0):
        for s in (1, -1):
            pt, n = tank_point(yy, -1.15, s)
            top = pt - n * 0.02
            base = Vector((pt.x + s * 0.9, yy, floor_z))
            add_box(bm, (base.x, yy, floor_z + 0.15), (0.8, 0.6, 0.3))
            add_cyl(bm, base + Vector((0, 0, 0.3)), top, 0.14, seg=8)
    bm_to_obj(bm, 'Studio_Blocks', c2, mats=['M_DeckWood'])
    for nm, loc, rot, size, energy, col in (
            ('Key', (38, 30, 32), (math.radians(52), 0, math.radians(128)), 26, 65000, (1.0, 0.96, 0.9)),
            # raised and tilted down so its emission plane meets the floor out of shot
            ('Fill', (48, -38, 26), (math.radians(55), 0, math.radians(50)), 34, 22000, (0.85, 0.9, 1.0)),
            ('Rim', (-25, -10, 28), (math.radians(-40), math.radians(10), math.radians(-90)), 22, 60000, (0.95, 0.97, 1.0)),
            ('Under', (6, 0, -1.3), (math.radians(160), 0, math.radians(90)), 60, 9000, (1.0, 0.94, 0.88))):
        ld = bpy.data.lights.new('Studio_' + nm, 'AREA')
        ld.energy = energy; ld.size = size; ld.color = col
        if nm == 'Under':   # long strip on the floor shining up at the hull, never at the floor
            ld.shape = 'RECTANGLE'; ld.size_y = 3.0
        lo = bpy.data.objects.new('Studio_' + nm, ld)
        lo.location = loc; lo.rotation_euler = rot
        lo.visible_camera = False
        c2.objects.link(lo)
    # ---------------------------------------------------------------- cameras
    cc = reset_coll('Cameras', None)
    for nm, (t, d, dist, lens, _) in CAMERAS.items():
        cam = bpy.data.objects.new(nm, bpy.data.cameras.new(nm))
        cc.objects.link(cam)
        _aim(cam, t, d, dist, lens)
        cam.data.dof.use_dof = False
    _world('W_Sea', sky=True)
    _world('W_Studio', sky=False)
    # ---------------------------------------------------------------- render settings
    try:
        sc.render.engine = 'CYCLES'
    except TypeError:
        pass
    sc.cycles.device = 'GPU'
    sc.cycles.use_denoising = True
    sc.cycles.samples = 256
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.max_bounces = 8
    sc.cycles.transparent_max_bounces = 24
    for vt in ('AgX', 'Filmic'):
        try:
            sc.view_settings.view_transform = vt; break
        except Exception:
            pass
    for lk in ('AgX - Medium High Contrast', 'Medium High Contrast', 'High Contrast'):
        try:
            sc.view_settings.look = lk; break
        except Exception:
            pass
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    use_set('sea')


def use_set(name):
    sc = bpy.context.scene
    want = {'sea': 'Set_Sea', 'studio': 'Set_Studio'}[name]
    for cn in SETS:
        col = bpy.data.collections.get(cn)
        if col:
            col.hide_render = (cn != want)
            col.hide_viewport = (cn != want)
    w = bpy.data.worlds.get('W_Sea' if name == 'sea' else 'W_Studio')
    if w:
        sc.world = w


def shoot(cam_name, path, samples=256, res=(1920, 1080)):
    sc = bpy.context.scene
    use_set(CAMERAS[cam_name][4])
    sc.camera = bpy.data.objects[cam_name]
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 92
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
