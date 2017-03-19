python-dali — lighting control interface
========================================

DALI ("Digital Addressable Lighting Interface") defines how lighting
control gear (eg. fluorescent ballasts, LED dimmers) and input devices
(push buttons, motion detectors, etc.) should interoperate.  It is
standardised in IEC 62386.

IEC 62386 contains several parts.  Part 101 contains general
requirements for all system components, part 102 covers general
requirements for control gear, and part 103 describes general
requirements for control devices.  Parts 2xx extend part 102 with
lamp-specific extensions and parts 3xx extend part 103 with input
device specific extensions.

This library has been written with reference to the following documents:

- IEC 62386-101:2014 (general requirements for system components)
- IEC 62386-102:2014 (general requirements for control gear)
- IEC 62386-103:2014 (general requirements for control devices)
- IEC 62386-201:2009 (fluorescent lamps)
- IEC 62386-202:2009 (self-contained emergency lighting)
- IEC 62386-205:2009 (supply voltage controller for incandescent lamps)
- IEC 62386-207:2009 (LED modules)

I do not have copies of the other parts of the standard; they are
fairly expensive to obtain.  The library is designed to be extensible;
adding support for the other parts ought to be easy and
self-contained.

Library structure
-----------------

- dali/

  - exceptions.py (not yet implemented - some exceptions defined in-place)
  - frame.py - forward and backward frames
  - command.py - command registry, interface to command decoding
  - gear/ - control gear

     - general.py - commands from part 102
     - fluorescent.py - commands from part 201 (not yet implemented)
     - emergency.py - commands from part 202
     - incandescent.py - commands from part 205
     - led.py - commands from part 207

  - device/ - control devices and events from them

    - general.py - commands and events from part 103

  - interface/

     - daliserver.py - interface to
       https://github.com/onitake/daliserver (not yet implemented -
       currently lives in dali.interfaces module directly)
     - tridonic.py - driver for Tridonic DALI-USB device (prototype -
       needs love)

Copyright
---------

python-dali is Copyright (C) 2013–2017 Stephen Early <steve@assorted.org.uk>

It is distributed under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License and GNU General Public License along with this program.  If
not, see `this link`_.

.. _this link: https://www.gnu.org/licenses/
