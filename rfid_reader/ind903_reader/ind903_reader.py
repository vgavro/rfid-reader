#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
copy of https://github.com/espinr/activioty/tree/master/python/ind903_reader
with socket channel support, unused parameters removed, and lint fixes.
(Latest commit 2450434 on Jan 30, 2018)
"""

import binascii
import time
import socket

from .ind903_packet import Ind903Packet


class Ind903Reader:
    """
    Reads from serial (for example usb) or tcp protocols.
    ```
    # The baud rates are 9600bps、19200bps、38400bps、115200bps.
    channel = serial.Serial('/dev/ttyUSB0', 115200)

    channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
    channel.connect(('192.168.0.178', 4001))

    reader = Ind903Reader(channel)
    reader.do_inventory(print)
    ```
    """

    def __init__(self, channel, wait_timeout=0.2, trace=lambda x: x):
        """
        The default baud rate is 115200bps.
        :param readerAddress: (byte) the address of the reader (\x01 by default)
        Structure of the Package [ Head | Length | Address | Cmd | Data[0…N] | Check ]
        """

        self.wait_timeout = wait_timeout
        self.trace = trace

        if isinstance(channel, socket.SocketType):
            self._write = channel.send
            self._read = channel.recv
        else:
            self._write = channel.write
            self._read = channel.read

    def _read_command(self):
        while True:
            time.sleep(self.wait_timeout)
            # At least a package of 4 bytes (minimum)
            # [ Head | Length | Address | Data[0…N] | Check ]

            # for serial there was "if self.channel.inWaiting() >= 4:" check,
            # removed it (as I guess it's not needed anyway, can't test serial)

            # Gets only the first byte of the packet (it should be HEAD)
            packet_header = self._read(1)
            if (packet_header != Ind903Packet.PACKET_HEAD):
                # the next one is the length of the packet
                packet_length_bytes = self._read(1)
                packet_length = int.from_bytes(packet_length_bytes, byteorder='big')
                if (packet_length > 0):
                    raw_packet = b"".join([packet_header, packet_length_bytes,
                                           self._read(packet_length)])
                    result_packet = Ind903Packet.parsePacket(raw_packet)
                    return (result_packet)

    def do_inventory(self, callback):
        """
        Process of inventory execution. After the reader is initialized,
        an infinite loop is executed with these tasks:
        (1) the antenna set
        (2) Inventory start requested
        (3) Wait for several responses (stop when a control package is received)
        (4) Process the response
        :param callback(epcID): callback function to process a EPC
        found during inventory.
        """
        setAntennaPacket = Ind903Packet.generatePacketSetAntenna()
        startRealTimeInventoryPacket = \
            Ind903Packet.generatePacketStartRealTimeInventory()

        self._write(setAntennaPacket.packet)
        self.trace('> ' + setAntennaPacket.toString())

        receivedPacket = self._read_command()
        self.trace('< ' + receivedPacket.toString())

        if (receivedPacket.isCommand(Ind903Packet.CMD_SET_WORKING_ANTENNA)):
            # to check if is a success of failure
            pass

        while (True):
            self._write(startRealTimeInventoryPacket.packet)
            self.trace('> ' + startRealTimeInventoryPacket.toString())
            # While a control package (success/error) is not received
            while (True):
                receivedPacket = self._read_command()
                self.trace('< ' + receivedPacket.toString())
                if (
                    receivedPacket.isCommand(
                        Ind903Packet.CMD_NAME_REAL_TIME_INVENTORY)
                    and receivedPacket.isEndRealTimeInventory() != b'\x00'
                ):
                    self.trace('[end of inventory command found]')
                    break   # jumps out the inventory loop
                # Reads EPCs
                epc = receivedPacket.getTagEPCFromInventoryData()
                if (int.from_bytes(epc, byteorder='big') == 0):
                    break  # jumps out the inventory loop
                epcString = binascii.hexlify(epc).decode()
                callback(epcString)
