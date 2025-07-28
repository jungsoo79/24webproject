import os
import requests
from PyQt5 import QtWidgets, uic, QtCore
from ui.widgets.dashboard_dialog import DashboardDialog
from api.config import get_api_base_url

class DeviceListItem(QtWidgets.QWidget):
    """장치 목록 카드형 위젯"""
    def __init__(self, device_data, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        label_name = QtWidgets.QLabel(f"이름: {device_data.get('device_name')}")
        label_model = QtWidgets.QLabel(f"모델: {device_data.get('model_name')}")
        lable_last_data_update = QtWidgets.QLabel(f"최근 데이터: {device_data.get('last_data_update')}")
        label_status = QtWidgets.QLabel(f"상태: {device_data.get('status')}")

        if device_data.get('status') == 'active':
            label_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            label_status.setStyleSheet("color: red; font-weight: bold;")

        layout.addWidget(label_name)
        layout.addWidget(label_model)
        layout.addWidget(lable_last_data_update)
        layout.addWidget(label_status)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)

class DeviceListWidget(QtWidgets.QWidget):
    def __init__(self, token):
        super().__init__()
        ui_path = os.path.join("ui", "forms", "device_list_widget.ui")
        uic.loadUi(ui_path, self)
        self.token = token

        self.listWidget_devices.itemClicked.connect(self.show_detail)
        self.button_refresh.clicked.connect(self.load_devices)
        self.load_devices()

    def load_devices(self):
        url = f"{get_api_base_url()}/api/devices"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(url, headers=headers)
            if response is None:
                raise ValueError("서버 응답이 없습니다.")
            if response.status_code == 200:
                devices = response.json()
                self.listWidget_devices.clear()
                for dev in devices:
                    item = QtWidgets.QListWidgetItem(self.listWidget_devices)
                    widget = DeviceListItem(dev)
                    item.setSizeHint(widget.sizeHint())
                    item.setData(QtCore.Qt.UserRole, dev)

                    self.listWidget_devices.addItem(item)
                    self.listWidget_devices.setItemWidget(item, widget)
            else:
                QtWidgets.QMessageBox.warning(self, "오류", f"장치 목록 조회 실패: {response.status_code}")
        except requests.exceptions.RequestException as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"서버 연결 실패: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"요청 실패: {e}")

    def get_selected_serial(self):
        """현재 선택된 장치의 시리얼 넘버 반환"""
        item = self.listWidget_devices.currentItem()
        if item:
            device_data = item.data(QtCore.Qt.UserRole)
            return device_data.get("serial_number")
        return None

    def show_detail(self, item):
        device_data = item.data(QtCore.Qt.UserRole)
        serial_number = device_data.get("serial_number")

        if not serial_number:
            QtWidgets.QMessageBox.warning(self, "오류", "디바이스 시리얼 번호가 없습니다.")
            return

        dialog = DashboardDialog(
            token=self.token,
            user_id=None,  # 필요 시 전달
            device_serial=serial_number,
            parent=self
        )
        dialog.exec_()
