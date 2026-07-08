from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLENDER_DIR = ROOT / "outputs" / "blender"

TEMPLATE = r'''# Blender Python helper for ICH Astra motion preview
# Run inside Blender: Text Editor → Run Script

import bpy
from pathlib import Path

SESSION_ID = "{session_id}"
BVH_PATH = Path(r"{bvh_path}")

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

if BVH_PATH.exists():
    bpy.ops.import_anim.bvh(filepath=str(BVH_PATH), axis_forward='-Z', axis_up='Y')
    print(f"Imported BVH: {{BVH_PATH}}")
else:
    print(f"BVH file not found: {{BVH_PATH}}")

# Add simple camera and light
bpy.ops.object.light_add(type='AREA', location=(0, -3, 4))
light = bpy.context.object
light.name = "ICH Preview Area Light"
light.data.energy = 450
light.data.size = 5

bpy.ops.object.camera_add(location=(0, -5, 2.2), rotation=(1.2, 0, 0))
bpy.context.scene.camera = bpy.context.object

print(f"ICH Astra motion preview ready for session: {{SESSION_ID}}")
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Blender helper script for a motion session.")
    parser.add_argument("--session_id", required=True)
    args = parser.parse_args()

    BLENDER_DIR.mkdir(parents=True, exist_ok=True)
    bvh_path = (ROOT / "outputs" / "bvh" / f"{args.session_id}.bvh").resolve()
    out_path = BLENDER_DIR / f"import_{args.session_id}.py"
    out_path.write_text(TEMPLATE.format(session_id=args.session_id, bvh_path=str(bvh_path)), encoding="utf-8")
    print(f"Blender helper script written: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
