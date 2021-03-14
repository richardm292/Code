from time import ticks_ms, ticks_diff, sleep_ms
import _thread

MAX_ITER = const(60)
pa=bytearray(81*35)    # totallseperate byte arrays for each core to minimise any um complexity
pb=bytearray(81*35)

@micropython.native
def calc_mandela(c):
    z = 0
    for i in range(MAX_ITER):
        z = z * z + c
        if abs(z) > 4:
            return i
    return MAX_ITER - 1

@micropython.native
def mandelbrot_08a(start,end):      # core0 -> pa
    global pa
    MANDEL_CHAR = (32, 46, 96, 44, 58, 59, 124, 111, 60, 62, 41, 40, 123, 125, 43, 126, 61, 45, 35, 64)
    N = len(MANDEL_CHAR)
    CM = calc_mandela
    for v in range(start,end,1):
        for u in range(81):
            n = CM((u / 30 - 2) + (v / 15 - 1) * 1j)
            pa[(v*81) + u]= MANDEL_CHAR[(MAX_ITER - n - 1)%N]

@micropython.native
def mandelbrot_08b(start,end):  # core1 -> pb
    global pb
    MANDEL_CHAR = (32, 46, 96, 44, 58, 59, 124, 111, 60, 62, 41, 40, 123, 125, 43, 126, 61, 45, 35, 64)
    N = len(MANDEL_CHAR)
    CM = calc_mandela
    for v in range(start,end,1):
        for u in range(81):
            n = CM((u / 30 - 2) + (v / 15 - 1) * 1j)
            pb[(v*81) + u]= MANDEL_CHAR[(MAX_ITER - n - 1)%N]

rows_in_parallel = 7
t1 = ticks_ms()
thread_started = False

# parallel starts------------------------------
for i in range(rows_in_parallel):  
    thread_started = False
    while not thread_started:
        try: # send a row to core1
            _thread.start_new_thread(mandelbrot_08b,(i, i+1))
            thread_started = True
            mandelbrot_08a(i+rows_in_parallel, i+rows_in_parallel+1)
            gc.collect()
        except:
            pass
# parallel ends -------------------------------

for i in range(rows_in_parallel*2,31,1):        # now do the rest on core0
    mandelbrot_08a(i,i+1)
for i in range(0,rows_in_parallel,1):           # print results from both cores.      
    print(pb[i*81: (i*81)+80].decode() )
for i in range(rows_in_parallel,31,1):
    print(pa[i*81: (i*81)+80].decode() )

t2 = ticks_ms()
print('calc time:', ticks_diff(t2, t1), 'ms')
