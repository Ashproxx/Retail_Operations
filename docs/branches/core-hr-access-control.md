# HR access control

Owns HR roles in shared API contracts, optional audit subject/field metadata, app/employees/security.py and security regressions. Existing token authenticator provisions HR_ADMIN and scoped HR_USER from server-owned grants. ADMIN/HR_ADMIN may view full profiles; HR_USER is store-scoped; STORE_MANAGER receives an explicit safe-field allowlist; ANALYST is aggregate-only; other roles are denied. No HR role gains legacy retail permissions.

Audit stores authenticated actor, target IDs and field names, never salary/DOB values or full question text. Existing hash-chain verification remains unchanged. Security tests: 20 passed, including legacy suite, field redaction, cross-store denial and audit integrity. No credentials committed.
