"""
trace_logging.py - Additional logging level, for very verbose development logging


This file is part of python-dali.

python-dali is free software: you can redistribute it and/or modify it under the terms of the GNU
Lesser General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.
"""
import logging

_LOG = logging.getLogger(f"dali")
_logging_trace_created = False


def add_logging_level(level_name: str, level_num: int):
    """
    Original source: https://stackoverflow.com/a/35804945

    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`.
    """
    method_name = level_name.lower()

    if hasattr(logging, level_name):
        _LOG.warning(f"{level_name} already defined in logging module")
        return
    if hasattr(logging, method_name):
        _LOG.warning(f"{method_name} already defined in logging module")
        return
    if hasattr(logging.getLoggerClass(), method_name):
        _LOG.warning(f"{method_name} already defined in logger class")
        return

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, logForLevel)
    setattr(logging, method_name, logToRoot)


if not _logging_trace_created:
    add_logging_level("TRACE", logging.DEBUG - 5)
    _logging_trace_created = True
