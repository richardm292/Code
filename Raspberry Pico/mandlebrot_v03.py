from time import ticks_ms, ticks_diff
import gc
import _thread
import time

MAX_ITER = const(60)
pa=bytearray(81*31)     # byte array.
pb=bytearray(81*31)     # byte array.

@micropython.native
def calc_mandela(c):
    z = 0
    for i in range(MAX_ITER):
        z = z * z + c
        if abs(z) > 4:
            return i
    return MAX_ITER - 1


def mandelbrot_08a(start,end): 
    global pa
    MANDEL_CHAR = (' ', '.', '`', ',', ':', ';', '|', 'o', '<', '>', '(', ')', '{', '}', '+', '~', '=', '-', '#', '@')
    N = len(MANDEL_CHAR)
    CM = calc_mandela
    for v in range(start,end,1):
        for u in range(81):
            n = CM((u / 30 - 2) + (v / 15 - 1) * 1j)
            pa[u + (v*81)]= ord(MANDEL_CHAR[(MAX_ITER - n - 1)%N]) #aaaa<<<


def mandelbrot_08b(start,end):  
    global pa
    MANDEL_CHAR = (' ', '.', '`', ',', ':', ';', '|', 'o', '<', '>', '(', ')', '{', '}', '+', '~', '=', '-', '#', '@')
    N = len(MANDEL_CHAR)
    CM = calc_mandela
    for v in range(start,end,1):
        for u in range(81):
            n = CM((u / 30 - 2) + (v / 15 - 1) * 1j)
            pb[u + (v*81)]= ord(MANDEL_CHAR[(MAX_ITER - n - 1)%N])  #bbbb<<<


max_row = 6  # number of rows to process in parallel. anymore than 6 and lockups occur.
batch_size = 1 # one row at a time. >1 lockup\error 
thread_started = False

t1 = ticks_ms()
for start in range(0, max_row, batch_size):  
    thread_started = False
    while not thread_started:
        try: 
            # send a row to core1
            _thread.start_new_thread(mandelbrot_08b,(start, start + batch_size))  # rows 0 to 5 on core1
            thread_started = True
            # send a row to core0
            mandelbrot_08a(16 + start,16 + start + batch_size)   # rows 16 to 21 on core0
        except:
            pass

mandelbrot_08b(max_row,16)              # do row 6 - 16 non parallel
mandelbrot_08a(max_row+16,31)           # do row 21- 30 non parallel

for i in range(0,16,1):
    print(pb[i*81: (i*81)+80].decode() )
for i in range(16,31,1):
    print(pa[i*81: (i*81)+80].decode() )
t2 = ticks_ms()
print('calc time:', ticks_diff(t2, t1), 'ms')