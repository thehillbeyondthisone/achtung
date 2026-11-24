"""Inspect the Atlantic Explorer FBX from a headless Blender process.

Usage:
  blender --background --python inspect.py -- input.fbx report.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def argv() -> list[str]:
    try:
        return sys.argv[sys.argv.index("--") + 1 :]
    except ValueError:
        return []


def world_bounds(obj: bpy.types.Object) -> tuple[list[float], list[float]]:
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return (
        [min(p[i] for p in points) for i in range(3)],
        [max(p[i] for p in points) for i in range(3)],
    )


def loose_components(obj: bpy.types.Object) -> list[dict[str, object]]:
    """Return useful loose-part bounds without changing the imported source."""
    mesh = obj.data
    neighbours: list[list[int]] = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbours[a].append(b)
        neighbours[b].append(a)

    unseen = set(range(len(mesh.vertices)))
    components: list[dict[str, object]] = []
    while unseen:
        seed = unseen.pop()
        stack = [seed]
        vertices = [seed]
        while stack:
            current = stack.pop()
            for adjacent in neighbours[current]:
                if adjacent in unseen:
                    unseen.remove(adjacent)
                    stack.append(adjacent)
                    vertices.append(adjacent)

        members = set(vertices)
        polygons = [poly for poly in mesh.polygons if poly.vertices[0] in members]
        if len(polygons) < 3:
            continue
        points = [obj.matrix_world @ mesh.vertices[index].co for index in vertices]
        bounds_min = [min(point[i] for point in points) for i in range(3)]
        bounds_max = [max(point[i] for point in points) for i in range(3)]
        components.append(
            {
                "vertices": len(vertices),
                "polygons": len(polygons),
                "triangles": sum(max(1, len(poly.vertices) - 2) for poly in polygons),
                "bounds_min": [round(float(value), 5) for value in bounds_min],
                "bounds_max": [round(float(value), 5) for value in bounds_max],
                "center": [round(float((bounds_min[i] + bounds_max[i]) / 2), 5) for i in range(3)],
                "dimensions": [round(float(bounds_max[i] - bounds_min[i]), 5) for i in range(3)],
            }
        )
    return sorted(components, key=lambda component: component["triangles"], reverse=True)


def main() -> None:
    args = argv()
    if len(args) != 2:
        raise SystemExit("expected input FBX and output JSON")

    source = Path(args[0]).resolve()
    destination = Path(args[1]).resolve()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_image_search=True)

    report: dict[str, object] = {
        "source": str(source),
        "blender": bpy.app.version_string,
        "objects": [],
        "materials": [],
        "images": [],
    }

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in meshes:
        bounds_min, bounds_max = world_bounds(obj)
        report["objects"].append(
            {
                "name": obj.name,
                "vertices": len(obj.data.vertices),
                "edges": len(obj.data.edges),
                "polygons": len(obj.data.polygons),
                "triangles": sum(max(1, len(poly.vertices) - 2) for poly in obj.data.polygons),
                "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
                "uv_layers": [layer.name for layer in obj.data.uv_layers],
                "dimensions": [round(float(v), 5) for v in obj.dimensions],
                "bounds_min": [round(float(v), 5) for v in bounds_min],
                "bounds_max": [round(float(v), 5) for v in bounds_max],
                "scale": [round(float(v), 5) for v in obj.scale],
                "rotation": [round(float(v), 5) for v in obj.rotation_euler],
                "loose_components": loose_components(obj),
            }
        )

    for material in bpy.data.materials:
        report["materials"].append(
            {
                "name": material.name,
                "use_nodes": material.use_nodes,
                "blend_method": getattr(material, "surface_render_method", None),
                "users": material.users,
            }
        )

    for image in bpy.data.images:
        report["images"].append(
            {
                "name": image.name,
                "filepath": image.filepath,
                "size": list(image.size),
                "source": image.source,
            }
        )

    if meshes:
        overall_min = [min(world_bounds(obj)[0][i] for obj in meshes) for i in range(3)]
        overall_max = [max(world_bounds(obj)[1][i] for obj in meshes) for i in range(3)]
        report["summary"] = {
            "mesh_objects": len(meshes),
            "vertices": sum(len(obj.data.vertices) for obj in meshes),
            "polygons": sum(len(obj.data.polygons) for obj in meshes),
            "triangles": sum(
                max(1, len(poly.vertices) - 2)
                for obj in meshes
                for poly in obj.data.polygons
            ),
            "bounds_min": [round(float(v), 5) for v in overall_min],
            "bounds_max": [round(float(v), 5) for v in overall_max],
            "dimensions": [round(float(overall_max[i] - overall_min[i]), 5) for i in range(3)],
        }

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
