import serial
import flatbuffers
from SerialMail.SerialMail import SerialMail
from SerialMail.Value import Value

def read_serial_mail(serial_connection):
    """
    Reads FlatBuffers data from a serial connection and decodes it as SerialMail.
    """
    # Read the buffer size first (assuming size is sent as 4 bytes, big-endian)
    size_bytes = serial_connection.read(4)
    if len(size_bytes) < 4:
        print("Failed to read the size of the buffer.")
        return None
    
    size = int.from_bytes(size_bytes, byteorder='big')  # Convert bytes to integer
    print(f"Expected buffer size: {size} bytes")

    # Read the serialized buffer
    buffer = serial_connection.read(size)
    if len(buffer) < size:
        print("Failed to read the complete buffer.")
        return None
    
    # Decode the FlatBuffers data
    return SerialMail.GetRootAs(buffer, 0)

def main():
    # Open the serial connection (adjust port and baudrate as needed)
    # Baud Rate: 115200 (set explicitly in Python).
    # Data Bits: 8 (bytesize=serial.EIGHTBITS by default).
    # Parity: None (parity=serial.PARITY_NONE by default).
    # Stop Bits: 1 (stopbits=serial.STOPBITS_ONE by default).
    serial_connection = serial.Serial(port="/dev/ttyS0", baudrate=115200, timeout=1)
    
    print("Listening for data...")
    
    try:
        while True:
            # Attempt to read and decode SerialMail data
            serial_mail = read_serial_mail(serial_connection)
            if serial_mail:
                # Process and print the decoded SerialMail object
                print("\nReceived SerialMail:")
                print(f"Classification Active: {serial_mail.ClassificationActive()}")
                print(f"Channel: {serial_mail.Channel()}")

                # Print inputs
                inputs_length = serial_mail.InputsLength()
                print(f"Inputs ({inputs_length}):")
                for i in range(inputs_length):
                    value = serial_mail.Inputs(i)
                    print(f"  Input {i}: ({value.Data0()}, {value.Data1()}, {value.Data2()})")

                # Print classifications
                classification_length = serial_mail.ClassificationLength()
                print(f"Classification ({classification_length}):")
                for j in range(classification_length):
                    print(f"  {serial_mail.Classification(j):.2f}")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        serial_connection.close()

if __name__ == "__main__":
    main()
