from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QMessageBox
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QDate, QTimer
import os
from database.backup_db import init_db, get_all_sender_serials, get_sensor_data_by_serial
from database.backup_db import get_unsynced_data, mark_data_as_synced
from api.db_api import send_sensor_data_batch
from datetime import datetime, timedelta


class BackupDataDialog(QDialog):
    def __init__(self, token, company_id, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join("ui", "forms", "backup_data_dialog.ui"), self)

        self.token = token
        self.company_id = company_id

        self.resize(1000, 600)

        self.comboBox_serial.currentIndexChanged.connect(self.load_table)
        self.button_close.clicked.connect(self.close)

        self.init_ui()

    def init_ui(self):
        init_db()
        self.button_send.clicked.connect(self.send_unsynced_data)
        self.button_filter.clicked.connect(self.load_table)

        today = QDate.currentDate()
        self.dateEdit_filter.setDate(today)

        serials = get_all_sender_serials()
        self.comboBox_serial.addItems(serials)
        if serials:
            self.load_table()

        # 🔁 1초마다 자동 새로고침
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.load_table)
        self.auto_refresh_timer.start(1000)


    def load_table(self):
        serial = self.comboBox_serial.currentText()
        rows = get_sensor_data_by_serial(serial)

        selected_date = self.dateEdit_filter.date().toString("yyyy-MM-dd")

        # 날짜 필터링
        filtered_rows = []
        for row in rows:
            timestamp_full = row[0]
            try:
                dt = datetime.fromisoformat(timestamp_full)
                if dt.strftime("%Y-%m-%d") == selected_date:
                    # ⏰ 시간만 추출
                    # row = (timestamp, receiver_serial, obj_temp, die_temp, roll, pitch, tilt, current, is_synced)
                    filtered_rows.append((dt.strftime("%H:%M:%S"), row[1], *row[2:9]))  # 시간, 수신부, 나머지
            except Exception as e:
                print(f"[timestamp 파싱 실패] {timestamp_full}, {e}")

        self.tableWidget_data.setRowCount(len(filtered_rows))
        self.tableWidget_data.setColumnCount(9)
        self.tableWidget_data.setHorizontalHeaderLabels([
            "시간", "수신부", "Obj온도(℃)", "Die온도(℃)", "Roll(°)", "Pitch(°)", "Tilt(°)", "전류(mA)", "전송 여부"
        ])

        for row_idx, row in enumerate(filtered_rows):
            for col_idx, value in enumerate(row):
                self.tableWidget_data.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(value)))

        self.tableWidget_data.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget_data.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidget_data.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tableWidget_data.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)

    def send_unsynced_data(self):
        unsynced_rows = get_unsynced_data()
        if not unsynced_rows:
            QMessageBox.information(self, "정보", "전송할 미전송 데이터가 없습니다.")
            return

        success_ids = []

        for row in unsynced_rows:
            id, sender_serial, receiver_serial, timestamp, obj_temp, die_temp, roll, pitch, tilt, current = row

            data_list = [
                {"sensor_type": "obj_temperature", "value": obj_temp, "unit": "℃", "timestamp": timestamp},
                {"sensor_type": "die_temperature", "value": die_temp, "unit": "℃", "timestamp": timestamp},
                {"sensor_type": "roll", "value": roll, "unit": "°", "timestamp": timestamp},
                {"sensor_type": "pitch", "value": pitch, "unit": "°", "timestamp": timestamp},
                {"sensor_type": "tilt", "value": tilt, "unit": "°", "timestamp": timestamp},
                {"sensor_type": "current", "value": current, "unit": "mA", "timestamp": timestamp}
            ]

            try:
                send_sensor_data_batch(self.token, self.company_id, sender_serial, data_list, receiver_serial=receiver_serial)
                success_ids.append(id)
            except Exception as e:
                print(f"[전송 실패] id={id}, 에러: {e}")

        mark_data_as_synced(success_ids)
        QMessageBox.information(self, "완료", f"{len(success_ids)}개의 데이터가 전송되었습니다.")
        self.load_table()