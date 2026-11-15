# Withdrawn capsules

`step-spec-v1.sc.json.withdrawn` is the Build Loop step-spec capsule as it
was written on 2026-08-28, byte for byte. It was never signed and could
never be: its `scp_id` used underscores (`forge-stack/keystone_gate/...`),
which the ratified scp_id pattern forbids, its `document` path did not
resolve from `sc/`, and its `document_sha256` was still `COMPUTE-ON-FREEZE`.

It is kept here, renamed so the Forge Stack's capsule tools
(`sc/**/*.sc.json`) no longer pick it up, and superseded by
`../step-spec-v2.sc.json` (`keystone-gate/build-loop/step-spec-v2`).
Withdrawn 2026-11-15, hardening 6.4 of the-full-stack.
