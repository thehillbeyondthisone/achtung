# U-505 exterior model: shared helpers.
#
# Coordinates (metres): +Y toward the bow, +X starboard, +Z up.
# Origin: Y = 0 at the pressure-hull midpoint, Z = 0 at the outside bottom of the
# pressure hull. Exported to glTF (Y-up), the bow points to three.js -Z, which matches
# the game's convention (three Z points aft).
#
# Principal dimensions come from Report 2G-9C (docs/sources/report-2g-9c), which
# gives Type IXC/40 figures. U-505 was a Type IXC, so treat them as approximate.
# LOA 76.76 m, max beam 6.86 m, pressure hull diameter 4.45 m.

import bpy, bmesh, math
from mathutils import Vector, Matrix

ROOT = 'U-505'

# ---------------------------------------------------------------- collections

def get_coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    par = parent if parent is not None else bpy.context.scene.collection
    if isinstance(par, str):
        par = get_coll(par)
    if c.name not in [x.name for x in par.children]:
        par.children.link(c)
    return c


def reset_coll(name, parent=ROOT):
    """Create the collection (under parent) and delete everything already in it."""
    if parent and parent != name:
        get_coll(parent)
    c = get_coll(name, parent if parent != name else None)

    def purge(col):
        for ch in list(col.children):
            purge(ch)
            bpy.data.collections.remove(ch)
        for o in list(col.objects):
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if data is not None and getattr(data, 'users', 1) == 0:
                try:
                    if isinstance(data, bpy.types.Mesh):
                        bpy.data.meshes.remove(data)
                    elif isinstance(data, bpy.types.Curve):
                        bpy.data.curves.remove(data)
                except Exception:
                    pass
    purge(c)
    return c

# ---------------------------------------------------------------- materials

def mat(name, color=(0.5, 0.5, 0.5)):
    """Get a material by name; create a plain placeholder if missing.
    materials.py fills in the real node trees later."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.diffuse_color = (*color, 1.0)
        p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p:
            p.inputs[0].default_value = (*color, 1.0)
    return m

# ---------------------------------------------------------------- mesh helpers

def mesh_obj(name, verts, faces, coll, mats=None, smooth=False, mat_idx=None,
             sharp_edges=None, loc=(0, 0, 0), recalc=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    coll.objects.link(ob)
    for m in (mats or []):
        me.materials.append(m if isinstance(m, bpy.types.Material) else mat(m))
    if mat_idx is not None:
        for p, i in zip(me.polygons, mat_idx):
            p.material_index = i
    if sharp_edges:
        attr = me.attributes.get('sharp_edge') or me.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
        want = set(tuple(sorted(e)) for e in sharp_edges)
        for i, e in enumerate(me.edges):
            if tuple(sorted(e.vertices)) in want:
                attr.data[i].value = True
    return ob


def loft(rings, closed=True, cap_start=False, cap_end=False):
    """rings: list of lists of points (same length). Returns verts, faces."""
    n = len(rings[0])
    verts, faces = [], []
    for r in rings:
        verts.extend(r)
    seg = n if closed else n - 1
    for i in range(len(rings) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(seg):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    if cap_start:
        faces.append(tuple(reversed(range(0, n))))
    if cap_end:
        base = (len(rings) - 1) * n
        faces.append(tuple(range(base, base + n)))
    return verts, faces


def bm_to_obj(bm, name, coll, mats=None, smooth=False, loc=(0, 0, 0), rot=None, recalc=True):
    me = bpy.data.meshes.new(name)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot is not None:
        ob.rotation_euler = rot
    coll.objects.link(ob)
    for m in (mats or []):
        me.materials.append(m if isinstance(m, bpy.types.Material) else mat(m))
    return ob


def add_box(bm, center, size, rot=None, mat_index=0):
    """Add an axis-aligned (or rotated) box to bmesh. size = full extents."""
    cx, cy, cz = center
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    corners = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
               (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    M = rot.to_3x3() if rot is not None else Matrix.Identity(3)
    vs = [bm.verts.new(Vector((cx, cy, cz)) + M @ Vector(c)) for c in corners]
    idx = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    fs = []
    for f in idx:
        face = bm.faces.new([vs[i] for i in f])
        face.material_index = mat_index
        fs.append(face)
    return fs


def add_cyl(bm, p0, p1, r, seg=16, cap=True, mat_index=0, r1=None, smooth=True):
    """Cylinder (or cone if r1) from p0 to p1."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    L = axis.length
    if L < 1e-9:
        return []
    z = axis.normalized()
    tmp = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((1, 0, 0))
    x = z.cross(tmp).normalized()
    y = z.cross(x)
    r1 = r if r1 is None else r1
    ring0, ring1 = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        d = x * math.cos(a) + y * math.sin(a)
        ring0.append(bm.verts.new(p0 + d * r))
        ring1.append(bm.verts.new(p1 + d * r1))
    fs = []
    for i in range(seg):
        j = (i + 1) % seg
        f = bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
        f.smooth = smooth
        f.material_index = mat_index
        fs.append(f)
    if cap:
        f = bm.faces.new(list(reversed(ring0)))
        f.material_index = mat_index
        fs.append(f)
        f = bm.faces.new(ring1)
        f.material_index = mat_index
        fs.append(f)
    return fs


def add_tube_path(bm, pts, r, seg=10, mat_index=0, cap=True):
    """Swept circular tube along a polyline (parallel-transport frames)."""
    pts = [Vector(p) for p in pts]
    if len(pts) < 2:
        return
    tangents = []
    for i in range(len(pts)):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        tangents.append(t.normalized())
    tmp = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    n = tangents[0].cross(tmp).normalized()
    rings = []
    for i, p in enumerate(pts):
        t = tangents[i]
        if i > 0:
            n = (n - t * n.dot(t)).normalized()
        b = t.cross(n)
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            ring.append(bm.verts.new(p + (n * math.cos(a) + b * math.sin(a)) * r))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            f.smooth = True
            f.material_index = mat_index
    if cap:
        f = bm.faces.new(list(reversed(rings[0])))
        f.material_index = mat_index
        f = bm.faces.new(rings[-1])
        f.material_index = mat_index


def add_loft_bm(bm, rings, closed=True, cap_start=False, cap_end=False, mat_index=0, smooth=True):
    vr = [[bm.verts.new(Vector(p)) for p in r] for r in rings]
    n = len(rings[0])
    seg = n if closed else n - 1
    for i in range(len(vr) - 1):
        for j in range(seg):
            j2 = (j + 1) % n
            f = bm.faces.new((vr[i][j], vr[i][j2], vr[i + 1][j2], vr[i + 1][j]))
            f.smooth = smooth
            f.material_index = mat_index
    if cap_start:
        f = bm.faces.new(list(reversed(vr[0])))
        f.material_index = mat_index
    if cap_end:
        f = bm.faces.new(vr[-1])
        f.material_index = mat_index
    return vr

def shrinkwrap(ob, target, offset=0.004):
    """Keep a decal-like object (slots, outlines) sitting on a curved surface."""
    t = bpy.data.objects.get(target) if isinstance(target, str) else target
    if t is None:
        return
    m = ob.modifiers.new('Shrinkwrap', 'SHRINKWRAP')
    m.target = t
    m.wrap_method = 'NEAREST_SURFACEPOINT'
    try:
        m.wrap_mode = 'OUTSIDE_SURFACE'
    except Exception:
        pass
    m.offset = offset

# ---------------------------------------------------------------- math

def clamp(x, a, b):
    return a if x < a else b if x > b else x


def ss(a, b, x):
    t = clamp((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def pchip(table, x):
    """Monotone cubic interpolation through [(x, y), ...] sorted by x."""
    xs = [p[0] for p in table]
    ys = [p[1] for p in table]
    n = len(xs)
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    i = max(k for k in range(n - 1) if xs[k] <= x)
    t = (x - xs[i]) / h[i]
    h00 = (1 + 2 * t) * (1 - t) ** 2
    h10 = t * (1 - t) ** 2
    h01 = t * t * (3 - 2 * t)
    h11 = t * t * (t - 1)
    return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]


def se_pow(c, e):
    """sign-preserving |c|^e."""
    return math.copysign(abs(c) ** e, c)


def stations(y0, y1, n, end_density=2.5):
    """Station positions from y0 to y1 clustered toward both ends."""
    out = []
    for i in range(n):
        u = i / (n - 1)
        # blend linear and cosine spacing
        c = 0.5 - 0.5 * math.cos(math.pi * u)
        w = 1.0 / end_density
        out.append(y0 + (y1 - y0) * (w * u + (1 - w) * c))
    return out
