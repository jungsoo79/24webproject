class TMP006:
    def __init__(self,i2c):
        self.i2c = i2c
        self.ADDR = 0x40 #TMP006센서의 i2c주소
        self.CONFING_REG = 0x02 #설정 레지스터 주소
        self.OBJ_REG = 0x00     #IR센서 데이터 레지스터(객체 온도)
        self.DIE_REG = 0x01     #다이(센서 자체) 온도 레지스터
        self.CONFING_VALUE =bytearray([0x74,0x00])  #설정 값(설정 레지스터 모드를 지정)

        self._init_sensor()

    def _init_sensor(self):
        self.i2c.writeto_mem(self.ADDR,self.CONFING_REG,self.CONFING_VALUE)
        #I2C를 통해 설정 값 전송

    def read_data(self):
        temp_obj_raw = self.i2c.readfrom_mem(self.ADDR,self.OBJ_REG,2)
        temp_die_raw = self.i2c.readfrom_mem(self.ADDR,self.DIE_REG,2)
        return temp_obj_raw + temp_die_raw 
