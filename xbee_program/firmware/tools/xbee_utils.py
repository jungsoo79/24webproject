import time
import serial

def enter_command_mode(ser):
    ser.write(b'+++')
    time.sleep(1.5)
    response = ser.read(ser.in_waiting)
    
    try:
        decoded = response.decode(errors='ignore')
    except Exception:
        decoded = ""

    print(f"[디버그] 명령 모드 응답: {decoded}")
    return "OK" in decoded

def send_at_command(ser, command):
    if isinstance(command, str):
        command_bytes = command.strip().encode() + b'\r'
    else:
        command_bytes = command

    ser.write(command_bytes)
    time.sleep(0.3)

    response = ser.read(ser.in_waiting)
    print(f"[디버그] {command.strip()} 응답: {response.decode(errors='ignore').strip()}")

    return b"OK" in response  # ✅ 'OK'는 바이트로 비교

def reopen_serial(ser_or_port, baudrate=115200, timeout=3):
    port = ser_or_port.port if hasattr(ser_or_port, 'port') else ser_or_port
    time.sleep(3)
    return serial.Serial(port, baudrate=baudrate, timeout=timeout)


def enter_repl(ser, retry=5):
    ser.reset_input_buffer()
    ser.flush()
    
    # 추가 대기 시간 (ATAP 4 → REPL 전환 시간 보장)
    print("[디버그] REPL 진입 전 대기 중...")
    time.sleep(3)

    for i in range(retry):
        print(f"[시도 {i+1}/{retry}] REPL 진입 시도 중...")
        ser.write(b'\r\n')
        time.sleep(1)
        ser.write(b'\x03')  # Ctrl+C
        time.sleep(1)
        ser.write(b'\r\n')
        time.sleep(1)

        response = ser.read(ser.in_waiting).decode(errors='ignore')
        print(f"[디버그] REPL 응답 확인: {response}")
        if ">>>" in response or "MicroPython" in response:
            return True
    return False

