#!/usr/bin/env python3

import re


VLAN_NAME_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9-]{0,30}\Z")


try:
    _TEXT_TYPE = unicode
except NameError:
    _TEXT_TYPE = str


def _parameter_text(value):
    """Normalize portal strings for both old Python 2 and Python 3 runtimes."""
    if value is None:
        return ""
    if _TEXT_TYPE is not str and isinstance(value, _TEXT_TYPE):
        return value.encode("ascii")
    if _TEXT_TYPE is str and isinstance(value, bytes):
        return value.decode("ascii")
    if isinstance(value, _TEXT_TYPE):
        return value
    return str(value)


def _parse_ipv4(value):
    """Return an IPv4 address as an integer, or None when invalid."""
    text = _parameter_text(value)
    parts = text.split(".")
    if len(parts) != 4:
        return None
    octets = []
    for part in parts:
        if not part or not part.isdigit():
            return None
        octet = int(part, 10)
        if octet > 255:
            return None
        octets.append(octet)
    return ((octets[0] << 24) | (octets[1] << 16) |
            (octets[2] << 8) | octets[3])


def _valid_netmask(mask):
    """Return the mask integer when contiguous, or None when invalid."""
    mask_value = _parse_ipv4(mask)
    if mask_value is None:
        return None
    inverse = (~mask_value) & 0xffffffff
    if inverse & (inverse + 1):
        return None
    return mask_value


def validate_parameters(shared_vlan_name, peer_ip, netmask, owner_ip, e2_port):
    errors = []

    vlan_name = _parameter_text(shared_vlan_name)
    peer_text = _parameter_text(peer_ip)
    netmask_text = _parameter_text(netmask)
    owner_text = _parameter_text(owner_ip)

    if not VLAN_NAME_RE.match(vlan_name):
        errors.append((
            "shared_vlan_name",
            "must contain 1-31 letters, digits, or hyphens and start with a letter or digit"))

    peer = _parse_ipv4(peer_text)
    if peer is None:
        peer = None
        errors.append(("peer_ip", "must be a valid IPv4 address"))

    owner = _parse_ipv4(owner_text)
    if owner is None:
        owner = None
        errors.append(("owner_ip", "must be a valid IPv4 address"))

    mask = _valid_netmask(netmask_text)
    if peer is None or mask is None:
        network = None
        errors.append(("shared_vlan_netmask", "must form a valid IPv4 network with peer_ip"))
    else:
        inverse = (~mask) & 0xffffffff
        network = (peer & mask, peer | inverse)

    if peer is not None and owner is not None and peer == owner:
        errors.append(("owner_ip", "must differ from peer_ip"))
    if network is not None and owner is not None and not network[0] <= owner <= network[1]:
        errors.append(("owner_ip", "must be in the peer shared-VLAN subnet"))
    if network is not None and peer is not None and peer in (network[0], network[1]):
        errors.append(("peer_ip", "must be a usable host address"))
    if network is not None and owner is not None and owner in (network[0], network[1]):
        errors.append(("owner_ip", "must be a usable host address"))

    try:
        port = int(e2_port)
        if not 1 <= port <= 65535:
            raise ValueError
    except (TypeError, ValueError):
        errors.append(("e2_node_port", "must be an integer from 1 through 65535"))

    return errors
