import RPi.GPIO as GPIO
import time

#Motor Pins von Raspi
#Motor [X,Y,Z]
STEP = [11,16,29]
DIR = [13,18,31]
EN = [15,22,32]

#Welle mit 1mm Abstand und 1,8° Steps
STEPS_IN_MM = 200
direction_pos = GPIO.HIGH
direction_neg = GPIO.LOW

#Enables all 3 Motors
def setup ():
    '''
    Setup and disable of all Motors
    '''
    GPIO.setmode(GPIO.BOARD)
    for motor in range(3):
        GPIO.setup(STEP[motor],GPIO.OUT)
        GPIO.setup(DIR[motor],GPIO.OUT)
        GPIO.setup(EN[motor],GPIO.OUT)
        GPIO.output(EN[motor],GPIO.HIGH) #Motor aus

#Moves the Motor and returns the amount of mm moved
def move_motor(motor,mm,direction,delay=0.001):
    '''
    Moves Motors and returns the amount moved in mm.
    param motor: 0 for X, 1 for Y, 2 for Z
    param mm: mm to move, min and multiple of 0.005
    param direction: direction_pos, direction_neg
    param delay: Movementspeed, default at 0.001
    '''
    GPIO.output(EN[motor],GPIO.LOW)
    GPIO.output(DIR[motor],direction)
    time.sleep(delay)
    steps = int(round(STEPS_IN_MM*mm))
    for _ in range(steps):
        GPIO.output(STEP[motor],GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP[motor],GPIO.LOW)
        time.sleep(delay)
    GPIO.output(EN[motor],GPIO.HIGH)
    return steps / STEPS_IN_MM

def cleanup():
    GPIO.cleanup()