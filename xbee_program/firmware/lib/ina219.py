class INA219:
    def __init__(self, i2c):
        self.i2c = i2c
        self.ADDR = 0x41
        self.REG_CONFIG = 0x00
        self.REG_SHUNTVOLTAGE = 0x01
        self.REG_CALIBRATION = 0x05
        
        # INA219 설정값
        self.BUS_VOLTAGE_LSB = 0.004
        self.SHUNT_VOLTAGE_LSB = 0.00001
        self.MAX_CURRENT = 0.1
        self.SHUNT_RESISTOR = 0.1
        
        # 전류 해상도 계산
        self.CURRENT_LSB = self.MAX_CURRENT / 32768
        
        # 보정값 계산
        self.CALIBRATION_VALUE = int(0.04096 / (self.CURRENT_LSB * self.SHUNT_RESISTOR))
        
        # 설정값 (BRNG=1, PGA=±40mV, BADC=12bit, SADC=12bit, MODE=7)
        self.config_value = 0x399F
        
        self._init_sensor()
    
    def _init_sensor(self):
        self.i2c.writeto_mem(self.ADDR, self.REG_CONFIG, 
                            bytearray([self.config_value >> 8, self.config_value & 0xFF]))
        self.i2c.writeto_mem(self.ADDR, self.REG_CALIBRATION, 
                            bytearray([self.CALIBRATION_VALUE >> 8, self.CALIBRATION_VALUE & 0xFF]))
    
    def read_data(self):
        return self.i2c.readfrom_mem(self.ADDR, self.REG_SHUNTVOLTAGE, 2)
