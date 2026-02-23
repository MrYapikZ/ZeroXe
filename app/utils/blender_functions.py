from textwrap import dedent
from string import Template
from app.utils.versioning import VersioningSystem

class BlenderFunctions:
	@staticmethod
	def up_version(filepath: str):
		tpl = Template(dedent("""
			import bpy

			bpy.ops.wm.open_mainfile(filepath="$FILEPATH")

			bpy.ops.wm.save_as_mainfile(filepath="$VERSION_PATH", copy=true)

			bpy.ops.wm.quit_blender()
			"""))

		version_path = VersioningSystem.get_next_version_path(filepath)

		script = tpl.substitute(
            FILEPATH=filepath,
            VERSION_PATH=version_path
		)

	def up_master(filepath: str):
		tpl = Template(dedent("""
			import bpy

			bpy.ops.wm.open_mainfile(filepath="$FILEPATH")

			bpy.ops.wm.save_as_mainfile(filepath="$MASTER_PATH", copy=true)
			bpy.ops.wm.save_as_mainfile(filepath="$VERSION_PATH", copy=true)

			bpy.ops.wm.quit_blender()
		"""))

		version_path = VersioningSystem.get_next_version_path(filepath)
		master_path = VersioningSystem.get_master_path(filepath)

		script = tpl.substitute(
            FILEPATH=filepath,
            VERSION_PATH=version_path,
			MASTER_PATH=master_path
		)