import sys
import os
from PyQt5 import QtWidgets, uic
from api.user_api import login_request
from api.auth_manager import AuthManager
from api.config_manager import app_config  # ✅ 추가
import requests

class LoginDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), "..", "forms", "login.ui")
        uic.loadUi(ui_path, self)

        self.server_lineEdit.setText("http://192.168.219.52:5000")  # ✅ 기본값 설정
        self.username_lineEdit.setText("")
        self.password_lineEdit.setText("")

        self.login_button.clicked.connect(self.login)

    def login(self):
        server_url = self.server_lineEdit.text().strip()  # ✅ 서버 주소 입력값
        username_input = self.username_lineEdit.text().strip()
        password = self.password_lineEdit.text().strip()

        if not (server_url and username_input and password):
            QtWidgets.QMessageBox.warning(self, "경고", "서버 주소, 아이디, 비밀번호를 모두 입력하세요.")
            return

        try:
            # ✅ 서버 주소 저장 (전역 싱글톤)
            app_config.set_base_url(server_url)

            # 로그인 API 요청
            result = login_request(username_input, password)

            if not result["success"]:
                QtWidgets.QMessageBox.warning(self, "로그인 실패", result["message"])
                return

            # 로그인 성공
            data = result["data"]
            token = data.get("access_token")
            user_info = data.get("user")

            companies = user_info.get("companies", [])
            if companies:
                user_info["company_id"] = companies[0].get("company_id")
                user_info["company_name"] = companies[0].get("company_name")
            else:
                user_info["company_id"] = None
                user_info["company_name"] = None

            if token and user_info:
                auth = AuthManager.get_instance()
                auth.set_token(token)
                auth.set_user_info(user_info)

                QtWidgets.QMessageBox.information(self, "로그인", f"{user_info.get('username', '사용자')}님 환영합니다!")
                self.accept()
            else:
                QtWidgets.QMessageBox.critical(self, "에러", "토큰 또는 사용자 정보가 비어 있습니다.")

        except requests.exceptions.RequestException as e:
            QtWidgets.QMessageBox.critical(self, "네트워크 오류", f"서버에 연결할 수 없습니다: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "예외 발생", f"알 수 없는 오류: {e}")
