# M12 security delta

```mermaid
flowchart TD
 token[Opaque bearer token] --> auth[Server-owned grant lookup]
 auth --> context[Trusted principal and scope]
 context --> policy[Role and resource authorization]
 policy --> tools[Registered tool callback]
 policy --> retrieval[Scoped retrieval provider]
 retrieval --> verify[Digest and HMAC verification]
 verify --> evidence[Untrusted evidence data]
 tools --> audit[Metadata audit chain]
 evidence --> audit
 audit --> anchor[Externally trusted anchor]
```

53 nodes / 69 edges. Foundation base 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045. 39 tests and demo passed. Savepoint publication-pending. Official completion 90%. Interfaces and limitations are in BRANCH_README.md. No source-branch integration or global graph mutation.
