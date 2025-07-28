import machine #하드웨어 제어를 위한 micropython 모듈 활성화
import time #시간 관련 함수
import xbee #Digi XBee 모듈을 위한 통신 라이브러리
import gc #Garbage collector 제어 모듈(프로그램에서 더 이상 사용되지 않는 메모리를 자동으로 찾아서 해제)
import sys #시스템 관련 함수(시스템 종료,예외처리)
from lib.adxl345 import ADXL345 #파일의 같은 위치 lib에서 파일을 가지고 오는 함수
from lib.tmp006 import TMP006
from lib.ina219 import INA219

PACKET_TYPE = {
    'DATA' : 0x01,  #정상 데이터 패킷 -> 정확한 데이터가 전송될 때는 0x01이 전송됨
    'ERROR' : 0x02, #에러 패
    }

ERROR_TYPE = {
    'I2C' : 0x01, # I2C 오류
}

def calculate_checksum(data): #오버플로우를 방지하기 위해
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFF #1바이트 범위로 제한, 결과값이 0~255 범위 넘지 않도록 마스킹(masking)
    return checksum

#XBee MAC 주소
SERIAL_NUM = xbee.atcmd("SH") + xbee.atcmd("SL")        #송신부 시리얼 넘버 SH = 상위, SL = 하위
DESTINATION_MAC = xbee.atcmd("DH") + xbee.atcmd("DL")   #수신부 시리얼 넘버 DH = 상위, DL = 하위
DEVICE_ID = b'\x03\xE9'                                 #장치 ID :1001 (0x03E9)

#센서 초기화
i2c = machine.I2C(1, freq = 100000) #초기화
MAX_RETRIES = 11    #최대 재시도 횟수

for attempt in range(MAX_RETRIES) :
    try:
        adxl345 = ADXL345(i2c)
        tmp006  = TMP006(i2c)
        ina219 = INA219(i2c)
        break #초기화 성공 시 루프 탈출
    except Exception as e:
        if attempt < MAX_RETRIES: #마지막 시도가 아니면
            print("i2c init error: {}".format(e)) #오류 메시지 출력하고, 오류 패킷 생성 후 전송
            error_packet = bytearray()
            error_packet.append(0xAA)
            error_packet.extend(SERIAL_NUM) #시작 바이트
            error_packet.extend(DESTINATION_MAC)
            error_packet.extend(DEVICE_ID)  #시리얼 넘버
            error_packet.append(PACKET_TYPE['ERROR'])   #패킷 종류: 오류
            error_packet.append(PACKET_TYPE['I2C'])     #오류 종류: I2C 오류
            error_packet.append(calculate_checksum(error_packet))   #체크섬
            xbee.transmit(DESTINATION_MAC,error_packet)
            gc.collect() #메모리 정리
        else:
            print("init failed")
            gc.collect()
            sys.exit() #마지막 시도 실패시, 시스템 종료

print("Starting XBee Data Transmit")

#전송 카운터 초기화
transmit_count = 0

while True:
    try:
        #10초 대기
        time.sleep(10)

        sensor_data = bytearray()

        #헤더
        sensor_data.append(0xAA)        #1바이트, 시작 바이트
        sensor_data.extend(SERIAL_NUM)  #8바이트, 송신 시리얼 넘버
        sensor_data.extend(DESTINATION_MAC) #8바이트, 수신 시리얼 넘버 
        sensor_data.extend(DEVICE_ID)   #2바이트, 장치 ID
        sensor_data.append(PACKET_TYPE['DATA']) #1바이트, 패킷 종류:정상 데이터

        #데이터
        sensor_data.extend(tmp006.read_data())  #4바이트,온도
        sensor_data.extend(adxl345.read_data()) #6바이트, 가속도 
        sensor_data.extend(ina219.read_data())  #2바이트, 전류

        #체크섬
        sensor_data.append(calculate_checksum(sensor_data)) #1바이트,체크섬

        #데이터 전송
        try:
            xbee.transmit(DESTINATION_MAC, sensor_data)
            print("Data sent:{}".format(sensor_data))

            #전송 카운트 증가
            transmit_count +=1
            if transmit_count >= 10:
                machine.reset() #장치 재부팅

        except Exception as e:
            print("Transmit Failed: {}".format(e))
            
    except Exception as e:
        print("Unexpected error{}".format(e))

    finally:
        del sensor_data
        gc.collect() #메모리 정리


