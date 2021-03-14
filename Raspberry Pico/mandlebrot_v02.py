from time import ticks_ms, ticks_diff
import gc
import _thread

# previous 3340 
# 3326

MAX_ITER = const(60)
NLEN = const(20)
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

@micropython.native  # native and v07 2582 2583 2579 2593 2601 2615 
                    # native and v07 and no print  2302 2302 2301 2301 2309 2301 2301 2302 2301 2301 2309 2301 
                    # native and v05 2468 2480 2477 2476 2477 2478 2481 2482 2484 2487 
                    # native and v00 2980 3027 3071 3162 3254 3300 
                    # native and v00 and no print 2306 2313 2305 2305 2305 2312 2306 2305 2305 23013
def calc_mandel(c):
    z = 0
    for i in range(MAX_ITER):
        z = z * z + c
        if abs(z) > 4:
            return i
    return MAX_ITER - 1
def mandelbrot_08a():  
    N = len(MANDEL_CHAR)
    p=bytearray(81)     # byte array preallocated.
    C = calc_mandel     # Preload function so lookup is local.
    print('')    
    for v in range(1,31,2):
        for u in range(81):
            n = C((u / 30 - 2) + (v / 15 - 1) * 1j)
            p[u]= ord(MANDEL_CHAR[(MAX_ITER - n - 1)%N])  # N and MAX_ITER as constants
        print(p.decode()) 

def mandelbrot_08b():  
    N = len(MANDEL_CHAR)
    p=bytearray(81)     # byte array preallocated.
    C = calc_mandel     # Preload function so lookup is local.
    print('')    
    for v in range(0,31,2):
        for u in range(81):
            n = C((u / 30 - 2) + (v / 15 - 1) * 1j)
            p[u]= ord(MANDEL_CHAR[(MAX_ITER - n - 1)%N])  # N and MAX_ITER as constants
        print(p.decode())    

def mandelbrot_07(): # times: 3109 3112 3124 3132 3148 3135 3114 3118 3126 3136 3141 3162 3173 3172 3168
    p=[]
    C = calc_mandel 
    print('')    
    for v in range(31):
        for u in range(81):
            n = C((u / 30 - 2) + (v / 15 - 1) * 1j)
            p.append((MANDEL_CHAR[(MAX_ITER - n - 1)%NLEN]))
        print(''.join(p))
        p.clear()


def mandelbrot_05():  # 3191 3202 3210 3224 3231 3238 3250 3240 3221 3218 3226 3230 3243 3256 3266 3283 3286
    N = len(MANDEL_CHAR)
    p=bytearray(81)
    C = calc_mandel     # Preload function so lookup is local.
    print('')    
    for v in range(31):
        for u in range(81):
            n = C((u / 30 - 2) + (v / 15 - 1) * 1j)
            p[u]= ord(MANDEL_CHAR[(MAX_ITER - n - 1)%N])
        print(p.decode())

def mandelbrot_04():  # no print - 2878 2885 2885 2884 2877 2885 2885 2885 2885 2877 2886
                     # preload function -  2869 2875 2875 2876 2875 2876 2868 2876 2876 2876 2868 2876
    N = len(MANDEL_CHAR)
    #p=[]
    C = calc_mandel     # Preload function so lookup is local.
    print('')    
    for v in range(31):
        for u in range(81):
            n = C((u / 30 - 2) + (v / 15 - 1) * 1j)
            #p.append(MANDEL_CHAR[(MAX_ITER - n - 1)%N])
        #print(''.join(p))
        #p.clear()


def mandelbrot_03():  # 3108 3127 3137 3138 3155 3177 3179 3169 3136 3139 3151 3161 3171 3175 3193 3200 3198 3182 3166 3171 3183 3201
    N = len(MANDEL_CHAR)
    p=[]
    print('')    
    for v in range(31):
        for u in range(81):
            n = calc_mandel((u / 30 - 2) + (v / 15 - 1) * 1j)
            p.append((MANDEL_CHAR[(MAX_ITER - n - 1)%N]))
        print(''.join(p))
        p.clear()
    #gc.collect()    

def mandelbrot_02(): # 3126 3124 3138 3152 3157 3168 3161 3149 3148 3167 3173 3185 3202 3190 3172 3159 31 73 3181 3190 
    N = len(MANDEL_CHAR)
    C = calc_mandel
    p=[]
    print('')    
    for v in range(31):
        for u in range(81):
            n = C((u / 30 - 2) + (v / 15 - 1) * 1j)
            p.append(MANDEL_CHAR[(MAX_ITER - n - 1)%N])
        print(''.join(p))
        p.clear()

def mandelbrot_01():  # 3340 3300 3041 3041 3044 3037 3048 3054 3060 3067 3072 3074 3097 3103 3106 3107
    N = len(MANDEL_CHAR)
    p=[]
    print('')    
    for v in range(31):
        for u in range(81):
            n = calc_mandel((u / 30 - 2) + (v / 15 - 1) * 1j)
            p.append(MANDEL_CHAR[(MAX_ITER - n - 1)%N])
        print(''.join(p))
        p.clear()

def mandelbrot_00():
    N = len(MANDEL_CHAR)
    print('')
    for v in range(31):
        for u in range(81):
            n = calc_mandel((u / 30 - 2) + (v / 15 - 1) * 1j)
         #   print(MANDEL_CHAR[(MAX_ITER - n - 1)%N], end='')
        #print()

while True:
    _thread.start_new_thread(mandelbrot_08b)
    mandelbrot_08a