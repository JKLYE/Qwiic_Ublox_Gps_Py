# Python library for the SparkFun's line of u-Blox GPS units.
#
# SparkFun GPS-RTK2 ZED-F9P:
#   https://www.sparkfun.com/products/15136
# SparkFun GPS-RTK2 NEO-M8P:
#   https://www.sparkfun.com/products/15005
# SparkFun GPS-RTK2 ZOE-M8Q:
#   https://www.sparkfun.com/products/15193
# SparkFun GPS-RTK2 SAM-M8Q:
#   https://www.sparkfun.com/products/15210
#
#------------------------------------------------------------------------
#
# Written by SparkFun Electronics, October 2019
#
# This python library supports the SparkFun Electroncis qwiic
# qwiic sensor/board ecosystem
#
# More information on qwiic is at https:// www.sparkfun.com/qwiic
#
# Do you like this library? Help support SparkFun. Buy a board!
#==================================================================================
# Copyright (c) 2019 SparkFun Electronics
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#==================================================================================
#
# This is mostly a port of existing Arduino functionaly, so pylint is sad.
# The goal is to keep the public interface pthonic, but internal is internal
#
# pylint: disable=line-too-long, bad-whitespace, invalid-name, too-many-public-methods
#


# ...and because I'm developing:
# pylint: disable-all  
import module_constants as ubc
import serial
import spidev
from time import sleep

class UbloxSpi(object):

    def __init__(self, port_settings):

        if port_settings is not None: 
            self.port_settings = port_settings
        else: 
            self.port_settings = {
                'max_speed': 5500, # Max Speed is 5.5MHz
                'spi_mode': 0b00, # SPI mode 0
                'bus' : 0,
                'device': 0
            }

    def calc_fletch_checksum(self, packet):

        checksum_B = 0
        checksum_A = packet.get('ubx_class')
        checksum_A = checksum_A + packet.get('ubx_id')
        checksum_B = checksum_A + checksum_B
        checksum_A = checksum_A + packet.get('ubx_length')
        checksum_B = checksum_A + checksum_B
        for item in packet.get('ubx_payload'):
            checksum_A = checksum_A + item
            checksum_B = checksum_B + checksum_A

        packet["ubx_checkA"] = checksum_A
        packet["ubx_checkB"] = checksum_B

        return packet

    def build_packet(self, ubx_class, ubx_id, ubx_length, ubx_payload):

        ubx_message = {
            "ubx_class" : ubx_class,
            "ubx_id" : ubx_id,
            "ubx_length_lsb" : ubx_length & 0xFF,
            "ubx_length_msb" : ubx_length >> 8,
            "ubx_length" : ubx_length,
            "ubx_payload" : ubx_payload, #list of bytes
            "ubx_checkA" : None,
            "ubx_checkB" : None
        }

        packet = self.calc_fletch_checksum(ubx_message)

        return packet

    def build_response(self, byte_list):

        packet = {}
        packet['ubx_class'] = byte_list[0]
        packet['ubx_id'] = byte_list[1]
        packet['ubx_length_lsb'] = byte_list[2]
        packet['ubx_length_msb'] = byte_list[3]
        packet['ubx_length'] = (byte_list[3] << 8) | byte_list[2]
        packet['payload'] = byte_list[4:-3]
        packet['ubx_checkA'] = byte_list[-2]
        packet['ubx_checkB'] = byte_list[-1]

        return packet


    def send_command(self, packet):

        spi = spidev.SpiDev()
        spi.max_speed_hz = self.port_settings.get('max_speed')
        spi.mode = self.port_settings.get('mode')

        spi.open(self.port_settings.get('bus'), 
                 self.port_settings.get('device'))

        to_send = [packet.get('class'), packet.get('id'),
                   packet.get('ubx_length_lsb'), packet.get('ubx_length_msb')]

        for byte in packet.get('payload'):
            to_send.append(byte)

        to_send.append(payload.get('ubx_checkA')) 
        to_send.append(payload.get('ubx_checkB'))

        # xfer2 holds chip select low until the entire block has been sent.
        spi.xfer2([to_send])


    def receive_command(self, packet):

        spi = spidev.SpiDev()
        spi.max_speed_hz = self.port_settings.get('max_speed')
        spi.mode = self.port_settings.get('mode')

        spi.open(self.port_settings.get('bus'), 
                 self.port_settings.get('device'))

        to_send = [packet.get('class'), packet.get('id'),
                   packet.get('ubx_length_lsb'), packet.get('ubx_length_msb'),
                   payload.get('ubx_checkA'), payload.get('ubx_checkB')]

        # xfer2 holds chip select low until the entire block has been sent.
        spi.xfer2([to_send])

        sleep(.3) # 300ms wait

        ublox_response = []

        while True: 
            ublox_response.append(spi.readBytes(1))
            if ublox_response[-1] == 0xFF:
                break
           
        if len(ublox_response) >= 1 
            ubx_response = self.build_response(ublox_response)
            return ubx_response
        else:
            return {}



class UbloxSerial(object):

    def __init__(self, port_settings):
        if port_settings is not None: 
            self.port_settings = port_settings
        else:
            self.port_settings = {
                'port': '/dev/ttyserial0',
                'baud': 9600,
                'timeout': 1
            } 


    def calc_fletch_checksum(self, packet):

        checksum_B = 0
        checksum_A = packet.get('ubx_class')
        checksum_A = checksum_A + packet.get('ubx_id')
        checksum_B = checksum_A + checksum_B
        checksum_A = checksum_A + packet.get('ubx_length')
        checksum_B = checksum_A + checksum_B
        for item in packet.get('ubx_payload'):
            checksum_A = checksum_A + item
            checksum_B = checksum_B + checksum_A

        packet["ubx_checkA"] = checksum_A
        packet["ubx_checkB"] = checksum_B

        return packet

    def build_packet(self, ubx_class, ubx_id, ubx_length, ubx_payload):

        ubx_message = {
            "ubx_class" : ubx_class,
            "ubx_id" : ubx_id,
            "ubx_length_lsb" : ubx_length & 0xFF,
            "ubx_length_msb" : ubx_length >> 8,
            "ubx_length" : ubx_length,
            "ubx_payload" : ubx_payload, #list of bytes
            "ubx_checkA" : None,
            "ubx_checkB" : None
        }

        packet = self.calc_fletch_checksum(ubx_message)

        return packet

    def build_response(self, byte_list):


        packet = {}
        packet['ubx_class'] = byte_list[0]
        packet['ubx_id'] = byte_list[1]
        packet['ubx_length_lsb'] = byte_list[2]
        packet['ubx_length_msb'] = byte_list[3]
        packet['ubx_length'] = (byte_list[3] << 8) | byte_list[2]
        packet['payload'] = byte_list[4:-3]
        packet['ubx_checkA'] = byte_list[-2]
        packet['ubx_checkB'] = byte_list[-1]

        return packet

    def confirm_send(self, ubx_response, packet):

        if ubx_response.get('ubx_class') == UBX_CLASS_ACK:
            if ubx_response.get('ubx_id') == UBX_ACK_ACK:
                if ubx_response.get('ubx_payload')[0] == \
                    packet.get('ubx_class') and \
                    ubx_response.get['ubx_payload'][1] == \
                    packet.get('ubx_id'):
                    return True

            elif ubx_response.get('ubx_id') == UBX_ACK_NAK:
                return False

    def send_command(self, packet):

        with serial.Serial(self.port_settings.get('port'),
                           self.port_settings.get('baud'),
                           timeout=self.port_settings.get('timemout')) as ser:

            ser.write(ubc.UBX_SYNCH_1)
            ser.write(ubc.UBX_SYNCH_2)
            ser.write(packet.get('ubx_class'))
            ser.write(packet.get('ubx_id'))
            ser.write(packet.get('ubx_length_lsb'))
            ser.write(packet.get('ubx_length_msb'))

            for p_item in packet.get('ubx_payload'):
                ser.write(p_item)

            ser.write(packet.get('ubx_checkA'))
            ser.write(packet.get('ubx_checkB'))

            if packet.get('ubx_class') == UBX_CLASS_CFG:

                ublox_response = []

                for byte in range(ser.in_waiting):
                    ublox_response.append(ser.read())

                ubx_response = self.build_response(ublox_response)
                return self.confirm_send(ubx_response, packet)

            return True # Not sure on this

    def receive_command(self, packet):

        with serial.Serial(self.port_settings.get('port'),
                           self.port_settings.get('baud'),
                           timeout=self.port_settings.get('timemout')) as ser:

            ser.write(ubc.UBX_SYNCH_1)
            ser.write(ubc.UBX_SYNCH_2)
            ser.write(packet.get('ubx_class'))
            ser.write(packet.get('ubx_id'))
            ser.write(packet.get('ubx_length_lsb'))
            ser.write(packet.get('ubx_length_msb'))
            ser.write(packet.get('ubx_checkA'))
            ser.write(packet.get('ubx_checkB'))

            sleep(.3) # 300ms wait

            ublox_response = []

            print(ser.in_waiting)
            for byte in range(ser.in_waiting):
                ublox_response.append(ser.read())

            if ublox_response:
                ubx_response = self.build_response(ublox_response)
                return ubx_response
            else
                return {}

