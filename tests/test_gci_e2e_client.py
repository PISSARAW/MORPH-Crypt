import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "genos" / "genos-client"))

from gci_e2e import (
    GciClient,
    GciError,
    Settings,
    read_approval,
    read_settings,
    run_e2e,
    safe_origin,
    SOURCE_COMMIT,
)


DESCRIPTOR = {
    "schema": "genos.gci.capability/v1",
    "capabilityId": "PROMOTION_GATE",
    "version": "1.0.0",
    "implementationDigest": "sha256:d4bd558694492718c7a18bcbb0ead36afbde5c09f08006a63b4ce5736c1b94c9",
    "provider": {"id": "genos"},
    "maturity": "integrated",
    "exportModes": ["linked"],
    "inputContract": {},
    "outputContract": {},
    "requiredAuthority": ["workspace:write"],
    "dependencies": [],
    "constraints": {"http": {"path": "/api/execution-runs/{runId}/approve"}},
    "sideEffects": [],
    "evidence": [],
    "revocationPolicy": {"revocable": True},
}
LOCKFILE = {
    "projectId": "project-test",
    "environment": "morph-crypt-e2e",
    "capabilities": [{
        "capabilityId": "PROMOTION_GATE",
        "version": "1.0.0",
        "mode": "linked",
        "implementationDigest": DESCRIPTOR["implementationDigest"],
        "effectiveAuthority": ["workspace:write"],
    }],
}


class FakeGenosHandler(BaseHTTPRequestHandler):
    calls = []
    bad_digest = False
    binding = None
    installation = None

    def log_message(self, _format, *_args):
        return

    def do_GET(self):
        path = urlsplit(self.path).path
        self.calls.append(("GET", path, self.headers.get("Authorization")))
        if path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/api/gci/v1/capabilities")
            self.end_headers()
        elif path == "/api/gci/v1/capabilities":
            self.send_json({"capabilities": [self.descriptor()]})
        elif path == "/api/gci/v1/capabilities/PROMOTION_GATE/1.0.0":
            self.send_json(self.descriptor())
        elif path == "/api/gci/v1/projects/project-test":
            self.send_json({"bindings": [self.binding] if self.binding else [],
                            "installations": [self.installation] if self.installation else []})
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        path = urlsplit(self.path).path
        self.calls.append(("POST", path, self.headers.get("Authorization")))
        if path == "/api/gci/v1/resolve":
            self.send_json({"lockfile": LOCKFILE})
        elif path == "/api/gci/v1/projects/project-test/link":
            self.assert_scope()
            self.__class__.binding = {"providerId": "genos", "revision": 1}
            self.send_json({"providerId": "genos", "revision": 1})
        elif path == "/api/gci/v1/adoptions":
            self.assert_scope()
            self.__class__.installation = {"environment": "morph-crypt-e2e", "revision": 1,
                                           "status": "active", "lockfile": LOCKFILE}
            self.send_json({"revision": 1, "lockfile": payload["manifest"]})
        elif path == "/api/gci/v1/projects/project-test/invocations":
            self.assert_scope()
            self.send_json({"result": {"id": "run-synthetic-1", "status": "completed",
                                        "epistemicState": {"verdict": "executed", "promotable": False}},
                            "receipt": {"schema": "genos.gci.invocation-receipt/v1", "id": "receipt-1",
                                        "implementationDigest": DESCRIPTOR["implementationDigest"]}})
        else:
            self.send_error(404)

    def descriptor(self):
        result = dict(DESCRIPTOR)
        if self.bad_digest:
            result["implementationDigest"] = "sha256:" + "0" * 64
        return result

    def assert_scope(self):
        if self.headers.get("X-Organization-Id") != "org-test" or self.headers.get("X-Project-Id") != "project-test":
            self.send_error(403)
            raise AssertionError("tenant scope headers missing")

    def send_json(self, payload):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class GciClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeGenosHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def setUp(self):
        FakeGenosHandler.calls = []
        FakeGenosHandler.bad_digest = False
        FakeGenosHandler.binding = None
        FakeGenosHandler.installation = None
        port = self.server.server_address[1]
        self.settings = Settings(f"http://127.0.0.1:{port}", "test-secret-do-not-print",
                                 "org-test", "project-test", "morph-crypt-e2e")

    def test_complete_linked_flow_checks_scope_and_never_returns_token(self):
        approval = {"runId": "run-synthetic-1", "signerId": "reviewer", "timestamp": 1,
                    "signature": "a" * 64, "humanApprovalReceipt": {
                        "approved": True, "approvalId": "approval-1", "approverId": "reviewer",
                        "approvedAt": "2026-10-24T12:00:00Z", "payloadHash": "b" * 64,
                    }}
        summary = run_e2e(GciClient(self.settings), "run-synthetic-1", approval)
        paths = [call[1] for call in FakeGenosHandler.calls]
        self.assertEqual(summary["status"], "completed")
        self.assertFalse(summary["promotable"])
        self.assertEqual(summary["implementationDigest"], DESCRIPTOR["implementationDigest"])
        self.assertEqual(summary["invocationReceiptId"], "receipt-1")
        self.assertNotIn(self.settings.token, json.dumps(summary))
        self.assertIn("/api/gci/v1/projects/project-test/link", paths)
        self.assertIn("/api/gci/v1/adoptions", paths)
        self.assertIn("/api/gci/v1/projects/project-test/invocations", paths)
        self.assertTrue(all(call[2] == "Bearer " + self.settings.token for call in FakeGenosHandler.calls))

    def test_digest_mismatch_fails_before_any_write(self):
        FakeGenosHandler.bad_digest = True
        approval = {"runId": "run-synthetic-1", "signerId": "reviewer", "timestamp": 1,
                    "signature": "a" * 64, "humanApprovalReceipt": {
                        "approved": True, "approvalId": "approval-1", "approverId": "reviewer",
                        "approvedAt": "2026-10-24T12:00:00Z", "payloadHash": "b" * 64,
                    }}
        with self.assertRaises(GciError):
            run_e2e(GciClient(self.settings), "run-synthetic-1", approval)
        self.assertFalse(any(method == "POST" for method, _path, _auth in FakeGenosHandler.calls))

    def test_url_requires_https_except_loopback(self):
        self.assertEqual(safe_origin("http://127.0.0.1:4000"), "http://127.0.0.1:4000")
        with self.assertRaises(GciError):
            safe_origin("http://api.example.test")
        with self.assertRaises(GciError):
            safe_origin("https://api.example.test/private")

    def test_systemd_credential_file_supplies_token_without_environment_value(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "GENOS_GCI_API_TOKEN").write_text("short-lived-token", encoding="utf-8")
            settings = read_settings({"GENOS_GCI_API_URL": "http://127.0.0.1:4000",
                "GENOS_GCI_ORGANIZATION_ID": "org-test", "GENOS_GCI_PROJECT_ID": "project-test",
                "CREDENTIALS_DIRECTORY": directory})
        self.assertEqual(settings.token, "short-lived-token")

    def test_authorization_is_not_forwarded_through_redirects(self):
        with self.assertRaises(GciError):
            GciClient(self.settings).call("GET", "/redirect")
        self.assertEqual([call[1] for call in FakeGenosHandler.calls], ["/redirect"])

    def test_approval_file_must_be_bound_to_selected_run(self):
        proof = {"runId": "other-run", "signerId": "reviewer", "timestamp": 1,
                 "signature": "a" * 64, "humanApprovalReceipt": {
                     "approved": True, "approvalId": "approval-1", "approverId": "reviewer",
                     "approvedAt": "2026-10-24T12:00:00Z", "payloadHash": "b" * 64,
                 }}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approval.json"
            path.write_text(json.dumps(proof), encoding="utf-8")
            with self.assertRaises(GciError):
                read_approval(str(path), "run-synthetic-1")

    def test_integration_manifest_pins_client_source(self):
        path = Path(__file__).resolve().parents[1] / "genos" / "integration-manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["genos"]["commit"], SOURCE_COMMIT)


if __name__ == "__main__":
    unittest.main()
