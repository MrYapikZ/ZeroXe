from app.core.gazu_client import gazu_client

class TaskServices:
    @staticmethod
    def get_tasks_by_asset_id(asset_id):
        return gazu_client.task.all_tasks_for_asset(asset_id)

    @staticmethod
    def get_task_by_id(task_id):
        return gazu_client.task.get_task(task_id)

    @staticmethod
    def get_task_by_entity(entity_id):
        return gazu_client.task.get_task_by_entity(entity_id)