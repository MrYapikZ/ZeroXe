from app.core.gazu_client import gazu_client

class ShotServices:
    @staticmethod
    def get_shots_by_project_id(project_id):
        return gazu_client.shot.all_shots_for_project(project_id)

    @staticmethod
    def get_shots_by_episode_id(episode_id):
        return gazu_client.shot.all_shots_for_episode(episode_id)

    @staticmethod
    def get_shots_by_sequence_id(sequence_id):
        return gazu_client.shot.all_shots_for_sequence(sequence_id)

    @staticmethod
    def get_shot_by_id(shot_id):
        return gazu_client.shot.get_shot(shot_id)

    @staticmethod
    def get_shot_by_name(sequence_id, shot_name):
        return gazu_client.shot.get_shot_by_name(sequence_id, shot_name)

    @staticmethod
    def get_episodes_by_project_id(project_id):
        return gazu_client.context.all_episodes_for_project(project_id)

    @staticmethod
    def get_sequences_by_episode_id(episode_id):
        return gazu_client.context.all_sequences_for_episode(episode_id)
