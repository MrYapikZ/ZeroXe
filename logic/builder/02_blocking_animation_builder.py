import sys
import json
from pathlib import Path
from textwrap import dedent
from string import Template

class BlockingAnimationBuilder:
    def extract_data(self, current_department, filepath):
        # Entry data
        # region Example Data
        # current_department = {
        #     "Layout": {
        #         "code": "lay",
        #         "based": "shot",
        #         "base_path": "/mnt/M/02_production/02_layout/",
        #         "source": "init",
        #         "presets": {
        #             "playblast": {
        #                 "path": "/mnt/M/00_tools/01_preset_script/mdt_preset_playblast.py"
        #             }
        #         },
        #     }
        # }
        # shot_data = {
        #     "id": "9745ed0d-8b43-4b61-88df-8e1171cdd1a3",
        #     "name": "sh0010",
        #     "code": None,
        #     "description": None,
        #     "shotgun_id": None,
        #     "canceled": False,
        #     "nb_frames": 84,
        #     "nb_entities_out": 0,
        #     "is_casting_standby": False,
        #     "is_shared": False,
        #     "status": "running",
        #     "project_id": "0f029a6d-603e-4d6d-8217-902e2e32f274",
        #     "entity_type_id": "1c2d916d-5e51-4cdb-83fc-147ec263c359",
        #     "parent_id": "a53271a6-3d0c-491e-8aed-a9d2e150046b",
        #     "source_id": None,
        #     "preview_file_id": "865ce228-567e-4c03-ad48-34eb1ccfa019",
        #     "data": {
        #         "fps": 24,
        #         "set": "s-sekolah",
        #         "char": "c-baha",
        #         "code": "",
        #         "prop": "p-dagangan,p-leupeut_single",
        #         "ms_lit": "LIT_s-ext_sekolah_PAGI",
        #         "ms_comp": "COMP_s-ext_sekolah_PAGI",
        #         "frame_in": 101,
        #         "frame_out": 184,
        #         "resolution": "2560x1080",
        #         "max_retakes": None,
        #     },
        #     "ready_for": None,
        #     "created_by": "03f81449-39fc-4b58-b0e6-d034f741bb1f",
        #     "created_at": "2026-02-24T04:14:42",
        #     "updated_at": "2026-04-15T09:10:49",
        #     "type": "Shot",
        # }
        # filepath = {"final": "", "version": "", "source": ""}
        # endregion
        
        # Create parent folder
        Path(filepath['version']).parent.mkdir(parents=True, exist_ok=True)
        
        # Copy from source
        start_script = f"import bpy; import os; bpy.ops.wm.open_mainfile(filepath='{filepath["source"]}'); bpy.ops.wm.save_as_mainfile(filepath='{filepath["version"]}');"
        end_script = f"bpy.ops.wm.save_as_mainfile(filepath='{filepath["final"]}'); bpy.ops.wm.save_as_mainfile(filepath='{filepath["version"]}')"
        
        # Apply preset
        dept_data = next(iter(current_department.values()))
        preset_name = "playblast"
        preset_path = dept_data.get("presets", {}).get(preset_name, {}).get("path")
        if preset_path:
            with open(preset_path, "r") as f:
                preset_code = f.read()
                create_script = start_script + "\n\n" + preset_code + "\n\n" + end_script
        else:
            create_script = end_script + "\n\n" + end_script
        
        return create_script
    
if __name__ == "__main__":
    # 1. Capture arguments from subprocess
    # We expect JSON strings for the dictionaries
    try:
        shot_info = json.loads(sys.argv[1])
        current_dept = json.loads(sys.argv[2])
        # asset_dept = json.loads(sys.argv[3])
        # mastershot_dept = json.loads(sys.argv[4])
        file_paths = json.loads(sys.argv[-1])

        # 2. Run the logic
        builder = BlockingAnimationBuilder()
        result = builder.extract_data(current_dept, file_paths)

        # 3. Print the result so the subprocess can "catch" it
        print(result)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)