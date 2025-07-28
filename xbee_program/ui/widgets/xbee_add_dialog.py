import os
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets, uic, QtCore
from api.device_api import register_device, get_device_models, get_receivers
from firmware.tools.receiver_setting import apply_receiver_setting
from firmware.tools.sender_setting import apply_sender_setting

class XbeeAddDialog(QtWidgets.QDialog):
    def __init__(self, token, company_id, parent=None):
        super().__init__(parent)
        ui_path = os.path.join("ui", "forms", "xbee_add_dialog.ui")
        uic.loadUi(ui_path, self)

        self.token = token
        self.company_id = company_id
        self.connected_port = None
        self.connected_baudrate = None

        self._init_ui()
        self._bind_signals()

        self.comboBox_baudrate_add.setCurrentText("9600")
        self.update_port_list()

    def _init_ui(self):
        self.label_parent.hide()
        self.comboBox_parent.hide()
        self.label_ch.hide()
        self.lineEdit_ch.hide()
        self.label_panid.hide()
        self.lineEdit_panid.hide()
        self.load_models()

    def _bind_signals(self):
        self.comboBox_model.currentIndexChanged.connect(self.model_changed)
        self.button_refresh.clicked.connect(self.update_port_list)
        self.button_connect.clicked.connect(self.connect_device)
        self.button_disconnect.clicked.connect(self.disconnect_device)
        self.button_add.clicked.connect(self.add_device)
        self.button_cancel.clicked.connect(self.close)

    def load_models(self):
        result = get_device_models(self.token)

        if result["success"]:
            models = result["data"]

            self.comboBox_model.clear()
            for model in models:
                text = f'{model["model_name"]} ({model["role"]})'
                self.comboBox_model.addItem(text, model)
        else:
            QtWidgets.QMessageBox.warning(self, "모델 로딩 실패", result["message"])

    def model_changed(self, index):
        model_data = self.comboBox_model.itemData(index)
        if model_data and model_data["role"].strip().lower() == "receiver":
            self._set_receiver_ui()
        else:
            self._set_sender_ui()

    def _set_receiver_ui(self):
        self.label_parent.hide()
        self.comboBox_parent.hide()
        self.label_ch.show()
        self.lineEdit_ch.show()
        self.label_panid.show()
        self.lineEdit_panid.show()

    def _set_sender_ui(self):
        self.label_parent.show()
        self.comboBox_parent.show()
        self.label_ch.hide()
        self.lineEdit_ch.hide()
        self.label_panid.hide()
        self.lineEdit_panid.hide()
        self.load_receivers()

    def load_receivers(self):
        result = get_receivers(self.token)

        self.comboBox_parent.clear()
        if result["success"]:
            receivers = result["data"]  # 실제 리스트를 꺼냄
            for device in receivers:
                text = f'{device["device_name"]} ({device["serial_number"]})'
                self.comboBox_parent.addItem(text, device)
        else:
            QtWidgets.QMessageBox.warning(self, "수신부 로딩 실패", result["message"])


    def update_port_list(self):
        ports = serial.tools.list_ports.comports()
        self.comboBox_port.clear()
        for port in ports:
            self.comboBox_port.addItem(port.device)

    def connect_device(self):
        port = self.comboBox_port.currentText()
        baudrate = int(self.comboBox_baudrate_add.currentText())

        if not port:
            self.textEdit_log.append("포트를 선택하세요.")
            return

        try:
            ser = serial.Serial(port, baudrate=baudrate, timeout=3)
            self.textEdit_log.append(f"{port} 포트에 XBee 연결 완료")

            QtCore.QThread.msleep(1500)
            ser.reset_input_buffer()

            ser.write(b'+++')
            ser.flush()
            QtCore.QThread.msleep(1500)

            response = b""
            for _ in range(30):
                if ser.in_waiting:
                    response += ser.read(ser.in_waiting)
                    if b'OK' in response:
                        break
                QtCore.QThread.msleep(100)

            if b"OK" in response:
                self.textEdit_log.append("명령 모드 진입 성공")
                self.request_serial_number(ser)

                if ser and ser.is_open:
                    ser.close()
                    self.textEdit_log.append("시리얼 번호 조회 후 XBee 연결 해제 완료")

                # ✅ 저장
                self.connected_port = port
                self.connected_baudrate = baudrate
            else:
                self.textEdit_log.append(f"명령 모드 진입 실패, 수신 데이터: {response.decode(errors='ignore').strip()}")

        except Exception as e:
            self.textEdit_log.append(f"연결 실패: {e}")

    def request_serial_number(self, ser):
        try:
            ser.write(b'ATSH\r')
            QtCore.QThread.msleep(200)
            sh_raw = ser.read(ser.in_waiting).decode(errors='ignore').strip()

            ser.write(b'ATSL\r')
            QtCore.QThread.msleep(200)
            sl_raw = ser.read(ser.in_waiting).decode(errors='ignore').strip()

            if not sh_raw or not sl_raw:
                self.textEdit_log.append("시리얼 번호 읽기 실패")
                return

            sn = f"{int(sh_raw, 16):08X}{int(sl_raw, 16):08X}"
            self.lineEdit_sn.setText(sn)
            self.textEdit_log.append(f"시리얼 번호: {sn}")

        except Exception as e:
            self.textEdit_log.append(f"시리얼 번호 읽기 실패: {e}")

    def disconnect_device(self):
        self.textEdit_log.append("연결은 시리얼 번호 조회 후 자동 해제됩니다.")

    def add_device(self):
        sn = self.lineEdit_sn.text().strip()
        model_data = self.comboBox_model.itemData(self.comboBox_model.currentIndex())
        device_name = self.lineEdit_name.text().strip()
        location = self.lineEdit_location.text().strip()

        if not sn or not model_data or not device_name or not location:
            self.textEdit_log.append("필수 정보를 입력하세요.")
            return

        if not self.connected_port or not self.connected_baudrate:
            self.textEdit_log.append("먼저 XBee 연결 버튼을 눌러 시리얼 번호를 조회하세요.")
            return

        parent_sn = None
        role = model_data["role"].strip().lower()
        BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "formware")

        try:
            ser = serial.Serial(self.connected_port, baudrate=self.connected_baudrate, timeout=3)

            if role == "receiver":
                ch = self.lineEdit_ch.text().strip()
                pan_id = self.lineEdit_panid.text().strip()

                if not ch or not pan_id:
                    self.textEdit_log.append("CH 및 PAN ID를 입력하세요.")
                    return

                ser, success = apply_receiver_setting(ser, ch, pan_id)

            elif role == "sender":
                parent_data = self.comboBox_parent.itemData(self.comboBox_parent.currentIndex())
                if not parent_data:
                    self.textEdit_log.append("부모 장치를 선택하세요.")
                    return

                dh = parent_data["serial_number"][:8]
                dl = parent_data["serial_number"][8:]
                ch = parent_data.get("device_ch")
                pan_id = parent_data.get("device_id")

                if ch is None or pan_id is None:
                    self.textEdit_log.append("부모 장치의 CH 또는 PAN ID 정보가 없습니다.")
                    return

                success = apply_sender_setting(ser, ch, pan_id, dh, dl)
                parent_sn = parent_data["serial_number"]

            else:
                self.textEdit_log.append(f"알 수 없는 역할: {role}")
                return

            if not success:
                self.textEdit_log.append("XBee 설정 실패")
                return

            reg_success = register_device(
                sn,
                model_data["model_name"],
                device_name,
                parent_sn,
                location,
                self.company_id,
                self.token,
                ch=ch,
                pan_id=pan_id
            )

            if reg_success:
                self.textEdit_log.append("장치 등록 및 설정 완료")
                if ser and ser.is_open:
                    ser.close()
                self.close()
            else:
                self.textEdit_log.append("장치 등록 실패")

        except Exception as e:
            self.textEdit_log.append(f"장치 추가 중 오류 발생: {e}")
