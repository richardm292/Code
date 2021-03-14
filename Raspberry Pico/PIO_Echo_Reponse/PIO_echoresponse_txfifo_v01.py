# Read HC-SR04 trigger and responses. 
# 1. as timers. done
# 2. as timer + interrupts. done
# 3. as pio + interrupt. done 
# 4. as all pio
# 5. as pio into dma to keep previous 5 values available
# 6. as a python class

# 1 second (s) = 1000 milliseconds (ms).  1 millsecond(ms) = 1000 microseconds (us)

from rp2 import PIO, StateMachine, asm_pio
from machine import Pin
import time
# HC-SR04 trigger and reply.  Run continually and keep last 5 results.

Echo_Trigger = Pin(9, Pin.OUT)
Echo_Response = Pin(12, Pin.IN, Pin.PULL_UP)

#red_button = Pin(13, Pin.IN ,Pin.PULL_UP)
#yellow_button = Pin(10, Pin.IN ,Pin.PULL_UP)
@asm_pio( out_init=PIO.IN_LOW, sideset_init=PIO.OUT_LOW)
def sm_echo():
                            # y scratch register holds the max number of cycles to wait for the echo.
    nop()        .side(0)   # set trigger pin low wait for 7 clicks for stability
    nop()    [7] .side(1)   # set trigger pin high
    nop()    [3]            # leave it on for 10us (7 + 3) to trigger the echo pulse
    nop()        .side(0)   
    mov(x,y)                # x loop counter set to y
    wait(1,pin,1)          # wait for echo duty cycle start
                            # loop till echo duty cycle end or x gets to 0.
    label("waiting")     
    jmp(pin,"stillone")     # pin is still 1 so skip to not not done
    jmp("done")             # pin has gone to 0 so jump to done
    label("stillone")
    jmp(x_dec,"waiting")    # loop again x--. each loop is two cycles
                            # if x is zero then we have timed out and shoudl continue
    label("done")
    mov(isr,x)              # ISR <-- x. 
    push()                  # RX_FIFO <-- ISR

f = 1_000_000  *1           # MBAUD  in theory this should equal a second
y = 10000

sm1 = StateMachine(1, sm_echo, freq=f,in_base=Echo_Response,  sideset_base=Echo_Trigger, jmp_pin=Echo_Response)

# Set an intial value the echo response period.
#y=int(1_048_576/3)          # freq / ops 
sm1.put(y)                  # put into TX_FIFO
sm1.exec("pull()")          # pulls from TX_FIFO --> OSR
sm1.exec("mov(y,osr)")      # moves OSR --> y scratch register
sm1.active(1)

while True:
    # get() the number of clicks remaining. Zero means no echo found. 
    _=Echo_Response.value()
    #if _ ==1:
    print(time.ticks_us() ,"==================>", y-sm1.get(),_)
    time.sleep(.06)     # recommended 60ms between trigger cycles.
