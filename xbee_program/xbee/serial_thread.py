from PyQt5 import QtCore
import serial
import time
from datetime import datetime, timedelta
from . import sensor
from api.db_api import send_sensor_data_batch
from database.backup_db import insert_sensor_data

class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(float, float, float, float, float, float)

    def __init__(self, ser, token=None, company_id=None):
        super().__init__()
        self.ser = ser
        self.token = token
        self.company_id = company_id
        self._running = True
        self.port_name = self.ser.port  # ✅ 포트 이름 저장

        print(f"[Init:{self.port_name}] token={repr(self.token)}")
        print(f"[Init:{self.port_name}] company_id={repr(self.company_id)}")

        if self.ser and self.ser.is_open:
            print(f"[SerialThread:{self.port_name}] 포트 연결 성공")
        else:
            print(f"[SerialThread:{self.port_name}] 시리얼 포트가 열려있지 않음")
            self._running = False

    def run(self):
        print(f"[SerialThread:{self.port_name}] run() 시작")
        if not self.ser or not self.ser.is_open:
            print(f"[SerialThread:{self.port_name}] 시리얼 포트가 열려있지 않음")
            return

        while self._running:
            try:
                data = self.ser.read(33)
                print(f"[SerialThread:{self.port_name}] 수신된 데이터 (길이 {len(data)}): {data}")

                if len(data) != 33:
                    print(f"[오류:{self.port_name}] 잘못된 패킷 길이: {len(data)}")
                    continue

                if data[0] != 0xAA:
                    print(f"[오류:{self.port_name}] 시작 바이트가 잘못됨: {data[0]}")
                    continue

                sender_high = data[1:5].hex().upper()
                sender_low = data[5:9].hex().upper()
                sender_serial = sender_high + sender_low
                print(f"[송신부 시리얼:{self.port_name}] sender_serial = {sender_serial}")
                receiver_high = data[9:13].hex().upper()
                receiver_low = data[13:17].hex().upper()
                receiver_serial = receiver_high + receiver_low
                print(f"[수신부 시리얼:{self.port_name}] receiver_serial = {receiver_serial}")

                packet_type = data[19]
                if packet_type == 0x01:
                    raw_values = {
                        "obj_temp": data[20:22],
                        "die_temp": data[22:24],
                        "roll": data[24:26],
                        "pitch": data[26:28],
                        "tilt": data[28:30],
                        "current": data[30:32],
                    }

                    obj_temp, die_temp = sensor.SensorHandler.process_TMP006(
                        raw_values["obj_temp"], raw_values["die_temp"]
                    )
                    roll, pitch, tilt = sensor.SensorHandler.process_ADXL345(
                        raw_values["roll"], raw_values["pitch"], raw_values["tilt"]
                    )
                    current = sensor.SensorHandler.process_INA219(raw_values["current"])

                    print(f"[emit:{self.port_name}] 온도={obj_temp:.2f}, 전류={current:.2f}, 틸트={tilt:.2f}")
                    self.data_received.emit(obj_temp, die_temp, roll, pitch, tilt, current)

                    print(f"[전송 준비:{self.port_name}] token={repr(self.token)}, company_id={repr(self.company_id)}, sender_serial={sender_serial}")

                    # KST 시간 생성
                    kst_now = datetime.utcnow() + timedelta(hours=9)
                    now_str = kst_now.isoformat() + "+09:00"

                    data_list = [
                        {"sensor_type": "obj_temperature", "value": obj_temp, "unit": "℃", "timestamp": now_str},
                        {"sensor_type": "die_temperature", "value": die_temp, "unit": "℃", "timestamp": now_str},
                        {"sensor_type": "roll", "value": roll, "unit": "°", "timestamp": now_str},
                        {"sensor_type": "pitch", "value": pitch, "unit": "°", "timestamp": now_str},
                        {"sensor_type": "tilt", "value": tilt, "unit": "°", "timestamp": now_str},
                        {"sensor_type": "current", "value": current, "unit": "mA", "timestamp": now_str}
                    ]

                    try:
                        if all([self.token, self.company_id, sender_serial]):
                            success = send_sensor_data_batch(
                                self.token,
                                self.company_id,
                                sender_serial,
                                data_list,
                                receiver_serial=receiver_serial
                            )

                            if success:
                                insert_sensor_data(sender_serial, receiver_serial, obj_temp, die_temp, roll, pitch, tilt, current, is_synced=1)
                                print(f"[✅ 전송 성공 + DB 저장됨:{self.port_name}]")
                            else:
                                insert_sensor_data(sender_serial, receiver_serial, obj_temp, die_temp, roll, pitch, tilt, current, is_synced=0)
                                print(f"[❌ 전송 실패 → 로컬 DB 저장됨:{self.port_name}]")
                        else:
                            print(f"[⚠️ 전송 정보 부족 → 저장만 수행:{self.port_name}]")
                            insert_sensor_data(sender_serial, receiver_serial, obj_temp, die_temp, roll, pitch, tilt, current, is_synced=0)
                    except Exception as api_err:
                        print(f"[예외 발생:{self.port_name}] API 전송 실패: {api_err}")
                        insert_sensor_data(sender_serial, receiver_serial, obj_temp, die_temp, roll, pitch, tilt, current, is_synced=0)

                elif packet_type == 0x02:
                    print(f"[SerialThread:{self.port_name}] 오류 패킷 수신")

            except serial.SerialException as e:
                print(f"[SerialThread:{self.port_name}] 시리얼 예외: {e}")
                self._running = False
            except Exception as e:
                print(f"[SerialThread:{self.port_name}] 일반 예외 발생: {e}")
                self._running = False

    def stop(self):
        self._running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                print(f"[SerialThread:{self.port_name}] 포트 닫힘")
            except Exception as e:
                print(f"[SerialThread:{self.port_name}] 포트 닫기 실패: {e}")
        self.wait()
