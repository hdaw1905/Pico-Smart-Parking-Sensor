from machine import Pin, time_pulse_us
import utime

# === Pin Setup ===
TRIG = Pin(3, Pin.OUT)
ECHO = Pin(2, Pin.IN)

# Active Buzzer Control Pin
# Connect the I/O pin of the buzzer module to GP16 (Pin 21)
# Connect VCC of buzzer module to 3V3 (Pin 36) or VBUS (Pin 40) - ensure your module is 3.3V or 5V tolerant respectively
# Connect GND of buzzer module to any GND pin on the Pico
buzzer = Pin(16, Pin.OUT)

# === Buzzer Control ===
# IMPORTANT: This assumes an "Active-Low" buzzer module (most common 3-pin type)
#   - Setting the I/O pin LOW (0V) turns the buzzer ON.
#   - Setting the I/O pin HIGH (3.3V) turns the buzzer OFF.
def buzzer_on():
    buzzer.low()  # Apply 0V to the I/O pin to turn the buzzer ON
    print("Buzzer: ON (GPIO 16 set to LOW/0V)")

def buzzer_off():
    buzzer.high() # Apply 3.3V to the I/O pin to turn the buzzer OFF
    print("Buzzer: OFF (GPIO 16 set to HIGH/3.3V)")

# === Distance Measurement ===
def get_distance():
    TRIG.low()
    utime.sleep_us(2)
    TRIG.high()
    utime.sleep_us(10)
    TRIG.low()

    try:
        pulse_time = time_pulse_us(ECHO, 1, 30000) # Timeout 30ms (enough for ~5 meters)

        if pulse_time < 0: # time_pulse_us returns negative on timeout or no pulse
            return None # Indicate no valid reading

        distance = (pulse_time / 2) / 29.1  # Calculate distance in cm (speed of sound in air)
        return distance
    except Exception as e:
        print(f"Error in get_distance: {e}")
        return None

# === Main Logic ===
def main():
    car_present = False # Flag to track if a car is currently detected in a zone
    start_time = 0      # To record when the car entered the zone

    # Ensure the buzzer is off right when the program starts
    buzzer_off()
    print("System starting. Buzzer initialized to OFF.")
    utime.sleep(1) # Small delay to ensure state is set

    while True:
        distance = get_distance()

        if distance is None:
            print("No Echo / Out of Range. Ensuring Buzzer OFF.")
            buzzer_off() # If no reading, ensure buzzer is off
            utime.sleep(0.5) # Short pause before next attempt
            continue

        print(f"Current Distance: {distance:.1f} cm")

        # Logic based on distance
        if distance > 50:
            # Clear zone: No car present or car has left
            if car_present: # If a car was previously detected, it has now left
                car_present = False
                end_time = utime.ticks_ms()
                parked_duration = (end_time - start_time) / 1000
                print(f"🚗 Car left. Was present for {parked_duration:.1f} seconds.")
            buzzer_off() # Buzzer must be OFF in the clear zone
            print("Status: Clear (Buzzer OFF)")

        elif 20 < distance <= 50:
            # Approaching zone: Car is detected, but not too close
            if not car_present: # If car was not previously detected, it's now entering
                car_present = True
                start_time = utime.ticks_ms() # Record entry time
            buzzer_off() # Buzzer must be OFF in the approaching zone
            print("Status: Approaching (Buzzer OFF)")

        else: # distance <= 20
            # Danger zone: Car is too close
            if not car_present: # If car was not previously detected, it's now entering
                car_present = True
                start_time = utime.ticks_ms() # Record entry time
            buzzer_on() # Buzzer must be ON in the danger zone
            print("Status: TOO CLOSE! 🛑 (Buzzer ON)")

        utime.sleep(0.3) # Short delay between loop iterations for stable readings and response

# === Run the Program ===
if __name__ == "__main__":
    main()
