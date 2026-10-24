#!/usr/bin/env python3
"""Bounded operator client for the MORPH-Crypt GCI Linked pilot."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


CAPABILITY = "PROMOTION_GATE"
VERSION = "1.0.0"
PROVIDER = "genos"
SOURCE_COMMIT = "236d9c404cbfcc4f305b1fb573b66ad9dbce144f"
IMPLEMENTATION_DIGEST = "sha256:d4bd558694492718c7a18bcbb0ead36afbde5c09f08006a63b4ce5736c1b94c9"
MAX_RESPONSE_BYTES = 1_048_576


class GciError(Exception):
    """Safe-to-display client error; never includes request credentials."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, _request, _response, _code, _message, _headers, _new_url):
        return None


@dataclass(frozen=True)
class Settings:
    origin: str
    token: str
    organization_id: str
    project_id: str
    environment: str


class GciClient:
    def __init__(self, settings: Settings, opener=None):
        self.settings = settings
        self.opener = opener or build_opener(NoRedirect()).open

    def call(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.settings.token}",
            "X-Organization-Id": self.settings.organization_id,
            "X-Project-Id": self.settings.project_id,
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.settings.origin + path, data=body, headers=headers, method=method)
        try:
            with self.opener(request, timeout=10) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise GciError("GenOS response exceeds the client size limit")
                return decode_json(raw)
        except HTTPError as error:
            raise GciError(f"GenOS returned HTTP {error.code}") from None
        except (URLError, TimeoutError, OSError) as error:
            raise GciError(f"GenOS request failed: {type(error).__name__}") from None

    def verify_export(self) -> dict:
        catalogue = self.call("GET", "/api/gci/v1/capabilities")
        exports = catalogue.get("capabilities")
        if not isinstance(exports, list):
            raise GciError("GenOS capability catalogue is invalid")
        listed = next((item for item in exports if is_pinned_export(item)), None)
        inspected = self.call("GET", f"/api/gci/v1/capabilities/{CAPABILITY}/{VERSION}")
        if not is_pinned_export(inspected) or listed != inspected:
            raise GciError("Pinned PROMOTION_GATE export is absent or inconsistent")
        return inspected

    def resolve(self, manifest: dict) -> dict:
        return self.call("POST", "/api/gci/v1/resolve", {"manifest": manifest})

    def status(self) -> dict:
        project = quote(self.settings.project_id, safe="")
        return self.call("GET", f"/api/gci/v1/projects/{project}")

    def link(self, manifest: dict, expected_revision: int) -> dict:
        project = quote(self.settings.project_id, safe="")
        return self.call("POST", f"/api/gci/v1/projects/{project}/link", {
            "manifest": manifest, "expectedRevision": expected_revision,
        })

    def adopt(self, manifest: dict, binding_revision: int, installation_revision: int) -> dict:
        return self.call("POST", "/api/gci/v1/adoptions", {
            "manifest": manifest,
            "expectedBindingRevision": binding_revision,
            "expectedInstallationRevision": installation_revision,
        })

    def invoke(self, payload: dict) -> dict:
        project = quote(self.settings.project_id, safe="")
        return self.call("POST", f"/api/gci/v1/projects/{project}/invocations", payload)


def decode_json(raw: bytes) -> dict:
    try:
        result = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise GciError("GenOS returned invalid JSON") from None
    if not isinstance(result, dict):
        raise GciError("GenOS returned an unexpected response")
    return result


def is_pinned_export(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    constraints = item.get("constraints")
    http = constraints.get("http") if isinstance(constraints, dict) else None
    modes = item.get("exportModes")
    return bool(item.get("capabilityId") == CAPABILITY
        and item.get("version") == VERSION
        and item.get("maturity") == "integrated"
        and item.get("implementationDigest") == IMPLEMENTATION_DIGEST
        and isinstance(modes, list) and "linked" in modes
        and item.get("requiredAuthority") == ["workspace:write"]
        and isinstance(http, dict)
        and http.get("path") == "/api/execution-runs/{runId}/approve")


def read_settings(env: dict[str, str] | None = None) -> Settings:
    values = os.environ if env is None else env
    token = values.get("GENOS_GCI_API_TOKEN") or read_token_credential(values)
    required = ["GENOS_GCI_API_URL", "GENOS_GCI_API_TOKEN",
                "GENOS_GCI_ORGANIZATION_ID", "GENOS_GCI_PROJECT_ID"]
    missing = [name for name in required if not (token if name == "GENOS_GCI_API_TOKEN" else values.get(name))]
    if missing:
        raise GciError("Missing required GCI settings: " + ", ".join(missing))
    origin = safe_origin(values["GENOS_GCI_API_URL"])
    return Settings(origin, token,
        values["GENOS_GCI_ORGANIZATION_ID"], values["GENOS_GCI_PROJECT_ID"],
        values.get("GENOS_GCI_ENVIRONMENT", "morph-crypt-e2e"))


def read_token_credential(values: dict[str, str]) -> str:
    directory = values.get("CREDENTIALS_DIRECTORY")
    if not directory:
        return ""
    try:
        return (Path(directory) / "GENOS_GCI_API_TOKEN").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def safe_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        raise GciError("GCI API URL is invalid") from None
    host = (parsed.hostname or "").lower()
    loopback = host in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise GciError("GCI API URL must use HTTPS, except HTTP on loopback")
    if not host or parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise GciError("GCI API URL must be an origin without credentials or path")
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def read_approval(path: str, run_id: str) -> dict:
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise GciError("Approval proof file cannot be read") from None
    if len(raw) > 65_536:
        raise GciError("Approval proof file exceeds 64 KiB")
    payload = decode_json(raw)
    receipt = payload.get("humanApprovalReceipt")
    if not valid_approval(payload, receipt, run_id):
        raise GciError("Approval proof must match the run and contain a signed human receipt")
    return payload


def valid_approval(payload: dict, receipt: object, run_id: str) -> bool:
    if payload.get("runId") != run_id or not isinstance(payload.get("signerId"), str):
        return False
    timestamp = payload.get("timestamp")
    signature = payload.get("signature")
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        return False
    if not isinstance(signature, str) or not re.fullmatch(r"[a-f0-9]{64}", signature):
        return False
    return valid_receipt(receipt, payload["signerId"])


def valid_receipt(receipt: object, signer_id: str) -> bool:
    if not isinstance(receipt, dict) or receipt.get("approved") is not True:
        return False
    if receipt.get("approverId") != signer_id:
        return False
    if not isinstance(receipt.get("approvalId"), str) or not receipt["approvalId"]:
        return False
    if not isinstance(receipt.get("payloadHash"), str) or not re.fullmatch(r"[a-f0-9]{64}", receipt["payloadHash"]):
        return False
    approved_at = receipt.get("approvedAt")
    if not isinstance(approved_at, str):
        return False
    try:
        datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    return True


def create_manifest(settings: Settings) -> dict:
    return {
        "schema": "genos.gci.project/v1",
        "project": {"id": settings.project_id, "environment": settings.environment},
        "provider": {"id": "morph-crypt"},
        "inherit": [{"capability": CAPABILITY, "version": VERSION, "mode": "linked",
                     "permissions": ["workspace:write"]}],
        "updates": {"policy": "manual", "require_independent_verification": True,
                    "auto_merge": False},
    }


def binding_revision(status: dict) -> int:
    bindings = status.get("bindings", [])
    item = next((row for row in bindings if row.get("providerId") == PROVIDER), None)
    return item.get("revision", 0) if item else 0


def installation_revision(status: dict, environment: str) -> int:
    rows = status.get("installations", [])
    item = next((row for row in rows if row.get("environment") == environment), None)
    return item.get("revision", 0) if item else 0


def validate_lockfile(lockfile: object, descriptor: dict, settings: Settings) -> dict:
    if not isinstance(lockfile, dict) or not isinstance(lockfile.get("capabilities"), list):
        raise GciError("GenOS did not return a resolved lockfile")
    entry = next((item for item in lockfile["capabilities"]
                  if isinstance(item, dict) and item.get("capabilityId") == CAPABILITY
                  and item.get("version") == VERSION), None)
    if (lockfile.get("projectId") != settings.project_id
            or lockfile.get("environment") != settings.environment
            or not entry or entry.get("mode") != "linked"
            or entry.get("implementationDigest") != descriptor["implementationDigest"]
            or entry.get("effectiveAuthority") != ["workspace:write"]):
        raise GciError("Resolved lockfile does not match the pinned Linked export")
    return lockfile


def run_e2e(client: GciClient, run_id: str, approval: dict) -> dict:
    settings = client.settings
    descriptor = client.verify_export()
    manifest = create_manifest(settings)
    plan = client.resolve(manifest)
    lockfile = validate_lockfile(plan.get("lockfile"), descriptor, settings)
    before = client.status()
    linked = client.link(manifest, binding_revision(before))
    adopted = client.adopt(manifest, linked["revision"],
                           installation_revision(before, settings.environment))
    after = client.status()
    installed = next((row for row in after.get("installations", [])
                      if row.get("environment") == settings.environment), None)
    installed_lockfile = installed.get("lockfile") if installed else None
    validate_lockfile(installed_lockfile, descriptor, settings)
    if not installed or installed.get("status") != "active":
        raise GciError("GenOS project does not have an active linked installation")
    invocation = client.invoke({"environment": settings.environment, "capabilityId": CAPABILITY, "args": approval})
    result = invocation.get("result", {})
    epistemic = result.get("epistemicState", {})
    receipt = invocation.get("receipt", {})
    if (result.get("status") != "completed" or epistemic.get("promotable") is not False
            or receipt.get("schema") != "genos.gci.invocation-receipt/v1"
            or receipt.get("implementationDigest") != descriptor["implementationDigest"]):
        raise GciError("Approval route returned an unexpected result contract")
    return {"capabilityId": descriptor["capabilityId"], "version": descriptor["version"],
            "implementationDigest": descriptor["implementationDigest"], "projectId": settings.project_id,
            "environment": settings.environment, "bindingRevision": linked["revision"],
            "installationRevision": adopted["revision"], "runId": run_id,
            "status": result["status"], "promotable": epistemic["promotable"],
            "invocationReceiptId": receipt["id"]}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bounded MORPH-Crypt GCI Linked pilot")
    parser.add_argument("command", choices=["inspect", "e2e"])
    parser.add_argument("--apply", action="store_true", help="allow linking, adoption, and the approval call")
    parser.add_argument("--run-id", help="pre-created synthetic GenOS strategy execution run")
    parser.add_argument("--approval-file", help="pre-existing signed human approval payload JSON")
    args = parser.parse_args(argv)
    if args.command == "e2e" and (not args.apply or not args.run_id or not args.approval_file):
        parser.error("e2e requires --apply, --run-id, and --approval-file")
    if args.command == "inspect" and args.apply:
        parser.error("inspect is read-only and does not accept --apply")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        settings = read_settings()
        client = GciClient(settings)
        if args.command == "inspect":
            descriptor = client.verify_export()
            summary = {"sourceCommit": SOURCE_COMMIT,
                       "capabilityId": descriptor["capabilityId"], "version": descriptor["version"],
                       "implementationDigest": descriptor["implementationDigest"],
                       "projectId": settings.project_id, "environment": settings.environment,
                       "applied": False}
        else:
            approval = read_approval(args.approval_file, args.run_id)
            summary = run_e2e(client, args.run_id, approval)
            summary["sourceCommit"] = SOURCE_COMMIT
        print(json.dumps(summary, sort_keys=True))
        return 0
    except GciError as error:
        print(f"GCI pilot failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
