# Serial Data Logger for Phyto Node Classifier

`serial-data-logger` is a Python-based tool for reading, processing, and exporting serial data transmitted via a serial port. It decodes structured data using the FlatBuffers serialization library, converts raw byte measurements into analog voltages, and exports the results to JSON or CSV formats.

---

## Features

- **Serial Communication**: Reads structured binary data from a serial port.
- **Data Conversion**: Converts 3-byte raw data into analog voltages using configurable parameters (`databits`, `vref`, `gain`).
- **Custom Export Options**:
  - Exports processed data to either JSON or CSV files.
  - Appends to existing files if specified.
- **Console Visualization**: Prints processed data in a human-readable format.

---

## Requirements

- **Python**: Version 3.8 or later
- **Libraries**:
  - `pyserial`
  - `flatbuffers`

Install dependencies using the provided `requirements.txt` file:
```bash
pip install -r requirements.txt
```
## Command-Line Arguments

| **Argument**   | **Required** | **Description**                                                         |
|-----------------|--------------|-------------------------------------------------------------------------|
| `--port`       | Yes          | Serial port to read from (e.g., `/dev/ttyS0` or `COM3`).                |
| `--baudrate`   | No           | Baud rate for serial communication (default: `115200`).                |
| `--path`       | No          | Path to save the output file (default: current directory .)              |

## Example Commands
### Log Data to a CSV File
```bash
python3 main.py --port /dev/ttyACM0 --baudrate 115200
```
## Docker
### Build the Docker Image
```bash
docker build -t serial-data-logger-classifier .
```

### Run in Docker
```bash
docker run --name serial-data-logger-classifier-container \
  --restart=always \
  --device=/dev/ttyACM2:/dev/ttyACM2 \
  -v /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77:/app/output \
   --log-opt max-size=10m \
  --log-opt max-file=3 \
  -d \
  serial-data-logger-classifier \
  --port /dev/ttyACM2 --baudrate 115200 --path /app/output
```

## How It Works

### Data Workflow

1. **Serial Data Read**:
   - Reads structured binary data over a serial connection using `serial.Serial`.

2. **Decoding**:
   - Decodes data using FlatBuffers.

3. **Processing**:
   - Converts 3-byte raw byte measurements into analog voltages using:
     - Configurable `databits` (default: `8388608`).
     - Configurable `vref` (default: `2.5V`).
     - Configurable `gain` (default: `4.0`).

4. **Output**:
   - Exports processed data to CSV, appending to existing files if applicable.
