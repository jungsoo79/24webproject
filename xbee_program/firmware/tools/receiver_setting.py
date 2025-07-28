import time
import serial
from api.auth_manager import AuthManager
from firmware.tools.file_manager import insert_main_files
from firmware.tools.xbee_utils import enter_command_mode, enter_repl, reopen_serial, send_at_command

def apply_receiver_setting(ser, ch, pan_id):
    try:
        if not ser or not ser.is_open:
            print("[에러] 시리얼 포트가 열려있지 않습니다.")
            return None, False

        # 명령 모드 진입
        ser.write(b'+++')
        time.sleep(2)
        response = ser.read(ser.in_waiting).decode(errors='ignore')
        print(f"[디버그] 명령 모드 응답: {response}")

        # AT 설정 적용
        at_commands = [
            f'ATCH {ch}\r'.encode(),
            f'ATID {pan_id}\r'.encode(),
            b'ATCE 1\r', b'ATPS 1\r', b'ATAP 4\r',
            b'ATBD 7\r', b'ATD1 6\r', b'ATP1 6\r', b'ATWR\r'
        ]

        for cmd in at_commands:
            ser.write(cmd)
            time.sleep(0.3)
            response = ser.read(ser.in_waiting).decode(errors='ignore')
            print(f"[디버그] {cmd.strip().decode()} 응답: {response}")

        # 시리얼 번호 추출
        ser.write(b'ATSH\r')
        time.sleep(0.3)
        high = ser.read(ser.in_waiting).decode().strip()

        ser.write(b'ATSL\r')
        time.sleep(0.3)
        low = ser.read(ser.in_waiting).decode().strip()

        serial_number = (high + low).replace('\r', '').replace('\n', '').zfill(16)
        print(f"[디버그] 시리얼 번호 추출: {serial_number}")

        # 시리얼 재열기
        port = ser.port
        ser.close()
        time.sleep(1.5)
        ser = serial.Serial(port, baudrate=115200, timeout=3)
        time.sleep(4)  # 중요: 충분한 대기 시간 확보

        # REPL 진입 시도
        if not enter_repl(ser):
            print("[에러] REPL 진입 실패")
            return ser, False

        # 파일 전송
        insert_main_files(ser, role="receiver")
        print("[완료] 수신부 설정 및 파일 전송 성공")
        return ser, True

    except Exception as e:
        print(f"[에러] 수신부 설정 실패: {e}")
        return ser, False

def enter_repl(ser, retry=5):
    ser.reset_input_buffer()
    ser.flush()
    for i in range(retry):
        print(f"[시도 {i+1}/{retry}] REPL 진입 시도 중...")
        ser.write(b'\r\n')
        time.sleep(0.5)
        ser.write(b'\x03')  # Ctrl+C
        time.sleep(1.5)
        ser.write(b'\r\n')
        time.sleep(1)

        response = ser.read(ser.in_waiting).decode(errors='ignore')
        print(f"[디버그] REPL 응답 확인: {response}")
        if ">>>" in response or "MicroPython" in response:
            return True
    return False
