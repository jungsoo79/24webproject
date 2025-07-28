class ADXL345:
    def __init__(self,i2c):
        self.i2c = i2c
        self.ADDR = 0x53 #가속도센서의 i2c주소
        self.POWER_CTL_REG = 0x2D   #설정 레지스터 주소
        self.DATA_FORMAT_REG = 0x31
        self.BW_RATE_REG = 0x2C
        self.DATAX0_REG = 0x32
        self.RANGE_2_G = 0x00
        self.DATARATE_100_HZ = 0x0A

        self._init_sensor()
        
    def _init_sensor(self):
        self.i2c.writeto_mem(self.ADDR,self.POWER_CTL_REG, b'\x08')     #가속도센서 활성화

        #측정범위 설정
        current = self.i2c.readfrom_mem(self.ADDR,self.DATA_FORMAT_REG,1)[0]
        new_value = (current & ~0x0F) | self.RANGE_2_G | 0x08
        self.i2c.writeto_mem(self.ADDR,self.DATA_FORMAT_REG,bytes([new_value]))

        #데이터 속도 설정
        self.i2c.writeto_mem(self.ADDR,self.BW_RATE_REG, bytes([self.DATARATE_100_HZ & 0x0F]))

    def read_data(self):
        return self.i2c.readfrom_mem(self.ADDR,self.DATAX0_REG,6) #x,y,z 각각 2바이

