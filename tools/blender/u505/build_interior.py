"""Rebuild the U-505 engineering route in Blender 5.2.

Run with Blender's --python flag. Add -- --graybox for the temporary diesel fit
asset, or -- --review to re-import the complete GLB and render matching views.
Blender X is starboard, Y is bow, and Z is up from the pressure-hull axis.
"""

import argparse
from dataclasses import dataclass
import json
from math import acos, atan2, cos, pi, sin, sqrt, tau
from pathlib import Path
import re
import sys

import bpy
from mathutils import Vector
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
ROOM_IDS = ('control', 'diesel', 'motor', 'aft_torpedo')
DIESEL_SHELL_SEGMENTS = 96


@dataclass
class Room:
    aft: float
    bow: float
    walk: float

    @property
    def mid(self):
        return (self.aft + self.bow) / 2

    @property
    def length(self):
        return self.bow - self.aft


def read_layout():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    rooms = {}
    data = json.loads(re.search(r'id="data-compartments">\s*(.*?)</script>', html, re.S)[1])
    systems = json.loads(re.search(r'id="data-systems">\s*(.*?)</script>', html, re.S)[1])
    hull = data['hull']
    station = hull['pressure_hull_length_m'] / 2
    for entry in data['compartments']:
        aft = station - entry['length_m']
        rooms[entry['id']] = Room(aft, station, entry['walk_half_width_m'])
        station = aft
    return hull, rooms, systems


class Assembly:
    def __init__(self, name, materials):
        self.root = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(self.root)
        self.materials = materials
        self.batches = {}

    def append(self, finish, vertices, faces, smooth=()):
        points, polygons, flags = self.batches.setdefault(finish, ([], [], []))
        offset = len(points)
        points.extend(vertices)
        polygons.extend(tuple(offset + index for index in face) for face in faces)
        smooth_faces = set(smooth)
        flags.extend(index in smooth_faces for index in range(len(faces)))

    def box(self, finish, center, size, angle=0):
        x, y, z = center
        w, d, h = (value / 2 for value in size)
        local = ((-w, -d), (w, -d), (w, d), (-w, d))
        points = [(x + u * cos(angle) - v * sin(angle), y + u * sin(angle) + v * cos(angle), z + j)
                  for j in (-h, h) for u, v in local]
        self.append(finish, points, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
                                     (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])

    def loft(self, finish, rings, smooth=False):
        n = len(rings[0])
        faces = [(row * n + k, row * n + (k + 1) % n,
                  (row + 1) * n + (k + 1) % n, (row + 1) * n + k)
                 for row in range(len(rings) - 1) for k in range(n)]
        curved = range(len(faces)) if smooth else ()
        faces += [tuple(reversed(range(n))), tuple(range((len(rings) - 1) * n, len(rings) * n))]
        self.append(finish, [point for ring in rings for point in ring], faces, curved)

    def cylinder(self, finish, start, end, radius, sides=12, end_radius=None):
        a, b = Vector(start), Vector(end)
        axis = (b - a).normalized()
        u = axis.cross(Vector((0, 0, 1)) if abs(axis.z) < .95 else Vector((0, 1, 0))).normalized()
        v = axis.cross(u)
        self.loft(finish, [[origin + (u * cos(tau * k / sides) + v * sin(tau * k / sides)) * r
                            for k in range(sides)] for origin, r in ((a, radius), (b, end_radius or radius))],
                  smooth=sides > 8)

    def pipe(self, finish, path, radius, sides=10, bend=.085):
        points = [Vector(point) for point in path]
        curved = [points[0]]
        for a, b, c in zip(points, points[1:], points[2:]):
            start = b.lerp(a, min(.38, bend / (b - a).length))
            end = b.lerp(c, min(.38, bend / (c - b).length))
            curved.extend(start.lerp(b, t / 4).lerp(b.lerp(end, t / 4), t / 4) for t in range(5))
        curved.append(points[-1])
        first = (curved[1] - curved[0]).normalized()
        u = first.cross(Vector((0, 0, 1)) if abs(first.z) < .95 else Vector((0, 1, 0))).normalized()
        rings = []
        for k, point in enumerate(curved):
            axis = (curved[min(k + 1, len(curved) - 1)] - curved[max(k - 1, 0)]).normalized()
            u = (u - axis * u.dot(axis)).normalized()
            v = axis.cross(u)
            rings.append([point + radius * (u * cos(tau * j / sides) + v * sin(tau * j / sides))
                          for j in range(sides)])
        self.loft(finish, rings, smooth=True)

    def ring(self, finish, center, radius, thickness, axis='y', sides=20, tube=6):
        x, y, z = center
        rings = []
        for k in range(sides):
            a = tau * k / sides
            points = []
            for j in range(tube):
                b = tau * j / tube
                r, offset = radius + thickness * cos(b), thickness * sin(b)
                radial, height = r * cos(a), r * sin(a)
                points.append((x + radial, y + offset, z + height) if axis == 'y'
                              else (x - offset, y + radial, z + height) if axis == 'x'
                              else (x + radial, y - height, z + offset))
            rings.append(points)
        faces = [(k * tube + j, k * tube + (j + 1) % tube,
                  ((k + 1) % sides) * tube + (j + 1) % tube, ((k + 1) % sides) * tube + j)
                 for k in range(sides) for j in range(tube)]
        self.append(finish, [point for ring in rings for point in ring], faces, range(len(faces)))

    def rounded(self, finish, center, size, radius, bevel=.009):
        x, y, z = center
        w, d, h = (value / 2 for value in size)
        radius = min(radius, .92 * w, .92 * d)
        bevel = min(bevel, radius * .5, h * .6)
        rings = []
        for height, inset in ((-h, bevel), (-h + bevel, 0), (h - bevel, 0), (h, bevel)):
            ring = []
            for k, (u, v) in enumerate(((w - radius, d - radius), (-w + radius, d - radius),
                                         (-w + radius, -d + radius), (w - radius, -d + radius))):
                for j in range(4):
                    a = k * pi / 2 + j * pi / 6
                    r = radius - inset
                    ring.append((x + u + r * cos(a), y + v + r * sin(a), z + height))
            rings.append(ring)
        self.loft(finish, rings)

    def finish(self, projections=None, wet_room=None):
        projections = projections or {}
        objects = []
        for label, (vertices, faces, smooth) in self.batches.items():
            name = f'{self.root.name}.{label}'
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata(vertices, [], faces)
            mesh.validate(clean_customdata=False)
            mesh.update()
            mesh.materials.append(self.materials[label])
            uv = mesh.uv_layers.new(name='Material UV')
            scale = 7 if label in ('bedding', 'grating', 'tread', 'diesel_tread') else 2.65
            project = projections.get(label)
            for face, soft in zip(mesh.polygons, smooth):
                face.use_smooth = soft
                axis = max(range(3), key=lambda k: abs(face.normal[k]))
                u, v = ((1, 2), (0, 2), (0, 1))[axis]
                sign = 1 if face.normal[axis] > 0 else -1
                for loop in face.loop_indices:
                    point = mesh.vertices[mesh.loops[loop].vertex_index].co
                    uv.uv[loop].vector = project(point, face) if project else (point[u] * scale * sign, point[v] * scale)
            obj = bpy.data.objects.new(name, mesh)
            bpy.context.scene.collection.objects.link(obj)
            obj.parent = self.root
            if wet_room:
                obj['wet_room'] = wet_room
            objects.append(obj)
        return objects


PALETTE = {
    'enamel': ((.45, .47, .41), (.19, .22, .18), .68, .12),
    'cabinet': ((.56, .55, .45), (.29, .28, .22), .64, .09),
    'paint': ((.29, .37, .34), (.135, .18, .16), .64, .15),
    'iron': ((.19, .22, .215), (.075, .085, .078), .73, .22),
    'steel': ((.43, .46, .46), (.22, .26, .26), .42, .42),
    'brass': ((.51, .40, .24), (.23, .22, .13), .47, .36),
    'black': ((.095, .11, .102), (.053, .061, .058), .68, .05),
    'red': ((.48, .215, .12), (.25, .125, .09), .63, .12),
    'ink': ((.095, .114, .112), (.056, .07, .067), .39, .14),
    'lettering': ((.68, .64, .48), (.4, .38, .29), .74, .0),
    'bedding': ((.44, .44, .34), (.16, .20, .19), .94, .0),
    'blanket': ((.24, .24, .19), (.14, .15, .12), .95, .0),
    'grating': ((.38, .40, .36), (.18, .21, .19), .61, .29),
    'tread': ((.39, .41, .39), (.24, .27, .26), .49, .36),
    'diesel_tread': ((.45, .47, .45), (.29, .32, .30), .41, .47),
    'rib_enamel': ((.48, .51, .45), (.28, .30, .27), .54, .07),
    'weld': ((.39, .41, .37), (.24, .26, .23), .61, .13),
    'rubber': ((.12, .131, .118), (.065, .070, .067), .82, .0),
    'worn_steel': ((.45, .47, .46), (.24, .27, .26), .35, .55),
    'sea_green': ((.24, .47, .31), (.23, .29, .23), .44, .10),
}


def srgb_to_linear(values):
    return np.where(values <= .04045, values / 12.92, ((values + .055) / 1.055) ** 2.4)


def packed_image(name, pixels, colorspace):
    height, width, _ = pixels.shape
    image = bpy.data.images.new(name, width=width, height=height, alpha=False)
    image.colorspace_settings.name = colorspace
    rgba = np.ones((height, width, 4), dtype=np.float32)
    rgba[:, :, :3] = pixels
    image.pixels.foreach_set(rgba.ravel())
    image.file_format = 'PNG'
    image.pack()
    return image


def link_surface_images(mat, label, color, roughness, metallic, relief, contact=None):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    pbr = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
    dy = np.roll(relief, -1, axis=0) - np.roll(relief, 1, axis=0)
    dx = np.roll(relief, -1, axis=1) - np.roll(relief, 1, axis=1)
    normal = np.stack((-dx * 1.3, -dy * 1.3, np.ones_like(dx)), axis=2)
    normal = .5 + .5 * normal / np.linalg.norm(normal, axis=2)[:, :, None]
    factors = np.stack((np.ones_like(roughness) if contact is None else contact, roughness, metallic), axis=2)

    def image_node(suffix, pixels, colorspace):
        node = nodes.new('ShaderNodeTexImage')
        node.label = suffix
        node.image = packed_image(f'{label}_{suffix}', pixels, colorspace)
        return node.outputs['Color']

    links.new(image_node('paint', color, 'sRGB'), pbr.inputs['Base Color'])
    factors_out = image_node('surface', factors, 'Non-Color')
    split = nodes.new('ShaderNodeSeparateColor')
    links.new(factors_out, split.inputs[0])
    links.new(split.outputs['Green'], pbr.inputs['Roughness'])
    links.new(split.outputs['Blue'], pbr.inputs['Metallic'])
    bump = nodes.new('ShaderNodeNormalMap')
    bump.inputs['Strength'].default_value = .65
    links.new(image_node('relief', normal, 'Non-Color'), bump.inputs['Color'])
    links.new(bump.outputs['Normal'], pbr.inputs['Normal'])
    if contact is not None:
        # The exporter reads this input as the glTF ambient-occlusion channel.
        name = 'glTF Material Output'
        group = bpy.data.node_groups.get(name)
        if group is None:
            group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
            group.interface.new_socket(name='Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
        export = nodes.new('ShaderNodeGroup')
        export.node_tree = group
        links.new(factors_out, export.inputs['Occlusion'])


def texture_noise(shape, octaves, rng):
    y, x = np.indices(shape) / np.array(shape)[:, None, None]
    noise = np.zeros(shape)
    for width, height, amplitude in octaves:
        grid = rng.random((height, width))
        i, j = np.floor(x * width).astype(int), np.floor(y * height).astype(int)
        u, v = x * width - i, y * height - j
        u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
        next_i, next_j = (i + 1) % width, (j + 1) % height
        noise += amplitude * ((1 - v) * ((1 - u) * grid[j, i] + u * grid[j, next_i])
                              + v * ((1 - u) * grid[next_j, i] + u * grid[next_j, next_i]))
    return (noise - noise.min()) / (noise.max() - noise.min())


def bake_materials(graybox):
    rng = np.random.default_rng(505)
    n = 128
    y, x = np.indices((n, n)) / n
    noise = texture_noise((n, n), [(k, k, a) for k, a in ((2, 1), (4, .64), (8, .45), (16, .26), (32, .17))], rng)
    grit = rng.random((n, n))
    result = {}
    for label, (base, worn, rough, metallic) in PALETTE.items():
        mat = bpy.data.materials.new(label.capitalize())
        mat.use_nodes = True
        pbr = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        pbr.inputs['Roughness'].default_value = rough
        pbr.inputs['Metallic'].default_value = metallic
        mat.diffuse_color = (*srgb_to_linear(np.array(base)), 1)
        pbr.inputs['Base Color'].default_value = mat.diffuse_color
        result[label] = mat
        if graybox or label in ('ink', 'lettering'):
            continue
        oxide = np.clip((noise - .44) * .72, 0, .38) + .018 * (grit < .06)
        relief = .045 * noise + .010 * grit
        if label == 'bedding':
            oxide = .63 * ((np.floor(x * 8) + np.floor(y * 8)) % 2) + .18 * noise
            relief += .009 * (np.sin(tau * x * 32) + np.sin(tau * y * 32))
        if label in ('grating', 'tread', 'diesel_tread'):
            ridge = np.maximum(0, np.sin(tau * (x + y) * 8) * np.sin(tau * (x - y) * 8)) ** 5
            oxide += .21 * (1 - ridge)
            relief += .15 * ridge
            if label in ('tread', 'diesel_tread'):
                scuff = np.maximum(0, np.sin(tau * (x * 14 + y))) ** 12 * grit
                oxide *= 1 - .32 * scuff
                relief -= .018 * scuff
            if label == 'diesel_tread':
                oxide += .10 * (1 - ridge)
                relief += .11 * ridge
        if label in ('steel', 'brass', 'worn_steel'):
            scratch = .024 * (grit < .06) * np.maximum(0, np.sin(tau * (x * 2 + y * 24)))
            relief += scratch
        chips = (noise > .62) & (grit < .095) if label in ('sea_green', 'rib_enamel') else np.zeros_like(noise, dtype=bool)
        oxide += .52 * chips
        colors = np.array(base)[None, None, :] * (1 - oxide[:, :, None]) + np.array(worn)[None, None, :] * oxide[:, :, None]
        colors *= (.91 + .16 * grit)[:, :, None]
        roughness = np.clip(rough + .18 * (noise - .5), .08, 1)
        link_surface_images(mat, label, colors, roughness - .15 * chips, metallic + .35 * chips, relief - .025 * chips)
    return result


def worn_plate(label, contact, paint_line, streaks, chips, upper, lower, rng):
    grain = rng.random(contact.shape)
    weather = texture_noise(contact.shape, ((8, 6, 1), (19, 14, .58), (62, 44, .25), (150, 90, .09)), rng)
    opacity = np.clip(streaks * (.58 + weather) + .35 * (1 - contact), 0, .72)
    paint = (1 - paint_line[..., None]) * np.array(lower) + paint_line[..., None] * np.array(upper)
    paint *= (1 + .12 * (weather - .5) + .025 * (grain - .5))[..., None]
    color = paint * (1 - opacity[..., None]) + np.array((.20, .194, .166)) * opacity[..., None]
    chips = np.clip(chips * np.maximum(0, (weather - .40) * 3.8) * (grain > .58), 0, .85)
    color = color * (1 - chips[..., None]) + np.array((.42, .43, .38)) * chips[..., None]
    relief = .099 * (weather - .5) + .012 * (grain - .5) - .063 * chips
    roughness = np.clip(.62 + .17 * (weather - .5) - .21 * opacity - .35 * chips, .18, .82)
    metallic = .03 + .59 * chips
    mat = bpy.data.materials.new(label)
    mat.use_nodes = True
    mat.diffuse_color = (*srgb_to_linear(np.array(upper)), 1)
    link_surface_images(mat, label, color, roughness, metallic, relief, contact)
    return mat


def structure_materials(materials, room, floor, radius, ribs):
    rng = np.random.default_rng(4405)
    v, u = np.indices((576, 864)) / np.array((576, 864))[:, None, None]
    theta = tau * (v - .5)
    y, z = room.aft + room.length * u, radius * np.cos(theta)
    from_ribs = np.minimum.reduce([np.abs(y - station) for station in ribs])
    from_end = np.minimum(y - room.aft, room.bow - y)
    joints = np.minimum(np.abs(from_ribs - .061), np.maximum(0, from_end - .032))
    contact = 1 - .46 * np.exp(-joints / .034) - .14 * np.exp(-np.abs(z - floor) / .11)
    vertical = texture_noise(u.shape, ((80, 5, 1), (144, 10, .44), (235, 14, .24)), rng)
    drips = np.maximum(0, vertical - .47) * np.clip((floor + 2.16 - z) / 1.1, 0, 1)
    drips *= .29 + 1.15 * np.exp(-from_ribs / .12)
    drips += .32 * np.exp(-np.abs(z - (floor + .86)) / .044) * vertical
    plate_joint = np.minimum(np.abs(np.abs(theta) - .72), np.abs(np.abs(theta) - 1.91))
    drips += .21 * np.exp(-plate_joint / .0055) * (.5 + vertical)
    chips = .39 * np.exp(-joints / .019) + .23 * np.exp(-np.abs(z - floor) / .03)
    lights = np.clip((z - (floor + .84)) / .045, 0, 1)
    materials['hull_plate'] = worn_plate('Diesel shell', contact, lights, drips, chips,
                                          (.61, .62, .548), (.32, .36, .313), rng)

    z, x = (np.indices((512, 512)) / 512 - .5) * (2 * radius)
    door_z = floor + .75
    from_hatch = np.abs(np.hypot(x, z - door_z) - .526)
    from_stiffener = np.minimum(np.abs(np.abs(x) - .79), np.abs(np.abs(x) - 1.46))
    contact = 1 - .47 * np.exp(-from_hatch / .047) - .24 * np.exp(-from_stiffener / .032)
    vertical = texture_noise(x.shape, ((59, 5, 1), (110, 13, .31)), rng)
    drips = np.maximum(0, vertical - .48) * np.clip((floor + 1.95 - z) / .67, 0, 1)
    drips *= .41 + 1.0 * np.exp(-from_stiffener / .081)
    chips = .78 * np.exp(-from_hatch / .021) + .20 * np.exp(-from_stiffener / .027)
    lights = np.clip((z - floor - .90) / .035, 0, 1)
    materials['pressure_plate'] = worn_plate('Hatch bulkhead', contact, lights, drips, chips,
                                               (.58, .59, .526), (.31, .345, .297), rng)

    v, u = np.indices((448, 704)) / np.array((448, 704))[:, None, None]
    half_width = sqrt(radius * radius - floor * floor)
    x, y = (2 * v - 1) * half_width, room.aft + room.length * u
    contact = 1 - .25 * np.exp(-((np.abs(x) - .72) / .29) ** 2) - .13 * np.exp(-(half_width - np.abs(x)) / .22)
    stain = texture_noise(u.shape, ((26, 22, 1), (57, 46, .55), (111, 117, .29)), rng)
    oil = .68 * np.exp(-((x - 1.04) / .34) ** 2 - ((y - (room.bow - .46)) / .53) ** 2)
    oil += .44 * np.exp(-((x - .96) / .23) ** 2 - ((y - (room.bow - .98)) / .96) ** 2)
    oil *= np.clip((stain - .14) * 2.65, 0, 1)
    oil += .22 * np.exp(-((np.abs(x) - 1.02) / .36) ** 2) * (.25 + .75 * np.sin(y * 2.6) ** 2)
    chips = .30 * np.exp(-((np.abs(x) - .52) / .19) ** 2)
    materials['deck_plate'] = worn_plate('Diesel deck', contact, np.ones_like(x), oil, chips,
                                          (.44, .46, .409), (.36, .39, .35), rng)


def diesel_structure(materials, room, floor, radius):
    rib_count = round((room.length - .64) / .62)
    ribs = [room.aft + .42 + .62 * k for k in range(rib_count)]
    structure_materials(materials, room, floor, radius, ribs)
    a = Assembly('diesel_structure', materials)
    a.root['shell_segments'] = DIESEL_SHELL_SEGMENTS
    a.root['shell_radius_m'] = radius
    steps = DIESEL_SHELL_SEGMENTS
    angles = [-pi + tau * k / steps for k in range(steps + 1)]
    vertices = [(radius * sin(angle), station, radius * cos(angle))
                for station in (room.aft, room.bow) for angle in angles]
    faces = [(k, steps + 1 + k, steps + 2 + k, k + 1) for k in range(steps)]
    a.append('hull_plate', vertices, faces, range(steps))

    # Rolled section with a flange at the skin, web, and bevelled inward cap.
    profile = ((-.063, -.015), (-.059, .013), (-.028, .018), (-.024, .096),
               (-.015, .111), (.015, .111), (.024, .096), (.028, .018), (.059, .013), (.063, -.015))
    end = acos((floor - .028) / radius)
    for station in ribs:
        rim = [(-end + 2 * end * k / 23) for k in range(24)]
        a.loft('rib_enamel', [[((radius - rise) * sin(angle), station + walk, (radius - rise) * cos(angle))
                              for walk, rise in profile] for angle in rim], smooth=True)
        for sign in (-1, 1):
            side = sign * (radius - .05) * sin(end)
            a.box('iron', (side - sign * .033, station, floor + .006), (.195, .168, .030))
            a.box('rib_enamel', (side - sign * .031, station, floor + .046), (.11, .094, .075))
            for offset in (-.058, .058):
                a.cylinder('worn_steel', (side - sign * .063, station + offset, floor + .019),
                           (side - sign * .063, station + offset, floor + .032), .014, 6)
            if station > room.bow - 2.6 or station < room.aft + 1.5:
                for offset in (-.070, .070):
                    a.pipe('weld', [((radius - .014) * sin(sign * (end - k * .11)), station + offset,
                                     (radius - .014) * cos(end - k * .11)) for k in range(5)], .008, sides=4)

    # The plates sit above a continuous substrate so the seam interiors read dark.
    half_width = sqrt(radius * radius - floor * floor) - .014
    a.box('iron', (0, room.mid, floor - .055), (2 * half_width, room.length - .018, .052))
    panels = round(room.length / 1.08)
    pitch = room.length / panels
    for k in range(panels):
        station = room.aft + (k + .5) * pitch
        for sign in (-1, 1):
            width = half_width - .40
            center = sign * (half_width + .40) / 2
            a.box('deck_plate', (center, station, floor - .009), (width, pitch - .012, .020))
            if k in (0, 1, panels - 2, panels - 1):
                for offset in (-.41, .41):
                    for side in (.49, half_width - .11):
                        a.cylinder('steel', (sign * side, station + offset, floor + .001),
                                   (sign * side, station + offset, floor + .007), .016, 6)
        if k in (0, panels - 1):
            a.box('worn_steel', (0, station, floor - .004), (.80, pitch - .012, .017))

    def shell_uv(point, face):
        return (point.y - room.aft) / room.length, .5 + atan2(point.x, point.z) / tau

    def deck_uv(point, face):
        radius_at_deck = sqrt(radius * radius - floor * floor)
        return (point.y - room.aft) / room.length, .5 + point.x / (2 * radius_at_deck)

    a.finish({'hull_plate': shell_uv, 'deck_plate': deck_uv})
    return a


def deck(assembly, room, floor, width, tread='tread'):
    panels = max(1, round(room.length / .94))
    span = (room.length - .23) / panels
    tread_width = min(width * .59, .45)
    flank = (width - tread_width) / 2
    for k in range(panels):
        station = room.aft + .115 + (k + .5) * span
        assembly.box(tread, (0, station, floor + .012), (tread_width, span - .018, .023))
        for side in (-1, 1):
            shoulder = side * (tread_width + flank) / 2
            assembly.box('grating', (shoulder, station, floor + .012), (flank, span - .018, .023))
            assembly.box('iron', (side * (width / 2 + .024), station, floor + .023), (.045, span - .012, .042))
            for end in (-1, 1):
                y = station + end * (span / 2 - .055)
                x = side * (width / 2 - .045)
                assembly.cylinder('steel', (x, y, floor + .023), (x, y, floor + .026), .012, 6)


DECKHEAD_RUNS = {
    'control': ((-.73, .039, .23, 'enamel'), (-1.18, .046, .25, 'paint'),
                (.98, .034, .31, 'iron'), (1.27, .054, .22, 'enamel')),
    'diesel': ((-.68, .042, .30, 'enamel'), (-1.09, .062, .22, 'iron'),
               (.76, .036, .27, 'steel'), (1.29, .068, .18, 'enamel')),
    'motor': ((-.69, .029, .26, 'iron'), (-.91, .035, .35, 'black'),
              (-1.18, .029, .25, 'enamel'), (1.07, .051, .21, 'paint')),
    'aft_torpedo': ((-.67, .035, .23, 'paint'), (-1.14, .052, .23, 'enamel'),
                    (.78, .033, .26, 'iron'), (1.29, .038, .30, 'steel')),
}


def deckhead(a, room, radius):
    # The older colored through-runs remain available with the procedural fallback.
    # Staggered elbows and collars leave the central practicals in clear space.
    a.root['replaces_deckhead'] = True
    for index, (side, bore, drop, finish) in enumerate(DECKHEAD_RUNS[a.root.name]):
        inward = -.19 if side > 0 else .19
        height = (radius ** 2 - side ** 2) ** .5 - drop
        far, near = room.aft + .09, room.bow - .10
        turn = far + .62 + .33 * (index % 3)
        a.pipe(finish, [(side + inward, far, height - .11), (side + inward, turn - .21, height - .11),
                        (side, turn, height), (side, near, height)], bore, sides=10, bend=.11)
        for factor in (.38, .71, .92):
            y = room.aft + room.length * factor
            if y < turn + .18:
                continue
            a.cylinder('iron', (side, y - .046, height), (side, y + .046, height), bore * 1.31, 12)
            a.box('paint', (side, y, height + drop * .52), (bore * 1.42, .09, drop - .035))
            a.box('steel', (side, y, height + drop - .035), (.13, .12, .025))

    for fraction, side in ((.20, -1), (.52, 1), (.80, -1)):
        y = room.aft + room.length * fraction
        x = side * 1.31
        height = (radius ** 2 - x ** 2) ** .5 - .41
        a.rounded('paint', (x, y, height), (.23, .35, .17), .028)
        a.rounded('iron', (x, y, height - .091), (.20, .31, .020), .024)
        for stagger in (-.11, .11):
            a.cylinder('steel', (x + stagger * .63, y + stagger, height - .11),
                       (x + stagger * .63, y + stagger, height - .098), .015, 6)
        a.pipe('black', [(x, y + .15, height), (x, y + .29, height),
                         (x - side * .20, y + .43, height + .20)], .016, sides=8)

    # Narrow backing seams follow the visible part of the circular shell.
    for y in (room.aft + .145, room.bow - .145):
        surface = radius - .061
        for sign in (-1, 1):
            arc = [(sign * surface * sin(angle), y, surface * cos(angle))
                   for angle in (.30, .52, .70, .89, 1.08, 1.24, 1.41)]
            a.pipe('paint', arc, .026, sides=8, bend=.03)
            for x, _, z in arc[1:-1]:
                a.cylinder('iron', (x * .985, y, z * .985), (x * .972, y, z * .972), .021, 6)


def diesel_room(a, room, floor, graybox):
    # G516: two continuous engine banks, nine caps on each, narrow walkway.
    mid = room.aft + 4.62
    deck(a, room, floor, .80, tread='tread' if graybox else 'diesel_tread')
    for sign in (-1, 1):
        side = sign * 1.14
        a.rounded('iron', (side, mid, floor + .12), (1.17, 7.98, .24), .055)
        a.rounded('paint', (side, mid, floor + .58), (1.12, 7.76, .86), .075)
        a.rounded('enamel', (side, mid, floor + 1.15), (1.02, 7.57, .33), .085)
        for k in range(9):
            station = room.aft + 1.32 + .82 * k
            a.rounded('enamel', (side, station, floor + 1.47), (.91, .70, .46), .11, .024)
            a.rounded('paint', (side, station, floor + 1.77), (.72, .58, .23), .10, .023)
            if graybox:
                continue
            shaft = sign * .567
            y = station
            a.rounded('iron', (shaft, y, floor + .59), (.09, .60, .45), .043, .019)
            a.rounded('steel', (sign * .515, y, floor + .60), (.027, .51, .34), .011)
            a.rounded('paint', (sign * .492, y, floor + .60), (.025, .465, .302), .010)
            for offset in (-.196, .196):
                for h in (.49, .70):
                    a.cylinder('steel', (sign * .48, y + offset, floor + h),
                               (sign * .455, y + offset, floor + h), .024, 6)
            a.pipe('steel', [(sign * .64, y - .18, floor + 1.05), (sign * .64, y - .18, floor + 1.62),
                             (sign * .85, y - .18, floor + 1.85)], .020, sides=8)
            a.cylinder('brass', (sign * .64, y - .18, floor + 1.13), (sign * .64, y - .18, floor + 1.21), .033, 6)
            a.cylinder('steel', (side, y, floor + 1.87), (side, y, floor + 1.94), .045, 10)
            a.pipe('iron', [(side, y, floor + 1.39), (sign * 1.54, y, floor + 1.55),
                           (sign * 1.54, y, floor + 1.97)], .072, sides=10)
            a.box('steel', (sign * .54, y + .29, floor + 1.34), (.028, .11, .026))
        if graybox:
            continue
        near, far = mid + 3.94, mid - 3.76
        cabinet = near - .30
        a.rounded('cabinet', (side, cabinet, floor + .97), (.93, .21, 1.93), .064, .02)
        a.rounded('iron', (side, cabinet + .117, floor + .95), (.54, .08, 1.18), .035)
        a.cylinder('paint', (side, cabinet + .16, floor + .68), (side, cabinet + .28, floor + .68), .235, 18)
        a.ring('steel', (side, cabinet + .287, floor + .68), .20, .015)
        a.cylinder('steel', (sign * 1.54, far, floor + 1.91), (sign * 1.54, near - .16, floor + 1.91), .142, 16)
        for y in (far + .3, mid, near - .48):
            a.cylinder('iron', (sign * 1.54, y - .033, floor + 1.91), (sign * 1.54, y + .033, floor + 1.91), .177, 12)
        a.pipe('brass', [(sign * .66, far, floor + 1.15), (sign * .66, cabinet - .62, floor + 1.15),
                         (sign * .83, cabinet - .41, floor + 1.26), (sign * .89, cabinet - .41, floor + 1.43)], .030)
        riser = -.76 if sign < 0 else 1.29
        return_pipe = -.62 if sign < 0 else 1.43
        a.pipe('enamel', [(riser, cabinet - .17, floor + .44), (riser, cabinet - .17, floor + 2.18),
                          (sign * .98, cabinet - .30, floor + 2.56), (sign * .98, cabinet - .89, floor + 2.56)], .058)
        a.pipe('steel', [(return_pipe, cabinet - .29, floor + .62), (return_pipe, cabinet - .29, floor + 1.62),
                         (sign * .80, cabinet - .42, floor + 1.82)], .037)
        wheel(a, (sign * .89, near + .31, floor + .55), .14, axis='y')
        wheel(a, (sign * 1.38, near + .27, floor + 1.28), .16, axis='y')
        gauge(a, sign, 1.36, near + .35, floor + 1.85, .077, axis='y')
        # Service wheels and pressure dial sit on valve bodies fastened to the engine bed.
        for lateral, z, front in ((.89, .55, near + .31), (1.38, 1.28, near + .27), (1.36, 1.85, near + .35)):
            a.cylinder('steel', (sign * lateral, front - .16, floor + z),
                       (sign * lateral, front - .02, floor + z), .031, 10)
            a.cylinder('iron', (sign * lateral, front - .20, floor + z),
                       (sign * lateral, front - .11, floor + z), .066, 12)
            a.pipe('enamel', [(sign*lateral, front - .17, floor + z),
                              (sign*max(1.29, lateral), front - .23, floor + z),
                              (sign*max(1.29, lateral), cabinet - .24, floor + z - .17)], .029, sides=8)
    if graybox:
        return
    # A low overhead vessel frames the step into the aisle in G516.
    y = room.bow - 2.2
    a.cylinder('enamel', (.14, y, floor + 2.53), (.14, y, floor + 3.06), .39, 20)
    a.ring('iron', (.14, y, floor + 2.56), .378, .025, axis='z')
    a.pipe('iron', [(.44, y, floor + 2.82), (.77, y, floor + 2.82), (.77, y - .74, floor + 2.71)], .057)


def wheel(a, center, radius, axis='x', finish='black'):
    x, y, z = center
    a.ring(finish, center, radius, max(.011, radius * .105), axis, 16, 6)
    for k in range(3):
        angle = tau * k / 3 + .3
        u, v = radius * .91 * cos(angle), radius * .91 * sin(angle)
        point = (x, y + u, z + v) if axis == 'x' else (x + u, y, z + v)
        a.cylinder(finish, center, point, max(.008, radius * .068), 6)
    begin = (x - .026, y, z) if axis == 'x' else (x, y - .026, z)
    end = (x + .026, y, z) if axis == 'x' else (x, y + .026, z)
    a.cylinder('steel', begin, end, radius * .25, 10)


def gauge(a, sign, lateral, station, height, radius, axis='x'):
    side = sign * lateral
    if axis == 'x':
        point = lambda depth, u, v: (side - sign * depth, station + u, height + v)
    else:
        point = lambda depth, u, v: (side + u, station + depth, height + v)
    a.cylinder('steel', point(0, 0, 0), point(.035, 0, 0), radius, 16)
    a.cylinder('ink', point(.035, 0, 0), point(.037, 0, 0), radius * .84, 16)
    for k in range(9):
        angle = pi * (.14 + k * .095)
        u, v = cos(angle), sin(angle)
        a.cylinder('lettering', point(.039, radius * .58 * u, radius * .58 * v),
                   point(.039, radius * .75 * u, radius * .75 * v), max(.0016, radius * .025), 4)
    a.cylinder('lettering', point(.040, 0, 0), point(.040, -.23 * radius, .61 * radius), radius * .048, 4)


def control_room(a, room, floor, hatch):
    # G437 and G435: worn castings, stacked valve wheels, elbows and sight glass.
    deck(a, room, floor, 1.18)
    for s in (-1, 1):
        a.cylinder('iron', (s * .214, hatch, floor), (s * .214, hatch, floor + 3.37), .032, 8)
        for h in (.12, .98, 1.9, 2.87):
            a.box('steel', (s * .21, hatch, floor + h), (.09, .133, .076))
    for z in np.arange(floor + .30, 2.0, .30):
        a.cylinder('steel', (-.211, hatch, z), (.211, hatch, z), .025, 10)
        a.box('iron', (0, hatch, z + .019), (.34, .031, .014))
    a.ring('iron', (0, hatch, 2.10), .343, .044, axis='z')
    for offset, radius in ((-1.20, .112), (-2.00, .089)):
        station = room.mid + offset
        a.cylinder('steel', (0, station, floor + .09), (0, station, 2.07), radius, 16)
        for height in (.25, .76, 1.72, 2.65):
            a.cylinder('iron', (0, station, floor + height - .035), (0, station, floor + height + .035), radius + .044, 12)
    # Gauge boards and dive wheels remain close to the live instrument placards.
    seat = room.mid + 1.20
    a.rounded('enamel', (1.81, seat, floor + 1.44), (.30, 1.30, 1.49), .094)
    for offset in (-.36, .36):
        y = seat + offset
        a.rounded('paint', (1.64, y, floor + .42), (.50, .29, .82), .056)
        wheel(a, (1.36, y, floor + .93), .25)
        a.pipe('enamel', [(1.65, y, floor + .34), (1.79, y, floor + .34), (1.79, y, floor + 2.12)], .038)
    for offset, height in ((.60, 1.79), (-.58, 1.79), (.59, 2.07), (-.56, 2.07)):
        gauge(a, 1, 1.64, seat + offset, floor + height, .073)
    # Port manifold sits outside the old hit volumes and leaves the ladder landing open.
    y0 = room.aft + .8
    a.rounded('enamel', (-1.82, y0 + 1.1, floor + 1.33), (.24, 2.3, 1.67), .082)
    for k in range(4):
        station = y0 + k * .46
        a.pipe('cabinet', [(-1.68, station, floor + .37), (-1.68, station, floor + 1.75),
                           (-1.44, station + .12, floor + 2.08), (-1.44, station + .30, floor + 2.08)], .052)
        for j in range(3):
            z = floor + .79 + j * .35 + .05 * (k % 2)
            a.cylinder('paint', (-1.69, station, z), (-1.48, station, z), .075, 10)
            wheel(a, (-1.43, station, z), .115 if j else .144, finish='iron' if j else 'black')
        gauge(a, -1, 1.60, station + .15, floor + 1.97, .080)
    for h in (.51, 2.29):
        a.pipe('paint', [(-1.62, y0 - .11, floor + h - .2), (-1.62, y0 - .11, floor + h),
                         (-1.62, y0 + 2.48, floor + h)], .067)
    for offset in (.10, 1.07, 2.04):
        y = y0 + offset
        a.pipe('enamel', [(-1.64, y, floor + .51), (-1.37, y, floor + .51),
                          (-1.37, y + .23, floor + .74), (-1.47, y + .23, floor + 1.05)], .035)
        a.cylinder('steel', (-1.63,y,floor+.51), (-1.54,y,floor+.51), .064, 8)
    a.rounded('cabinet', (-1.42, y0 + 2.10, floor + 1.60), (.075, .115, .83), .027)
    for z in np.arange(floor + 1.23, floor + 1.97, .055):
        a.box('ink', (-1.376, y0 + 2.10, z), (.008, .07, .008))
    for s in (-1, 1):
        for o in (0, .16, .32):
            a.pipe('enamel', [(s * (1.24 + o), room.aft + .23, 1.27), (s * (1.24 + o), room.aft + 1.1, 1.27),
                              (s * (.90 + o), room.aft + 1.48, 1.48), (s * (.90 + o), room.bow - .29, 1.48)], .032 + o * .025)


def motor_room(a, room, floor):
    # G523: longitudinal switchboard, cream housings, recessed black faces and a low handrail.
    deck(a, room, floor, .86)
    for sign in (-1, 1):
        side = sign * 1.14
        near, far = room.mid + 1.34, room.mid - 1.42
        a.rounded('iron', (side, room.mid, floor + .07), (1.06, 3.14, .14), .06)
        a.cylinder('paint', (side, far, floor + .52), (side, near, floor + .52), .48, 18)
        for j in range(12):
            station = far + .25 + j * .20
            a.ring('iron', (side, station, floor + .52), .47, .023, 'y', 16, 5)
        for sign_y, y in ((-1, far), (1, near)):
            a.cylinder('iron', (side, y, floor + .52), (side, y + sign_y * .16, floor + .52), .445, 16, .355)
            a.cylinder('steel', (side, y + sign_y * .16, floor + .52),
                       (side, y + sign_y * .28, floor + .52), .158, 14)
        a.rounded('paint', (side, room.mid + .49, floor + 1.04), (.46, .46, .26), .069)
        a.pipe('black', [(side, room.mid + .49, floor + 1.18), (side, room.mid + .49, floor + 1.35),
                         (sign * 1.77, room.mid + .49, floor + 1.50)], .051)
    for side_sign, reach in ((-1, 4.25), (1, 2.48)):
        main = room.mid + (.12 if side_sign < 0 else -.52)
        a.rounded('cabinet', (side_sign * 1.71, main, floor + 1.73), (.28, reach, 1.37), .074, .018)
        rows = 6 if side_sign < 0 else 4
        for k in range(rows):
            station = main + (k - (rows - 1) / 2) * (reach / rows)
            a.box('iron', (side_sign * 1.565, station + reach / rows * .48, floor + 1.71), (.012, .012, 1.18))
            for h in (1.81, 2.04):
                gauge(a, side_sign, 1.56, station, floor + h, .088 if h == 2.04 else .064)
            a.cylinder('enamel', (side_sign * 1.51, station - .22, floor + 1.35),
                       (side_sign * 1.51, station + .22, floor + 1.35), .17, 14)
            a.cylinder('black', (side_sign * 1.31, station - .16, floor + 1.33),
                       (side_sign * 1.31, station + .16, floor + 1.33), .022, 8)
            a.box('ink', (side_sign * 1.561, station, floor + 2.22), (.011, .21, .036))
            for offset in (-.23, .23):
                a.cylinder('steel', (side_sign * 1.567, station + offset, floor + 1.22),
                           (side_sign * 1.538, station + offset, floor + 1.22), .024, 8)
            a.pipe('black', [(side_sign * 1.61, station - .15, floor + 1.14),
                             (side_sign * 1.61, station - .15, floor + .96),
                             (side_sign * 1.75, station - .15, floor + .85)], .024, sides=8)
            for j in range(6):
                a.box('iron', (side_sign * 1.557, station, floor + 1.47 + j * .033), (.01, .115, .010))
        x = side_sign * .62
        a.pipe('steel', [(side_sign * .93, main - reach / 2, floor + .69), (x, main - reach / 2, floor + .69),
                         (x, main + reach / 2, floor + .69), (side_sign * .93, main + reach / 2, floor + .69)], .030)
        for f in (-.43, -.19, .19, .43):
            a.cylinder('steel', (x, main + reach * f, floor + .69), (side_sign * .70, main + reach * f, floor + .12), .023, 8)


def aft_passage(a, room, floor):
    # G522: stowed bedding, chains and dense overhead wiring enclose the aisle.
    deck(a, room, floor, 1.20)
    for sign in (-1, 1):
        a.cylinder('paint', (sign * 1.24, room.aft + 1.40, floor + .44),
                   (sign * 1.24, room.bow - .55, floor + .44), .35, 16)
        for station in (room.aft + 1.55, room.mid, room.bow - 1.18):
            a.ring('iron', (sign * 1.24, station, floor + .44), .349, .027)
        for tier in (1.03, 1.86):
            for k in range(3):
                station = room.bow - 1.48 - 2.08 * k
                side = sign * 1.13
                a.rounded('iron', (side, station, floor + tier), (.78, 1.91, .072), .035)
                a.rounded('bedding', (side, station, floor + tier + .092), (.69, 1.78, .148), .10, .031)
                a.rounded('blanket', (side, station - .17, floor + tier + .155), (.71, 1.20, .074), .10, .024)
                a.rounded('cabinet', (side, station + .63, floor + tier + .21), (.48, .31, .147), .086, .027)
                a.box('steel', (sign * .74, station, floor + tier + .101), (.028, 1.86, .11))
                a.box('iron', (side, station + .70, floor + tier - .14), (.70, .048, .25))
                a.rounded('blanket', (sign * .96, station - .51, floor + tier + .175),
                          (.32, .45, .081), .065, .021)
                for offset in (-.55, .43):
                    a.box('black', (side, station + offset, floor + tier + .195), (.63, .052, .015))
                if tier < 1.5:
                    for j in range(12):
                        axis = 'x' if j % 2 else 'y'
                        a.ring('steel', (sign * .79, station + .69, floor + tier + .22 + j * .053), .032, .007, axis, 8, 4)
        for k in range(5):
            lateral = sign * (.79 + k * .082)
            a.cylinder('black' if k % 2 else 'steel', (lateral, room.aft + .22, 1.62),
                       (lateral, room.bow - .24, 1.62 + k * .006), .022, 8)
        a.box('iron', (sign * .93, room.mid, 1.563), (.43, room.length - .37, .055))
        side = sign * .89
        a.cylinder('iron', (side, room.aft + .10, floor + .75),(side, room.aft + 1.30, floor + .75), .355, 18)
        a.cylinder('steel', (side, room.aft + 1.30, floor + .75),(side, room.aft + 1.43, floor + .75), .366, 18)
        a.ring('iron', (side, room.aft + 1.44, floor + .75), .295, .032)
        wheel(a, (side, room.aft + 1.53, floor + .75), .167, 'y')


def hatch_band(a, finish, station, height, face, profile, steps):
    vertices = [(r * cos(tau * k / steps), station + face * depth, height + r * sin(tau * k / steps))
                for r, depth in profile for k in range(steps)]
    quads = [(i * steps + k, (i + 1) * steps + k, (i + 1) * steps + (k + 1) % steps, i * steps + (k + 1) % steps)
             for i in range(len(profile) - 1) for k in range(steps)]
    if face < 0:
        quads = [q[::-1] for q in quads]
    a.append(finish, vertices, quads, range(len(quads)))


def bulkhead_face(materials, name, room, station, face, hull_radius, r, floor, height):
    a = Assembly(name, materials)
    steps = 48
    arc = [(cos(tau * k / steps), sin(tau * k / steps)) for k in range(steps)]
    surface = station + face * .024
    vertices = [(r * x, surface, height + r * z) for x, z in arc]
    for x, z in arc:
        distance = -height * z + sqrt(hull_radius ** 2 - (height * x) ** 2)
        vertices.append((distance * x, surface, height + distance * z))
    quads = [(k, (k + 1) % steps, steps + (k + 1) % steps, steps + k) for k in range(steps)]
    a.append('pressure_plate', vertices, quads if face > 0 else [q[::-1] for q in quads])

    # The rolled hatch throat terminates at the rated clear opening.
    hatch_band(a, 'rib_enamel', station, height, face,
               [(r + .144, .023), (r + .137, .036), (r + .106, .042), (r + .088, .077),
                (r + .062, .098), (r + .018, .102)], steps)
    hatch_band(a, 'worn_steel', station, height, face,
               [(r + .018, .102), (r + .006, .097), (r, .085), (r, 0)], steps)
    a.ring('rubber', (0, station + face * .099, height), r + .022, .009, 'y', 32, 5)
    for k in range(12):
        angle = (k + .5) * tau / 12
        x, z = (r + .114) * cos(angle), height + (r + .114) * sin(angle)
        a.cylinder('iron', (x, station + face * .039, z), (x, station + face * .057, z), .021, 8)
        a.cylinder('worn_steel', (x, station + face * .054, z), (x, station + face * .066, z), .013, 6)

    # Formed stiffeners and their feet run clear of the hatch and its nameplate.
    for sign in (-1, 1):
        for side in (.79, 1.46):
            x = sign * side
            top = sqrt(hull_radius ** 2 - x ** 2) - .088
            bottom = floor + .053
            a.box('rib_enamel', (x, station + face * .040, (top + bottom) / 2), (.080, .038, top - bottom))
            a.box('rib_enamel', (x, station + face * .069, (top + bottom) / 2), (.045, .042, top - bottom - .050))
            a.box('iron', (x, station + face * .057, floor + .049), (.158, .100, .085))
            for offset in (-.051, .051):
                a.cylinder('worn_steel', (x + offset, station + face * .082, floor + .07),
                           (x + offset, station + face * .111, floor + .07), .013, 6)

    # A central tread bridges the clearance at floor level and has exposed wear at its ends.
    tread_depth = .208 if room == 'diesel' else .168
    a.box('iron', (0, station + face * tread_depth / 2, floor + .006), (.71, tread_depth, .029))
    a.box('worn_steel', (0, station + face * .103, floor + .020), (.66, .157 if room == 'diesel' else .116, .013))
    for x in (-.285, .285):
        a.cylinder('steel', (x, station + face * .111, floor + .025),
                   (x, station + face * .111, floor + .031), .014, 6)

    if face < 0:
        # Both hinges align with the game's animated leaf pivot.
        for offset in (-.208, .208):
            z = height + offset
            a.box('iron', (r + .128, station - .060, z), (.180, .078, .108))
            a.cylinder('iron', (r + .06, station - .085, z - .065), (r + .06, station - .085, z + .065), .047, 12)
            a.cylinder('worn_steel', (r + .06, station - .085, z + .062), (r + .06, station - .085, z + .090), .029, 10)

    a.finish({'pressure_plate': lambda point, face: (.5 + point.x / (2 * hull_radius),
                                                    .5 + point.z / (2 * hull_radius))}, wet_room=room)
    return a


def hatch_hardware(materials, hull, rooms, systems, floor):
    names = []
    for fwd, aft in (('control', 'diesel'), ('diesel', 'motor')):
        door = next(door for door in systems['doors'] if door['between'] == [fwd, aft])
        station, r = rooms[fwd].aft, door['diameter_m'] / 2
        height = floor + door['sill_m'] + r
        pair = f'{fwd}_{aft}'
        for face, room in ((1, fwd), (-1, aft)):
            name = f'{pair}_bulkhead_{room}'
            bulkhead_face(materials, name, room, station, face, hull['radius_m'], r, floor, height)
            names.append(name)

        leaf = Assembly(f'{pair}_leaf', materials)
        leaf.cylinder('iron', (0, -.037, 0), (0, .037, 0), r * .991, 40)
        leaf.finish()
        for face, room in ((1, fwd), (-1, aft)):
            side = Assembly(f'{pair}_leaf_{room}', materials)
            side.cylinder('rib_enamel', (0, face * .037, 0), (0, face * .047, 0), r * .966, 36)
            side.cylinder('rib_enamel', (0, face * .047, 0), (0, face * .066, 0), r * .76, 36, r * .72)
            side.ring('iron', (0, face * .048, 0), r * .86, .015, 'y', 28, 6)
            side.cylinder('iron', (0, face * .057, 0), (0, face * .112, 0), .094, 16, .071)
            wheel(side, (0, face * .136, 0), r * .34, axis='y', finish='red')
            side.cylinder('brass', (0, face * .155, 0), (0, face * .177, 0), .027, 10)
            for k in range(6):
                angle = (k + .5) * tau / 6
                x, z = r * .79 * cos(angle), r * .79 * sin(angle)
                side.box('iron', (x, face * .062, z), (.048, .045, .063))
                side.cylinder('worn_steel', (x, face * .072, z), (x, face * .090, z), .014, 6)
            for obj in side.finish(wet_room=room):
                obj.parent = leaf.root
            bpy.data.objects.remove(side.root, do_unlink=True)
        names.append(leaf.root.name)
        # Save the edit scene with the hatch stored beside the opening.
        leaf.root.location = (r * 2 + .12, station - .17, height)
        leaf.root.rotation_euler.z = pi
    return names


def cooling_valve(materials, systems, floor, deck_height):
    valve = next(v for v in systems['valves'] if v['id'] == 'v_cooling_hull')
    strainer = next(o for o in systems['sources'] if o['id'] == 'sea_strainer')
    x, y, z = valve['side_m'], valve['x_m'], floor + valve['z_m'] - deck_height
    body = Assembly('cooling_valve_body', materials)
    body.cylinder('worn_steel', (x, y, z - .089), (x, y, z + .023), .025, 12)
    body.cylinder('brass', (x, y, z - .136), (x, y, z - .060), .064, 8, .042)
    body.cylinder('iron', (x, y, z - .194), (x, y, z - .127), .093, 16)
    body.rounded('sea_green', (x, y, z - .234), (.25, .22, .176), .078, .018)

    high, low = z - .23, floor + .09
    to_x, to_y = strainer['side_m'] + .23, strainer['x_m']
    body.pipe('sea_green', [(x + .07, y, high), (x + .56, y, high), (x + .60, y, low),
                            (x + .48, to_y, low), (to_x, to_y, low)], .052, sides=12, bend=.135)
    for side, start, direction in ((x + .19, y, 1), (to_x + .10, to_y, -1)):
        h = high if direction > 0 else low
        body.cylinder('iron', (side - .026, start, h), (side + .026, start, h), .086, 16)
        body.cylinder('rib_enamel', (side - .012, start, h), (side + .012, start, h), .092, 16)
        for k in range(6):
            angle = (k + .5) * tau / 6
            dy, dz = .073 * cos(angle), .073 * sin(angle)
            body.cylinder('worn_steel', (side - .031, start + dy, h + dz), (side + .031, start + dy, h + dz), .011, 6)
    body.pipe('sea_green', [(x, y, high - .05), (x, y, floor + .114),
                            (x + .14, y, floor + .104)], .054, sides=10, bend=.09)
    body.rounded('iron', (x + .16, y, floor + .016), (.32, .24, .048), .03)
    body.box('iron', (x + .185, y, floor + .056), (.08, .095, .083))
    body.ring('worn_steel', (x + .16, y, floor + .105), .056, .010, 'x', 16, 5)
    for side in (-1, 1):
        body.cylinder('worn_steel', (x + .27, y + side * .086, floor + .03),
                      (x + .27, y + side * .086, floor + .049), .016, 6)
    # Back the retained in-game lettering and carry it past the wheel on a bent bracket.
    body.box('iron', (x + .023, y, z + .28), (.024, .338, .112))
    body.box('worn_steel', (x + .123, y - .118, z + .259), (.192, .030, .022))
    body.box('iron', (x + .212, y - .118, z + .017), (.023, .030, .490))
    body.box('iron', (x + .145, y - .085, z - .226), (.156, .098, .026))
    body.finish()

    handwheel = Assembly('cooling_valve_wheel', materials)
    # Local -Y becomes +Z in glTF, matching the runtime spin axis before the valve holder rotates it upward.
    handwheel.ring('sea_green', (0, 0, 0), .171, .019, 'y', 32, 8)
    handwheel.ring('worn_steel', (0, -.012, 0), .170, .004, 'y', 32, 5)
    for k in range(4):
        angle = (k + .5) * tau / 4
        handwheel.cylinder('sea_green', (.034 * cos(angle), 0, .034 * sin(angle)),
                           (.167 * cos(angle), .001, .167 * sin(angle)), .021, 9, .012)
    handwheel.cylinder('sea_green', (0, .025, 0), (0, -.025, 0), .051, 16, .042)
    handwheel.cylinder('worn_steel', (0, -.024, 0), (0, -.040, 0), .025, 6)
    handwheel.finish()
    handwheel.root.location = (x, y, z)
    handwheel.root.rotation_euler.x = -pi / 2
    return (body.root.name, handwheel.root.name)


def hardware(materials, floor, deck_height, systems):
    strainer = next(o for o in systems['sources'] if o['id'] == 'sea_strainer')
    strainer_side, strainer_station = strainer['side_m'], strainer['x_m']
    body = Assembly('strainer_body', materials)
    body.cylinder('iron', (0, 0, -.26), (0, 0, .05), .19, 18)
    body.cylinder('brass', (0, 0, -.23), (0, 0, .21), .159, 18)
    body.cylinder('iron', (0, 0, .06), (0, 0, .23), .110, 18)
    body.ring('steel', (0, 0, .265), .137, .025, 'z')
    body.ring('brass', (0, 0, .236), .150, .032, 'z')
    body.cylinder('brass', (.11, 0, .08), (.25, 0, .08), .065, 12)
    body.rounded('iron', (0, 0, .014), (.415, .45, .036), .055)
    body.cylinder('rib_enamel', (0, 0, .027), (0, 0, .067), .162, 16)
    body.ring('worn_steel', (0, 0, .073), .164, .012, 'z', 24, 5)
    for x in (-.154, .154):
        for y in (-.169, .169):
            body.cylinder('worn_steel', (x, y, .028), (x, y, .046), .018, 6)
    for k in range(8):
        t = tau * k / 8
        x, y = .161 * cos(t), .161 * sin(t)
        body.cylinder('steel', (x, y, .206), (x, y, .237), .018, 6)
    body.finish()
    body.root.location = (strainer_side, strainer_station, floor)
    cover = Assembly('strainer_cover', materials)
    # Griffin MSI object 54.93.2, 14.5 in diameter and 3 in high overall.
    cover.cylinder('steel', (0, 0, -.023), (0, 0, .012), .154, 28)
    cover.ring('iron', (0, 0, -.009), .14, .013, 'z')
    for k in range(4):
        angle = (k + .5) * pi / 2
        outward = Vector((cos(angle), sin(angle), 0))
        crosswise = Vector((-sin(angle), cos(angle), 0))
        for offset in (-.019, .019):
            center = outward * .149 + crosswise * offset
            cover.box('steel', (center.x, center.y, -.003), (.064, .020, .032), angle)
    cover.pipe('steel', [(0, -.08, .012), (0, -.064, .029), (0, -.032, .04), (0, .032, .04),
                         (0, .064, .029), (0, .08, .012)], .013, bend=.018)
    cover.finish()
    cover.root.location = (strainer_side - .35, strainer_station - .45, floor + .03)
    lever = Assembly('diesel_lever', materials)
    lever.cylinder('steel', (0, 0, .025), (0, 0, .31), .026, 10)
    lever.cylinder('red', (0, 0, .277), (0, 0, .366), .044, 12, .033)
    lever.cylinder('iron', (0, 0, .015), (0, 0, .045), .049, 12)
    lever.finish()
    stop = next(v for v in systems['valves'] if v['id'] == 'v_stop_port')
    lever.root.location = (stop['side_m'], stop['x_m'], floor + stop['z_m'] - deck_height)
    lever.root.rotation_euler.y = 1.05
    starboard = next(v for v in systems['valves'] if v['id'] == 'v_stop_stbd')
    return lever.root, starboard


def export_file(path):
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', export_yup=True,
                              export_apply=True, export_extras=True, export_cameras=False, export_lights=False)


def verify_fit(assembly, room, floor):
    for object in assembly.root.children:
        for vertex in object.data.vertices:
            x, y, z = vertex.co
            if not room.aft - .02 <= y <= room.bow + .02:
                raise ValueError(f'{object.name} crosses a bulkhead at {vertex.co[:]}')
            # Props stay outside the path. In control, the ladder and periscope
            # landings are an established part of the walking space.
            if assembly.root.name in ('diesel', 'motor') and floor + .14 < z < floor + 2.16 and abs(x) < room.walk + .016:
                raise ValueError(f'{object.name} obstructs the aisle at {vertex.co[:]}')


def verify_export(assemblies):
    names = [obj.name for obj in assemblies]
    triangle_total = 0
    for name in names:
        root = bpy.data.objects[name]
        for ob in root.children:
            if ob.type != 'MESH':
                continue
            mesh = ob.data
            mesh.calc_loop_triangles()
            triangle_total += len(mesh.loop_triangles)
            if not mesh.uv_layers.active or not mesh.materials:
                raise ValueError(f'{ob.name} lost UVs or materials on import')
    if triangle_total > 125_000:
        raise ValueError(f'Interior export exceeds its triangle budget ({triangle_total})')
    print(f'Round-trip checked {len(names)} assemblies and {triangle_total:,} triangles')


def preview_copy(root, starboard, floor, original_floor_height):
    clone = root.copy()
    clone.name = 'Starboard stop lever (edit preview)'
    clone.location = (starboard['side_m'], starboard['x_m'], floor + starboard['z_m'] - original_floor_height)
    bpy.context.scene.collection.objects.link(clone)
    for mesh in root.children:
        component = mesh.copy()
        component.parent = clone
        bpy.context.scene.collection.objects.link(component)


def round_trip(path, names, rooms, floor, hatch, render):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    verify_export([bpy.data.objects[name] for name in names])
    if not render:
        return
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 900, 540, 100
    scene.render.image_settings.file_format = 'JPEG'
    scene.world = bpy.data.worlds.new('Interior review ambient')
    scene.world.use_nodes = True
    ambient = next(node for node in scene.world.node_tree.nodes if node.type == 'BACKGROUND')
    ambient.inputs['Color'].default_value = (.35, .39, .43, 1)
    ambient.inputs['Strength'].default_value = .18
    view_data = bpy.data.cameras.new('Interior review camera')
    view_data.lens = 24
    view = bpy.data.objects.new(view_data.name, view_data)
    scene.collection.objects.link(view)
    scene.camera = view
    target = ROOT / 'docs/visuals/interior'
    target.mkdir(parents=True, exist_ok=True)
    for name in ROOM_IDS:
        room = rooms[name]
        side = -.18 if name in ('motor', 'control') else .02
        station = min(room.bow - .9, hatch + 1.6) if name == 'control' else room.bow - .78
        view.location = (side, station, floor + 1.60)
        look = Vector((-.60 if name in ('control', 'motor') else .08, room.mid - .85, floor + 1.10))
        view.rotation_euler = (look - view.location).to_track_quat('-Z', 'Y').to_euler()
        for index, fraction in enumerate((.18, .54, .85)):
            data = bpy.data.lights.new(f'Review {index}', 'AREA')
            data.energy = (135, 105, 165)[index]
            data.size = .75
            light = bpy.data.objects.new(data.name, data)
            light.location = ((-.30, .73, -.25)[index], room.aft + room.length * fraction, floor + 2.68)
            scene.collection.objects.link(light)
        scene.render.filepath = str(target / f'blender-{name}.jpg')
        bpy.ops.render.render(write_still=True)
        for light in list(bpy.data.objects):
            if light.type == 'LIGHT':
                bpy.data.objects.remove(light, do_unlink=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--graybox', action='store_true')
    checks = parser.add_mutually_exclusive_group()
    checks.add_argument('--review', action='store_true')
    checks.add_argument('--verify', action='store_true', help='Re-import and check the GLB without rendering previews')
    options = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    hull, rooms, systems = read_layout()
    floor = hull['floor_height_m'] - hull['radius_m']
    materials = bake_materials(options.graybox)
    diesel = Assembly('diesel', materials)
    diesel_room(diesel, rooms['diesel'], floor, options.graybox)
    if not options.graybox:
        deckhead(diesel, rooms['diesel'], hull['radius_m'])
    diesel.finish()
    verify_fit(diesel, rooms['diesel'], floor)
    if options.graybox:
        export_file(ROOT / 'art/u505_interior_graybox.glb')
        return
    structure = diesel_structure(materials, rooms['diesel'], floor, hull['radius_m'])
    for label, populate in (('control', control_room), ('motor', motor_room), ('aft_torpedo', aft_passage)):
        room = Assembly(label, materials)
        if label == 'control':
            populate(room, rooms[label], floor, hull['hatch']['x_m'])
        else:
            populate(room, rooms[label], floor)
        deckhead(room, rooms[label], hull['radius_m'])
        room.finish()
        verify_fit(room, rooms[label], floor)
    lever, starboard = hardware(materials, floor, hull['floor_height_m'], systems)
    hardware_names = hatch_hardware(materials, hull, rooms, systems, floor)
    hardware_names.extend(cooling_valve(materials, systems, floor, hull['floor_height_m']))
    names = (*ROOM_IDS, 'strainer_body', 'strainer_cover', 'diesel_lever', structure.root.name, *hardware_names)
    asset = ROOT / 'art/u505_interior.glb'
    verify_export([bpy.data.objects[name] for name in names])
    export_file(asset)
    preview_copy(lever, starboard, floor, hull['floor_height_m'])
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'art/u505_interior.blend'))
    if options.review or options.verify:
        round_trip(asset, names, rooms, floor, hull['hatch']['x_m'], options.review)


if __name__ == '__main__':
    main()
