#include <ArduinoBLE.h>

// Defined the trigger and echo pins of the ultrasonic sensor
const int trigPin = 3;
const int echoPin = 4;  

// Defining the Bluetooth® Low Energy (BLE) service and characteristic
// The service allows communication between the Arduino and another BLE device
BLEService NanoService("19B10000-E8F2-537E-4F6C-D104768A1214");

// The characteristic is used to send the distance data (calculated from the ultrasonic sensor)
BLEUnsignedShortCharacteristic HC_SR04Characteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify);

void setup() {
  
  Serial.begin(9600);
  while (!Serial);  

  // Setting up the ultrasonic sensor pins. The trigPin will send out ultrasonic pulses, and the echoPin will listen for their reflections
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // If BLE fails to initialize, the program prints an error message and the program will run in an infinite loop
  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);  
  }

  // Setting the local BLE device name as "ParkingSensor" for discovery by other BLE devices
  BLE.setLocalName("ParkingSensor");

  // Defining and advertising the BLE service so that other devices can detect it
  BLE.setAdvertisedService(NanoService);

  // Adding the distance characteristic to the BLE service
  NanoService.addCharacteristic(HC_SR04Characteristic);
  BLE.addService(NanoService);

  // Begin advertising the BLE service, so other devices can discover and connect
  BLE.advertise();
  Serial.println("BLE Parking Sensor Peripheral Ready!");  
}

void loop() {
  // Waiting for a central BLE device to connect to the Arduino
  BLEDevice central = BLE.central();

  // If a central device has connected, proceed to send data
  if (central) {
    Serial.print("Connected to central: ");
    // Printing the address of the connected device
    Serial.println(central.address());  

    // Stay in this loop as long as the central device remains connected
    while (central.connected()) {
      // Get the distance reading from the ultrasonic sensor
      int distance = getDistance();

      // Send the distance value to the Raspberry Pi or central device via BLE
      HC_SR04Characteristic.writeValue(distance);

      // Printing the distance to the serial monitor for debugging purposes
      Serial.print("Distance: ");
      Serial.print(distance);
      Serial.println(" cm");

      delay(1000);
    }

    // If the central device disconnects, print a message
    Serial.println("Disconnected from central");
  }
}

// a function to calculate the distance using the ultrasonic sensor
int getDistance() {
  int duration, distance;

  // Ensuring the trigPin is low before starting a new measurement
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Sending a 10-microsecond HIGH pulse to trigPin to trigger the ultrasonic burst
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);

  // Calculate the distance in centimeters based on the time duration of the pulse
  distance = (duration * 0.0343) / 2;
  
  return distance;  
}
