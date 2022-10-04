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
- IEC 62386-301:2017 (particular requirements for push button input devices)
- IEC 62386-303:2017 (particular requirements for occupancy sensor input devices)

I do not have copies of the other parts of the standard; they are
fairly expensive to obtain.  The library is designed to be extensible;
adding support for the other parts ought to be easy and
self-contained.

The ``dali.memory`` module supports the extended memory bank
specifications created and maintained by the `Digital Illumination
Interface Alliance`_:

- DiiA DALI Part 251 — Memory Bank 1 Extension
- DiiA DALI Part 252 — Energy Reporting
- DiiA DALI Part 253 — Diagnostics & Maintenance

Python versions supported
-------------------------

This library currently requires Python version 3.7 or later.

Stability
---------

Some of the code in this project is experimental and its API is
subject to change. Modules with stable APIs are noted below.

Library structure
-----------------

- ``dali``

  - ``address`` - Device addressing; stable for gear, not stable for devices

  - ``command`` - Command registry, interface to command decoding; stable

  - ``device`` - DALI control devices as defined in IEC 62386; not stable

    - ``general`` - Commands and events from part 103

    - ``helpers`` - Useful functions and classes for working with DALI control devices

    - ``occupancy`` - Commands from part 303

    - ``pushbutton`` - Commands from part 301

    - ``sequences`` - Packaged sequences for working with DALI control devices

  - ``driver`` - Objects to communicate with physical DALI gateways or
    services; not stable

    - ``base`` - General driver contracts

    - ``hasseb`` - Driver for Hasseb DALI Master

    - ``tridonic`` - Driver for Tridonic DALI USB

    - ``daliserver`` - Driver for https://github.com/onitake/daliserver (needs to be adopted to dali.driver.base API)

    - ``hid`` - asyncio-based drivers for Tridonic DALI USB and hasseb DALI Master

    - ``serial`` - asyncio-based driver for Lunatone LUBA RS232 interfaces

  - ``exceptions`` - DALI related exceptions

  - ``frame`` - Forward and backward frames; stable

  - ``gear`` - DALI control gear as defined in IEC 62386; stable

    - ``colour`` - Commands from part 209 (Device Type 8)

    - ``emergency`` - Commands from part 202

    - ``general`` - Commands from part 102

    - ``incandescent`` - Commands from part 205

    - ``led`` - Commands from part 207

  - ``memory`` - access to memory banks; not stable

  - ``sequences`` - packaged sequences of commands; stable


Contributors
------------

- Stephen Early (Author)

- Robert Niederreiter

- Diogo Gomes

- Caiwan

- Boldie

- Martijn Hemeryck

- Hans Baumgartner

- Ferdinand Keil

- Sean Lanigan, Wallace Building Systems Pty Ltd


Copyright
---------

python-dali is Copyright (C) 2013–2022 Stephen Early <steve@assorted.org.uk>
and other contributors.

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
.. _Digital Illumination Interface Alliance: https://www.dali-alliance.org/dali/data.html
