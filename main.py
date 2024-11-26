import argparse
import serial
import flatbuffers
import csv
from SerialMail.SerialMail import SerialMail
from SerialMail.Value import Value


def read_serial_mail(serial_connection):
    # Read the buffer size (4 bytes)
    size_bytes = serial_connection.read(4)
    if len(size_bytes) < 4:
        print("Failed to read the size of the buffer.")
        return None
    
    size = int.from_bytes(size_bytes, byteorder='little')  # Match C++ endianness
    print(f"Expected buffer size: {size} bytes")

    # Read the serialized buffer
    buffer = serial_connection.read(size)
    if len(buffer) < size:
        print("Failed to read the complete buffer.")
        return None

    # Decode the FlatBuffers data
    buffer = bytearray(buffer)
    serial_mail = SerialMail.GetRootAs(buffer, 0)
    return serial_mail


def extract_serial_mail_data(serial_mail):
    # Extract voltage values (inputs)
    inputs_length = serial_mail.InputsLength()
    voltages = []
    for i in range(inputs_length):
        value = serial_mail.Inputs(i)
        voltages.append((value.Data0(), value.Data1(), value.Data2()))

    # Extract classifications
    classification_length = serial_mail.ClassificationLength()
    classifications = [serial_mail.Classification(j) for j in range(classification_length)]

    # Extract other fields
    classification_active = int(serial_mail.ClassificationActive())
    channel = int(serial_mail.Channel())

    return classification_active, channel, voltages, classifications


def write_to_csv(classification_active, channel, voltages, classifications, csv_writer):
    # Write data to the CSV file
    csv_writer.writerow({
        "ClassificationActive": classification_active,
        "Channel": channel,
        "Voltages": voltages,
        "Classifications": classifications
    })


def print_serial_mail_data(classification_active, channel, voltages, classifications):
    # Print data to the console
    print(f"Classification Active: {classification_active}")
    print(f"Channel: {channel}")

    print(f"Voltages ({len(voltages)}):")
    for i, voltage in enumerate(voltages):
        print(f"  Input {i}: {voltage}")

    print(f"Classifications ({len(classifications)}): {classifications}")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Read and decode SerialMail data from a serial port.")
    parser.add_argument("--port", type=str, required=True, help="Serial port (e.g., /dev/ttyS0 or COM3)")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--csv", type=str, default="output.csv", help="Output CSV file (default: output.csv)")
    args = parser.parse_args()

    # Open the serial connection
    serial_connection = serial.Serial(port=args.port, baudrate=args.baudrate, timeout=1)
    print(f"Listening for data on port {args.port} at {args.baudrate} baud...")

    # Open the CSV file for writing
    with open(args.csv, mode="w", newline="") as csvfile:
        # Define CSV fieldnames and writer
        fieldnames = ["ClassificationActive", "Channel", "Voltages", "Classifications"]
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csv_writer.writeheader()

        try:
            while True:
                # Attempt to read and decode SerialMail data
                serial_mail = read_serial_mail(serial_connection)
                if serial_mail:
                    # Extract data
                    classification_active, channel, voltages, classifications = extract_serial_mail_data(serial_mail)

                    # Print data
                    print("\nReceived SerialMail:")
                    print_serial_mail_data(classification_active, channel, voltages, classifications)

                    # Write data to the CSV file
                    write_to_csv(classification_active, channel, voltages, classifications, csv_writer)
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            serial_connection.close()

if __name__ == "__main__":
    main()