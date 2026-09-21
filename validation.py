#!/usr/bin/env python3

import ipaddress
import re


VLAN_NAME_RE = re.compile(r"^[A-Za-z0-9]{1,31}$")


def validate_parameters(shared_vlan_name, peer_ip, netmask, owner_ip, e2_port):
    errors = []

    if not VLAN_NAME_RE.fullmatch(shared_vlan_name or ""):
        errors.append(("shared_vlan_name", "must contain 1-31 alphanumeric characters"))

    try:
        peer = ipaddress.IPv4Address(peer_ip)
    except ValueError:
        peer = None
        errors.append(("peer_ip", "must be a valid IPv4 address"))

    try:
        owner = ipaddress.IPv4Address(owner_ip)
    except ValueError:
        owner = None
        errors.append(("owner_ip", "must be a valid IPv4 address"))

    try:
        network = ipaddress.IPv4Network("{}/{}".format(peer_ip, netmask), strict=False)
    except ValueError:
        network = None
        errors.append(("shared_vlan_netmask", "must form a valid IPv4 network with peer_ip"))

    if peer is not None and owner is not None and peer == owner:
        errors.append(("owner_ip", "must differ from peer_ip"))
    if network is not None and owner is not None and owner not in network:
        errors.append(("owner_ip", "must be in the peer shared-VLAN subnet"))
    if network is not None and peer is not None and peer in (network.network_address, network.broadcast_address):
        errors.append(("peer_ip", "must be a usable host address"))
    if network is not None and owner is not None and owner in (network.network_address, network.broadcast_address):
        errors.append(("owner_ip", "must be a usable host address"))

    try:
        port = int(e2_port)
        if not 1 <= port <= 65535:
            raise ValueError
    except (TypeError, ValueError):
        errors.append(("e2_node_port", "must be an integer from 1 through 65535"))

    return errors
