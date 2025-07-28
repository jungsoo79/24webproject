# 이 코드는 이제 사용 안함!!!
import os
import requests
from PyQt5 import QtWidgets, uic, QtCore
from api.config import get_api_base_url

class DeviceDetailDialog(QtWidgets.QDialog):
    def __init__(self, device_data, token, parent=None):
        super().__init__(parent)
        ui_path = os.path.join("ui", "forms", "device_detail_dialog.ui")
        uic.loadUi(ui_path, self)

        self.device_data = device_data
        self.token = token
        self.api_base = get_api_base_url()
        self.serial_number = device_data.get("serial_number")
        self.status = device_data.get("status")
        self.role = device_data.get("role")

        self.setWindowTitle(f"장치 상세 정보 - {self.serial_number}")
        self.label_device_info.setText(
            f"이름: {device_data.get('device_name')}\n"
            f"모델: {device_data.get('model_name')}\n"
            f"위치: {device_data.get('location')}\n"
            f"상태: {self.status}\n"
            f"역할: {self.role}"
        )

        self.table_sensors.setRowCount(0)

        self.button_close.clicked.connect(self.close)
        self.button_toggle_status.clicked.connect(self.toggle_status)

        self.load_sensor_data()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.load_sensor_data)
        self.timer.start(3000)

    def load_sensor_data(self):
        try:
            if self.role == "Sender":
                self.load_sender_data()
            elif self.role == "Receiver":
                self.load_receiver_data()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"데이터 요청 실패: {e}")

    def load_sender_data(self):
        try:
            res = requests.get(
                f"{self.api_base}/api/devices/{self.serial_number}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if res is None:
                raise ValueError("서버 응답이 없습니다.")
            if res.status_code == 200:
                device_info = res.json()
                sensors = device_info.get("sensors", [])

                self.table_sensors.setRowCount(0)
                for sensor in sensors:
                    row = self.table_sensors.rowCount()
                    self.table_sensors.insertRow(row)
                    self.table_sensors.setItem(row, 0, QtWidgets.QTableWidgetItem(sensor.get("sensor_name")))
                    self.table_sensors.setItem(row, 1, QtWidgets.QTableWidgetItem(sensor.get("sensor_type")))

                    latest = sensor.get("latest_data", {})
                    value = f"{latest.get('value')} {latest.get('unit')}" if latest else "N/A"
                    timestamp = latest.get("timestamp", "N/A")

                    self.table_sensors.setItem(row, 2, QtWidgets.QTableWidgetItem(value))
                    self.table_sensors.setItem(row, 3, QtWidgets.QTableWidgetItem(timestamp))
            else:
                QtWidgets.QMessageBox.warning(self, "오류", f"센서 데이터 조회 실패: {res.text}")
        except requests.exceptions.RequestException as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"서버 연결 실패: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"요청 실패: {e}")

    def load_receiver_data(self):
        try:
            res = requests.get(
                f"{self.api_base}/api/devices/{self.serial_number}/sensor-data",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if res is None:
                raise ValueError("서버 응답이 없습니다.")
            if res.status_code == 200:
                data_list = res.json()
                self.table_sensors.setRowCount(0)

                for data in data_list:
                    row = self.table_sensors.rowCount()
                    self.table_sensors.insertRow(row)

                    self.table_sensors.setItem(row, 0, QtWidgets.QTableWidgetItem(data["device_serial"]))
                    self.table_sensors.setItem(row, 1, QtWidgets.QTableWidgetItem(data["sensor_type"]))
                    self.table_sensors.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{data['value']} {data['unit']}"))
                    self.table_sensors.setItem(row, 3, QtWidgets.QTableWidgetItem(data["timestamp"]))
            else:
                QtWidgets.QMessageBox.warning(self, "오류", f"센서 데이터 조회 실패: {res.text}")
        except requests.exceptions.RequestException as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"서버 연결 실패: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"요청 실패: {e}")

    def toggle_status(self):
        new_status = "inactive" if self.status == "active" else "active"
        try:
            res = requests.put(
                f"{self.api_base}/api/devices/{self.serial_number}/status",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"status": new_status}
            )
            if res is None:
                raise ValueError("서버 응답이 없습니다.")
            if res.status_code == 200:
                QtWidgets.QMessageBox.information(self, "성공", "상태 변경 완료")
                self.status = new_status
                self.label_device_info.setText(self.label_device_info.text().replace(
                    f"상태: {'active' if new_status == 'inactive' else 'inactive'}", f"상태: {new_status}"
                ))
            else:
                QtWidgets.QMessageBox.warning(self, "오류", f"상태 변경 실패: {res.text}")
        except requests.exceptions.RequestException as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"서버 연결 실패: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "에러", f"요청 실패: {e}")
