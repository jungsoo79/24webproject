import os
import time

def insert_main_files(ser, role, main_dir=None, lib_dir=None):
    """
    XBee에 main.py 및 lib 파일 삽입
    - sender: main.py + lib/*.py 전송
    - receiver: main.py만 전송
    """
    # 기본 경로 설정
    if not main_dir:
        if role == "sender":
            main_dir = r"C:\Users\park2\workspace\jungsoo\xbee_program\firmware\xbee_send"
        elif role == "receiver":
            main_dir = r"C:\Users\park2\workspace\jungsoo\xbee_program\firmware\xbee_receive"
        else:
            raise ValueError("main_dir 또는 role(sender/receiver) 중 하나는 지정되어야 합니다.")
    main_file = os.path.join(main_dir, "main.py")

    if not lib_dir:
        lib_dir = r"C:\Users\park2\workspace\jungsoo\xbee_program\firmware\lib"
    lib_files = ["adxl345.py", "ina219.py", "tmp006.py"]

    try:
        # Paste 모드 진입 테스트
        enter_paste_mode(ser)
        send_text(ser, 'print("TEST")')
        exit_paste_mode(ser)
        time.sleep(0.5)

        # main.py 전송
        if not os.path.exists(main_file):
            raise Exception(f"main.py 파일을 찾을 수 없습니다: {main_file}")
        print(f"main.py 전송 시작: {main_file}")
        write_file_to_xbee(ser, main_file, "/flash/main.py")

        # sender일 경우만 lib 전송 수행
        if role == "sender":
            # /flash/lib 생성
            make_lib_directory(ser)

            # lib 파일 전송
            for lib_name in lib_files:
                full_path = os.path.join(lib_dir, lib_name)
                if not os.path.exists(full_path):
                    print(f"{lib_name} 파일이 없습니다, 건너뜀")
                    continue
                print(f"lib 파일 전송: {lib_name}")
                write_file_to_xbee(ser, full_path, f"/flash/lib/{lib_name}")

        print("전체 전송 완료")

    except Exception as e:
        raise Exception(f"파일 전송 중 오류: {e}")

def enter_paste_mode(ser):
    ser.write(b'\r\n')
    time.sleep(0.5)
    ser.write(b'\x03')  # Ctrl+C
    time.sleep(0.5)
    ser.write(b'\x05')  # Ctrl+E
    time.sleep(0.5)

def exit_paste_mode(ser):
    ser.write(b'\x04')  # Ctrl+D

def send_text(ser, text):
    ser.write(f'{text}\n'.encode())

def write_file_to_xbee(ser, local_path, xbee_path):
    enter_paste_mode(ser)
    send_text(ser, f'f = open("{xbee_path}", "w")')

    with open(local_path, "r", encoding="utf-8") as f:
        for line in f:
            safe_line = line.rstrip('\n').replace('"', '\\"')
            send_text(ser, f'f.write("{safe_line}\\n")')

    send_text(ser, "f.close()")
    exit_paste_mode(ser)
    time.sleep(0.5)

def make_lib_directory(ser):
    enter_paste_mode(ser)
    send_text(ser, "import os")
    send_text(ser, "try:")
    send_text(ser, "    os.mkdir('/flash/lib')")
    send_text(ser, "except:")
    send_text(ser, "    pass")
    exit_paste_mode(ser)
    time.sleep(0.5)
