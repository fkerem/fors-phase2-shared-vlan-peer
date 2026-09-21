#!/usr/bin/env python3

import geni.portal as portal
import geni.rspec.igext as IG
import geni.rspec.pg as rspec
import geni.rspec.emulab  # Load Emulab shared-VLAN RSpec extensions.

from validation import validate_parameters


UBUNTU_IMAGE = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
COMPONENT_MANAGER = "urn:publicid:IDN+emulab.net+authority+cm"

pc = portal.Context()
pc.defineParameter(
    "shared_vlan_name", "Existing private shared VLAN name",
    portal.ParameterType.STRING, "",
    longDescription="Required. Treat this random name as a secret and do not commit it.")
pc.defineParameter(
    "peer_ip", "Peer shared-VLAN IPv4 address",
    portal.ParameterType.STRING, "10.254.254.2")
pc.defineParameter(
    "shared_vlan_netmask", "Shared-VLAN netmask",
    portal.ParameterType.STRING, "255.255.255.0")
pc.defineParameter(
    "owner_ip", "Owner shared-VLAN IPv4 address",
    portal.ParameterType.STRING, "",
    longDescription="Required. This is the owner experiment's node-0 address.")
pc.defineParameter(
    "e2_node_port", "E2Term SCTP NodePort",
    portal.ParameterType.INTEGER, 32222)

params = pc.bindParameters()
for field, message in validate_parameters(
        params.shared_vlan_name, params.peer_ip, params.shared_vlan_netmask,
        params.owner_ip, params.e2_node_port):
    pc.reportError(portal.ParameterError(message, [field]))
pc.verifyParameters()

request = pc.makeRequestRSpec()
peer = request.RawPC("peer")
peer.component_manager_id = COMPONENT_MANAGER
peer.hardware_type = "d430"
peer.disk_image = UBUNTU_IMAGE

vlan_if = peer.addInterface("shared-vlan-if")
vlan_if.addAddress(rspec.IPv4Address(params.peer_ip, params.shared_vlan_netmask))
vlan = request.Link("phase2-shared-vlan")
vlan.addInterface(vlan_if)
vlan.connectSharedVlan(params.shared_vlan_name)

peer.addService(rspec.Execute(
    shell="bash",
    command=(
        "sudo mkdir -p /local/logs && sudo chown $(id -u):$(id -g) /local/logs && "
        "/local/repository/bin/preflight-e2.py --owner-ip '{}' --port '{}' "
        "--expect-source '{}' --wait 120 --output /local/logs/e2-preflight.json"
    ).format(params.owner_ip, params.e2_node_port, params.peer_ip)))

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, """
### Phase 2 private shared-VLAN peer

This one-node, non-RF profile validates cross-experiment routing and E2Term
SCTP reachability before scarce OTA resources are reserved.
""")
tour.Instructions(IG.Tour.MARKDOWN, """
Wait for the startup service to finish, then inspect:

```
cat /local/logs/e2-preflight.json
```

A successful result proves only routing and SCTP transport reachability. It
does not send E2AP messages or establish an E2 node association. Perform only
the management-boundary probes authorized by the Phase 2 runbook, then
terminate this peer before creating the OTA experiment.
""")
request.addTour(tour)
pc.printRequestRSpec(request)
