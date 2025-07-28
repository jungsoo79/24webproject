import os
import serial
import serial.tools.list_ports
import time
from PyQt5 import QtWidgets, uic

class XbeeOptionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join("ui", "forms", "xbee_edit_dialog.ui")
        uic.loadUi(ui_path, self)

        self.ser = None

        self.button_refresh.clicked.connect(self.update_port_list)
        self.button_connect.clicked.connect(self.connect_clicked)
        self.button_show.clicked.connect(self.show_settings)
        self.button_reset.clicked.connect(self.reset_default)
        self.button_change.clicked.connect(self.apply_settings)
        self.button_disconnect.clicked.connect(self.disconnect)

        self.init_combobox()

    def init_combobox(self):
        self.comboBox_baudrate.addItem("9600bps", "9600")
        self.comboBox_baudrate.addItem("115200bps", "115200")

        self.comboBox_ce.addItem("End Device [0]", "0")
        self.comboBox_ce.addItem("Coordinator [1]", "1")

        self.comboBox_ps.addItem("Disabled [0]", "0")
        self.comboBox_ps.addItem("Enabled [1]", "1")

        self.comboBox_ap.addItem("Transparent [0]", "0")
        self.comboBox_ap.addItem("API Without Escape [1]", "1")
        self.comboBox_ap.addItem("API Escape [2]", "2")
        self.comboBox_ap.addItem("Na [3]", "3")
        self.comboBox_ap.addItem("MicroPython REPL [4]", "4")

        self.comboBox_bd.addItem("9600bps", "3")
        self.comboBox_bd.addItem("115200bps", "7")

        self.comboBox_d1.addItem("Disabled [0]", "0")
        self.comboBox_d1.addItem("I2C SCL[6]", "6")

        self.comboBox_p1.addItem("Disabled [0]", "0")
        self.comboBox_p1.addItem("I2C SCL[6]", "6")

    def update_port_list(self):
        self.comboBox_port.clear()
        for port in serial.tools.list_ports.comports():
            self.comboBox_port.addItem(port.device)

    def connect_clicked(self):
        port = self.comboBox_port.currentText()
        baudrate_str = self.comboBox_baudrate.currentData()

        if port and baudrate_str:
            try:
                self.ser = serial.Serial(port, int(baudrate_str), timeout=1)
                self.textEdit_status.setPlainText(f"{port} 연결 완료 (속도: {baudrate_str}bps)")
                self.show_settings()
            except Exception as e:
                self.textEdit_status.setPlainText(f"연결 실패: {e}")

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None

        self.lineEdit_ch.clear()
        self.lineEdit_id.clear()
        self.lineEdit_dh.clear()
        self.lineEdit_dl.clear()
        self.comboBox_ce.setCurrentIndex(-1)
        self.comboBox_ps.setCurrentIndex(-1)
        self.comboBox_ap.setCurrentIndex(-1)
        self.comboBox_bd.setCurrentIndex(-1)
        self.comboBox_d1.setCurrentIndex(-1)
        self.comboBox_p1.setCurrentIndex(-1)

        self.textEdit_status.setPlainText("포트 연결 해제 완료")
    def enter_command_mode(self):
        if not self.ser or not self.ser.is_open:
            self.textEdit_status.setPlainText("포트가 연결되지 않았습니다.")
            return False

        self.ser.reset_input_buffer()
        time.sleep(4)

        self.ser.write(b'+++')
        self.ser.flush()
        time.sleep(4)

        response = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        if "OK" in response:
            return True
        else:
            self.textEdit_status.append(f"명령 모드 진입 실패, 수신 데이터: {response}")
            return False

    def show_settings(self):
        if not self.enter_command_mode():
            return

        self.ser.write(b'ATCH\r')
        time.sleep(0.1)
        ch = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        self.lineEdit_ch.setText(ch)

        self.ser.write(b'ATID\r')
        time.sleep(0.1)
        id_ = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        self.lineEdit_id.setText(id_)

        self.ser.write(b'ATDH\r')
        time.sleep(0.1)
        dh = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        self.lineEdit_dh.setText(dh)

        self.ser.write(b'ATDL\r')
        time.sleep(0.1)
        dl = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        self.lineEdit_dl.setText(dl)

        self.ser.write(b'ATCE\r')
        time.sleep(0.1)
        ce = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        index = self.comboBox_ce.findData(ce)
        if index != -1:
            self.comboBox_ce.setCurrentIndex(index)

        self.ser.write(b'ATPS\r')
        time.sleep(0.1)
        ps = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        index = self.comboBox_ps.findData(ps)
        if index != -1:
            self.comboBox_ps.setCurrentIndex(index)

        self.ser.write(b'ATAP\r')
        time.sleep(0.1)
        ap = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        index = self.comboBox_ap.findData(ap)
        if index != -1:
            self.comboBox_ap.setCurrentIndex(index)

        self.ser.write(b'ATBD\r')
        time.sleep(0.1)
        bd = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        index = self.comboBox_bd.findData(bd)
        if index != -1:
            self.comboBox_bd.setCurrentIndex(index)

        self.ser.write(b'ATD1\r')
        time.sleep(0.1)
        d1 = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        index = self.comboBox_d1.findData(d1)
        if index != -1:
            self.comboBox_d1.setCurrentIndex(index)

        self.ser.write(b'ATP1\r')
        time.sleep(0.1)
        p1 = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
        index = self.comboBox_p1.findData(p1)
        if index != -1:
            self.comboBox_p1.setCurrentIndex(index)

        self.ser.write(b'ATCN\r')

    def reset_default(self):
        if not self.enter_command_mode():
            return

        self.ser.write(b'ATRE\r')
        time.sleep(0.2)
        self.ser.write(b'ATWR\r')
        time.sleep(0.2)
        self.ser.write(b'ATCN\r')
        self.textEdit_status.setPlainText("설정 초기화 완료")

    def apply_settings(self):
        if not self.enter_command_mode():
            return

        cmds = [
            f"ATCH {self.lineEdit_ch.text()}",
            f"ATID {self.lineEdit_id.text()}",
            f"ATDH {self.lineEdit_dh.text()}",
            f"ATDL {self.lineEdit_dl.text()}",
            f"ATCE {self.comboBox_ce.currentData()}",
            f"ATPS {self.comboBox_ps.currentData()}",
            f"ATAP {self.comboBox_ap.currentData()}",
            f"ATBD {self.comboBox_bd.currentData()}",
            f"ATD1 {self.comboBox_d1.currentData()}",
            f"ATP1 {self.comboBox_p1.currentData()}"
        ]

        for cmd in cmds:
            self.ser.write(f"{cmd}\r".encode())
            time.sleep(0.1)

        self.ser.write(b'ATWR\r')
        time.sleep(0.1)
        self.ser.write(b'ATCN\r')
        self.textEdit_status.setPlainText("설정 적용 완료")
