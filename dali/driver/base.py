"""Basic DALI driver related objects.

A DALI driver is any service or gateway which is able to communicate with a
physical DALI bus.
"""

class DALIDriver(object):
    """Object for handling data received from and sent to specific DALI
    Gateways.

    The API design is meant to fit synchronous and asynchronous implementations.
    """

    dispatcher = None
    """Callable used for dispatching incoming forward frames."""

    def receive(self, data):
        """Extract and dispatch DALI Frame from received data.

        If a forward frame is received, ``self.dispatcher`` is used for
        delegating.

        If a backward frame is received, the ``callback`` given in
        ``self.send`` is used.

        @param data: raw data received from gateway.
        """
        raise NotImplementedError(
            'Abstract ``DALIDriver`` does not implement ``receive``')

    def send(self, command, callback=None, **kw):
        """Construct raw data containing the packed DALI frame from command and
        send to gateway.

        @param command: DALI command to send.
        @param callback: Function which gets called with received response.
        @param **kw: Optional keyword arguments which get passed to response
                     callback
        """
        raise NotImplementedError(
            'Abstract ``DALIDriver`` does not implement ``send``')
