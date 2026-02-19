from app.core.gazu_client import gazu_client

class ProjectServices:
    @staticmethod
    def get_projects():
        return gazu_client.project.all_projects()

    @staticmethod
    def get_project_by_id(project_id):
        return gazu_client.project.get_project(project_id)

    @staticmethod
    def get_project_by_name(project_name):
        return gazu_client.project.get_project_by_name(project_name)
