# PIO Notes 

"...there are four pin groups ... "

# Base + Count Pin Groups
There are 4 "Base"+"Count" pin groups.
-    Set Base + Set Count
-    Sideset Base + Sideset Count
-    Out Base + Out Index
-    In Base + In Index

Counts are offsets from the base. A base of 5 and count of 3 covers pins 5,6,7. 

Pins can then set in one go using a bit mask. Eg ```set(PINS,6)``` will set two pins on and one pin off. Seeing it in binary ```set(PINS,int('0b110'))``` shows the pins will be set as such:

    
    110 masks to:
       PIN7 -> 1    (Base pin + 2 gets the leftmost bit)
       PIN6 -> 1    (Base pin + 1 gets the middle bit)
       PIN5 -> 0    (Base pin + 0 gets the rightmost bit)

# How to set  Base and Count.

|Parameter | Valid Values | Initialising example  | Desc
|----------|:--------------:|:-------------|----
|Set Base | Pin 1..32 | ```StateMachine (sm_id, pwm_prog, set_base=Pin(2))``` | "Set Base" will be pin 2.
|Set Count | 1..5 |  ```@asm_pio(set_init=(PIO.OUT_LOW, PIO.OUT_HIGH, PIO.OUT_LOW ))``` |"Set Count" will be 3. It is the number of pins passed to set_init.
|Side Set Base | Pin 1..32 | ```StateMachine (sm_id, pwm_prog, sideset_base=Pin(5))``` | "Side Set Base" will be pin 5.
|Side Set Count | 1..5 |  ```@asm_pio(sideset_init=(PIO.OUT_LOW,) * 4 )``` |"Side Set Count" will be 4. It is the number of pins passed to sideset_init.
|Out Base | Pin 1..32 | ```StateMachine (sm_id, pwm_prog, out_base=Pin(8))```|"Out Base" will be pin 8.
|Out Index | 1..32 | NA | Any of the 32 pins can be accessed by using index. Index will be added to "Out Base".
|In Base | Pin 1..32 | ```StateMachine (sm_id, pwm_prog, in_base=Pin(8))```|"In Base" will be pin 8.
|In Index | 1..32 | NA | Any of the 32 pins can be accessed by using index. Index will be added to the "In Base".

## Additional Parameters

|Parameter | Valid Values | Initalising example  | Desc
|--|:--:|--|-
|Jmp Pin Base | Pin 1..32 | ```StateMachine (sm_id, pwm_prog, jmp_pin=Pin(10))``` |Set jmp pin to 10. Used by ```jmp(pin,"label")```


#
## Notes

### Using PINS

|Command|Desc|
|------------:|:--------------|
```Set(pins,7)``` | Uses mask 101 on three pins relative to "Set Base". Will set the pin to the mask value
```.side(7)``` | Uses mask 101 on three pins relative to "Side Set Base". Will set the bit to the mask value. 
```IN_(pins,3)``` | Number of pins to copy. Copies pin 5,6 and 7 into the OSR LSBs."
```OUT(pins,3)``` | Number of pins from base to copy. Copies pin 5,6 and 7 out from the OSR LSBs."

### Gotchas
```set(pin,index)``` will not give an error though it is not correct. It should be ```set(PINS,index)``` PINS with the S.

```jmp(pins,"loop")```  will not give an error even though it is not correct. It should be ```jmp(pin,"loop")``` pin not pins.
