import network
import urequests
import ntptime
import utime
import json
import WiFimgr_main
import wifimgr
import machine
from machine import SPI, Pin, RTC, deepsleep, DEEPSLEEP_RESET, reset_cause
import time

# Define pins for the shift register
data_pin = machine.Pin(18, machine.Pin.OUT)
clock_pin = machine.Pin(5, machine.Pin.OUT)
latch_pin = machine.Pin(33, machine.Pin.OUT)
blank_pin = machine.Pin(27, machine.Pin.OUT)
polarity_pin = machine.Pin(12, machine.Pin.OUT)
red_pin = machine.Pin(14, machine.Pin.OUT)
blue_pin = machine.Pin(32, machine.Pin.OUT)
green_pin = machine.Pin(15, machine.Pin.OUT)
oe_pin = machine.Pin(13, machine.Pin.OUT)
btn0 = machine.Pin(34, machine.Pin.IN)
btn1 = machine.Pin(39, machine.Pin.IN)
btn2 = machine.Pin(36, machine.Pin.IN)

vspi = SPI(2, baudrate=1000000, polarity=0, phase=1, firstbit=SPI.MSB, sck=Pin(5), mosi=Pin(18), miso=Pin(19))

btn0_state_new = btn1.value()
btn1_state_new = btn1.value()
btn2_state_new = btn2.value()
btn0_state_old = btn0.value()
btn1_state_old = btn0.value()
btn2_state_old = btn0.value()
time_counter = 0
btn0_counter = 0
btn1_counter = 0
btn2_counter = 0

# Set up the RTC (Real-Time Clock)
rtc = RTC()

numbers = [0b1000000000, 0b0000000001, 0b0000000010, 0b0000000100, 0b0000001000, 0b0000010000, 0b0000100000, 0b0001000000, 0b0010000000, 0b0100000000]

combinations = [
    [0, 0, 0],
    [0, 0, 1],
    [0, 1, 0],
    [0, 1, 1],
    [1, 0, 0],
    [1, 0, 1],
    [1, 1, 0],
    [1, 1, 1]
]

current_combination = 0

f = open('ntp_servers.json')
ntp_servers = json.loads(f.read())
f.close()

# Get the device's latitude and longitude from its IP address
def get_location():
    try:
        response = urequests.get('http://ip-api.com/json')
        json_data = response.json()
        country = json_data['country']
        lat = json_data['lat']
        lon = json_data['lon']
        return country, lat, lon
    except:
        return None

def get_timezone(lat, lon):
    global timezone_offset
    try:
        response = urequests.get('http://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid=4320d4cc56178b8331158fc91653d12d'.format(lat, lon))
        json_data = response.json()
        timezone_offset = json_data['timezone']
        return timezone_offset
    except:
        return None
    
# Find the closest NTP server using the NTP Pool Project
def get_ntp_server(country):
    for i in ntp_servers:
        if country == i:
            return ntp_servers[i]
    return None

# Set the device's time using the chosen NTP server
def set_time_machine():
    country, lon, lat = get_location()
    if country:
        ntp_server = get_ntp_server(country)
        if ntp_server:
            get_timezone(lon,lat)
        else:
            print('Could not find NTP server')
    else:
        print('Could not determine time')
    global local_time
    ntptime.host = ntp_server
    ntptime.settime()
    seconds = utime.time()
    local_time = utime.localtime(seconds + timezone_offset)
    rtc.init((local_time[0],local_time[1],local_time[2],local_time[6],local_time[3],local_time[4], local_time[5], local_time[7]))

def set_time():
    hour = str(rtc.datetime()[4])
    minute = str(rtc.datetime()[5])
    if len(hour) == 1:
        hour = '0' + hour
    if len(minute) == 1:
        minute = '0' + minute
    time_value = hour+minute
    return time_value

def init():
    red_pin.off()
    blue_pin.off()
    green_pin.off()
    blank_pin.off()
    polarity_pin.on()
    latch_pin.off()
    oe_pin.on()

def shift_number(number):
    tube4 = numbers[int(number[3])] << 30
    tube3 = numbers[int(number[2])] << 20
    tube2 = numbers[int(number[1])] << 10
    tube1 = numbers[int(number[0])]
    out_compo = (tube1|tube2|tube3|tube4)
    ocb = out_compo.to_bytes(8,"big")
    blank_pin.on()
    polarity_pin.on()
    latch_pin.off()
    time.sleep(0.01)
    vspi.write(ocb)
    time.sleep(0.01)
    latch_pin.on()
    time.sleep(0.01)
    latch_pin.off()

def recalibrate_clock():
    print("recalibrate clock...")
    set_time_machine()
    init()
    time.sleep(1)
    shift_number("0000")
    time.sleep(1)
    init()
    time.sleep(1)
    shift_number("0000")
    time.sleep(1)
    init()
    time.sleep(1)
    shift_number("0000")

# Main code
print("Start routine")
init()
set_time_machine()

while True:
    if btn0.value() == 0:
        btn0_counter += 1
    else:
        btn0_counter = 0
    if btn0_counter >= 10:
        btn0_state_new = btn0.value()
        btn0_counter = 0
    else:
        pass
    if btn1.value() == 0:
        btn1_counter += 1
    else:
        btn1_counter = 0
    if btn1_counter >= 10:
        btn1_state_new = btn1.value()
        btn1_counter = 0
    else:
        pass
    if btn2.value() == 0:
        btn2_counter += 1
    else:
        btn2_counter = 0
    if btn2_counter >= 10:
        btn2_state_new = btn2.value()
        btn2_counter = 0
    else:
        pass
    if btn0_state_new != btn0_state_old:
        current_combination += 1
        if current_combination > (len(combinations)-1):
            current_combination = 0
        blue_pin.value(combinations[current_combination][0])
        green_pin.value(combinations[current_combination][1])
        red_pin.value(combinations[current_combination][2])
    if btn1_state_new != btn1_state_old:
        recalibrate_clock()
    if btn2_state_new != btn2_state_old:
        current_combination -= 1
        if current_combination < 0:
            current_combination = (len(combinations)-1)
        blue_pin.value(combinations[current_combination][0])
        green_pin.value(combinations[current_combination][1])
        red_pin.value(combinations[current_combination][2])
    if time_counter == 5:
        time_counter = 0
        shift_number(set_time())
    btn0_state_old = btn0.value()
    btn1_state_old = btn1.value()
    btn2_state_old = btn2.value()
    time.sleep(0.2)
    time_counter += 1

##### Sources #####
# https://lastminuteengineers.com/esp32-ntp-server-date-time-tutorial/ (Atomic Clock)
# https://RandomNerdTutorials.com (Wi-Fi Manager)
