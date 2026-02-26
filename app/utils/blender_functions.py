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
			bpy.ops.wm.save_as_mainfile(filepath="$VERSION_PATH", copy=True)

			bpy.ops.wm.quit_blender()
		"""))

		version_path = VersioningSystem.get_next_version_path(filepath)
		master_path = VersioningSystem.get_master_path(filepath)

		script = tpl.substitute(
            FILEPATH=filepath,
            VERSION_PATH=version_path,
			MASTER_PATH=master_path
		)
		return script, version_path, master_path

	@staticmethod
	def build_animation_script(filepath: str, version_path: str, collections: dict):
		tpl = Template(dedent("""
			import bpy
			from pathlib import Path

			collections = $COLLECTIONS
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
								print(f"Linked collection '{linked_collection.name}' into '{category_name}'")

			link_collection(collections)

			bpy.ops.wm.save_as_mainfile(filepath="$MASTER_PATH", copy=True)
			bpy.ops.wm.save_as_mainfile(filepath="$VERSION_PATH", copy=True)

			bpy.ops.wm.quit_blender()
		"""))

		script = tpl.substitute(
			VERSION_PATH=version_path,
			MASTER_PATH=filepath,
			COLLECTIONS=collections
		)
		return script