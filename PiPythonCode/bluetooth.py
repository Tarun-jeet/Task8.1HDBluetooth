import asyncio
from bleak import BleakClient
from gpiozero import PWMLED, Buzzer, LED
from time import sleep

# The Bluetooth address of the Arduino Nano 33 IoT that I am using
ARDUINO_ADDRESS = "E0:5A:1B:7A:1B:F2" 

# UUIDs for the Nano service and HC_SR04 characteristic, specifically for reading the distance data from ultrasonic sensor
NANO_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"  
HC_SR04_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"  

led = PWMLED(17)  # PWM LED connected to GPIO pin 17 BLUE
buzzer = Buzzer(27)  # Buzzer connected to GPIO pin 27 
redLed = LED(18)  # Additional warning LED connected to GPIO pin 18

def scale_brightness(distance):
    """
    Function to Scale the brightness of the LED based on the distance received.
    - Max brightness (1.0) when the car is 0 cm away.
    - Min brightness (0.0) when the object is 100 cm away.
    - If the object is less than 3 cm away, the red LED is turned on instead of adjusting the brightness.
    """
    if distance <= 0:
        redLed.off()  
        return 1.0  
    elif distance >= 100:
        # off the red LED for large distances
        redLed.off()  
        return 0.0  
    elif distance <= 3:
        # on the red LED if the object is too close (<3 cm)
        redLed.on()  
        # off the main LED in this case
        return 0.0  
    else:
        redLed.off()
        # scaling for brightness if range is not max , min and less than 3
        return 1.0 - (distance / 100.0)  

def buzzer_pattern(distance):
    """
    Function to determine the buzzer's beep pattern based on the distance.
    - Closer distances lead to faster and short beeps
    - Far distances lead to longer beep
    - The function returns two values: beep_delay (delay between beeps) and beep_duration.
    """
    if distance > 100:
        # No beeping if the distance is over 100 cm
        return 0, 0  
    elif distance <= 5:
        # Fast beeping for very close distances
        return 0.01, 0.2  
    elif distance <= 10:
        # Medium beeping for moderate distances
        return 0.3, 0.5  
    elif distance <= 30:
        # Slower beeping for farther distances
        return 0.5, 1  
    else:
        # Very slow beeping for distances beyond 30 cm but less than 100 cm
        return 1, 2  
async def control_led_buzzer(client):
    """
    Main function to control the LED brightness and the buzzer beep pattern based on data from Arduino
    via bluetooth.
    """
    try:
        while True:
            # Read the distance value from the Bluetooth characteristic
            distance_data = await client.read_gatt_char(HC_SR04_CHARACTERISTIC_UUID)
            # Convert the byte data to an integer (the distance in cm)
            distance = int.from_bytes(distance_data, byteorder='little')
            print(f"Received distance: {distance} cm")  

            # caling the function scale_brightness and storing value I get it from it in a variable
            brightness = scale_brightness(distance)
            print(f"Setting LED brightness to: {brightness * 100}%")
            # Setting the PWM value to control LED brightness
            led.value = brightness  

            # calling the buzzer_pattern function and storing the returned values in two variables
            beep_delay, beep_duration = buzzer_pattern(distance)
            if beep_delay > 0:
                print(f"Buzzer beeping for {beep_duration} seconds with {beep_delay} second delay.")
                buzzer.on()  
                await asyncio.sleep(beep_duration)  # Buzzer stays on for this long
                buzzer.off() 
                await asyncio.sleep(beep_delay)  # Wait before the next beep
            else:
                # If delay is 0, no beeping
                print("Buzzer off")  
                buzzer.off()  
            # Waiting for 1 second before reading distance again
            await asyncio.sleep(1)  
    except Exception as e:
        print(f"Error: {e}")  # Printing any errors that occur
    finally:
        # explicitly Turning off the LEDs and buzzer when the program stops
        led.off()
        buzzer.off()  
        redLed.off()  

async def main():
    """
    This is the main function to establish the Bluetooth connection with the Arduino Nano 33 IoT.
    - Once connected, it runs the LED and buzzer control loop.
    """
    try:
        # Using BleakClient to connect to the Arduino via Bluetooth
        async with BleakClient(ARDUINO_ADDRESS) as client:
            print(f"Connected to {ARDUINO_ADDRESS}")  
            await control_led_buzzer(client)  
    except Exception as e:
        # Print any errors that occur during connection
        print(f"Failed to connect: {e}")  

# This starts the asyncio event loop and calls the main function
asyncio.run(main())  