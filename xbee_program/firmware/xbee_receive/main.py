import xbee
import sys
import gc

xb = xbee.XBee()
print("Starting XBee Data Receiver...")

with xb.wake_lock:
    while True:
        try:
            data_received = xbee.receive()

            if data_received:
                sensor_data = data_received['payload']  #Payload 부분 사용
                sys.stdout.buffer.write(sensor_data) #데이터 그대로 PC로 전송
                
        except Exception as e:
            print("Receive Failed: {}".format(e))
        
        finally:
            gc.collect()