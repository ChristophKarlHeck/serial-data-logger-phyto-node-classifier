import argparse
import serial
import flatbuffers
import json
import csv
import os
from datetime import datetime
from SerialMail.SerialMail import SerialMail
from SerialMail.Value import Value


def read_serial_mail(serial_connection):
    """
    Reads a serialized FlatBuffers message from the serial connection and decodes it.
    
    The function uses a synchronization marker (0xAAAA) to align with the start of a valid message,
    reads the size field to determine the message length, and then processes the message if valid.

    Args:
        serial_connection: The serial connection object.

    Returns:
        A SerialMail object if a valid message is read and decoded, None otherwise.
    """
    buffer = bytearray()
    sync_marker = b'\xAA\xAA'

    while True:
        try:
            # Read data from the serial port
            chunk = serial_connection.read(1024)  # Adjust chunk size as needed
            if not chunk:
                continue  # Wait for data if nothing is read
            buffer.extend(chunk)

            # Synchronize to the marker
            marker_index = buffer.find(sync_marker)
            if marker_index != -1:
                buffer = buffer[marker_index + len(sync_marker):]  # Align to the start of the message
            else:
                if len(buffer) > 2048:  # Avoid infinite buffer growth
                    buffer.clear()
                continue  # Wait for synchronization

            # Check if there is enough data to read the size field (4 bytes)
            if len(buffer) < 4:
                continue  # Not enough data for size field

            # Read the size field (first 4 bytes after the sync marker)
            size = int.from_bytes(buffer[:4], byteorder='little')

            # Validate the size field
            if size < 24 or size > 1024:  # Adjust limits based on schema expectations
                print(f"Invalid message size: {size}. Skipping bytes.")
                buffer.pop(0)  # Skip one byte and keep searching
                continue

            # Check if the full message is available
            if len(buffer) < size + 4:
                continue  # Wait for more data

            # Extract the message
            message = buffer[4:size + 4]
            buffer = buffer[size + 4:]  # Remove processed message

            # Decode the FlatBuffers message
            try:
                serial_mail = SerialMail.GetRootAs(message, 0)
                return serial_mail  # Return the decoded object
            except Exception as e:
                print(f"Failed to decode FlatBuffers data: {e}")
                continue

        except Exception as e:
            print(f"Error while reading serial data: {e}")
            return None


def get_analog_inputs(raw_input_bytes, databits=8388608, vref=2.5, gain=4.0):
    """
    Calculate analog values from 3-byte measurements.

    Args:
        byte_inputs (list of list of int): List of 3-byte measurements, where each measurement is a list of three uint8 values.
        databits (int): Number of data bits (e.g., 24 for 24-bit resolution).
        vref (float): Reference voltage.
        gain (float): Gain applied to the measurement.

    Returns:
        list of float: Calculated analog voltages in millivolts.
    """
    inputs = []

    for byte_dict in raw_input_bytes:
        # Extract the bytes from the dictionary
        byte0 = byte_dict["Data0"]
        byte1 = byte_dict["Data1"]
        byte2 = byte_dict["Data2"]

        # Combine the 3 bytes into a single integer
        measurement = ((byte0 << 16) | (byte1 << 8) | (byte2))

        # Calculate the voltage
        voltage = (float(measurement) / databits - 1)  # Normalize measurement
        voltage = voltage * vref / gain  # Apply reference voltage and gain
        voltage *= 1000  # Convert to millivolts

        inputs.append(round(voltage,4))

    return inputs


def extract_serial_mail_data(serial_mail):
    # Extract voltage values ch0(inputs)
    inputs_length_ch0 = serial_mail.InputsCh0Length()
    raw_input_bytes_ch0 = []
    for i in range(inputs_length_ch0):
        value = serial_mail.InputsCh0(i)
        byte_dict = {"Data0": value.Data0(), "Data1": value.Data1(), "Data2": value.Data2()}
        raw_input_bytes_ch0.append(byte_dict)

    voltages_ch0 = get_analog_inputs(raw_input_bytes_ch0)

    # Extract voltage values ch0(inputs)
    inputs_length_ch1 = serial_mail.InputsCh1Length()
    raw_input_bytes_ch1 = []
    for i in range(inputs_length_ch1):
        value = serial_mail.InputsCh1(i)
        byte_dict = {"Data0": value.Data0(), "Data1": value.Data1(), "Data2": value.Data2()}
        raw_input_bytes_ch1.append(byte_dict)

    voltages_ch1 = get_analog_inputs(raw_input_bytes_ch1)

    # Extract classifications
    classification_ch0_length = serial_mail.ClassificationCh0Length()
    classification_ch0 = [round(serial_mail.ClassificationCh0(j),3) for j in range(classification_ch0_length)]

    # Extract classifications
    classification_ch1_length = serial_mail.ClassificationCh1Length()
    classification_ch1 = [round(serial_mail.ClassificationCh1(j),3) for j in range(classification_ch1_length)]


    return voltages_ch0, voltages_ch1, classification_ch0, classification_ch1


def write_to_json(filename, classification_active, channel, raw_input_bytes, voltages, classifications):
    # Format classifications with three decimal places
    formatted_classifications = [c for c in classifications]

    # Prepare data to save
    data = {
        "Timestamp": datetime.now().isoformat(),
        "ClassificationActive": classification_active,
        "Channel": channel,
        "RawInputBytes": raw_input_bytes,
        "InputVoltages": voltages,  # Keep as a list of dicts
        "Classifications": formatted_classifications  # Formatted list
    }

    # Check if the file exists and initialize if necessary
    if not os.path.isfile(filename):
        with open(filename, mode="w") as jsonfile:
            json.dump([], jsonfile)  # Write an empty JSON array

    # Read existing content
    with open(filename, mode="r") as jsonfile:
        try:
            existing_data = json.load(jsonfile)
            if not isinstance(existing_data, list):
                raise ValueError("JSON file must contain a list at the root.")
        except json.JSONDecodeError:
            existing_data = []  # If file is empty or invalid, start with an empty list

    # Append the new record
    existing_data.append(data)

    # Write the updated JSON array back to the file
    with open(filename, mode="w") as jsonfile:
        json.dump(existing_data, jsonfile, indent=4)  # Write with formatting for readability


def write_to_csv(filename, classification_active, channel, raw_input_bytes, voltages, classifications):
    # Check if the file exists to decide whether to write a header
    file_exists = os.path.isfile(filename)

    # Open the CSV file in append mode
    with open(filename, mode="a", newline="") as csvfile:
        # Define CSV fieldnames and writer
        fieldnames = ["Timestamp","ClassificationActive", "Channel", "RawInputBytes", "InputVoltages", "Classifications"]
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header only if the file does not exist
        if not file_exists:
            csv_writer.writeheader()

        # Write the data row
        csv_writer.writerow({
            "Timestamp": datetime.now().isoformat(),
            "ClassificationActive": classification_active,
            "Channel": channel,
            "RawInputBytes": raw_input_bytes,
            "InputVoltages": voltages, 
            "Classifications": classifications
        })


def print_serial_mail_data(voltages_ch0, voltages_ch1, classification_ch0, classification_ch1):
    # Print data to the console in the specified format
    print("\nReceived SerialMail:")

    # print(f"RawInputBytes ({len(raw_input_bytes)}):")
    # for i, raw_input_byte in enumerate(raw_input_bytes):
    #     print(f"  Input {i}: ({raw_input_byte['Data0']}, {raw_input_byte['Data1']}, {raw_input_byte['Data2']})")

    print(f"InputVoltagesCh0 ({len(voltages_ch0)}):")
    for i, voltage in enumerate(voltages_ch0, start=1):
        print(f"  InputVoltageCh0 {i}: {voltage:.3f}")

    print(f"InputVoltagesCh1 ({len(voltages_ch1)}):")
    for i, voltage in enumerate(voltages_ch1, start=1):
        print(f"  InputVoltageCh1 {i}: {voltage:.3f}")

    print(f"ClassificationCh0 ({len(classification_ch0)}):")
    for i, classification in enumerate(classification_ch0, start=1):
        print(f"  ClassificationCh0 {i}: {classification:.3f}")

        print(f"ClassificationCh1 ({len(classification_ch1)}):")
    for i, classification in enumerate(classification_ch1, start=1):
        print(f"  ClassificationCh1 {i}: {classification:.3f}")



def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Read and decode SerialMail data from a serial port.")
    parser.add_argument("--port", type=str, required=True, help="Serial port (e.g., /dev/ttyS0 or COM3)")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--file", type=str, required=True, help="Output file name (e.g., output.csv or output.json)")
    parser.add_argument("--format", type=str, choices=["csv", "json"], required=True, help="Output format (csv or json)")
    args = parser.parse_args()

    # Ensure the file has the correct extension
    if args.format == "csv" and not args.file.endswith(".csv"):
        args.file += ".csv"
    elif args.format == "json" and not args.file.endswith(".json"):
        args.file += ".json"

    # Warn if the output file already exists
    if os.path.isfile(args.file):
        print(f"Warning: The file '{args.file}' already exists and will be appended to.")
        user_input = input("Do you want to continue? (y/n): ").strip().lower()
        if user_input != 'y':
            print("Exiting without modifying the file.")
            exit(0)

    # Open the serial connection
    serial_connection = serial.Serial(port=args.port, baudrate=args.baudrate, timeout=1)
    print(f"Listening for data on port {args.port} at {args.baudrate} baud...")

    try:
        while True:
            # Attempt to read and decode SerialMail data
            serial_mail = read_serial_mail(serial_connection)
            if serial_mail:
                # Extract data
                voltages_ch0, voltages_ch1, classification_ch0, classification_ch1 = extract_serial_mail_data(serial_mail)

                # Print data
                print_serial_mail_data(voltages_ch0, voltages_ch1, classification_ch0, classification_ch1)

                # Write data to the selected file format
                # if args.format == "csv":
                #     try:
                #         write_to_csv(args.file, classification_active, channel, raw_input_bytes, voltages, classifications)
                #         print(f"Data successfully written to {args.file} in CSV format.")
                #     except Exception as e:
                #         print(f"Failed to write data to {args.file} in CSV format: {e}")
                # elif args.format == "json":
                #     try:
                #         write_to_json(args.file, classification_active, channel, raw_input_bytes, voltages, classifications)
                #         print(f"Data successfully written to {args.file} in JSON format.")
                #     except Exception as e:
                #         print(f"Failed to write data to {args.file} in JSON format: {e}")
                # else:
                #     print(f"Unsupported format: {args.format}")

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        serial_connection.close()

if __name__ == "__main__":
    main()