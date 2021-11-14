Changes
=======

Unreleased
----------

- Driver updates [jbaptperez, awahlig, rousveiga, rnixx]

0.7.1 (2020-09-02)
------------------

- Remove unused problematic imports from ``dali.driver.hasseb``
  [dgomes]

0.7 (2020-08-10)
----------------

- Frame improvements: add ``pack_len()`` method and simplify
  ``str(BackwardFrame())`` output

- Add ``Response.raw_value`` attribute to ``Response`` objects to give
  access to the underlying ``BackwardFrame`` of the response (or
  ``None`` if no response was received)

- Add ``NumericResponse`` and ``NumericResponseMask`` classes and make
  use of them where appropriate

- Rename some ``Command`` class attributes, removing the initial ``_``
  to indicate that they are public. The API now supports
  ``Command.response``, ``Command.devicetype``,
  ``Command.uses_dtr{0,1,2}``, ``Command.inputdev`` and
  ``Command.appctrl`` attributes.

- Add support for "sequences" of commands that implement higher-level
  operations. Initial sequences include commisioning of control gear
  (discovering bus units and assigning short addresses), reading the
  list of device types, querying and setting group membership.

- Remove the obsolete ``dali.bus`` module; all of the useful code from
  it is now implemented as sequences

- 4–5× performance improvement of the ``command.from_frame()``
  function

- Remove support for Python 2

- Some driver additions and changes [sde1000, hasseb, mhemeryck]


0.6 (2018-11-11)
----------------

- Python 3 fix in async Tridonic driver
  [jjonek]

- Updated Hasseb driver
  [dgomes]


0.5 (2017-05-15)
----------------

- Move tests to dedicated package.
  [rnix]

- Rename ``dali.device.Device._addressobj`` to
  ``dali.device.Device.address_obj`` since it is used as API in
  ``dali.command.Command``.
  [rnix]

- Move ``dali.device.Device`` class to ``dali.bus``, ``dali.device`` module
  has been removed which conflicted with ``dali.device`` package.
  [rnix]

- Add ``dali.exceptions`` module and move all DALI related exceptions to it.
  [rnix]

- Move ``dali.interfaces`` to ``dali.drivers.daliserver``.
  [rnix]

- Update Package structure documentation.
  [rnix]


0.4 (2017-03-19)
----------------

- PyPI support
  [dgomes]


0.3
---

- Python 3 support
  [sde1000]


0.2
---

- Introduce basic sync and async drivers.
  [rnix]

- Basic implementation of LUNATONE Dali USB driver.
  [rnix]


0.1
---

- Initial release.
  [sde1000]
