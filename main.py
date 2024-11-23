import flatbuffers
import csv
import serial
import sys
from Mail.Mail import Mail
from Mail.Input import Input

# Function to deserialize the Flatbuffer data
def deserialize_mail(serial_data):
    # Create a FlatBuffer builder and deserialize the incoming byte array
    buf = bytearray(serial_data)
    mail = Mail.GetRootAsMail(buf, 0)

    # Extract the inputs (3-byte arrays) and classification floats
    inputs = []
    for i in range(mail.InputsLength()):
        input_data = mail.Inputs(i)
        inputs.append(list(input_data.DataAsNumpy()))  # Convert input to list for easier manipulation

    classification = list(mail.ClassificationAsNumpy())
    classification_active = mail.ClassificationActive()
    channel = mail.Channel()

    return inputs, classification, classification_active, channel

# Function to save data to CSV
def save_to_csv(inputs, classification, classification_active, channel):
    with open('output.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write headers for CSV
        writer.writerow(['Input 1', 'Input 2', 'Input 3', 'Classification', 'Active', 'Channel'])
        
        # Write each input and its associated classification
        for input_data, class_value in zip(inputs, classification):
            writer.writerow(input_data + [class_value, classification_active, channel])

# Main function to run the program
def main():
    # Open the UART port (ttyS0) for reading
    try:
        ser = serial.Serial('/dev/ttyS0', 19200, timeout=1, parity=serial.PARITY_ODD)  # Set baud rate and timeout as necessary
        print("Connected to UART on /dev/ttyS0")
    except serial.SerialException as e:
        print(f"Error: Unable to open UART port: {e}")
        sys.exit(1)

    while True:
        # Read data from UART (you may want to adjust the size based on your message size)
        serial_data = ser.read(1024)  # Read up to 1024 bytes (adjust if necessary)
        
        if len(serial_data) == 0:
            print("No data received, retrying...")
            continue

        print(f"Received {len(serial_data)} bytes of data.")

        # Deserialize the data
        inputs, classification, classification_active, channel = deserialize_mail(serial_data)

        # Save the deserialized data to a CSV file
        save_to_csv(inputs, classification, classification_active, channel)
        print("Data successfully saved to output.csv!")

        # Optionally, break the loop after one iteration or run indefinitely
        break  # Remove this line if you want the program to run continuously

    # Close the UART port
    ser.close()

if __name__ == "__main__":
    main()
