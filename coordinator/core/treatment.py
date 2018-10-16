#!/usr/bin/env python3


class Treatment():
    """Represents the actions that should be taken when a threshold is exceeded."""

    def __init__(self):
        pass

    def apply(self, match, treatment_fields):
        """Apply the required treatment by calling the appropriate function.

        Args:
          match: Match object, containing the match priority, the required
            treatment and the criteria needed to apply this treatment.
          message: Message object, as received at the collector.

        """
        getattr(self, '_' + match['treatment'])(treatment_fields)

    def add_rpc_handler(self, rpc_handler):
        """Set the object used to send procedure calls to remote endpoints."""
        self._rpc_handler = rpc_handler

    def _ipfix(self, treatment_fields):
        """Call the ONOS API to install a ipfix monitoring rule in the network """
        self._rpc_handler.call('onos', 'add', payload=treatment_fields, module='ipfix')

    def _snort_mirror(self, treatment_fields):
        """Call the ONOS API to install a mirroring rule in the network."""
        self._rpc_handler.call('onos', 'add', payload=treatment_fields, module='mirror')

    def _snort_redir(self, treatment_fields):
        """Call the ONOS API to install a redirection rule in the network."""
        self._rpc_handler.call('onos', 'add', payload=treatment_fields, module='redirect')

    def _block(self, treatment_fields):
        """Call the ONOS API to install a block rule in the network."""
        self._rpc_handler.call('onos', 'add', payload=treatment_fields, module='block')

    def _ddos_set(self, treatment_fields):
        self._rpc_handler.call('onos', 'add', payload=treatment_fields, module='block')

    def _ddos_clear(self, treatment_fields):
        self._rpc_handler.call('onos', 'delete', payload=treatment_fields, module='block')

