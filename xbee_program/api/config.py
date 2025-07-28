# api/config.py
from api.config_manager import app_config

def get_api_base_url():
    return app_config.get_base_url()
