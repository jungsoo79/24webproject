import os
import requests
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QWidget, QHeaderView
)
from PyQt5.QtCore import QDate, QTimer
from api.config import get_api_base_url
from graph.graph_manager import SingleGraphManager


class DashboardDialog(QDialog):
    def __init__(self, token, user_id=None, device_serial=None, parent=None):
        super().__init__(parent)

        self.token = token
        self.user_id = user_id
        self.selected_serial = device_serial
        self.setWindowTitle("결과 데이터 대시보드")
        self.resize(1000, 700)

        self.device_label = QLabel("장치 선택:")
        self.device_combobox = QComboBox()
        self.date_label = QLabel("날짜:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.refresh_button = QPushButton("새로고침")

        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.device_label)
        self.top_layout.addWidget(self.device_combobox)
        self.top_layout.addWidget(self.date_label)
        self.top_layout.addWidget(self.date_edit)
        self.top_layout.addWidget(self.refresh_button)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.top_layout)
        self.setLayout(self.main_layout)

        self.device_combobox.currentIndexChanged.connect(self.on_device_selected)
        self.refresh_button.clicked.connect(self.on_device_selected)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_data_if_receiver)
        self._refresh_timer.setInterval(10000)  # 🔄 10초 간격
        self._refresh_timer.start()

        self.load_devices()

    def load_devices(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            res = requests.get(f"{get_api_base_url()}/api/devices", headers=headers)
            if res.status_code == 200:
                devices = res.json()
                self.device_combobox.clear()
                for idx, device in enumerate(devices):
                    serial = device["serial_number"]
                    name = device.get("device_name", "")
                    label = f"{name} ({serial})" if name else serial
                    self.device_combobox.addItem(label, serial)
                    if self.selected_serial and serial == self.selected_serial:
                        self.device_combobox.setCurrentIndex(idx)
            else:
                print("[에러] 장치 목록 실패", res.text)
        except Exception as e:
            print("[예외] 장치 목록 로드 오류", e)

    def on_device_selected(self):
        serial = self.device_combobox.currentData()
        if not serial:
            return

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            res = requests.get(f"{get_api_base_url()}/api/devices/{serial}", headers=headers)
            if res.status_code != 200:
                raise Exception(f"디바이스 정보 조회 실패: {res.status_code}")
            device_info = res.json()
            role = device_info.get("role")
            self.selected_role = role
            self.build_layout_by_role(role, serial)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"디바이스 역할 불러오기 실패: {e}")

    def build_layout_by_role(self, role, serial):
        for i in reversed(range(self.main_layout.count())):
            if i == 0:
                continue
            widget = self.main_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if role == "Receiver":
            self.build_receiver_layout(serial)
        elif role == "Sender":
            self.build_sender_layout(serial)

    def build_receiver_layout(self, serial):
        self.date_edit.setEnabled(True)

        self.temp_graph = SingleGraphManager("온도", "℃", "red", y_range=(0, 40))
        self.current_graph = SingleGraphManager("전류", "mA", "green", y_range=(0, 30))
        self.tilt_graph = SingleGraphManager("기울기", "°", "blue", y_range=(0, 180))

        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.temp_graph)
        graph_layout.addWidget(self.current_graph)
        graph_layout.addWidget(self.tilt_graph)

        graph_container = QWidget()
        graph_container.setLayout(graph_layout)

        self.tableWidget_data = QTableWidget()
        self.tableWidget_data.setColumnCount(6)
        self.tableWidget_data.setHorizontalHeaderLabels(["시간", "수신부", "송신부", "온도", "전류", "기울기"])
        self.tableWidget_data.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        body_layout = QHBoxLayout()
        body_layout.addWidget(self.tableWidget_data, stretch=3)
        body_layout.addWidget(graph_container, stretch=2)

        container = QWidget()
        container.setLayout(body_layout)
        self.main_layout.addWidget(container)

        self.load_receiver_data(serial)

    def build_sender_layout(self, serial):
        self.date_edit.setEnabled(False)

        self.tableWidget_data = QTableWidget()
        self.tableWidget_data.setColumnCount(4)
        self.tableWidget_data.setHorizontalHeaderLabels(["시간", "센서 이름", "종류", "값"])
        self.tableWidget_data.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.main_layout.addWidget(self.tableWidget_data)
        self.load_sender_data(serial)

    def load_receiver_data(self, serial):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            url = f"{get_api_base_url()}/api/devices/{serial}/sensor-data?from={date}T00:00:00&to={date}T23:59:59"
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                records = res.json()
                self.update_receiver_ui(records, serial)
            else:
                print(f"[에러] 데이터 실패: {res.text}")
        except Exception as e:
            print(f"[예외] 수신 데이터 오류: {e}")

    def update_receiver_ui(self, records, receiver_serial):
        self.temp_graph.clear()
        self.current_graph.clear()
        self.tilt_graph.clear()

        records.sort(key=lambda r: r["timestamp"], reverse=True)

        filtered_data = {"obj_temperature": [], "current": [], "tilt": []}
        timestamps = []

        for r in records:
            t = r["sensor_type"]
            if t in filtered_data:
                filtered_data[t].append(r)
                if t == "obj_temperature":
                    timestamps.append(r["timestamp"])

        max_len = max(len(v) for v in filtered_data.values())
        self.tableWidget_data.setRowCount(max_len)

        for row in range(max_len):
            timestamp = timestamps[row][11:19] if row < len(timestamps) else ""
            sender_serial = (filtered_data["obj_temperature"][row].get("device_serial")
                            if row < len(filtered_data["obj_temperature"]) else "")

            self.tableWidget_data.setItem(row, 0, QTableWidgetItem(timestamp))
            self.tableWidget_data.setItem(row, 1, QTableWidgetItem(receiver_serial))
            self.tableWidget_data.setItem(row, 2, QTableWidgetItem(sender_serial))
            self.tableWidget_data.setItem(row, 3, QTableWidgetItem(
                str(filtered_data["obj_temperature"][row]["value"])) if row < len(filtered_data["obj_temperature"]) else QTableWidgetItem(""))
            self.tableWidget_data.setItem(row, 4, QTableWidgetItem(
                str(filtered_data["current"][row]["value"])) if row < len(filtered_data["current"]) else QTableWidgetItem(""))
            self.tableWidget_data.setItem(row, 5, QTableWidgetItem(
                str(filtered_data["tilt"][row]["value"])) if row < len(filtered_data["tilt"]) else QTableWidgetItem(""))

        for sensor_type in filtered_data:
            filtered_data[sensor_type].sort(key=lambda r: r["timestamp"])

        for sensor_type, data in filtered_data.items():
            for r in data:
                val = r["value"]
                ts = r["timestamp"]
                if sensor_type == "obj_temperature":
                    self.temp_graph.update_graph(val, ts)
                elif sensor_type == "current":
                    self.current_graph.update_graph(val, ts)
                elif sensor_type == "tilt":
                    self.tilt_graph.update_graph(val, ts)

    def _refresh_data_if_receiver(self):
        serial = self.device_combobox.currentData()
        if not serial:
            return
        if hasattr(self, "selected_role") and self.selected_role == "Receiver":
            self.load_receiver_data(serial)

    def load_sender_data(self, serial):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            url = f"{get_api_base_url()}/api/devices/{serial}"
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                sensors = data.get("sensors", [])
                self.tableWidget_data.setRowCount(0)

                for sensor in sensors:
                    latest = sensor.get("latest_data")
                    if latest:
                        row = self.tableWidget_data.rowCount()
                        self.tableWidget_data.insertRow(row)

                        timestamp = latest.get("timestamp", "N/A")[11:19]
                        sensor_name = sensor.get("sensor_name", "N/A")
                        sensor_type = sensor.get("sensor_type", "N/A")
                        value = f"{latest.get('value')} {latest.get('unit')}" if latest.get("value") else "N/A"

                        self.tableWidget_data.setItem(row, 0, QTableWidgetItem(timestamp))
                        self.tableWidget_data.setItem(row, 1, QTableWidgetItem(sensor_name))
                        self.tableWidget_data.setItem(row, 2, QTableWidgetItem(sensor_type))
                        self.tableWidget_data.setItem(row, 3, QTableWidgetItem(value))
            else:
                QMessageBox.warning(self, "오류", f"센서 데이터 조회 실패: {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "에러", f"데이터 불러오기 오류: {e}")
