import os
import time
import struct
import math

# TMP006 상수
TMP006_B0 = -0.0000294
TMP006_B1 = -0.00000057
TMP006_B2 = 0.00000000463
TMP006_C2 = 13.4
TMP006_TREF = 298.15
TMP006_A2 = -0.00001678
TMP006_A1 = 0.00175
TMP006_S0 = 6.4  # * 10^-14

# I2C 데이터 변환 클래스
class I2CHandler:
    @staticmethod
    def readU16(data, little_endian=True):
        return int.from_bytes(data, 'little' if little_endian else 'big')

    @staticmethod
    def readS16(data, little_endian=True):
        result = I2CHandler.readU16(data, little_endian)
        return result - 65536 if result > 32767 else result

    @staticmethod
    def readS16BE(data):
        return I2CHandler.readS16(data, little_endian=False)

# 센서 데이터 해석 클래스
class SensorHandler:
    @staticmethod
    def process_TMP006(raw_obj_temp, raw_die_temp):
        try:
            raw_obj_temp = I2CHandler.readS16BE(raw_obj_temp)
            raw_die_temp = I2CHandler.readS16BE(raw_die_temp)
            Tdie = raw_die_temp >> 2
            die_temp = Tdie * 0.03125
            Vobj = raw_obj_temp * 156.25 / 1e9
            Tdie = Tdie * 0.03125 + 273.14
            Tdie_ref = Tdie - TMP006_TREF
            S = (1.0 + TMP006_A1*Tdie_ref + TMP006_A2*Tdie_ref**2) * TMP006_S0 / 1e14
            Vos = TMP006_B0 + TMP006_B1*Tdie_ref + TMP006_B2*Tdie_ref**2
            fVobj = (Vobj - Vos) + TMP006_C2 * (Vobj - Vos)**2
            Tobj = math.sqrt(math.sqrt(Tdie**4 + fVobj/S))
            obj_temp = Tobj - 273.15
            return round(obj_temp, 4), round(die_temp, 4)
        except Exception as e:
            print(f"TEMP006 계산 오류: {e}")
            return 0.0, 0.0

    @staticmethod
    def process_INA219(raw_current):
        raw_value = struct.unpack(">h", raw_current)[0] * 0.1
        return round(raw_value, 2)

    @staticmethod
    def process_ADXL345(raw_x, raw_y, raw_z):
        ax = struct.unpack('<h', raw_x)[0]
        ay = struct.unpack('<h', raw_y)[0]
        az = struct.unpack('<h', raw_z)[0]
        roll = math.degrees(math.atan2(ax, math.sqrt(ay**2 + az**2)))
        pitch = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
        tilt = math.degrees(math.atan2(az, math.sqrt(ax**2 + ay**2)))
        return round(roll, 4), round(pitch, 4), round(tilt, 4)

