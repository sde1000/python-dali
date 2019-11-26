hasseb USB DALI Master firmware
===============================

## Updating the firmware

The firmware of hasseb USB DALI Master can be updated through USB. By booting
the device with jumper JP1 short circuited, the device appears as a mass
storage to your computer. The firmware can be update by removing the old
firmware.bin file from the mass storage and copying the new firmware to the
device. The name of the firmware file does not need to be changed. The most
resent firmware can be found in this folder.

## hasseb USB DALI Master protocol

The protocol used in hasseb USB DALI Master is described in this text file.
The device appears to the host PC as an HID (Human Interface Device) device,
such as mouse or keyboard. No special drivers are required. The device is
based on NXP LPC1343 microcontroller and the schematics diagram of the device
can be found in this folder.

hasseb USB DALI Master device communicated with the host PC using 10 long HID
in and out reports. The messages are parsed in the device and data sent to the
DALI bus. Input buffer of 10 messages and output buffer of 2 messages are
implemented into the device. The protocol and message structure is described
below. Note that all functions are not implemented in the present device but
reserved for future use.

Reports from host to interface
------------------------------

* Byte 0: Preamble, always 0xAA
* Byte 1: Command code
* Byte 2: Sequence number
* Bytes 3–9: Command dependent

### List of command codes

* 0x00: No operation, ignore this command
* 0x01: Read hardware type
* 0x02: Read firmware version
* 0x03: Read device serial number
* 0x04: Read bus status
* 0x05: Configure device
* 0x06: Configure bus
* 0x07: Send frame

#### 0x00, No operation

Command code 0x00 is a dummy code and all messages with this code shall be
ignored.

#### 0x01, Read hardware type, NOT IMPLEMENTED

The device responds with a message including the hardware type.

#### 0x02, Read firmware version

The device responds with a message including the firmware version. Only the
command byte is significant, data in the other octets are omitted.

#### 0x03, Read device serial number, NOT IMPLEMENTED

When receiving a message with a command code 0x03, the device responds with
a message including the device serial number.

#### 0x04, Read bus status, NOT IMPLEMENTED

The device responds with a bus status message.

#### 0x05, Configure device

* Byte 3: Mode
  * 0x00: Default mode
  * 0x01: Data sniffing mode, in this mode the device can also sniff the bus

#### 0x06, Configure bus, NOT IMPLEMENTED

Bytes 3 and 4 are only used if the "set power supply" flag bit is set.
Sending this command with the bit not set can be used to read the
current status.

* Byte 3 of the command sets the maximum output current of the
  interface's internal power supply, in mA.  Setting to zero will
  disable the power supply.  Setting to 255 shall be interpreted as
  "the maximum the hardware is capable of".  The standard specifies a
  maximum of 250mA.

  If the device doesn't have an internal power supply, or the internal
  power supply isn't controllable by software, this will be indicated
  in the response.

* Byte 4 of the command sets the voltage of the internal power supply,
  in tenths of a volt.

* Byte 5 contains flag bits:

  * Set power supply

  * Short the bus

  * Byte 6 sets the maximum number of retransmission attempts during
    collision avoidance.

#### 0x07, Send frame

* Byte 2 is the incrementing sequence number of the command. Sequence
  is incremented by one every frame sent. If a response is expected, the
  sequence number of the response frame equals the sequence number of the
  sent frame. Sequence number have to be in range 1-255, zero is not an
  allowed sequence number.
  
* Byte 3 is the length of the DALI data frame in bits. The default is 16
  bits. 24-bit frames will be supported in future.
  
* Byte 4 is a flag indicating if a response is expected. 0 for no response,
  1 for response.
  
* Byte 5: Reserved

* Byte 6: If set to other value than 0, the message will be sent twice. The
  value in byte 6 determines the delay between messages in milli seconds.

* Bytes 7-9: Data bytes sent to DALI bus.

Reports from interface to host
------------------------------

* Byte 0: Preamble, always 0xAA
* Byte 1: Report type
* Byte 2: Sequence number
* Bytes 3–9: Report dependent

Reports generated in response to a command from the host will include
the sequence number of the command in byte 2. Reports generated
otherwise (for example in response to bus activity) byte 2 is set to
zero. Commands with sequence number zero are not allowed from host.

### List of report types

* 0x00: No operation, ignore this report
* 0x01: Hardware type
* 0x02: Firmware version
* 0x03: Device serial number
* 0x04: Bus status
* 0x05: Unused
* 0x06: Bus configuration
* 0x07: Transmission report

### Report descriptions

#### Hardware type, NOT IMPLEMENTED

* Byte 3: capability bits
  * Bit0: Has internal power supply
  * Bit1: Internal power supply can be switched in software
  * Bit2: Can detect bus over voltage
* Bytes 4–n: reserved, zero

#### Firmware version

* Byte 3: major version
* Byte 4: minor version

#### Device serial number, NOT IMPLEMENTED

* Byte 3: length of serial number in bytes; zero means "unsupported"
* Byte 4–n: serial number, LSB first

#### Bus status, NOT IMPLEMENTED

This report can be sent spontaneously when the bus status changes, as
well as in response to a "read bus status" command.

* Byte 3: detected idle bus voltage in tenths of a volt, or zero if
  not implemented

* Byte 4: status bits
  * Bus shorted
  * Bus over voltage

#### Bus configuration, NOT IMPLEMENTED

* Byte 3: internal power supply maximum current. If configurable,
  this is the actual maximum current. If no internal power supply is
  present, this is zero. If there is an internal power supply but its
  current is set in hardware and not known in firmware, this is 255.

* Byte 4: internal power supply voltage. If configurable, this is the
  actual voltage in tenths of a volt. If there is an internal power
  supply but its voltage is set in hardware and not known in firmware,
  this is 255. If no internal power supply is present, this is zero.

* Byte 5: flags
  * Bit 0: Bus short circuited.

#### Transmission report

A report sent to host when a DALI message is received from the bus.

* Byte 2: Sequence number. If the report is a backward frame, the sequence
  number equals the sequence number of the forward frame. For a 
  sniffing byte, the sequence number is zero.
  
* Byte 3: Report type
  * 0x01: No response received
  * 0x02: Response data received
  * 0x03: Invalid data
  * 0x04: Answer too early
  * 0x05: Sniffing byte
  * 0x06: Sniffing byte error

* Byte 4: Data length in bits

* Byte 5-7: Data

