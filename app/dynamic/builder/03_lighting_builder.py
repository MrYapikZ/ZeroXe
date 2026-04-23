import sys
import json
from pathlib import Path
from textwrap import dedent
from string import Template


class LightingBuilder:
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
        
        # Create parent folder
        Path(filepath['version']).parent.mkdir(parents=True, exist_ok=True)
        
        # Get mastershot base path
        mastershot_name = "mastershot_lit"
        current_mastershot = mastershots_data.get("mastershots", {}).get(
            mastershot_name, {}
        )

        # Get lit mastershot path
        lit_mastershot_name = shot_data.get("data", {}).get("ms_lit", "")
        lit_mastershot_file = (
            Path(current_mastershot.get("base_path", ""))
            / lit_mastershot_name
            / f"{lit_mastershot_name}.blend"
        )

        # Get preset
        dept_data = next(iter(current_department.values()))
        preset_name = "preset"
        preset_path = dept_data.get("presets", {}).get(preset_name, {}).get("path")

        # Get addon preset
        addon_preset_path = (
            addons_data.get("addons", {})
            .get("ExLauncher", {})
            .get("ops_blp", {})
            .get("base_path", "")
        )
        addon_preset_file = Path(addon_preset_path) / f"{lit_mastershot_name}.json"

        # Collection list
        asset_types = asset_department.get("Asset", {}).get("asset_type", {})
        collection_list = [
            (config.get("code"), config.get("prefix"))
            for config in asset_types.values()
        ]
        # Add the camera entry manually
        collection_list.append(("cam", None))

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
            "ops_blp": addon_preset_file,
            "script_path": preset_path,
        }

        lighting_script = self.script_builder(
            filepath=filepath["final"],
            version_path=filepath["version"],
            master_file=str(lit_mastershot_file),
            animation_file=filepath["source"],
            setting_data=setting_data,
            collection_list=collection_list,
        )
        return lighting_script

    def script_builder(
        self,
        filepath: str,
        version_path: str,
        master_file: str,
        animation_file: str,
        setting_data: dict,
        collection_list: list,
    ):
        tpl = Template(
            dedent(
                """
import bpy
from pathlib import Path
							  
bpy.ops.wm.open_mainfile(filepath="$FILEPATH")

def _unlink_collection_from(parent, target):
	for child in list(parent.children):
		if child == target:
			parent.children.unlink(child)
		else:
			_unlink_collection_from(child, target)		

def _force_remove_collection(name: str):
	coll = bpy.data.collections.get(name)
	if not coll:
		return
	for scene in bpy.data.scenes:
		_unlink_collection_from(scene.collection, coll)
	try:
		bpy.data.collections.remove(coll)
		print(f"Removed existing collection: {name}")
	except RuntimeError as e:
		print(f"[WARNING] Could not remove '{name}': {e}")

def ensure_parent_in_scene(name: str) -> bpy.types.Collection:
	if name.lower() != "$CAMERA_COLLECTION".lower():
		_force_remove_collection(name)
		parent = bpy.data.collections.new(name)
		bpy.context.scene.collection.children.link(parent)
		print(f"Created and linked parent collection: {name}")
		return parent


def get_empty_groups_from_collection(collection_name: str):
	coll = bpy.data.collections.get(collection_name)
	if not coll:
		raise ValueError(f"Collection '{collection_name}' not found.")

	result = []

	def recurse(c: bpy.types.Collection):
		for obj in c.objects:
			if obj.type == 'EMPTY' and obj.name.endswith("_grp"):
				result.append(obj.name)
		for child in c.children:
			recurse(child)
	recurse(coll)
	return result
	
# Main Fucntion
def link_animation():
	# Link the animation file
	print("Animation file:", "$ANIMATION_FILE")
	parents = {}
	for name, prefix in $COLLECTION_LIST:
		if name.lower() == "$CAMERA_COLLECTION".lower():
			_force_remove_collection("$CAMERA_COLLECTION")
			continue
		parents[name] = ensure_parent_in_scene(name)

	desired = {}

	with bpy.data.libraries.load("$ANIMATION_FILE", link=True) as (data_from, data_to):
		for parent_name, prefix in $COLLECTION_LIST:
			if prefix is None:
				cam_coll = next((c for c in data_from.collections if c.lower() == "$CAMERA_COLLECTION".lower()), None)
				if cam_coll:
					desired[parent_name] = [cam_coll]
				else:
					desired[parent_name] = []
					print("[WARNING] '$CAMERA_COLLECTION' not found in library")
			else:
				names = [n for n in data_from.collections if n.startswith(prefix)]
				desired[parent_name] = names

	to_link = []
	for parent_name, names in desired.items():
		if parent_name.lower() == "$CAMERA_COLLECTION".lower():
			continue
		to_link.extend(names)

	to_link = [n for n in to_link if n not in bpy.data.collections]

	if to_link:
		with bpy.data.libraries.load("$ANIMATION_FILE", link=True) as (data_from, data_to):
			data_to.collections = [n for n in to_link if n in data_from.collections]

	for parent_name, child_names in desired.items():
		if parent_name.lower() == "$CAMERA_COLLECTION".lower():
			continue
		parent = parents[parent_name]
		for cname in child_names:
			col = bpy.data.collections.get(cname)
			if not col:
				print(f"[WARNING] Expected linked collection missing: {cname}")
				continue

			if not (col.library and bpy.path.abspath(col.library.filepath) == bpy.path.abspath("$ANIMATION_FILE")):
				col = next((c for c in bpy.data.collections
							if c.name == cname and c.library and
							bpy.path.abspath(c.library.filepath) == bpy.path.abspath("$ANIMATION_FILE")), None)
				if not col:
					print(f"[WARNING] No valid linked collection found for: {cname}")
					continue

			if cname not in parent.children.keys():
				parent.children.link(col)
				print(f"Linked '{cname}' under '{parent_name}'")
			else:
				pass

	link_mode = bool($METHOD)
	cam_names = next((v for k, v in desired.items() if k.lower() == "$CAMERA_COLLECTION".lower()), [])
	if cam_names:
		cam_name = cam_names[0]

		for c in [c for c in list(bpy.data.collections) if c.name == cam_name or c.name.startswith(cam_name + ".")]:
			for scene in bpy.data.scenes:
				_unlink_collection_from(scene.collection, c)
			try:
				bpy.data.collections.remove(c)
			except RuntimeError:
				pass

		try:
			bpy.data.orphans_purge(do_recursive=True)
		except Exception:
			pass

		with bpy.data.libraries.load("$ANIMATION_FILE", link=link_mode) as (data_from, data_to):
			if cam_name in data_from.collections:
				data_to.collections = [cam_name]
			else:
				print(f"[WARNING] '{cam_name}' missing in library during {'link' if link_mode else 'append'}")
				return

		found = next((c for c in bpy.data.collections
					  if (c.name == cam_name or c.name.startswith(cam_name + "."))
					  and ((link_mode and c.library) or (not link_mode and not c.library))), None)

		if not found:
			print(f"[WARNING] Failed to {'link' if link_mode else 'append'} '{cam_name}'")
			return

		if not link_mode:
			other = bpy.data.collections.get(cam_name)
			if other and other is not found:
				try:
					bpy.data.collections.remove(other)
				except RuntimeError:
					pass
			if found.name != cam_name:
				try:
					found.name = cam_name
				except Exception:
					pass

		if found.name not in bpy.context.scene.collection.children.keys():
			bpy.context.scene.collection.children.link(found)

		print(f"[CAM] {'Linked' if link_mode else 'Appended'} '{cam_name}' as "
			  f"{'library' if link_mode else 'local'} collection '{found.name}'")


def update_camera():
	# Update camera settings
	scene = bpy.data.scenes['Scene']

	cam_obj = next((obj for obj in scene.objects if obj.type == 'CAMERA'), None)

	if cam_obj:
		scene.camera = cam_obj
	else:
		print("cam not found")

	active_camera = bpy.context.scene.camera
	if active_camera:
		active_camera.data.clip_end = 1000
		active_camera.data.dof.use_dof = True
		active_camera.data.dof.driver_remove("aperture_fstop")
		active_camera.data.dof.driver_remove("focus_distance")
		print(f"Camera '{active_camera.name}' settings updated: DOF disabled, clip_end set to 1000")
	else:
		print("No active camera found in the scene.")

def set_relative():
	# Make all file paths relative
	bpy.context.preferences.filepaths.use_relative_paths = True
	bpy.ops.file.make_paths_relative()
						 
# Execute functions
link_animation()
update_camera()
set_relative()
print("All operations completed successfully.")

settings = $SETTINGS
bpy.context.scene.frame_end = settings["frame_out"]
bpy.context.scene.frame_start = settings["frame_in"]
bpy.context.scene.render.fps = settings["fps"]
bpy.context.scene.render.resolution_x = settings["resolution"][0]
bpy.context.scene.render.resolution_y = settings["resolution"][1]
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
            ANIMATION_FILE=animation_file,
            COLLECTION_LIST=collection_list,
            CAMERA_COLLECTION="cam",
            METHOD=False,
            OUTPUT_PATH=filepath,
            SETTINGS=setting_data,
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
        builder = LightingBuilder()
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
