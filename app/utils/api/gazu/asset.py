from app.core.gazu_client import gazu_client

class AssetServices:
    @staticmethod
    def get_assets_by_project_id(project_id):
        return gazu_client.asset.all_assets_for_project(project_id)

    @staticmethod
    def get_assets_by_episode_id(episode_id):
        return gazu_client.asset.all_assets_for_episode(episode_id)

    @staticmethod
    def get_asset_by_id(asset_id):
        return gazu_client.asset.get_asset(asset_id)

    @staticmethod
    def get_asset_by_name(project_id, asset_name):
        return gazu_client.asset.get_asset_by_name(project_id, asset_name)

    @staticmethod
    def get_asset_types():
        return gazu_client.asset.all_asset_types()

    @staticmethod
    def get_asset_type_by_id(asset_type_id):
        return gazu_client.asset.get_asset_type(asset_type_id)

    @staticmethod
    def get_asset_type_by_name(asset_type_name):
        return gazu_client.asset.get_asset_type_by_name(asset_type_name)

    @staticmethod
    def get_asset_types_by_project_id(project_id):
        return gazu_client.asset.all_asset_types_for_project(project_id)