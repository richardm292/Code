# Read HC-SR04 trigger and responses. 
# 1. as timers. done
# 2. as timer + interrupts. done
# 3. as pio + interrupt. done 
# 4. as all pio
# 5. as pio into dma to keep previous 5 values available
# 6. as a python class

# 1 second (s) = 1000 milliseconds (ms).  1 millsecond(ms) = 1000 microseconds (us).  1 second(s) = 1_000_000 microseconds(us)

from rp2 import PIO, StateMachine, asm_pio
from machine import Pin
import time
# HC-SR04 trigger and reply.  Run continually and keep last 5 results.

Trigger_Pin = Pin(10,Pin.OUT)
Echo_Pin = Pin(9, Pin.IN, Pin.PULL_UP)
red_button = Pin(13, Pin.IN ,Pin.PULL_UP)

@asm_pio(set_init=PIO.OUT_LOW )
def sm_echo():
    set(pins,1)     [10]         # start the trigger, delay 10us
    set(pins,0)

    wait(1,gpio,9)

    mov(x,y)
    jmp (x_dec, "loop")

    label("loop")
    jmp(x_dec,"next")
    jmp("fin")
    label("next")
    jmp(pins,"loop")

    label("fin")
    mov(isr,x)              # ISR <-- x. 
    push()                  # RX_FIFO <-- ISR

f = 125_000_000               # MBAUD  in theory this should equal a second
y = 125_000_0

sm1 = StateMachine(1,        \
    sm_echo,                 \
    set_base=Trigger_Pin)

# Set an intial value the echo response period.
sm1.put(y)                  # put into TX_FIFO
sm1.exec("pull()")          # pulls from TX_FIFO --> OSR
sm1.exec("mov(y,osr)")      # moves OSR --> y scratch register
time.sleep_us(18)
sm1.active(1)

#for i in range(10):
print("wiaitnig")
while True:
    # get() the number of clicks remaining. Zero means no echo found. 
    print(time.ticks_us() ,"==================>", sm1.get())
    #time.sleep(0.060)     # recommended 60ms between trigger cycles.
