# Read HC-SR04 trigger and responses. 
# 1. as timers. done
# 2. as timer + interrupts. done
# 3. as pio + interrupt. done 
# 4. as all pio  - done.
# 5. as pio into dma this app
# 6. as a python class with pio

# 1 second (s) = 1000 milliseconds (ms).  1 millsecond(ms) = 1000 microseconds (us).  1 second(s) = 1_000_000 microseconds(us)

from rp2 import PIO, StateMachine, asm_pio
from machine import Pin
import time
import rp2_util

# Richard Marris
# Feb 2021 
# 3 x HC-SR04 trigger and echo response.
Trigger_Pin1 = Pin(9,Pin.OUT)
Trigger_Pin2 = Pin(10,Pin.OUT)
Trigger_Pin3 = Pin(11,Pin.OUT)
Echo_Pin1 = Pin(12, Pin.IN, Pin.PULL_UP)
Echo_Pin2 = Pin(13, Pin.IN, Pin.PULL_UP)
Echo_Pin3 = Pin(14, Pin.IN, Pin.PULL_UP)
irq_flags = 0

# IRQs from PIO -----------------------------------------------
#                           IRQ 0..3 can go back to micropython
#                           IRQ 4..7 betweeen state machines.
# IRQ use in this app:
# 0 not used
# 1 Rasied by sm1. Value ready for get by micropython.
# 2 Rasied by sm2. Value ready for get by micropython. 
# 3 Rasied by sm3. Value ready for get by micropython.
# 4 not used
# 5 Raised by sm0. 60ms gap has passed sm1 can continue. Cleared by sm1.
# 6 Raised by sm0. 60ms gap has passed sm2 can continue. Cleared by sm2.
# 7 Raised by sm0. 60ms gap has passed sm3 can continue. Cleared by sm3.

def set_irq_flags(q):
    global irq_flags
    irq_flags = irq_flags | q.irq().flags()     # update any flag bits.

#---------------------------State Machine 0 - set a interrupt every 60ms
@asm_pio()
def sm_irq_60():
    irq(5)              # raise irq 5 (for state machine 1)
    mov(x,y)            # y holds the delay value
    label("delay1")
    jmp(x_dec,"delay1") # delay until x is below zero
    irq(6)              # raise irq 6 (for state machine 2)
    mov(x,y)            # y holds the delay value
    label("delay2")
    jmp(x_dec,"delay2") # delay until x is below zero
    irq(7)              # raise irq 7 (for state machine 3)
    mov(x,y)            # y holds the delay value
    label("delay3")
    jmp(x_dec,"delay3") # delay until x is below zero

#--------------------------- State MacMachine 1,2 & 3 - set pulse trigger and wait for result
@asm_pio(set_init=(PIO.OUT_LOW))
def sm_echo(autopush=True):
    wait(1,irq, int('0b10100') )    # wait till irq(4 + state machine number) is raised, clear it and keep going
    set(pins,1)     [9]     # use a bit mask to turn on pins. ie start the trigger 
    mov(x,y)                # reset x from y
    set(pins,0)             # use a bit mask to turn off the pins. ie stop the trigger 10us later
    wait(1,pin,0)           # wait for a 1 on pin(in_base + 0)
    label("loop1")
    jmp(x_dec,"next1")      # decrement x and keep looping
    jmp("fin1")             # x is below 0 we have timed out.
    label("next1")          # 
    jmp(pin,"loop1")        # keep looping until the jmp_pin goes to 0
    label("fin1")
    mov(isr,x)              # ISR <-- x. 
    irq(int('0b10000'))     # raise irq(0 + state machine number) back to micropython
    push()                  # RX_FIFO <-- ISR and wait till it has been got by micropython


# --set up state machines
f = 1_000_000               # MBAUD for easy calculation

sm0 = StateMachine(0, sm_irq_60, freq=f)
sm0.put(60_000 - 4)         # 60ms and 4 instructions betwwn each interrupt.
sm0.exec("pull()")          # send value to osr
sm0.exec("mov(y,osr)")      # move into Y <-- OSR

sm1 = StateMachine(1, sm_echo, freq=f, set_base=Trigger_Pin1, jmp_pin=Echo_Pin1, in_base=Echo_Pin1)
sm2 = StateMachine(2, sm_echo, freq=f, set_base=Trigger_Pin2, jmp_pin=Echo_Pin2, in_base=Echo_Pin2)
sm3 = StateMachine(3, sm_echo, freq=f, set_base=Trigger_Pin3, jmp_pin=Echo_Pin3, in_base=Echo_Pin3)
# Set an intial value - the echo response timeout figure.
y = int(f/10)               # Timeout on echo length. 
sm1.put(y)                  # put into TX_FIFO
sm1.exec("pull()")          # pull into OSR <-- TX_FIFO
sm1.exec("mov(y,osr)")      # move in scratch register y <-- OSR
sm2.put(y)                  # put into TX_FIFO
sm2.exec("pull()")          # pull into OSR <-- TX_FIFO
sm2.exec("mov(y,osr)")      # move in scratch register y <-- OSR
sm3.put(y)                  # put into TX_FIFO
sm3.exec("pull()")          # pull into OSR <-- TX_FIFO
sm3.exec("mov(y,osr)")      # move in scratch register y <-- OSR

rp2.PIO(0).irq(set_irq_flags)   #link to PIO interrupts

sm1.active(1)               # start x
sm2.active(1)               # start y
sm3.active(1)               # start z
sm0.active(1)               # start timer

SIZE_OF_RING_BUFFER = 64
NUMBER_OF_READINGS = 600    

readings1=bytearray(100*4)
readings2=bytearray(100*4)
readings3=bytearray(100*4)

rp2_util.sm_dma_get(0, 1, readings1, NUMBER_OF_READINGS )  # DMA channel, state machine, buffer, how many
rp2_util.sm_dma_get(1, 2, readings2, NUMBER_OF_READINGS )
rp2_util.sm_dma_get(2, 3, readings3, NUMBER_OF_READINGS )

while True:                 # print the raw values. ( haven't bothered to convert to mm)

    if rp2_util.dma_transfer_count(0) == 0:
           pass
           # print("11111",readings1)
            
         #   rp2_util.sm_dma_get(0, 1, readings1, len(readings1) )
    #if rp2_util.dma_transfer_count(1) == 0:
    #        print("22222",readings2)
            
    #if rp2_util.dma_transfer_count(2) == 0:
    #        print("33333",readings3)
    
    if irq_flags & (1 << 9):                # 9th bit is set.
        irq_flags = irq_flags ^ (1 << 9)    # clear the 9th bit.
        #print( rp2_util.dma_transfer_count(0), rp2_util.dma_write_addr(0), rp2_util.dma_read_addr(0) )
        print( int.from_bytes(readings1[1:4],'little') , int.from_bytes(readings1[5:8],'little') , int.from_bytes(readings1[9:12],'little'), int.from_bytes(readings1[13:16],'little'))
        #print( avg1/3 )

    if irq_flags & (1 << 10):
        irq_flags = irq_flags ^ (1 << 10)
        #print( rp2_util.dma_transfer_count(1), rp2_util.dma_write_addr(1), rp2_util.dma_read_addr(1) )
        #print(" y=",y-sm2.get(), end='' )

    if irq_flags & (1 << 11):
        irq_flags = irq_flags ^ (1 << 11)
        #print( rp2_util.dma_transfer_count(2), rp2_util.dma_write_addr(2), rp2_util.dma_read_addr(2) )
        #print(" z=",y-sm3.get() )