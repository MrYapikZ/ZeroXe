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

bpy.ops.wm.save_as_mainfile(filepath="$MASTER_PATH", copy=True)
bpy.ops.wm.save_as_mainfile(filepath="$VERSION_PATH", copy=True)

bpy.ops.wm.quit_blender()
		"""))

		script = tpl.substitute(
			VERSION_PATH=version_path,
			MASTER_PATH=filepath,
			COLLECTIONS=collections,
			SETTINGS=setting_data
		)
		return script