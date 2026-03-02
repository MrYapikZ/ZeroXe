from textwrap import dedent
from string import Template
from app.utils.versioning import VersioningSystem

class BlenderFunctions:
	@staticmethod
	def up_version(filepath: str):
		tpl = Template(dedent("""
			import bpy

			bpy.ops.wm.open_mainfile(filepath="$FILEPATH")

			bpy.ops.wm.save_as_mainfile(filepath="$VERSION_PATH", copy=True)

			bpy.ops.wm.quit_blender()
			"""))

		version_path = VersioningSystem.get_next_version_path(filepath)

		script = tpl.substitute(
            FILEPATH=filepath,
            VERSION_PATH=version_path
		)
		return script, version_path

	@staticmethod
	def up_master(filepath: str):
		tpl = Template(dedent("""
			import bpy

			bpy.ops.wm.open_mainfile(filepath="$FILEPATH")

			bpy.ops.wm.save_as_mainfile(filepath="$MASTER_PATH", copy=True)

			bpy.ops.wm.quit_blender()
		"""))
		master_path = VersioningSystem.get_master_path(filepath)

		script = tpl.substitute(
            FILEPATH=filepath,
			MASTER_PATH=master_path
		)
		return script, master_path

	@staticmethod
	def build_layout_script(filepath: str, version_path: str, collections: dict, setting_data: dict):
		tpl = Template(dedent("""
import bpy
import os
from pathlib import Path

collections = $COLLECTIONS

# Clear all existing collections and objects before linking new ones
def clear_all():
	# Remove all objects
	for obj in bpy.data.objects:
		bpy.data.objects.remove(obj, do_unlink=True)

	# Remove all collections
	for collection in bpy.data.collections:
		bpy.data.collections.remove(collection)

clear_all()

def select_only(obj):
	for o in bpy.context.view_layer.objects:
		o.select_set(False)
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj

def link_collection(collections_dict):
	for category_name, file_paths in collections_dict.items():
		# Create or get top-level category collection
		if category_name in bpy.data.collections:
			category_collection = bpy.data.collections[category_name]
		else:
			category_collection = bpy.data.collections.new(category_name)
			bpy.context.scene.collection.children.link(category_collection)

		# Link collections from each .blend file
		for asset_path_str in file_paths:
			asset_path = Path(asset_path_str)

			# Collection name = stem of file (filename without extension)
			collection_name = asset_path.stem  # e.g., "c-bahlil"

			# Load collection from the blend file
			with bpy.data.libraries.load(str(asset_path), link=True) as (data_from, data_to):
				if collection_name in data_from.collections:
					data_to.collections = [collection_name]  # Only load this collection
				else:
					print(f"Collection '{collection_name}' not found in {asset_path}")
					continue

			# Link the loaded collection into the category collection
			for linked_collection in data_to.collections:
				if linked_collection and linked_collection.name not in category_collection.children:
					category_collection.children.link(linked_collection)
					armatures = [obj for obj in linked_collection.all_objects if obj.type == 'ARMATURE']

					if not armatures:
						print(f"[SKIP] '{linked_collection.name}' tidak punya Armature.")
						continue

					# Override the entire collection
					for arm in armatures:
						select_only(arm)  # Ensure the object is active and selected
						bpy.context.view_layer.update()  # Update the context

						try:
							bpy.ops.object.make_override_library(collection=linked_collection.session_uid)
						except Exception:
							bpy.ops.object.make_override_library()

					# Ensure the overridden collection remains in the category collection and remove it from the root
					if linked_collection.name in bpy.data.collections:
						overridden_collection = bpy.data.collections[linked_collection.name]
						if overridden_collection.name not in [child.name for child in category_collection.children]:
							category_collection.children.link(overridden_collection)
							print(f"Kept overridden collection '{overridden_collection.name}' in category '{category_collection.name}'")

						# Remove the overridden collection from the root collection
						if overridden_collection.name in [child.name for child in bpy.context.scene.collection.children]:
							bpy.context.scene.collection.children.unlink(overridden_collection)
							print(f"Removed overridden collection '{overridden_collection.name}' from root collection")

					bpy.context.view_layer.update()
				print(f"Linked collection '{linked_collection.name}' into '{category_name}'")

link_collection(collections)

def add_camera_rig():
	# Create new collection named "cam"
	cam_collection = bpy.data.collections.new("cam")
	bpy.context.scene.collection.children.link(cam_collection)

	# Deselect all objects
	bpy.ops.object.select_all(action='DESELECT')

	# Build camera rig (Dolly type)
	bpy.ops.object.build_camera_rig(mode='DOLLY')
 
	# Function to get object + all children recursively
	def get_children_recursive(obj):
		objs = [obj]
		for child in obj.children:
			objs.extend(get_children_recursive(child))
		return objs

	# Collect all selected objects and their children
	objects_to_move = []
	for obj in bpy.context.selected_objects:
		objects_to_move.extend(get_children_recursive(obj))

	# Remove duplicates (in case of shared hierarchy)
	objects_to_move = list(set(objects_to_move))

	# Move to cam collection
	for obj in objects_to_move:
		for col in obj.users_collection:
			col.objects.unlink(obj)
		cam_collection.objects.link(obj)

add_camera_rig()

settings = $SETTINGS
bpy.context.scene.frame_end = settings["frame_out"]
bpy.context.scene.frame_start = settings["frame_in"]
bpy.context.scene.render.fps = settings["fps"]
bpy.context.scene.render.resolution_x = settings["resolution"][0]
bpy.context.scene.render.resolution_y = settings["resolution"][1]

bpy.ops.wm.save_as_mainfile(filepath="$VERSION_PATH")
bpy.ops.wm.save_as_mainfile(filepath="$MASTER_PATH", copy=True)
		"""))
		end_script = Template(dedent("""
bpy.ops.wm.save_as_mainfile(filepath="$VERSION_PATH")

bpy.ops.wm.quit_blender()
		"""))

		script = tpl.substitute(
			COLLECTIONS=collections,
			SETTINGS=setting_data,
			VERSION_PATH=version_path,
			MASTER_PATH=filepath
		)
		end_script = end_script.substitute(
			VERSION_PATH=version_path
		)

		if setting_data.get("script"):
			with open(setting_data.get("script"), "r") as f:
				preset_code = f.read()
				script = script + "\n\n" + preset_code
		script = script + end_script
		return script

	@staticmethod
	def build_lighting_script(filepath: str, version_path: str, master_file: str, animation_file : str, setting_data: dict):
		tpl = Template(dedent("""
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
"""))

		end_script = Template(dedent("""
# Save the modified Blender file
bpy.ops.wm.save_as_mainfile(filepath="$OUTPUT_PATH")
bpy.ops.wm.save_as_mainfile(filepath="$OUTPUT_PATH_PROGRESS")
print("File saved as: $OUTPUT_PATH")
	
# Quit Blender
bpy.ops.wm.quit_blender()
		"""))
		collection_list = [
			("chr", "c-"),
			("prp", "p-"),
			("set", "s-"),
			("veh", "v-"),
			("cam", None),
		]
		script = tpl.substitute(
			FILEPATH=master_file,
			ANIMATION_FILE=animation_file,
			COLLECTION_LIST=collection_list,
			CAMERA_COLLECTION="cam",
			METHOD=False,
			OUTPUT_PATH=filepath,
			SETTINGS=setting_data
		)
		end_script = end_script.substitute(
			OUTPUT_PATH=filepath,
			OUTPUT_PATH_PROGRESS=version_path
		)

		if setting_data.get("script"):
			with open(setting_data.get("script"), "r") as f:
				preset_code = f.read()
				script = script + "\n\n" + preset_code
		script = script + end_script
		return script
