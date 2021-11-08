Changes
=======

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
