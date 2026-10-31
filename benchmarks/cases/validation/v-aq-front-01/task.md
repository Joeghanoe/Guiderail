# The customer list stops at 50

An admin reports that the customer list in the sidebar and on the admin screens has exactly 50 entries, and the
customers they added last week are missing. The customer exists when they look it up by direct link.

API contract for the list call, as published by the service:

- GET /api/v1/customers?pageSize={1..100, default 50}&continuationToken={opaque}
- 200 returns `{ "customers": [...], "continuationToken": "<opaque>" | null }`; a null token means this was the last page.

Fix the portal so every customer is available.
