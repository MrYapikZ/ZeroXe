import sys
import json
import shutil
from pathlib import Path
from textwrap import dedent
from string import Template

class EditingBuilder:
    def extract_data(self, filepath):
        full_path = Path(filepath['final'])
        episode_path = full_path.parents[2]
        if episode_path.exists():
            return
        (episode_path / "progress").mkdir(parents=True, exist_ok=True)
        sequence_path = full_path.parents[1]
            
        if sequence_path.exists() and sequence_path.is_dir():
            try:
                shutil.rmtree(sequence_path)
                # print(f"Successfully removed sequence folder: {sequence_path}")
            except Exception as e:
                # print(f"Error deleting folder: {e}")
                pass
        else:
            pass
            # print(f"Path not found or already deleted: {sequence_path}")
        return "import bpy"
        

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
        builder = EditingBuilder()
        result = builder.extract_data(
            filepath=file_paths
        )

        # 3. Print the result so the subprocess can "catch" it
        print(result)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
