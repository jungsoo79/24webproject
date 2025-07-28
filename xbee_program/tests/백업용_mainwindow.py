from PyQt5 import QtCore, QtWidgets, uic
import os
import serial.tools.list_ports
import matplotlib
from datetime import datetime
from xbee.serial_thread import SerialThread
from ui.widgets.xbee_edit_dialog import XbeeOptionDialog
from ui.widgets.xbee_add_dialog import XbeeAddDialog
from ui.widgets.device_list_widget import DeviceListWidget
from ui.widgets.profile_dialog import ProfileDialog
from ui.widgets.backup_data_dialog import BackupDataDialog
from api.auth_manager import AuthManager

matplotlib.rc('font', family='Malgun Gothic')

class XBeeConfigurator(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join("ui", "forms", "mainwindow.ui"), self)

        # 상태 표시창 추가
        self.status_label = QtWidgets.QLabel("초기화 중...", self)
        self.statusBar().addPermanentWidget(self.status_label)

        # 사용자 정보 초기화
        auth = AuthManager.get_instance()
        self.token = auth.get_token()
        self.user_info = auth.get_user_info()

        self.username = self.user_info.get("username")
        self.user_id = self.user_info.get("user_id")
        self.is_admin = self.user_info.get("is_admin")
        self.company_id = self.user_info.get("company_id")

        self.label_welcome.setText(f"{self.username}님")
        self.label_status.setFixedSize(12, 12)
        self.set_status_led(False)

        self.serial_thread = None

        self.main_combobox()
        self.main_refresh()

        # 버튼 이벤트 연결
        self.main_refresh_button.clicked.connect(self.main_refresh)
        self.main_connect_button.clicked.connect(self.main_connect)
        self.disconnect_port_button.clicked.connect(self.disconnect_port)
        self.xbee_edit_button.clicked.connect(self.xbee_edit_dialog)
        self.xbee_add_button.clicked.connect(self.xbee_add_dialog)
        self.logout_button.clicked.connect(self.logout)
        self.profile_button.clicked.connect(self.open_profile_dialog)
        self.backup_button.clicked.connect(self.open_backup_dialog)

        # 디바이스 목록 추가
        self.device_list = DeviceListWidget(self.token)
        self.verticalLayout_device_area.addWidget(self.device_list)

    def main_combobox(self):
        self.comboBox_baudrate_main.addItem("9600bps", "9600")
        self.comboBox_baudrate_main.addItem("115200bps", "115200")

    def scan_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def main_refresh(self):
        self.comboBox_port.clear()
        self.comboBox_port.addItems(self.scan_ports())
        self.update_status("포트 목록 새로고침 완료")

    def main_connect(self):
        port = self.comboBox_port.currentText()
        baudrate_str = self.comboBox_baudrate_main.currentData()

        if not port or not baudrate_str:
            return

        try:
            ser = serial.Serial(port, int(baudrate_str), timeout=1)
            ser.write(b'+++')
            QtCore.QThread.msleep(1000)
            response = ser.read(10)

            if b'OK' in response:
                ser.reset_input_buffer()
                QtCore.QThread.msleep(500)
                self.set_status_led(True)

                print("[디버그] 현재 토큰:", self.token)
                print("[디버그] 현재 company_id:", self.company_id)

                self.serial_thread = SerialThread(ser, token=self.token, company_id=self.company_id)
                self.serial_thread.start()

                self.update_status("XBee 연결 성공")
            else:
                ser.close()
                self.set_status_led(False)
                self.update_status("XBee 연결 실패")
        except Exception as e:
            print(f"[연결 실패] {e}")
            self.set_status_led(False)
            self.update_status("XBee 연결 실패")

    def disconnect_port(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None
        self.set_status_led(False)
        self.update_status("포트 연결 해제")

    def set_status_led(self, is_connected):
        color = "green" if is_connected else "red"
        self.label_status.setStyleSheet(f"background-color: {color}; border-radius: 6px;")

    def update_status(self, message):
        self.status_label.setText(message)

    def logout(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "로그아웃 확인",
            "정말 로그아웃 하시겠습니까?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            AuthManager.get_instance().clear()
            self.disconnect_port()
            self.close()
            QtWidgets.QApplication.quit()

    def closeEvent(self, event):
        self.disconnect_port()
        event.accept()

    def xbee_edit_dialog(self):
        dialog = XbeeOptionDialog(self)
        dialog.exec_()

    def xbee_add_dialog(self):
        dialog = XbeeAddDialog(self.token, self.company_id, self)
        dialog.exec_()

    def open_profile_dialog(self):
        dlg = ProfileDialog(self.token, self)
        dlg.exec_()

    def open_backup_dialog(self):
        auth = AuthManager.get_instance()
        token = auth.get_token()
        company_id = auth.get_user_info().get("company_id")

        dlg = BackupDataDialog(token, company_id, self)
        dlg.exec_()
