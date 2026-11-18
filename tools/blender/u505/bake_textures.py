# U-505 exterior model: bake the procedural paint and deck timber to textures for glTF.
#
# Run after build() (the builders regenerate meshes, which drops the bake UVs):
#   exec(open(D + 'bake_textures.py').read(), G)
#   G['bake_all'](r'<repo>\art\textures')
# Then export with G['export_glb'](path, draco=True, textured=True).
#
# Two images, base colour only (lighting-free DIFFUSE/COLOR bake):
#   u505_paint_basecolor.jpg  4096 x 4096  every hull-paint object, Smart-UV-unwrapped
#                                          together into one atlas (about 1.3 cm per texel)
#   u505_deck_basecolor.jpg   4096 x 512   Deck_Planks, projected from above along the deck
# The paint shader works in object coordinates, so the bake carries the boot-top two-tone,
# peeling, rust runs, salt and waterline growth regardless of the UV layout. Bump-only
# detail (weld beads, fine paint texture) is not baked.

import os

BAKE_UV = 'BakeUV'
PAINT_SKIP = {'Casing_Seams'}       # thousands of tiny weld-bead tubes: keep flat colour
PAINT_IMG = ('U505_Paint_BaseColor', 4096, 4096, 'u505_paint_basecolor.jpg')
DECK_IMG = ('U505_Deck_BaseColor', 4096, 512, 'u505_deck_basecolor.jpg')


def paint_objects():
    root = bpy.data.collections[ROOT]
    out = []
    for o in root.all_objects:
        if o.type != 'MESH' or o.name in PAINT_SKIP:
            continue
        if any(s.material and s.material.name in ('M_HullPaint', 'M_HullDark') for s in o.material_slots):
            out.append(o)
    return out


def _uv_layer(o):
    me = o.data
    uv = me.uv_layers.get(BAKE_UV) or me.uv_layers.new(name=BAKE_UV)
    me.uv_layers.active = uv
    uv.active_render = True
    return uv


def _select_only(objs):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def unwrap_paint(objs):
    """Smart UV project all paint objects together, packed into one 0..1 layout."""
    for o in objs:
        _uv_layer(o)
    _select_only(objs)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0015,
                             area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def unwrap_deck(o):
    """Top-down projection along the deck: u along the length, v across."""
    uv = _uv_layer(o)
    me = o.data
    y0, y1 = DECK_Y0 - 0.2, DECK_Y1 + 0.2
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.y - y0) / (y1 - y0), (co.x + 1.85) / 3.7)


def uv_area(objs):
    """Total UV area of the objects (an atlas packed as one should stay below 1)."""
    tot = 0.0
    for o in objs:
        uv = o.data.uv_layers[BAKE_UV].data
        for p in o.data.polygons:
            pts = [uv[li].uv for li in p.loop_indices]
            a = 0.0
            for i in range(len(pts)):
                x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
                a += x0 * y1 - x1 * y0
            tot += abs(a) / 2
    return tot


def _bake(objs, spec, out_dir, samples=8, margin=16):
    name, w, h, fname = spec
    img = bpy.data.images.get(name)
    if img and (img.size[0] != w or img.size[1] != h):
        bpy.data.images.remove(img); img = None
    img = img or bpy.data.images.new(name, w, h, alpha=False)
    mats = []
    for o in objs:
        for s in o.material_slots:
            if s.material and s.material not in mats:
                mats.append(s.material)
    added = []
    try:
        for m in mats:
            nt = m.node_tree
            n = nt.nodes.new('ShaderNodeTexImage')
            n.name = 'BAKE_TARGET'
            n.image = img
            nt.nodes.active = n
            added.append((m, n))
        sc = bpy.context.scene
        try:
            sc.render.engine = 'CYCLES'
        except TypeError:
            pass
        prev = sc.cycles.samples
        sc.cycles.samples = samples
        _select_only(objs)
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=margin,
                            use_selected_to_active=False, target='IMAGE_TEXTURES', use_clear=True)
        sc.cycles.samples = prev
    finally:
        for m, n in added:
            m.node_tree.nodes.remove(n)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, fname)
    # Image.save writes the baked bytes as they are (save_render would apply the AgX view)
    img.filepath_raw = path
    img.file_format = 'JPEG'
    try:
        img.save(filepath=path, quality=90)
    except TypeError:
        img.save()
    img.filepath = path
    img.source = 'FILE'
    img.reload()
    return path


def bake_all(out_dir):
    import time
    t = time.time()
    paint = paint_objects()
    unwrap_paint(paint)
    area = uv_area(paint)
    deck = bpy.data.objects['Deck_Planks']
    unwrap_deck(deck)
    p1 = _bake(paint, PAINT_IMG, out_dir)
    p2 = _bake([deck], DECK_IMG, out_dir)
    return dict(paint_objects=len(paint), paint_uv_area=round(area, 3), paint=p1, deck=p2,
                seconds=round(time.time() - t, 1))
