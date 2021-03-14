from time import ticks_ms, ticks_diff
import gc
MAX_ITER = 60
MANDEL_CHAR = (
    ' ', '.', '`', ',', ':', ';', '|', 'o', '<', '>',
    '(', ')', '{', '}', '+', '~', '=', '-', '#', '@'
)

def run(func, param = None):
    t1 = ticks_ms()
    if param == None:
        func()
    else:
        func(param)
    t2 = ticks_ms()
    print('calc time:', ticks_diff(t2, t1), 'ms')

# @micropython.native
def calc_mandel(c):
    z = 0
    for i in range(MAX_ITER):
        z = z * z + c
        if abs(z) > 4:
            return i
    return MAX_ITER - 1

def mandelbrot():
    N = len(MANDEL_CHAR)
    p=[]
    print('')    
    for v in range(31):
        for u in range(81):
            n = calc_mandel((u / 30 - 2) + (v / 15 - 1) * 1j)
            p.append(MANDEL_CHAR[(MAX_ITER - n - 1)%N])
        print(''.join(p))
        p.clear()

while True:
    run(mandelbrot)