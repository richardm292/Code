from machine import Pin, ADC, I2C, PWM#, WDT
import machine
import time
import math
import random
import gc
# no timers 
# no threads
# no core1

COMMS_ACTIVE = const(1)   # turn on/off the I2C comms. 
DEBUG_ACTIVE = const(1)   # 1 second print message of Debug count.
PRINT_ACTIVE = const(0)   # turn off printing of some messages
CONVERSION33 = 3.3/65535  # conversion for 3.3 volts and unsigned 16.
Debug_Count = 0           # Count in main loop. gives an idea of spare capacity.
Message_String = []       # IC2 message to be sent from this central to the peripherals
thread_please_exit = 0    
# globals for data tfer
xv=0
xva=0
yv=0
yva=0
zv=0
zva=0

#-- Pins -------------------
tilt_switch = Pin(0, Pin.IN, Pin.PULL_UP)
# Servo motors tbd
#servo1 = Servo(8,1200,8100,1,179)  # blue server 1200 - 8100 ( from the dfrobot kit)
#servo2 = Servo(9,1700,8100,1,179)  # balck servo 1700 - 8100 ( from the sparkfun kit)
# UI buttons
yel_button = Pin(1, Pin.IN ,Pin.PULL_UP)
gre_button = Pin(2, Pin.IN ,Pin.PULL_UP)
blu_button = Pin(3, Pin.IN ,Pin.PULL_UP)
red_button = Pin(4, Pin.IN ,Pin.PULL_UP)
spare_button1 = Pin(5, Pin.IN ,Pin.PULL_UP)
spare_button2 = Pin(6, Pin.IN ,Pin.PULL_UP)
# pins 9..14 3xHC-S04
#x = HCSR04(trigger_pin=10, echo_pin=9)
#y = HCSR04(trigger_pin=12, echo_pin=11)
#z = HCSR04(trigger_pin=14, echo_pin=13)
break_button = Pin(15, Pin.IN ,Pin.PULL_UP)   # Break button used to exit main loop
# GPIO16
# GPIO17
i2c = I2C(1,scl=Pin(19),sda=Pin(18),freq=400000)     # I2C1
# Motor pins (the shaker)
#motora1=Pin(19,Pin.OUT)   # to motor controllor to set direction
#motora2=Pin(20,Pin.OUT)   # to motor controllor to set direction
#shaker=PWM(Pin(21))       # to motor controllor to set rpm
led = Pin(25, Pin.OUT)    # Pico hardwired
pot1 = ADC(0)             # GPPIO26 potentiometer 1
pot2 = ADC(1)             # GPPIO27 potentiometer 2 
# available ADC(2) GPPIO28
volt = ADC(3)             # Pico hardwired 
temp = ADC(4)             # Pico hardwired

# UI control values array.
YELLOW_BUTTON = const(0)
GREEN_BUTTON = const(1)
BLUE_BUTTON = const(2)
RED_BUTTON = const(3)
A_POT = const(4)
B_POT = const(5)
VOLTS = const(6)
TEMPERATURE = const(7)
SPARE_BUTTON1 = const(8)
SPARE_BUTTON2 = const(9)
BREAK_BUTTON = const(10)
TILT_SWITCH = const(11)
SR0401 = const(12)
SR0402 = const(13)
SR0403 = const(14)
ctl=[] # u16
for I in range(15):
  ctl.append(0)
ctl[BREAK_BUTTON] = 1   # set to 1 so main loop can be a simple while check.

# staging variables & initialise. 
peripheral_list = i2c.scan()    # scan for devices on start up.
# ----- start of classes  ---------------

class HCSR04:
    # class variables
    SAMPLES_COUNT = const(3)    # use this many samples when calculating average.
    DATA_SIZE = const(10)       # size of cicular data store of measurments
    TIMEOUT = const(3000)       # ignore things further than this.  
 
    def __init__(self, trigger_pin, echo_pin):
        self.trigger_pin = Pin(trigger_pin, Pin.OUT )
        self.echo_pin = Pin(echo_pin,Pin.IN, Pin.PULL_UP)
        self._measurement_array=[]  # circular data store. storing mm
        for i in range(HCSR04.DATA_SIZE):
            self._measurement_array.append(0)
        self._data_index = 0                  # current/latest measurement index
        self.v=0
        self.va=0

    def __set_value(self,val,vala):
            self.v = val
            self.va = vala

    def __add_measurement(self,measurement):
        self._data_index  = int((self._data_index  + 1) % HCSR04.DATA_SIZE)
        self._measurement_array[self._data_index] = measurement  # add into circular data cache
        new_avg = 0                       
        for i in range(0, SAMPLES_COUNT,1):  
            new_avg = new_avg + self._measurement_array[((self._data_index - i) + HCSR04.DATA_SIZE ) % HCSR04.DATA_SIZE ]
        new_avg = int(new_avg / HCSR04.SAMPLES_COUNT)
        self.__set_value(measurement,new_avg)

    def single_measurement(self):
        self.trigger_pin.high()
        time.sleep_us(10)
        self.trigger_pin.low()
        echotime = machine.time_pulse_us(self.echo_pin, 1, HCSR04.TIMEOUT)
        if echotime < 0:
            echotime = 0
        self.__add_measurement( (int( 10 * (echotime) * 0.0343 ) ) )

    def get_value(self):
        return self.v

    def get_value_averaged(self):
        return self.va     

# end of classs HCSR04 ------------------


# ----- start of functions --------------

def PinToCelsuis(p):
  reading = p * CONVERSION33
  temperature_in_c = 37 - (reading - 0.706)/0.001721
  return temperature_in_c

def PinToVolts(p):
  volts = p * CONVERSION33
  return volts

def free(full=False):
  gc.collect()
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

def PerformScan(): # catch error silently
    global peripheral_list
    try:
      peripheral_list = i2c.scan()
    except:
      pass

def CommsSend():   
    global Message_String, CommsSendFlag, peripheral_list
    CommsSendFlag=False
    if len(Message_String) > 0:               # any messages to send. Quick exit most of the time.   
      if PRINT_ACTIVE:
        print(Message_String,end='')
      if COMMS_ACTIVE:                            # the comms message string is always built. Turning it off just stops the printing and sending. 
        comms_error = False
        if len(peripheral_list) == 0:
          PerformScan()
        for i in peripheral_list:
          try:
            i2c.writevto(i,Message_String)
          except:
            comms_error = True 
            if PRINT_ACTIVE:
              print("error transmitting")
      if comms_error:
        PerformScan()
      Message_String.clear()                # empty the list for new messages.
      led.toggle()

# UI functions.
def checkbutton(old, new, label):
    global Message_String 
    # has button changed
    if old != new:
        Message_String.append(label)
        Message_String.append(str(new)) # add to I2C message string
        return new
    return old

def checkpot(old, new, label):
    global Message_String 
    # potentiometer broken up into intervals 
    if (int(new/60) != int(old/60) and (abs(new-old)>5000)):  # lots of bounce and wobble in these pots so big intervals like 5000.
        Message_String.append(label)
        Message_String.append(str(new))   # add to I2c message string
        return new
    return old

# UI Timer
def UISweep():
    global xva, yva, zva
    # push current values into the controls array. Call functions to add any values to I2C message.
    ctl[YELLOW_BUTTON] = checkbutton(ctl[YELLOW_BUTTON], yel_button.value(), "ye")
    ctl[GREEN_BUTTON] = checkbutton(ctl[GREEN_BUTTON], gre_button.value(), "gr")
    ctl[BLUE_BUTTON] = checkbutton(ctl[BLUE_BUTTON], blu_button.value(), "bl")
    ctl[RED_BUTTON] = checkbutton(ctl[RED_BUTTON], red_button.value(), "re")
    ctl[A_POT] = checkpot(ctl[A_POT], pot1.read_u16(), "PA")
    ctl[B_POT] = checkpot(ctl[B_POT], pot2.read_u16(), "PB")
    ctl[VOLTS] = volt.read_u16()
    ctl[TEMPERATURE] = temp.read_u16()
    ctl[SPARE_BUTTON1] = checkbutton(ctl[SPARE_BUTTON1], (spare_button1.value()), "Spare1")
    ctl[SPARE_BUTTON2] = checkbutton(ctl[SPARE_BUTTON2], (spare_button2.value()), "Spare2")
    ctl[BREAK_BUTTON] = break_button.value() 
    ctl[TILT_SWITCH] = checkbutton(ctl[TILT_SWITCH], (tilt_switch.value()), "Tilt")
    ctl[SR0401] = checkbutton(ctl[SR0401], xva, "X") 
    ctl[SR0402] = checkbutton(ctl[SR0402], yva, "Y") 
    ctl[SR0403] = checkbutton(ctl[SR0403], zva, "Z") 

def ServoTick(t):
  global servo1, servo2
  #servo1.move_to(int(ctl[A_POT]/365),0)
  #servo2.move_to(int(ctl[B_POT]/365),0)

def MotorTick(t):
  global shaker, ctl                # set motor shake if buttons are pressed or something is in front of the HC-SR04
  if 1 ^ ctl[YELLOW_BUTTON] == 1:   # XOR with 1 to flip 0 <-> 1 and vica versa
    shaker.duty_u16(12000)
  elif 1 ^ ctl[GREEN_BUTTON] == 1:  # fast  
    shaker.duty_u16(19000)
  elif 1 ^ ctl[BLUE_BUTTON] == 1:   # faster
    shaker.duty_u16(24000)
  elif 1 ^ ctl[RED_BUTTON] == 1:    # fastest
    shaker.duty_u16(60000)
  elif ctl[DISTANCE1] < 1000:       # less than a meter from echo so set speed depending on closeness
    shaker.duty_u16(65535 - int((ctl[DISTANCE1]*30)))
  else:
    shaker.duty_u16(0)              # no shake for you

def Debug():
  global ctl, Debug_Count
  if DEBUG_ACTIVE:      # flash the LED and print semi interesting stuff.
    led.toggle()
    gc.collect
    if PRINT_ACTIVE:
      print("Debug count = ", Debug_Count,"Temp=", PinToCelsuis(ctl[TEMPERATURE]), "Volt=", PinToVolts(ctl[VOLTS]), free(True))
  Debug_Count = 0

# ----- end of functions ------------------------
# ----- HCSR04 -----------------------
HCSRO4id = 0
x = HCSR04(trigger_pin=9, echo_pin=12)
y = HCSR04(trigger_pin=10, echo_pin=13)
z = HCSR04(trigger_pin=11, echo_pin=14) 

def HCSR04Collect(index):
    global thread_please_exit, xva, yva, zva, xv, yv, zv, x, y, z
    if index == 0:
      x.single_measurement()
      xv = x.get_value()
      xva = x.get_value_averaged()

    if index == 1:
      y.single_measurement()
      yv = y.get_value()
      yva = y.get_value_averaged()

    if index ==2:
      z.single_measurement()
      zv = z.get_value()
      zva = z.get_value_averaged()

# main loop here ------------
# manual timer set up
HSC04_INTERVAL = const(60000)           # 60 ms between echos
COMMS_INTERVAL = const(60000)           # faster than UI to ensure buffer is cleared
UI_INTERVAL = const(70000)              # 15 times/sec for a good feel. 
DEBUG_INTERVAL = const(2_000_000)       # show a count every n seconds - gives an idea of spare cpu cycles
HCS04Start = time.ticks_us()
CommsStart = time.ticks_us()
UIStart = time.ticks_us()
DebugStart = time.ticks_us()

#wdt=machine.WDT(timeout=10000)

if PRINT_ACTIVE:  
  print('Starting...terminate with break button or Ctl+C.')

while ctl[BREAK_BUTTON]:
  Debug_Count += 1

  if time.ticks_diff(time.ticks_us(),HCS04Start) >= HSC04_INTERVAL:
    HCSRO4id = (HCSRO4id + 1 ) % 3      # do the next of three bands of sensors
    HCSR04Collect(HCSRO4id)             # ping and store for averaging
    HCS04Start = time.ticks_us()

  if time.ticks_diff(time.ticks_us(),UIStart) >= UI_INTERVAL:
    UISweep()                           # sweep pots, buttons, tilts, temp, volts, kitchen sink
    UIStart = time.ticks_us()

  if time.ticks_diff(time.ticks_us(),CommsStart) >= COMMS_INTERVAL:
    CommsSend()                         # send ui commands via I2c to the 5v arduino with the lcd
    CommsStart = time.ticks_us()

  if time.ticks_diff(time.ticks_us(),DebugStart) >= DEBUG_INTERVAL:
    Debug()                             # how many loops, memfree, and flash led.
   # wdt.feed()
    DebugStart = time.ticks_us()

# finish up -----------------
thread_please_exit = 1 
if PRINT_ACTIVE:
  print('Finishing...')
if PRINT_ACTIVE:
  print('Done.')