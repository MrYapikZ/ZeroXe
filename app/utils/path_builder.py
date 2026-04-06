from pathlib import Path


class PathBuilder:
    @staticmethod
    def build_shot_name(project_code: str, episode_name: str, sequence_name: str, shot_name: str, department_code: str | None = None):
        if department_code:
            return f"{project_code}_{episode_name}_{sequence_name}_{shot_name}_{department_code}"
        return f"{project_code}_{episode_name}_{sequence_name}_{shot_name}"
        pass

    @staticmethod
    def build_shot_path(episode_name: str, sequence_name: str, shot_name: str):
        shot_path = Path(f"{episode_name}/{episode_name}_{sequence_name}/{episode_name}_{sequence_name}_{shot_name}")
        return shot_path