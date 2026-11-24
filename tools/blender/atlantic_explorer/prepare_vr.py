"""Build VR-ready Atlantic Explorer assets from the original Sketchfab FBX.

The source FBX and textures remain untouched. The script cleans the imported
scene, separates failure-relevant parts, adds XR/failure anchors and collision
proxies, limits texture resolution, saves a Blender working file, and exports
plain and Draco-compressed GLBs.

Run from the repository root:
  blender --background --python tools/blender/atlantic_explorer/prepare_vr.py
"""

from __future__ import annotations

import json
import math
from array import array
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
ASSET_DIR = ROOT / "art" / "atlantic_explorer"
SOURCE = ASSET_DIR / "source" / "AtlanticExplorer.fbx"
TEXTURES = ASSET_DIR / "source" / "textures"
BLEND = ASSET_DIR / "atlantic_explorer_vr.blend"
GLB = ASSET_DIR / "atlantic_explorer_vr.glb"
DRACO_GLB = ASSET_DIR / "atlantic_explorer_vr_draco.glb"
COLLISION_GLB = ASSET_DIR / "atlantic_explorer_collision.glb"
MANIFEST = ASSET_DIR / "vr_manifest.json"
PREVIEW = ASSET_DIR / "atlantic_explorer_vr_preview.png"


CORE_NAMES = {
    "InnerHull.001": "PressureHull_InteriorShell",
    "Interior.001": "Cabin_Interior",
    "LowerHull.001": "Hull_Lower",
    "UpperHull.001": "Hull_Upper",
    "OutsideDetails02.001": "Exterior_Structure",
}


def mesh_objects() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def select_only(objects: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]


def triangle_count(obj: bpy.types.Object) -> int:
    return sum(max(1, len(poly.vertices) - 2) for poly in obj.data.polygons)


def world_center(obj: bpy.types.Object) -> Vector:
    first = obj.matrix_world @ Vector(obj.bound_box[0])
    opposite = obj.matrix_world @ Vector(obj.bound_box[6])
    return first.lerp(opposite, 0.5)


def separate_loose(obj: bpy.types.Object) -> list[bpy.types.Object]:
    before = set(bpy.context.scene.objects)
    select_only([obj])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    return [obj] + list(set(bpy.context.scene.objects) - before)


def join_as(objects: list[bpy.types.Object], name: str) -> bpy.types.Object | None:
    if not objects:
        return None
    select_only(objects)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    result = objects[0]
    result.name = name
    result.data.name = f"{name}_Mesh"
    return result


def find_mesh(prefix: str) -> bpy.types.Object:
    obj = next((candidate for candidate in mesh_objects() if candidate.name.startswith(prefix)), None)
    if not obj:
        raise RuntimeError(f"missing imported mesh {prefix}")
    return obj


def repair_texture_paths() -> None:
    """Point the FBX material images at the preserved source texture folder."""
    for image in list(bpy.data.images):
        filename = Path(bpy.path.abspath(image.filepath)).name
        replacement = TEXTURES / filename
        if replacement.exists():
            image.filepath = str(replacement)
            try:
                image.reload()
            except RuntimeError:
                pass


def deduplicate_images() -> None:
    canonical: dict[str, bpy.types.Image] = {}
    for image in list(bpy.data.images):
        key = Path(bpy.path.abspath(image.filepath)).name.lower()
        if not key:
            continue
        if key not in canonical:
            canonical[key] = image
            image.name = Path(key).name
            continue
        replacement = canonical[key]
        for material in bpy.data.materials:
            if not material.use_nodes:
                continue
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image == image:
                    node.image = replacement
        bpy.data.images.remove(image)


def optimize_images() -> list[dict[str, object]]:
    report = []
    for image in bpy.data.images:
        before = [int(image.size[0]), int(image.size[1])]
        if max(before) > 2048:
            factor = 2048 / max(before)
            image.scale(max(1, round(before[0] * factor)), max(1, round(before[1] * factor)))
        # Pack the in-memory resized pixels so GLB export cannot silently read
        # the untouched 4K source file again.
        if image.source == "FILE":
            try:
                image.pack()
            except RuntimeError:
                pass
        report.append(
            {
                "name": image.name,
                "source_size": before,
                "vr_size": [int(image.size[0]), int(image.size[1])],
            }
        )
    return sorted(report, key=lambda item: item["name"])


def image_by_filename(filename: str) -> bpy.types.Image:
    filename = filename.lower()
    image = next(
        (candidate for candidate in bpy.data.images if Path(bpy.path.abspath(candidate.filepath)).name.lower() == filename),
        None,
    )
    if not image:
        raise RuntimeError(f"missing texture image {filename}")
    return image


def combined_transparency() -> bpy.types.Image:
    color = image_by_filename("TransparentItemsColour.png")
    alpha = image_by_filename("TransparentItemsAlpha.png")
    width, height = int(color.size[0]), int(color.size[1])
    if list(alpha.size) != [width, height]:
        alpha.scale(width, height)
    color_pixels = array("f", [0.0]) * (width * height * 4)
    alpha_pixels = array("f", [0.0]) * (width * height * 4)
    color.pixels.foreach_get(color_pixels)
    alpha.pixels.foreach_get(alpha_pixels)
    for offset in range(0, len(color_pixels), 4):
        color_pixels[offset + 3] = alpha_pixels[offset]
    combined = bpy.data.images.new("TransparentItemsRGBA.png", width=width, height=height, alpha=True)
    combined.pixels.foreach_set(color_pixels)
    combined.pack()
    return combined


def connect_image(
    nodes: bpy.types.Nodes,
    links: bpy.types.NodeLinks,
    image: bpy.types.Image,
    target: bpy.types.NodeSocket,
    *,
    non_color: bool = False,
) -> bpy.types.Node:
    node = nodes.new("ShaderNodeTexImage")
    node.image = image
    node.label = image.name
    node.interpolation = "Linear"
    if non_color:
        image.colorspace_settings.name = "Non-Color"
    links.new(node.outputs["Color"], target)
    return node


def rebuild_material(
    material_name: str,
    prefix: str,
    *,
    emission: bool = False,
    transparent: bool = False,
) -> None:
    material = bpy.data.materials.get(material_name)
    if not material:
        raise RuntimeError(f"missing imported material {material_name}")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.45
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    if transparent:
        base = combined_transparency()
        color_node = connect_image(nodes, links, base, bsdf.inputs["Base Color"])
        links.new(color_node.outputs["Alpha"], bsdf.inputs["Alpha"])
        connect_image(
            nodes,
            links,
            image_by_filename(f"{prefix}Roughness.png"),
            bsdf.inputs["Roughness"],
            non_color=True,
        )
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Transmission Weight"].default_value = 0.12
        bsdf.inputs["IOR"].default_value = 1.49
        material.diffuse_color = (0.16, 0.23, 0.28, 0.22)
        material.surface_render_method = "DITHERED"
        material.use_transparency_overlap = False
        material.show_transparent_back = True
        return

    connect_image(nodes, links, image_by_filename(f"{prefix}Colour.png"), bsdf.inputs["Base Color"])
    if emission:
        connect_image(nodes, links, image_by_filename(f"{prefix}Emission.png"), bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 5.0
        bsdf.inputs["Roughness"].default_value = 0.18
        return

    connect_image(
        nodes,
        links,
        image_by_filename(f"{prefix}Metallic.png"),
        bsdf.inputs["Metallic"],
        non_color=True,
    )
    connect_image(
        nodes,
        links,
        image_by_filename(f"{prefix}Roughness.png"),
        bsdf.inputs["Roughness"],
        non_color=True,
    )
    normal_tex = nodes.new("ShaderNodeTexImage")
    normal_tex.image = image_by_filename(f"{prefix}Normal.png")
    normal_tex.image.colorspace_settings.name = "Non-Color"
    normal_tex.interpolation = "Linear"
    normal = nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = 0.75
    links.new(normal_tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])


def rebuild_materials() -> None:
    rebuild_material("InsideHull", "InnerHull")
    rebuild_material("Interior02", "Interior")
    rebuild_material("Lights", "Lights", emission=True)
    rebuild_material("LowerHull", "LowerHull")
    rebuild_material("OutsideDetails01", "OutsideDetails01")
    rebuild_material("OutsideDetails02", "OutsideDetails02")
    rebuild_material("TransparentItems", "TransparentItems", transparent=True)
    rebuild_material("UpperHull.001", "UpperHull")


def apply_transforms_and_names() -> None:
    for old, new in CORE_NAMES.items():
        obj = bpy.data.objects.get(old)
        if obj:
            obj.name = new
            obj.data.name = f"{new}_Mesh"
    select_only(mesh_objects())
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def triangulate(objects: list[bpy.types.Object]) -> None:
    for obj in objects:
        if obj.type != "MESH":
            continue
        select_only([obj])
        modifier = obj.modifiers.new(name="VR_Triangulate", type="TRIANGULATE")
        modifier.keep_custom_normals = True
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def prepare_viewports() -> list[bpy.types.Object]:
    source = find_mesh("Transparency")
    pieces = separate_loose(source)
    pilot: list[bpy.types.Object] = []
    passenger: list[bpy.types.Object] = []
    remainder: list[bpy.types.Object] = []
    for piece in pieces:
        center = world_center(piece)
        if triangle_count(piece) >= 500 and piece.dimensions.x > 1.4:
            (pilot if center.y > 0 else passenger).append(piece)
        else:
            remainder.append(piece)
    output = [
        join_as(pilot, "Viewport_Pilot"),
        join_as(passenger, "Viewport_Passenger"),
        join_as(remainder, "Transparent_Details"),
    ]
    for obj in output[:2]:
        if obj:
            obj["failure_system"] = "viewport"
            obj["xr_interactable"] = True
            obj["material_behavior"] = "swap intact/crazed/cracked shaders at runtime"
    return [obj for obj in output if obj]


def prepare_lights() -> list[bpy.types.Object]:
    source = find_mesh("Lights")
    pieces = separate_loose(source)
    front: list[bpy.types.Object] = []
    rear: list[bpy.types.Object] = []
    cabin: list[bpy.types.Object] = []
    for piece in pieces:
        center = world_center(piece)
        if center.y > 2.5:
            front.append(piece)
        elif center.y < -2.5:
            rear.append(piece)
        else:
            cabin.append(piece)
    output = [
        join_as(front, "Lights_PilotEnd"),
        join_as(rear, "Lights_PassengerEnd"),
        join_as(cabin, "Lights_Cabin"),
    ]
    for obj in output:
        if obj:
            obj["failure_system"] = "lighting"
    return [obj for obj in output if obj]


def thruster_name(center: Vector) -> str:
    side = "Starboard" if center.x > 0 else "Port"
    end = "PilotEnd" if center.y > 0 else "PassengerEnd"
    plane = "Vertical" if center.z > 0.2 else "Horizontal"
    return f"Thruster_{end}_{side}_{plane}"


def prepare_thrusters() -> list[bpy.types.Object]:
    source = find_mesh("OutsideDetails01")
    pieces = separate_loose(source)
    thrusters: list[bpy.types.Object] = []
    remainder: list[bpy.types.Object] = []
    for piece in pieces:
        dims = sorted(float(value) for value in piece.dimensions)
        tris = triangle_count(piece)
        if 1250 <= tris <= 1450 and dims[0] > 0.34 and dims[2] < 0.55:
            piece.name = thruster_name(world_center(piece))
            piece.data.name = f"{piece.name}_Mesh"
            piece["failure_system"] = "thruster"
            piece["xr_interactable"] = True
            thrusters.append(piece)
        else:
            remainder.append(piece)
    details = join_as(remainder, "Exterior_Details")
    if details:
        details["failure_system"] = "structure"
    if len(thrusters) != 8:
        raise RuntimeError(f"expected 8 separable thrusters, found {len(thrusters)}")
    return thrusters + ([details] if details else [])


def add_empty(name: str, location: tuple[float, float, float], **metadata: object) -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.12
    empty.location = location
    for key, value in metadata.items():
        empty[key] = value
    return empty


def create_anchors() -> list[bpy.types.Object]:
    common = {"units": "metres", "forward": "+Y in Blender; -Z after glTF export"}
    definitions = [
        ("XR_ORIGIN", (0.0, 0.0, -0.45), {"role": "tracking_origin"}),
        ("XR_HEAD_PILOT", (0.0, 1.22, 0.72), {"role": "seated_head"}),
        ("XR_HANDS_PILOT", (0.0, 1.76, 0.13), {"role": "control_reach"}),
        ("XR_HEAD_PASSENGER_PORT", (-0.36, -1.22, 0.72), {"role": "seated_head"}),
        ("XR_HEAD_PASSENGER_STARBOARD", (0.36, -1.22, 0.72), {"role": "seated_head"}),
        ("ANCHOR_VIEWPORT_PILOT", (0.0, 2.73, 0.0), {"failure_system": "viewport"}),
        ("ANCHOR_VIEWPORT_PASSENGER", (0.0, -2.73, 0.0), {"failure_system": "viewport"}),
        ("ANCHOR_PRESSURE_HULL", (0.0, 0.0, 0.25), {"failure_system": "pressure_hull"}),
        ("ANCHOR_BATTERY", (0.0, 0.0, -0.72), {"failure_system": "battery"}),
        ("ANCHOR_LIFE_SUPPORT", (-0.75, -0.1, 0.45), {"failure_system": "life_support"}),
        ("ANCHOR_AUDIO_HULL", (0.0, 0.0, 1.1), {"role": "structure_audio"}),
        ("ANCHOR_LEAK_PILOT", (0.0, 2.62, -0.12), {"failure_system": "leak"}),
        ("ANCHOR_LEAK_PASSENGER", (0.0, -2.62, -0.12), {"failure_system": "leak"}),
    ]
    return [add_empty(name, location, **common, **metadata) for name, location, metadata in definitions]


def add_cube(name: str, location: tuple[float, float, float], scale: tuple[float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = f"{name}_Mesh"
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj["collision_proxy"] = True
    return obj


def create_collisions() -> tuple[bpy.types.Collection, list[bpy.types.Object]]:
    collection = bpy.data.collections.new("VR_Collision")
    bpy.context.scene.collection.children.link(collection)
    objects: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=(0.0, 0.0, 0.12))
    exterior = bpy.context.object
    exterior.name = "COL_ExteriorHull"
    exterior.data.name = "COL_ExteriorHull_Mesh"
    exterior.scale = (1.52, 3.25, 1.45)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    exterior["collision_proxy"] = True
    objects.append(exterior)

    objects.extend(
        [
            add_cube("COL_CabinFloor", (0.0, 0.0, -0.48), (1.75, 4.45, 0.08)),
            add_cube("COL_CabinCeiling", (0.0, 0.0, 1.38), (1.75, 4.45, 0.08)),
            add_cube("COL_CabinPort", (-0.98, 0.0, 0.42), (0.08, 4.45, 1.75)),
            add_cube("COL_CabinStarboard", (0.98, 0.0, 0.42), (0.08, 4.45, 1.75)),
            add_cube("COL_CabinPilotEnd", (0.0, 2.23, 0.42), (1.75, 0.08, 1.75)),
            add_cube("COL_CabinPassengerEnd", (0.0, -2.23, 0.42), (1.75, 0.08, 1.75)),
        ]
    )

    for obj in objects:
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)
    return collection, objects


def render_objects(collisions: list[bpy.types.Object]) -> list[bpy.types.Object]:
    collision_set = set(collisions)
    return [obj for obj in bpy.context.scene.objects if obj not in collision_set and obj.type in {"MESH", "EMPTY"}]


def export_glb(path: Path, objects: list[bpy.types.Object], *, draco: bool = False) -> None:
    select_only(objects)
    options = dict(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_cameras=False,
        export_lights=False,
        export_extras=True,
        export_apply=True,
        export_yup=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_jpeg_quality=85,
    )
    if draco:
        options.update(
            export_draco_mesh_compression_enable=True,
            export_draco_mesh_compression_level=6,
            export_draco_position_quantization=14,
            export_draco_normal_quantization=10,
            export_draco_texcoord_quantization=12,
        )
    bpy.ops.export_scene.gltf(**options)


def point_camera(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(renderables: list[bpy.types.Object]) -> None:
    bpy.ops.object.camera_add(location=(7.7, 9.2, 4.8))
    camera = bpy.context.object
    camera.name = "PREVIEW_Camera"
    camera.data.lens = 58
    point_camera(camera, Vector((0.0, 0.1, 0.2)))
    bpy.context.scene.camera = camera

    for name, location, energy, size in [
        ("PREVIEW_Key", (4.5, 3.0, 7.0), 1500, 5.0),
        ("PREVIEW_Fill", (-5.0, 1.0, 2.0), 900, 4.0),
        ("PREVIEW_Rim", (0.0, -6.0, 4.0), 1200, 3.0),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        point_camera(light, Vector((0.0, 0.0, 0.2)))

    world = bpy.context.scene.world or bpy.data.worlds.new("AbyssalWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.002, 0.008, 0.018, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.18

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEW)
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    for obj in renderables:
        obj.hide_render = False
    bpy.ops.render.render(write_still=True)


def bounds(objects: list[bpy.types.Object]) -> tuple[list[float], list[float]]:
    points = [obj.matrix_world @ Vector(corner) for obj in objects if obj.type == "MESH" for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) for i in range(3)]
    maximum = [max(point[i] for point in points) for i in range(3)]
    return minimum, maximum


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"missing source FBX: {SOURCE}")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SOURCE), use_image_search=True)
    repair_texture_paths()
    deduplicate_images()
    image_report = optimize_images()
    rebuild_materials()
    apply_transforms_and_names()

    prepare_viewports()
    prepare_lights()
    prepared = prepare_thrusters()
    anchors = create_anchors()
    collision_collection, collisions = create_collisions()
    renderables = render_objects(collisions)
    triangulate([obj for obj in renderables if obj.type == "MESH"])

    for obj in renderables:
        if obj.type == "MESH":
            obj["units"] = "metres"
            obj["asset"] = "Atlantic Explorer"
    minimum, maximum = bounds(renderables)

    export_glb(GLB, renderables)
    export_glb(DRACO_GLB, renderables, draco=True)
    export_glb(COLLISION_GLB, collisions)

    collision_collection.hide_viewport = True
    collision_collection.hide_render = True
    render_preview(renderables)

    manifest = {
        "asset": "Atlantic Explorer",
        "coordinate_system": {
            "source": "Blender Z-up, +Y pilot-forward",
            "gltf": "metres, Y-up, -Z pilot-forward",
        },
        "bounds_blender": {
            "min": [round(value, 5) for value in minimum],
            "max": [round(value, 5) for value in maximum],
            "dimensions": [round(maximum[i] - minimum[i], 5) for i in range(3)],
        },
        "render": {
            "mesh_nodes": len([obj for obj in renderables if obj.type == "MESH"]),
            "triangles": sum(triangle_count(obj) for obj in renderables if obj.type == "MESH"),
            "anchors": [obj.name for obj in anchors],
            "failure_meshes": sorted(
                obj.name for obj in renderables if obj.type == "MESH" and "failure_system" in obj
            ),
        },
        "collision": {
            "mesh_nodes": len(collisions),
            "nodes": [obj.name for obj in collisions],
        },
        "textures": image_report,
        "outputs": [GLB.name, DRACO_GLB.name, COLLISION_GLB.name, BLEND.name, PREVIEW.name],
        "notes": [
            "Viewport meshes are separated for runtime intact/crazed/cracked material swaps.",
            "Eight thrusters are separated and named for independent damage and repair state.",
            "Collision geometry is exported separately and is hidden in the Blender working file.",
            "XR head/hand anchors are starting points and require in-headset comfort validation.",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))


if __name__ == "__main__":
    main()
