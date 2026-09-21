"""Generate the generic EasyAIoT industrial park in Blender.

Usage:
  blender --background --python blender/generate_park.py

Outputs are written next to this script as industrial_park.blend and
industrial_park.glb. Every sensor marker carries a stable `device_id` custom
property so runtime telemetry can bind to the exported asset.
"""

from pathlib import Path
import bpy
import math

ROOT = Path(__file__).resolve().parent

DEVICES = [
    ("AIR-01", "一号空压机", (-20, -6, 3.2), "online"),
    ("CNC-07", "七号加工中心", (-9, -4, 2.6), "online"),
    ("PMP-03", "循环水泵P03", (8, 1, 2.6), "warning"),
    ("TRF-01", "园区主变压器", (26, -12, 3.5), "online"),
    ("ENV-04", "东区环境站", (30, 10, 4.5), "online"),
    ("CAM-12", "南门摄像机", (-2, 22, 5.5), "offline"),
    ("PV-02", "二号光伏阵列", (9, -17, 6.4), "online"),
    ("GAS-06", "六号燃气探头", (18, 8, 4.2), "online"),
]


def material(name, color, metallic=0.05, roughness=0.7):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.metallic = metallic
    mat.roughness = roughness
    return mat


MATS = {
    "ground": material("MAT_Ground", (0.035, 0.09, 0.07)),
    "road": material("MAT_Road", (0.08, 0.12, 0.11)),
    "building": material("MAT_Building", (0.28, 0.38, 0.35), 0.18, 0.58),
    "roof": material("MAT_Roof", (0.08, 0.16, 0.14), 0.35, 0.44),
    "glass": material("MAT_Glass", (0.08, 0.43, 0.40), 0.35, 0.25),
    "tank": material("MAT_Tank", (0.40, 0.50, 0.47), 0.6, 0.35),
    "pipe": material("MAT_Pipe", (0.72, 0.45, 0.12), 0.55, 0.35),
    "solar": material("MAT_Solar", (0.015, 0.22, 0.25), 0.65, 0.22),
    "online": material("MAT_Status_Online", (0.08, 0.90, 0.52), 0.1, 0.3),
    "warning": material("MAT_Status_Warning", (1.0, 0.55, 0.08), 0.1, 0.3),
    "offline": material("MAT_Status_Offline", (1.0, 0.12, 0.16), 0.1, 0.3),
}


def cube(name, location, scale, mat, collection=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (scale[0] / 2, scale[1] / 2, scale[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if collection:
        for current in list(obj.users_collection):
            current.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def add_building(name, x, y, width, depth, height):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    cube(f"{name}_Body", (x, y, height / 2), (width, depth, height), MATS["building"], collection)
    cube(f"{name}_Roof", (x, y, height + .18), (width + .7, depth + .7, .35), MATS["roof"], collection)
    for px in range(math.ceil(-width / 2 + 2), math.floor(width / 2 - 1), 3):
        cube(f"{name}_Window_{px}", (x + px, y + depth / 2 + .07, height * .58), (1.65, .12, 1.1), MATS["glass"], collection)


def add_tank(x, y):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=2.1, depth=6, location=(x, y, 3))
    bpy.context.object.data.materials.append(MATS["tank"])
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(x, y, 5.9), scale=(2.1, 2.1, 1.0))
    bpy.context.object.data.materials.append(MATS["tank"])


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    cube("Park_Ground", (0, 0, -.25), (76, 58, .5), MATS["ground"])
    cube("Road_Main_NS", (0, 0, .02), (10, 58, .08), MATS["road"])
    cube("Road_Main_EW", (0, 15, .03), (76, 8, .08), MATS["road"])
    add_building("智能制造中心", -19, -8, 26, 17, 8)
    add_building("精密加工中心", 13, -11, 17, 20, 6)
    add_building("仓储物流中心", 22, 8, 20, 10, 5)
    add_building("综合管理中心", -20, 8, 17, 10, 7)

    for x in (8, 14, 20):
        add_tank(x, 5)
    for x in range(7, 20, 4):
        for y in range(-18, -4, 4):
            panel = cube(f"Solar_{x}_{y}", (x, y, 6.65), (3.2, 2.2, .15), MATS["solar"])
            panel.rotation_euler[0] = math.radians(-7)

    for device_id, display_name, (x, y, z), status in DEVICES:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=.34, location=(x, y, z))
        marker = bpy.context.object
        marker.name = f"DEVICE_{device_id}"
        marker.data.materials.append(MATS[status])
        marker["device_id"] = device_id
        marker["display_name"] = display_name
        marker["status"] = status

    world = bpy.context.scene.world
    world.color = (0.015, 0.035, 0.028)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "METERS"
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "industrial_park.blend"))
    bpy.ops.export_scene.gltf(
        filepath=str(ROOT / "industrial_park.glb"),
        export_format="GLB",
        export_extras=True,
        export_apply=True,
    )


if __name__ == "__main__":
    main()
