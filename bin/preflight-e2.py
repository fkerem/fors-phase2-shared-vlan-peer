#!/usr/bin/env python3

import argparse
import json
import socket
import subprocess
import sys
import time


IPPROTO_SCTP = getattr(socket, "IPPROTO_SCTP", 132)


def route_to(target):
    proc = subprocess.run(
        ["ip", "-j", "route", "get", target], check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ip route get failed")
    routes = json.loads(proc.stdout)
    if not routes:
        raise RuntimeError("no route returned")
    return routes[0]


def sctp_connect(owner_ip, port, source_ip, timeout):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, IPPROTO_SCTP)
    try:
        sock.settimeout(timeout)
        sock.bind((source_ip, 0))
        sock.connect((owner_ip, port))
        return sock.getsockname(), sock.getpeername()
    finally:
        sock.close()


def main():
    parser = argparse.ArgumentParser(
        description="Check shared-VLAN routing and SCTP transport without E2AP payloads")
    parser.add_argument("--owner-ip", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--expect-source", required=True)
    parser.add_argument("--wait", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--output")
    args = parser.parse_args()

    deadline = time.monotonic() + max(0, args.wait)
    attempts = 0
    error = "not attempted"
    result = {
        "owner_ip": args.owner_ip,
        "owner_port": args.port,
        "expected_source": args.expect_source,
        "transport": "SCTP",
        "payload_sent": False,
        "success": False,
    }

    while True:
        attempts += 1
        try:
            route = route_to(args.owner_ip)
            result["route"] = route
            if route.get("prefsrc") != args.expect_source:
                raise RuntimeError(
                    "route source {} does not match {}".format(
                        route.get("prefsrc"), args.expect_source))
            local, remote = sctp_connect(
                args.owner_ip, args.port, args.expect_source, args.timeout)
            result["local_socket"] = list(local)
            result["remote_socket"] = list(remote)
            result["success"] = True
            error = None
            break
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            error = str(exc)
            if time.monotonic() >= deadline:
                break
            time.sleep(2)

    result["attempts"] = attempts
    if error:
        result["error"] = error
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output:
            output.write(rendered)
    sys.stdout.write(rendered)
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
