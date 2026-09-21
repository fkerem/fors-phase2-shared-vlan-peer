#!/usr/bin/env python3

import importlib.util
import pathlib
import subprocess
import unittest
from unittest import mock


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "bin" / "preflight-e2.py"
SPEC = importlib.util.spec_from_file_location("phase2_preflight", MODULE_PATH)
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class FakeSocket:
    def __init__(self, connect_error=None):
        self.connect_error = connect_error
        self.closed = False

    def settimeout(self, timeout):
        self.timeout = timeout

    def bind(self, address):
        self.bound = address

    def connect(self, address):
        if self.connect_error:
            raise self.connect_error
        self.connected = address

    def getsockname(self):
        return (self.bound[0], 49152)

    def getpeername(self):
        return self.connected

    def close(self):
        self.closed = True


class PreflightTests(unittest.TestCase):
    @mock.patch.object(preflight.subprocess, "run")
    def test_route_json_is_returned(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 0, '[{"dst":"10.254.254.1","prefsrc":"10.254.254.2"}]', "")
        self.assertEqual(
            "10.254.254.2", preflight.route_to("10.254.254.1")["prefsrc"])

    @mock.patch.object(preflight.socket, "socket")
    def test_successful_sctp_connect_closes_without_payload(self, socket_factory):
        fake = FakeSocket()
        socket_factory.return_value = fake
        local, remote = preflight.sctp_connect(
            "10.254.254.1", 32222, "10.254.254.2", 1.0)
        self.assertEqual(("10.254.254.2", 49152), local)
        self.assertEqual(("10.254.254.1", 32222), remote)
        self.assertTrue(fake.closed)

    @mock.patch.object(preflight.socket, "socket")
    def test_closed_endpoint_propagates_and_closes(self, socket_factory):
        fake = FakeSocket(ConnectionRefusedError("closed"))
        socket_factory.return_value = fake
        with self.assertRaises(ConnectionRefusedError):
            preflight.sctp_connect(
                "10.254.254.1", 32222, "10.254.254.2", 1.0)
        self.assertTrue(fake.closed)

    @mock.patch.object(preflight.socket, "socket")
    def test_timeout_propagates_and_closes(self, socket_factory):
        fake = FakeSocket(TimeoutError("timed out"))
        socket_factory.return_value = fake
        with self.assertRaises(TimeoutError):
            preflight.sctp_connect(
                "10.254.254.1", 32222, "10.254.254.2", 1.0)
        self.assertTrue(fake.closed)


if __name__ == "__main__":
    unittest.main()
