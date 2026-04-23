import sys
import json
from pathlib import Path
from textwrap import dedent
from string import Template


class CompositingBuilder:
    def extract_data(
        self,
        shot_data,
        current_department,
        asset_department,
        mastershots_data,
        addons_data,
        filepath,
    ):
        # Entry data
        # region Example Data
        # asset_department = {
        #     "Asset": {
        #         "code": "",
        #         "based": "asset",
        #         "asset_type": {
        #             "CHAR": {
        #                 "code": "chr",
        #                 "prefix": "c-",
        #                 "suffix": "",
        #                 "base_path": "/mnt/M/02_production/01_asset/01_char/",
        #             },
        #             "PROPS": {
        #                 "code": "prp",
        #                 "prefix": "p-",
        #                 "suffix": "",
        #                 "base_path": "/mnt/M/02_production/01_asset/02_prop/",
        #             },
        #             "SET": {
        #                 "code": "set",
        #                 "prefix": "s-",
        #                 "suffix": "",
        #                 "base_path": "/mnt/M/02_production/01_asset/03_set/",
        #             },
        #             "VEHICLE": {
        #                 "code": "vhc",
        #                 "prefix": "v-",
        #                 "suffix": "",
        #                 "base_path": "/mnt/M/02_production/01_asset/04_vehicle/",
        #             },
        #         },
        #     }
        # }
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
        # mastershots_data = {
        #     "mastershots": {
        #         "mastershot_compositing": {
        #             "code": "ms-comp",
        #             "base_path": "/mnt/M/03_post_production/02_compositing/00_preset_comp/",
        #         },
        #         "mastershot_lit": {
        #             "code": "ms-lit",
        #             "base_path": "/mnt/M/03_post_production/01_lighting/00_preset_lighting/",
        #         },
        #     },
        # }
        # filepath = {"final": "", "version": "", "source": ""}
        # endregion

        # Get mastershot base path
        mastershot_name = "mastershot_compositing"
        current_mastershot = mastershots_data.get("mastershots", {}).get(
            mastershot_name, {}
        )

        # Get comp mastershot path
        comp_mastershot_name = shot_data.get("data", {}).get("ms_comp", "")
        comp_mastershot_file = (
            Path(current_mastershot.get("base_path", ""))
            / comp_mastershot_name
            / f"{comp_mastershot_name}.blend"
        )

        # Get preset
        dept_data = next(iter(current_department.values()))
        preset_name = "preset"
        preset_path = dept_data.get("presets", {}).get(preset_name, {}).get("path")

        # Construct shot metadata
        frame_in = int(shot_data.get("data", {}).get("frame_in", "0"))
        frame_out = int(shot_data.get("data", {}).get("frame_out", "0"))
        fps = int(shot_data.get("data", {}).get("fps", "24"))
        res_str = str(shot_data.get("data", {}).get("resolution", "1920x1080"))
        resolution = (
            [int(res.strip()) for res in res_str.split("x")] if "x" in res_str else []
        )
        setting_data = {
            "frame_in": frame_in,
            "frame_out": frame_out,
            "fps": fps,
            "resolution": resolution,
            "script_path": preset_path,
        }

        comp_script = self.script_builder(
            filepath=filepath["final"],
            version_path=filepath["version"],
            master_file=str(comp_mastershot_file),
            setting_data=setting_data,
        )
        
        return comp_script

    def script_builder(
        self, filepath: str, version_path: str, master_file: str, setting_data: dict
    ):
        tpl = Template(
            dedent(
                """
import bpy
from pathlib import Path

bpy.ops.wm.open_mainfile(filepath="$FILEPATH")

bpy.ops.wm.save_as_mainfile(filepath="$OUTPUT_PATH")
"""
            )
        )
        end_script = Template(
            dedent(
                """
# Save the modified Blender file
bpy.ops.wm.save_as_mainfile(filepath="$OUTPUT_PATH")
bpy.ops.wm.save_as_mainfile(filepath="$OUTPUT_PATH_PROGRESS")
print("File saved as: $OUTPUT_PATH")

# Quit Blender
bpy.ops.wm.quit_blender()
"""
            )
        )
        script = tpl.substitute(
            FILEPATH=master_file,
            OUTPUT_PATH=filepath,
        )
        end_script = end_script.substitute(
            OUTPUT_PATH=filepath, OUTPUT_PATH_PROGRESS=version_path
        )

        script_path = setting_data.get("script_path")
        if script_path:
            with open(script_path, "r") as f:
                preset_code = f.read()
                script = (
                    script
                    + "\n\n"
                    + preset_code.replace("$SETTINGS", json.dumps(setting_data))
                    + "\n\n"
                )
        script = script + end_script
        return script

if __name__ == "__main__":
    # 1. Capture arguments from subprocess
    # We expect JSON strings for the dictionaries
    try:
        shot_info = json.loads(sys.argv[1])
        current_dept = json.loads(sys.argv[2])
        asset_dept = json.loads(sys.argv[3])
        mastershot_data = json.loads(sys.argv[4])
        addon_data = json.loads(sys.argv[5])
        file_paths = json.loads(sys.argv[-1])

        # 2. Run the logic
        builder = CompositingBuilder()
        result = builder.extract_data(
            shot_data=shot_info,
            current_department=current_dept,
            asset_department=asset_dept,
            mastershots_data=mastershot_data,
            addons_data=addon_data,
            filepath=file_paths,
        )

        # 3. Print the result so the subprocess can "catch" it
        print(result)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
