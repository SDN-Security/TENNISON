#!/usr/bin/env python3

import requests
import copy

class RPC():
  """Base class for handling messages sent to a remote endpoint, such as Snort
  or ONOS."""

  _snort_endpoint = 'snort'
  _onos_endpoint = 'mervyn'
  _onos_keys = ['sourceIPv4Address', 'sourceTransportPort', \
  'destinationIPv4Address', 'destinationTransportPort', \
  'protocolIdentifier']
  _protocol_identifier_map = {1:"icmp", 6:"tcp", 17:"udp", 58:"icmp6"}
  _valid_protocol_identifiers = [1,6,17,58,"icmp","tcp","udp","icmp"]

  def __init__(self, config):
    """Store the configuration for the Snort and ONOS endpoints."""
    self._snort_uris = config['snort_uris']
    self._onos_uri = config['onos']['uri']

  def call(self, component, method, payload=None, module=None):
    """Make a call to the relevant remote endpoint.

    If the endpoint is used for multiple modules, these can be defined in the
    function call.

    Args:
      component: Element of the Mervyn architecture that should be called (Snort
        or ONOS).
      method: Method name that should be called on that endpoint.
      payload: Data that should be passed in the call.
      module: name of specific module that should be called at the endpoint e.g.
        redirection, mirror and block for the ONOS endpoint.

    """
    return getattr(self, '_' + component)(method, payload, module)

  def _snort(self, method, payload, _):
    """Form the URL for a Snort call. Make a call using HTTP POST. Include the
    payload if necessary."""
    """Form the URL for a Snort call. Make a call using HTTP POST. Include the
    payload if necessary."""
    request_res = []
    for uri in self._snort_uris:
      url = 'http://' + uri + '/' + self._snort_endpoint + '/' + 'rule/' + method
      print(url)

      try:
        if payload:
          request_res.append(self._parse_http_return_code(requests.post(url, json=payload, timeout=1)))
        else:
          request_res.append(self._parse_http_return_code(requests.post(url, timeout=1)))
      except Exception as e:
        print(e)

    return len(request_res) == len(self._snort_uris)

  def _parse_http_return_code(self, request):
    """Parse the HTTP return code into a boolean truth value."""
    print('Response = ' + str(request.status_code))
    if request.status_code == 200:
      return True
    else:
      return False

  def _onos(self, method, payload, module):
    """Form the URL for an ONOS call. Convert a dictionary into the required
    URL string. Make a call using HTTP POST."""
    if payload:
      payload = self._dict_to_url_string(payload)
      if payload is None:
        return False
      url = 'http://' + self._onos_uri + '/' + self._onos_endpoint + '/' + module + '/' + method + '/' + payload
    else:
      url = 'http://' + self._onos_uri + '/' + self._onos_endpoint + '/' + module + '/' + method

    print(url)

    try:
      request = requests.get(url, timeout=1)
      return self._parse_http_return_code(request)
    except Exception as e:
      print(e)
      return False

  def _dict_to_url_string(self, payload):
    """Convert the payload dictionary into the required URL structure and format."""
    if 'protocolIdentifier' in payload and payload['protocolIdentifier'] not in self._valid_protocol_identifiers:
      print("Invalid protocolIdentifier")
      return None 
    
    if 'protocolIdentifier' in payload and payload['protocolIdentifier'] in self._protocol_identifier_map:
      protocol_identifier = self._protocol_identifier_map[payload['protocolIdentifier']]
      payload['protocolIdentifier'] = protocol_identifier

    payload = self._wildcard_payload(payload)
    url = payload['sourceIPv4Address'] + '/' + str(payload['sourceTransportPort']) + '/' + \
          payload['destinationIPv4Address']  + '/' + str(payload['destinationTransportPort'])  + \
          '/' + payload['protocolIdentifier']
    return url

  def _wildcard_payload(self, payload):
    """If a field isn't included in the payload, wildcard this using the '*' symbol."""
    payload = copy.copy(payload)
    for key in self._onos_keys:
      if not key in payload.keys():
        payload[key] = '*'
    return payload
