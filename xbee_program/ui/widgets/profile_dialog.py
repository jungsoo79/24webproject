import os
from PyQt5 import QtWidgets, uic
from api.user_api import get_my_info
from api.device_api import get_my_devices

class ProfileDialog(QtWidgets.QDialog):
    def __init__(self, token, parent=None):
        super().__init__(parent)

        ui_path = os.path.join("ui", "forms", "profile_dialog.ui")
        uic.loadUi(ui_path, self)

        self.token = token
        self.close_button.clicked.connect(self.close)

        self.load_user_info()
        self.load_device_list()

    def load_user_info(self):
        result = get_my_info(self.token)

        if not result["success"]:
            QtWidgets.QMessageBox.warning(self, "오류", result.get("message", "내 정보를 불러오지 못했습니다."))
            return

        info = result["data"]

        self.label_username.setText(f"아이디: {info.get('username', '')}")
        self.label_email.setText(f"이메일: {info.get('email', '')}")
        self.label_phone.setText(f"전화번호: {info.get('phone', '')}")

        company_name = ""
        try:
            company_name = info["companies"][0]["company_name"]
        except (KeyError, IndexError, TypeError):
            company_name = "(없음)"
        self.label_company.setText(f"회사명: {company_name}")

    def load_device_list(self):
        result = get_my_devices(self.token)

        if not result["success"]:
            QtWidgets.QMessageBox.warning(self, "오류", result.get("message", "장치 목록을 불러오지 못했습니다."))
            return

        devices = result["data"]  # ✅ 실제 장치 리스트

        self.device_listWidget.clear()
        for device in devices:
            text = f"{device['device_name']} - {device['serial_number']} ({device['role']})"
            self.device_listWidget.addItem(text)

