###############################################################################
# driver contracts
###############################################################################
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from dali.command import Command
    from dali.frame import Frame


class DALIDriver:
    """Object for handling wrapped DALI frames sent to and received from
    DALI drivers.

    A DALI driver represents a service or physical gateway which is able to
    communicate with a DALI bus.
    """

    backend: Optional[Backend] = None
    """``Backend`` instance used for reading and writing."""

    def construct(self, command: Command) -> bytes:
        """Construct raw data containing the packed DALI frame from command
        which can be sent to DALI driver.

        @param command: DALI command to send.
        @return data: Returns data which can be sent to backend.
        """
        raise NotImplementedError(
            'Abstract ``DaliDriver`` does not implement ```construct`')

    def extract(self, data: bytes) -> Frame:
        """Extract and return DALI Frame from data which has been received
        from DALI driver.

        @param data: Raw data received from gateway.
        @return frame: Returns ``dali.frame.Frame`` deriving object.
        """
        raise NotImplementedError(
            'Abstract ``DaliDriver`` does not implement ``extract``')


class SyncDALIDriver(DALIDriver):
    """Object for synchronously sending data to DALI drivers immediately
    expecting and returning a result.
    """

    def send(self, command: Command, timeout: Optional[int] = None) -> Any:
        """Send command to gateway and return response.

        @param command: DALI command to send.
        @param timeout: Timeout in milliseconds.
        @return response: response to command.
        """
        raise NotImplementedError(
            'Abstract ``SyncDALIDriver`` does not implement ``send``')


class AsyncDALIDriver(DALIDriver):
    """Object for asynchronously handling data sent to and received from
    DALI drivers.
    """

    dispatcher: Optional[Callable[..., Any]] = None
    """Callable used for dispatching incoming forward frames.
    """

    def send(
        self,
        command: Command,
        callback: Optional[Callable[..., Any]] = None,
        **kw: Any,
    ) -> None:
        """Send command to gateway.

        @param command: DALI command to send.
        @param callback: Function which gets called with received response.
        @param **kw: Optional keyword arguments which get passed to response
                     callback
        """
        raise NotImplementedError(
            'Abstract ``AsyncDALIDriver`` does not implement ``send``')

    def receive(self, frame: Frame) -> None:
        """Receive DALI Frame.

        If a forward frame is received, ``self.dispatcher`` is used for
        delegating it.

        If a backward frame is received, the ``callback`` given in
        ``self.send`` is used.

        @param frame: ``dali.frame.Frame`` deriving object.
        """
        raise NotImplementedError(
            'Abstract ``AsyncDALIDriver`` does not implement ``receive``')


###############################################################################
# backend contracts
###############################################################################

class Backend:
    """Object representing a backend.
    """

    def read(self, timeout: Optional[int] = None) -> Any:
        raise NotImplementedError(
            'Abstract ``Backend`` does not implement ``read``')

    def write(self, data: bytes) -> None:
        raise NotImplementedError(
            'Abstract ``Backend`` does not implement ``write``')

    def close(self) -> None:
        raise NotImplementedError(
            'Abstract ``Backend`` does not implement ``close``')


class Listener(Backend):
    """Object representing a backend which is permanently listening for
    incoming frames.
    """

    driver: Optional[AsyncDALIDriver] = None
    """``AsyncDALIDriver`` instance.
    """

    def listen(self) -> None:
        """Listen to backend and dispatch receiced data to ``self.driver``.
        """
        raise NotImplementedError(
            'Abstract ``Listener`` does not implement ``listen``')
