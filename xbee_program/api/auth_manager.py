# auth_manager.py
import threading

class AuthManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._token = None
        self._user_info = {}

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def set_token(self, token):
        with self._lock:
            self._token = token

    def get_token(self):
        with self._lock:
            return self._token

    def set_user_info(self, info):
        with self._lock:
            self._user_info = info

    def get_user_info(self):
        with self._lock:
            return self._user_info

    def clear(self):
        with self._lock:
            self._token = None
            self._user_info = {}
