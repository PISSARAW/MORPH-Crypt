# GenOS GCI operator client

`gci_e2e.py` exercises the Linked pilot from MORPH-Crypt without importing
GenOS into the Rust cryptographic runtime. It discovers the pinned export,
resolves a fixed manifest, links and adopts it for the configured GenOS test
project, checks the installed lockfile, then invokes the descriptor handler
through GenOS's Linked invocation API. GenOS returns a GCI invocation receipt.

## Safety boundary

- Use a dedicated GenOS test project with no production crypto workspace data.
- The client never creates a run, signs an approval, generates a human receipt,
  or changes MORPH-Crypt source.
- The approval payload must already contain valid human approval evidence for
  the selected synthetic test run. The client does not print its token or the
  approval payload.
- Mutations require the explicit `e2e --apply` command. Use a short-lived
  service key limited to `gci:read`, `gci:link`, `gci:adopt`, and `gci:invoke`,
  plus a writable membership in only the test project. Add an IAM policy that
  grants `workspace:write` only to that key, for resource type `gci-capability`,
  ID `PROMOTION_GATE`, and the test tenant/project. Revoke the key, remove the
  policy, and restore the membership after the run.
- GenOS outages never affect the crypto runtime. No GenOS endpoint or secret is
  used by the Rust crates.

## Configure and run

Set `GENOS_GCI_API_URL`, `GENOS_GCI_API_TOKEN`,
`GENOS_GCI_ORGANIZATION_ID`, and `GENOS_GCI_PROJECT_ID` in the operator's
approved secret manager. On systemd, the client can read the token from the
`GENOS_GCI_API_TOKEN` credential file in `CREDENTIALS_DIRECTORY`, so a
transient unit can use `LoadCredentialEncrypted` without placing the token in
its environment. The API URL must be an HTTPS origin, except loopback HTTP for
a same-host deployment. Set `GENOS_GCI_ENVIRONMENT` to a disposable environment
name, for example `morph-crypt-e2e`.

First verify the pinned export with the read-only service key:

```sh
python genos/genos-client/gci_e2e.py inspect
```

Then, after preparing a synthetic run and obtaining its human-signed approval
payload through the approved review process:

```sh
python genos/genos-client/gci_e2e.py e2e --apply \
  --run-id <synthetic-run-id> --approval-file <approval-payload.json>
```

The command reports only the pinned source commit, export digest,
project/environment, binding and installation revisions, invocation result,
and GCI receipt ID. It fails before
any write if the proof file or run ID is missing, the export contract differs,
or the resolver denies authority. It never fabricates a successful receipt.

This validates only the Linked PROMOTION_GATE slice. It does not qualify
Embedded/Managed modes, independent verification, or automatic evolution.
