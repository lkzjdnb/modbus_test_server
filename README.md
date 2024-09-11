# Modbus test server
Python script to allow the emulation of multiple modbus devices (TCP or RTU).

## Configuration
Configuration is provided via a yaml file (see [config.yaml](/config.yaml) for an example). Emulated values are provided as a dump of the registers in a simple text file where each line correpond to one registers (as u16) and undefined registers are set to None.

## Usage
Easiest way to run is through docker : 
```bash
docker build -t modbus-test-server:1 .
docker run -it -v /dev:/dev -p502:4502 modbus-test-server
```

Otherwise directly :
```bash
python -m venv .venv
pip install -r requirements
python server.py -c config.yaml
```

## Implementation details
For ModBus RTU on execution the script will create two symlinks to pty :
- \<specified_port\>
- \<specified_port\>_master

Both are linked but the one to use is \<specified_port\>, \<specified_port\> is "the other side" on which the the server will connect. On exit both should be deleted, if it's not the case it is safe to force delete same manually.
