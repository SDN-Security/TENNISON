#!/usr/bin/env python3

import collections
import ast
import copy
import core.treatment as treatment
import logging
from scapy.layers.inet import Ether, IP
from datetime import datetime
from collections import namedtuple
from netaddr import IPNetwork, IPAddress

class MessageHandler():
    """Base class for handling messages of all types."""

    Match = collections.namedtuple('Match', ['priority', 'treatment', 'criteria'])
    treatment = treatment.Treatment()

    def __init__(self, ipfix_thresholds, snort_thresholds, rpc_handler):
        """Create new instances of the different message handlers.

        Args:
            thresholds: a list of threshold values for each type of message.

        """

        self.log = logging.getLogger('message_handler')
        self.treatment.add_rpc_handler(rpc_handler)
        self._ipfix = IPFIX(ipfix_thresholds)
        self._snort = Snort(snort_thresholds)
        self._sflowrt = sFlowRT()

    def handle(self, message):
        """Handle a message sent from the coordinator by selecting the correct
        object."""
        #self.log.info("Message recieved " + str(message))
        getattr(self, '_' + message['type']).handle(message)

    def _form_match_result(self, matches):
        """Prepare the result return values, given the amount of matches found.

        Returns:
            Success or failure of match along with a list of matches.
        """
        if len(matches) > 0:
            return True, matches
        else:
            return False, None

    def _find_highest_priority_match(self, matches):
        """Given a number of matches, return the highest priority match.

        Returns:
            The highest match.
        """
        highest = matches[0]
        for match in matches:
            if match['priority'] > highest['priority']:
                highest = match
        return highest

    def _create_treatment_fields(self, match, message):
        """Compiles a list of fields to wich to apply the treatment. Combination
        of fields within message and variable treatment_fields.

        Returns:
            Dictironary of treatment fields.
        """
        if 'treatment_fields' not in match:
            return message

        for key, value in match['treatment_fields'].items():
            if value == '$':
                match['treatment_fields'][key] = message[key]

        return match['treatment_fields']


class Snort(MessageHandler):
    """Message handler for Snort-based messages."""

    def __init__(self, thresholds):
        """Initialise the handler class.

        Store the thresholds loaded from the thresholds.yaml configuration file.

        Args:
            thresholds: a list of threshold values for Snort messages.

        """
        self._thresholds = thresholds
        self.log = logging.getLogger('message_handler')

    def handle(self, message):
        """Handle a Snort message forwarded from the coordinator.

        If there is one or more matches, determine the highest priority match.
        Then apply the configured treatment.

        Args:
            message: Snort message to parse.

        """
        # TODO default treatment for snort alerts with no threshold
        success, matches = self._find_match(message)
        if success:
            highest_match = super()._find_highest_priority_match(matches)
            self.log.info("Match found: " + str(highest_match))

            treatment_fields = self._create_treatment_fields(highest_match, message['pkt'])
            self.log.info("Treatment fields: " + str(treatment_fields))
            super().treatment.apply(highest_match, treatment_fields)
        else:
            self.log.info("No match for snort alert: " + message['alertmsg'])

    def _find_match(self, message):
        """Compile a list of threshold matches.

        Finds the relevant thresholds that match the Snort message. Uses the
        'alertmsg' field within the message to match against the Snort rule
        definitions included in each threshold. The content of 'alertmsg' should
        have been set to the raw alert definition to make for easier matching.

        Returns:
            A list of threshold matches, including the priority level, the
            treatment required and the rule it matched upon.
        """
        matches = []
        for ti, threshold in self._thresholds.items():
            if threshold['alertmsg'] == message['alertmsg']:
                matches.append(threshold)
        return super()._form_match_result(matches)

class sFlowRT(MessageHandler):
    def __init__(self):
        self.log = logging.getLogger('sFlowRT message handler')
        self.log.info("Starting sFlowRT message handler")

    def handle(self, message):
        # WARNING TODO there seems to be no error handling in this function
        self.log.info(message)
        # get the dst(or src) IP to block?
        matches = []
        if message['action'] == 'ddos_set':
            host = message['dst'].split(':')[0]
        else:
            host = message['flowKey'].split(',')[0]

        # matches.append(self.Match(10, message['action'], {"sourceIPv4Address": host}))
        matches.append({'priority':10,
                        'treatment': message['action'],
                        'criteria': {'sourceIPv4Address': host}
                      })
        self.log.info('sFlowRT match rule: {} ({})'.format(host, message['action']))
        super().treatment.apply(matches[0], matches[0]['criteria'])


class IPFIX(MessageHandler):
    """Message handler for IPFIX-based messages."""

    _masks = {}
    _delta_bps = {}
    _avg_bps = {}

    Flow = namedtuple("Flow", ["sourceIPv4Address", "destinationIPv4Address", "sourceTransportPort", "destinationTransportPort"])

    _protocol_identifiers = {1:"icmp", 6:"tcp", 17:"udp", 58:"icmp6"}

    def __init__(self, thresholds):
        """Initialise the handler class.

        Create the IPFIX masks loaded from the thresholds.yaml configuration file.

        Args:
            thresholds: a list of threshold values for IPFIX messages.

        """
        self._thresholds = thresholds
        self.log = logging.getLogger('IPFIX Message handler')
        self._create_initial_masks(thresholds)

    def _create_initial_masks(self, thresholds):
        """For each of the masks in the configuration file, create and add a
        new mask to the handlers master set."""

        # Make copy of loaded thresholds - may need to do deepcopy here
        self._loaded_thresholds = dict(thresholds)
        self._masks = {}

        for mi, mask in thresholds.items():
            self._add_mask(mask)

    def _add_mask(self, state):
        """For each unique combination of fields, create a new mask. Then attach
        a set of acceptable values for that mask."""
        keys = state['fields'].keys()
        if not tuple(keys) in self._masks:
            self._masks[tuple(keys)] = []
        self._masks[tuple(keys)].append(state)

    def handle(self, message):
        """Handle an IPFIX message forwarded from the coordinator.

        If there is one of more matches, determine the highest priority match.
        Then apply the configured treatment.

        Args:
            message: IPFIX message to parse.

        """

        # Check if thresholds have been updated (via watson NBI) - reload if so
        if self._loaded_thresholds != self._thresholds:
            self.log.info('Reloading thresholds')
            self._create_initial_masks(self._thresholds)

        # TODO Consider IPv6
        if 'sourceIPv4Address' not in message or 'destinationIPv4Address' not in message or 'sourceTransportPort' not in message or 'destinationTransportPort' not in message:
            self.log.warning("Did not recognise IPFIX message")
            return


        flow = self.Flow(sourceIPv4Address=message['sourceIPv4Address'], destinationIPv4Address=message['destinationIPv4Address'], sourceTransportPort=message['sourceTransportPort'], destinationTransportPort=message['destinationTransportPort'])

        self.log.info("IPFIX update srcTP: " + str(message['sourceTransportPort']) + ' destTP: ' + str(message['destinationTransportPort']))

        flow_stats = {}
        flow_stats['byte_total'] = message['octetDeltaCount']
        flow_stats['packet_total'] = message['packetDeltaCount']
        if flow in self._delta_bps:
            flow_stats['byte_diff'] = message['octetDeltaCount']  - self._delta_bps[flow]['last_byte_count']
            flow_stats['packet_diff'] = message['packetDeltaCount'] - self._delta_bps[flow]['last_packet_count']
            flow_stats['time_diff'] = datetime.now() - self._delta_bps[flow]['last_message_time']
            if flow_stats['time_diff'].seconds > 0:
                flow_stats['delta_bps'] = flow_stats['byte_diff'] / flow_stats['time_diff'].seconds
                flow_stats['delta_pps'] = flow_stats['packet_diff'] / flow_stats['time_diff'].seconds

        self._delta_bps[flow] = {"last_message_time" : datetime.now(), "last_byte_count" : message['octetDeltaCount'], "last_packet_count" : message['packetDeltaCount']}

        # update totals
        if flow in self._avg_bps and 'delta_bps' in flow_stats and 'delta_pps' in flow_stats:
            total_bps = self._avg_bps[flow]['total_bps'] + flow_stats['delta_bps']
            total_pps = self._avg_bps[flow]['total_pps'] + flow_stats['delta_pps']
            message_count = self._avg_bps[flow]['message_count'] + 1
            self._avg_bps[flow] = {'total_bps' : total_bps, 'total_pps' : total_pps, 'message_count' : message_count}
        elif flow not in self._avg_bps and 'delta_bps' in flow_stats and 'delta_pps' in flow_stats:
            total_bps = flow_stats['delta_bps']
            total_pps = flow_stats['delta_pps']
            self._avg_bps[flow] = {'total_bps' : total_bps, 'total_pps' : total_pps, 'message_count' : 1}

        # calculate averages
        if flow in self._avg_bps:
            flow_stats['avg_bps'] = self._avg_bps[flow]['total_bps'] / self._avg_bps[flow]['message_count']
            flow_stats['avg_pps'] = self._avg_bps[flow]['total_pps'] / self._avg_bps[flow]['message_count']

        success, matches = self._find_mask_match(message)
        if success:
            highest_match = super()._find_highest_priority_match(matches)
            self.log.info("Match found: " + str(highest_match))

            if self._check_threshold(flow_stats, highest_match):
                if 'treatment_fields' in highest_match:
                    super().treatment.apply(highest_match, highest_match['treatment_fields'])
                else:
                    super().treatment.apply(highest_match, message)
        else:
            self.log.info("No threshold found for IPFIX message")

    def _check_threshold(self, flow_stats, match):
        """Check if a threshold has been exceeded and should be triggered

        Args:
            flow_stats: gathered statistics of the flow
            match: threshold to checki

        Returns:
            True if exceeded, False otherwise.
        """

        # TODO Tidy
        valid_metrics = ['byte_total', 'packet_total', 'byte_diff', 'packet_diff', 'time_diff', 'delta_bps', 'delta_pps', 'avg_bps', 'avg_pps']

        # no threshold
        if 'metric' not in match or 'threshold' not in match:
            self.log.info("No metric or threshold for" + str(match))
            return True

        # invalid metric - should this be True????
        if match['metric'] not in valid_metrics:
            self.log.info("Invalid metric: " + match['metric'])
            return False

        # dont have data
        if match['metric'] not in flow_stats:
            self.log.info("Insufficent data")
            return False

        # test threshold
        if match['threshold'] < flow_stats[match['metric']]:
            self.log.info("Threshold " + match['metric'] + "(" + str(match['threshold']) + ") exceeded with value " + str(flow_stats[match['metric']]))
            return True
        else:
            self.log.info("Threshold " + match['metric'] + "(" + str(match['threshold']) + ") not exceeded with value " + str(flow_stats[match['metric']]))
            return False

    def _find_mask_match(self, message):
        """Compile a list of threshold matches.

        Compares the message to each of the available masks. Determine if the
        masked values are a match. Check if the message subtype matches.

        Returns:
            A list of threshold matches, including the priority level, the
            fields and the treatment required.
        """
        matches = []
        for mask in self._masks:
            if frozenset(mask).issubset(frozenset(message.keys())):
                for state in self._masks[mask]:
                    if self._test_match_similarity(state, message):
                        if self._test_subtype(state, message):
                            matches.append(state)
        return super()._form_match_result(matches)


    def _test_match_similarity(self, state, message):
        """ Determine whether all of the field values match between the
        threshold and the IPFIX record.

        Returns:
            Success or failure of field matching.
        """
        for key, value in state['fields'].items():
            if key == 'protocolIdentifier':
                if not self._test_protocol(message[key], value):
                    return False
            elif key == 'sourceIPv4Address' or key == 'destinationIPv4Address':
                if not self._test_ip_address(message[key], value):
                    return False
            elif message[key] != value:
                return False
        return True

    def _test_protocol(self, message_value, state_value):
        """Checks if the integer protocolIdenifier from an IPFIX message matches
        the string representation from the threshold

        Args:
            message_value: protocolIdentifier from the IPFIX message
            state_value: protoclIdentifier from the threhsold/state

        Returns:
            True if matching, Flase otherwise.
        """
        if self._protocol_identifiers[message_value] == state_value.lower():
            return True
        return False

    def _test_ip_address(self, message_value, state_value):
        """ Checks if the specific IP address from an IPFIX messages matches
        or is within IP address from the threshold, which can be a subnet.

        Args:
            message_value: IPv4 Address from the IPFIX message
            state_value: IPv4 Address from the threshold/state

        Returns:
            True if matching, False otherwise.
        """
        # Check if masked
        if '/' in state_value:
            return IPAddress(message_value) in IPNetwork(state_value)
        else:
            return state_value == message_value

    def _test_subtype(self, state, message):
        """Check to see if the state contains a subtype, and ensure that it
        matches if it is included.

        Returns:
            Success or failure of subtype match.
        """
        if 'subtype' in state and 'subtype' in message:
            if message['subtype'] == state['subtype']:
                return True
            else:
                return False
        return True



