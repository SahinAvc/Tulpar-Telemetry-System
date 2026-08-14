
import serial, time

s = serial.Serial('COM5', 57600, timeout=2)
time.sleep(1.2)
s.write(b'+++')
time.sleep(1.2)
cevap = s.read(20)
print("Cevap:", cevap)