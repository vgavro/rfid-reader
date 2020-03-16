RFID reader (also named UHF RFID) for IND903, YR903, YR904, possible others with same protocol.
Allow connections with serial port or socket.

python3.6+ required

```
python -m venv venv
./venv/bin/pip install -e git+https://github.com/vgavro/rfid-reader#egg=rfid-reader
./venv/bin/rfid-reader --help

cp ./rfid_reader/rfid-reader.example.conf ./rfid-reader.conf
sudo ifconfig enp5s0f1 192.168.0.1 netmask 255.255.255.0 up
./venv/bin/rfid-reader
```
