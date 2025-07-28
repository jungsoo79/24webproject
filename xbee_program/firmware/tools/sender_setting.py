import time
import serial
from firmware.tools.file_manager import insert_main_files
from firmware.tools.xbee_utils import enter_command_mode, enter_repl, reopen_serial, send_at_command

def apply_sender_setting(ser, ch, pan_id, dh, dl):
    try:
        if not ser or not ser.is_open:
            print("[에러] 시리얼 포트가 열려있지 않습니다.")
            return False

        # 명령 모드 진입
        if not enter_command_mode(ser):
            print("[에러] 명령 모드 진입 실패")
            return False

        # AT 명령 설정
        commands = [
            f'ATCH {ch}',
            f'ATID {pan_id}',
            'ATCE 0',
            'ATPS 1',
            'ATAP 4',
            'ATBD 7',
            'ATD1 6',
            'ATP1 6',
            f'ATDH {dh}',
            f'ATDL {dl}',
            'ATWR'
        ]

        for cmd in commands:
            send_at_command(ser, cmd)

        # 시리얼 번호 확인
        ser.write(b'ATSH\r')
        time.sleep(0.2)
        high = ser.read(ser.in_waiting).decode(errors='ignore').strip().zfill(8)

        ser.write(b'ATSL\r')
        time.sleep(0.2)
        low = ser.read(ser.in_waiting).decode(errors='ignore').strip().zfill(8)

        serial_number = high + low
        print(f"[디버그] 시리얼 번호 추출: {serial_number}")

        if ser and ser.is_open:
            ser.close()
            print("[디버그] 포트 닫기 완료")
        time.sleep(1.5)

        # ✅ 포트 재열기 후 REPL 진입
        ser = reopen_serial(ser.port)
        print(f"[디버그] 포트 재연결 완료: {ser.port}")

        if not enter_repl(ser):
            print("[에러] REPL 진입 실패")
            return False
        # 파일 전송
        insert_main_files(ser, role="sender")

        print("[완료] 송신부 설정 및 파일 전송 성공")
        return True

    except Exception as e:
        print(f"[에러] 송신부 설정 실패: {e}")
        return False
