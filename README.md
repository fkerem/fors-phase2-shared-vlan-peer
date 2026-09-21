# Phase 2 shared-VLAN peer

This repository-based POWDER profile creates one non-RF d430 peer and connects
it to an existing private shared VLAN. It validates route selection and opens,
then immediately closes, an SCTP association to the configured E2Term NodePort.
It sends no E2AP payload.

The owner experiment must be created first. Supply its random VLAN name,
shared-VLAN address, and live E2Term NodePort when parameterizing this profile.
Do not save the VLAN name in this repository or in shared evidence.

After the startup check, execute only the authorized ingress and isolation
matrix documented in `../../../reports/phase-2-owner-runbook.md`. Terminate this
peer before reserving the indoor OTA resources.
