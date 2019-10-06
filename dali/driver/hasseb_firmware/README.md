hasseb USB DALI Master firmware
===============================

## Updating the firmware

The firmware of hasseb USB DALI Master can be updated through USB. By booting the device with jumper JP1 short circuited, the device appears as a mass storage to your computer. The firmware can be update by removing the old firmware.bin file from the mass storage and copying the new firmware to the device. The name of the firmware file does not need to be changed. The most resent firmware can be found in this folder.

## hasseb USB DALI Master protocol

The protocol used in hasseb USB DALI Master is described in this text file. The device appears to the PC as an HID (Human Interface Device) device, such as mouse or keyboard. No special drivers are required. The device is based on NXP LPC1343 microcontroller and the schematics diagram of the device can be found in this folder.



Reports from host to interface
------------------------------

All these reports are 10 bytes long. (? - TBD!)

* Byte 0: command code
* Byte 1: serial number
* Bytes 2–n: depend on command

The device must implement a queue for incoming commands of at least
length 1, i.e. it must be possible to receive and store a command
while still executing the previous command.  This is important for the
implementation of DALI transactions.

### List of command codes

* 0: no operation, ignore this command
* 1: read hardware type
* 2: read firmware version
* 3: read device serial number
* 4: read bus status
* 5: enter firmware update mode
* 6: configure bus
* 7: send frame

### Command code descriptions

Commands 1–4 cause the device to emit a report of the appropriate type.

#### Enter firmware update mode

The device should restart in firmware update mode.  Returning to DALI
Master mode after firmware update is device dependent!

#### Configure bus

Bytes 2 and 3 are only used if the "set power supply" flag bit is set.
Sending this command with the bit not set can be used to read the
current status.

* Byte 2 of the command sets the maximum output current of the
  interface's internal power supply, in mA.  Setting to zero will
  disable the power supply.  Setting to 255 shall be interpreted as
  "the maximum the hardware is capable of".  The standard specifies a
  maximum of 250mA.

  If the device doesn't have an internal power supply, or the internal
  power supply isn't controllable by software, this will be indicated
  in the response.

* Byte 3 of the command sets the voltage of the internal power supply,
  in tenths of a volt.

* Byte 4 contains flag bits:

** Set power supply

** Short the bus (this is useful for testing control gear's response
   to power supply failures)

* Byte 5 sets the maximum number of retransmission attempts during
  collision avoidance.  (The standard doesn't specify a minimum or
  maximum, but it's sensible for the firmware not to retry forever!)

Bytes 6–n must be set to zero.

#### Send frame

XXX I haven't finished assigning data to bits and bytes in this
section yet!  What do we need?

* Frame length 0-31  (for 1-32 bits)  (4 bits)
* Expect reply? (1 bit)
* Transmitter settling time in multiples of 0.1ms (8 bits)
* Send twice settling time in multiples of 0.1ms (8 bits)
* Frame data (up to 32 bits)

The device responds with a transmission report.  If sending twice,
responds with TWO transmission reports.  (NB no reply is expected when
sending twice.)

Settling time is used to implement transactions.  IEC 62386-101
defines a range of settling times for each "priority" in table 22, and
recommends that the precise settling time for each transmission is
chosen at random within the acceptable range.  Simply specifying
settling time in the command allows us to move this logic into the
driver rather than having to implement it in the device.

Reports from interface to host
------------------------------

All these reports are 10 bytes long.  (? - TBD!)

Byte 0: report type
Byte 1: serial number
Bytes 2–n: depend on report type

Reports generated in response to a command from the host will include
the serial number of the command in byte 1.  Reports generated
otherwise (for example in response to bus activity) set byte 1 to
zero.  By convention, the host should not send a command with serial
number zero.

Any bits or bytes not described below should be set to zero.

### List of report types

* 0: no operation, ignore this report
* 1: hardware type
* 2: firmware version
* 3: device serial number
* 4: bus status
* 5: unused
* 6: bus configuration
* 7: transmission report

### Report descriptions

#### Hardware type

* Byte 2: capability bits
** Has internal power supply
** Internal power supply can be switched in software
** Can detect bus overvoltage
* Bytes 3–n: reserved, zero

#### Firmware version

* Byte 2: major version
* Byte 3: minor version

#### Device serial number

* Byte 2: length of serial number in bytes; zero means "unsupported"
* Byte 3–n: serial number, LSB first

#### Bus status

This report can be sent spontaneously when the bus status changes, as
well as in response to a "read bus status" command.

* Byte 2: detected idle bus voltage in tenths of a volt, or zero if
  not implemented

* Byte 3: status bits
** Bus shorted
** Bus overvoltage

#### Bus configuration

* Byte 2: internal power supply maximum current.  If configurable,
  this is the actual maximum current.  If no internal power supply is
  present, this is zero.  If there is an internal power supply but its
  current is set in hardware and not known in firmware, this is 255.

* Byte 3: internal power supply voltage.  If configurable, this is the
  actual voltage in tenths of a volt.  If there is an internal power
  supply but its voltage is set in hardware and not known in firmware,
  this is 255.  If no internal power supply is present, this is zero.

* Byte 4: flags
** Are we deliberately shorting the bus?

#### Transmission report

Sent spontaneously when a forward frame (and possible corresponding
backward frame) is observed on the bus.  Sent once or twice in
response to a "send frame" command.  (If the "send frame" command
specified send-twice, but the first transmission failed, there will be
no attempt to transmit a second time and no second transmission
report.)

XXX I haven't finished assigning data to bits and bytes in this
section yet!  What does this include?

Forward frame - up to 32 bits
Backward frame - 8 bits
Observed settling time - 16 bits
Transmission failure flag - 1 bit (never set for reception)
Backward frame present - 1 bit
Backward frame framing error - 1 bit
Backward frame early - 1 bit

(Framing errors on backward frames are an expected part of the
protocol: they mean "multiple units replied".  If there are multiple
logical units sharing a single physical transmitter, that transmitter
is *required* to transmit a frame with a framing error if multiple
logical units are replying.)
