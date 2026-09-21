# Phase 2 shared-VLAN peer

This repository-based POWDER profile creates one non-RF d430 peer and connects
it to an existing private shared VLAN. It validates route selection and opens,
then immediately closes, an SCTP association to the configured E2Term NodePort.
It sends no E2AP payload.

The profile imports in an inert preview state. When instantiating it, set
`enable_shared_vlan_peer` to true and supply the owner experiment's random VLAN
name and shared-VLAN address. Confirm the live E2Term NodePort, leaving `32222`
only when it matches the owner. The peer address defaults to `10.254.254.2/24`.
Do not instantiate the disabled preview configuration, and do not save the VLAN
name in this repository or in shared evidence.

After the startup check, execute only the authorized ingress and isolation
matrix documented in `../../../reports/phase-2-owner-runbook.md`. Terminate this
peer before reserving the indoor OTA resources.
