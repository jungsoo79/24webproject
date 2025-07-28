# api/config_manager.py
class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._base_url = "http://"  # 기본값 설정
        return cls._instance

    def set_base_url(self, url: str):
        """로그인 후 서버 주소 설정"""
        if not url.startswith("http://") and not url.startswith("https://"):
            raise ValueError("서버 주소는 http:// 또는 https:// 로 시작해야 합니다.")
        self._base_url = url.rstrip("/")

    def get_base_url(self) -> str:
        """현재 서버 주소 반환"""
        return self._base_url

# 글로벌 인스턴스를 미리 만들어서 가져다 쓰도록 할 수도 있습니다
app_config = AppConfig()
