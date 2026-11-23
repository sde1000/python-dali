"""Commands and responses from IEC 62386 part 201."""

from dali.gear.general import _StandardCommand, QueryExtendedVersionNumberMixin


class _FluorescentCommand(_StandardCommand):
    devicetype = 0


###############################################################################
# Commands from IEC 62386-201 section 11.3.1
###############################################################################


class QueryExtendedVersionNumber(QueryExtendedVersionNumberMixin,
                                 _FluorescentCommand):
    """Query Extended Version Number

    Returns the version number of IEC 62386-201 implemented by the
    control gear.

    This is the only application extended command defined by part 201:
    everything fluorescent lamp control gear can be asked to do is in
    part 102.  Opcodes 224 to 254 are reserved and shall be ignored.
    """
    pass
