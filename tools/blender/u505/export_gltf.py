# U-505 exterior model: glTF export (web test).
#
# In Blender, after build.py has been exec'd into G:
#   exec(open(D + 'export_gltf.py').read(), G)
#   G['export_glb'](r'<repo>\art\u505_exterior.glb')            # plain
#   G['export_glb'](r'<repo>\art\u505_exterior_draco.glb', draco=True)
#
# The procedural Cycles shaders do not survive glTF, so this exports temporary copies
# of the boat meshes with flat web materials (constant PBR factors). Painted faces
# below the boot-top (centre z < WL + 0.12) get the dark bottom colour, which keeps the
# two-tone without textures. Tower_Netting is left out (alpha panels sort badly in
# three.js). The originals and their materials are never modified.
#
# Axes: Blender +Y (bow) becomes glTF/three.js -Z, +Z up becomes +Y. One unit = 1 m.
# Origin: pressure-hull midpoint, outside bottom of the pressure hull.

WEB_WL = 4.30
SKIP = {'Tower_Netting'}


def _lin(c):
    f = lambda u: u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return tuple(f(u) for u in c)


WEB = {  # name: (srgb colour, metallic, roughness)
    'X_Paint':     ((0.55, 0.555, 0.55), 0.0, 0.7),
    'X_PaintLow':  ((0.2, 0.205, 0.21), 0.0, 0.6),
    'X_Deck':      ((0.38, 0.36, 0.33), 0.0, 0.85),
    'X_Void':      ((0.03, 0.03, 0.03), 0.0, 0.95),
    'X_Hole':      ((0.01, 0.01, 0.01), 0.0, 1.0),
    'X_Gun':       ((0.3, 0.3, 0.3), 0.3, 0.5),
    'X_Galv':      ((0.5, 0.5, 0.49), 0.5, 0.45),
    'X_Bronze':    ((0.72, 0.5, 0.3), 1.0, 0.35),
    'X_Iron':      ((0.25, 0.17, 0.12), 0.4, 0.8),
    'X_Porcelain': ((0.62, 0.55, 0.45), 0.0, 0.2),
}
MAP = {'M_HullPaint': 'X_Paint', 'M_HullDark': 'X_PaintLow', 'M_DeckWood': 'X_Deck',
       'M_DeckVoid': 'X_Void', 'M_Hole': 'X_Hole', 'M_Gunmetal': 'X_Gun', 'M_Galv': 'X_Galv',
       'M_Bronze': 'X_Bronze', 'M_Iron': 'X_Iron', 'M_Porcelain': 'X_Porcelain'}


def _web_mats():
    out = {}
    for nm, (c, metal, rough) in WEB.items():
        m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
        m.use_nodes = True
        p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        p.inputs['Base Color'].default_value = (*_lin(c), 1.0)
        p.inputs['Metallic'].default_value = metal
        p.inputs['Roughness'].default_value = rough
        m.diffuse_color = (*_lin(c), 1.0)
        out[nm] = m
    return out


TEX_MATS = {  # textured web material: (baked image name, roughness)
    'X_PaintTex': ('U505_Paint_BaseColor', 0.7),
    'X_DeckTex': ('U505_Deck_BaseColor', 0.85),
}


def _tex_mats():
    out = {}
    for nm, (img_name, rough) in TEX_MATS.items():
        img = bpy.data.images.get(img_name)
        if img is None:
            raise RuntimeError(f'{img_name} missing: run bake_all() from bake_textures.py first')
        m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        p = nt.nodes.new('ShaderNodeBsdfPrincipled')
        o = nt.nodes.new('ShaderNodeOutputMaterial')
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = img
        uvn = nt.nodes.new('ShaderNodeUVMap')
        uvn.uv_map = 'BakeUV'
        nt.links.new(uvn.outputs['UV'], t.inputs['Vector'])
        nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
        nt.links.new(p.outputs[0], o.inputs['Surface'])
        p.inputs['Roughness'].default_value = rough
        p.inputs['Metallic'].default_value = 0.0
        out[nm] = m
    return out


def export_glb(path, draco=False, textured=False):
    """textured=True uses the baked images (bake_textures.py) on objects that carry the
    BakeUV layer: paint faces get X_PaintTex, Deck_Planks gets X_DeckTex."""
    root = bpy.data.collections[ROOT]
    web = _web_mats()
    if textured:
        web.update(_tex_mats())
    srcs = [o for o in root.all_objects if o.type == 'MESH' and o.name not in SKIP]
    tmp = bpy.data.collections.new('_glb_export')
    bpy.context.scene.collection.children.link(tmp)
    renamed, copies = [], []
    try:
        for o in srcs:
            nm = o.name
            o.name = nm + '__src'
            renamed.append((o, nm))
            c = o.copy()
            c.data = o.data.copy()
            c.name = nm
            tmp.objects.link(c)
            copies.append(c)
            me = c.data
            old = [s.material.name if s.material else '' for s in c.material_slots]
            # read face slots first: clearing the materials resets every face to slot 0
            face_slot = [p.material_index for p in me.polygons]
            me.materials.clear()
            baked = textured and 'BakeUV' in me.uv_layers
            names = []
            for on in old:
                wn = MAP.get(on, 'X_Paint')
                if baked and wn in ('X_Paint', 'X_PaintLow'):
                    wn = 'X_PaintTex'
                elif baked and wn == 'X_Deck' and c.name == 'Deck_Planks':
                    wn = 'X_DeckTex'
                names.append(wn)
            if baked:
                me.uv_layers.active = me.uv_layers['BakeUV']
            else:
                while me.uv_layers:
                    me.uv_layers.remove(me.uv_layers[0])
            uniq = list(dict.fromkeys(names + (['X_PaintLow'] if 'X_Paint' in names else [])))
            for u in uniq:
                me.materials.append(web[u])
            low_i = uniq.index('X_PaintLow') if 'X_PaintLow' in uniq else None
            for p, fs in zip(me.polygons, face_slot):
                tgt = names[fs] if fs < len(names) else 'X_Paint'
                idx = uniq.index(tgt)
                if tgt == 'X_Paint' and low_i is not None and p.center.z < WEB_WL + 0.12:
                    idx = low_i
                p.material_index = idx
        # select only the copies
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        for c in copies:
            c.select_set(True)
        bpy.context.view_layer.objects.active = copies[0]
        kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                  export_yup=True, export_cameras=False, export_lights=False,
                  export_attributes=False, export_extras=False, export_materials='EXPORT',
                  export_texcoords=True, export_normals=True,
                  export_draco_mesh_compression_enable=draco)
        if draco:
            kw['export_draco_mesh_compression_level'] = 6
        if textured:
            kw['export_image_format'] = 'JPEG'
            kw['export_jpeg_quality'] = 88
        bpy.ops.export_scene.gltf(**kw)
    finally:
        for c in copies:
            me = c.data
            bpy.data.objects.remove(c, do_unlink=True)
            if me.users == 0:
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(tmp)
        for o, nm in renamed:
            o.name = nm
    import os
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in srcs)
    return dict(path=path, bytes=os.path.getsize(path), objects=len(srcs), tris_before_modifiers=tris)
