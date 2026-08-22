# Security policy

This pilot is local-first. Do not expose its development ports directly to the
public internet. Store credentials only in ignored `.env` files or a deployment
secret manager; never place them in source, logs, browser bundles, lock manifests,
or post-match case memory.

Report suspected credential exposure, cross-workspace access, prediction-lock
mutation, cutoff leakage, or post-match contamination as a security incident.
Preserve the correlation ID, affected resource IDs, and timestamps without
copying raw provider payloads or secrets into an issue.
