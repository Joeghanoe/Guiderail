# Criteria v-aq-front-01 (hidden from the candidate)

Functional
- G01 All pages are fetched until the token is null or absent; the hook still returns a flat list of customers.
- G02 The response type uses the name the service really publishes (`continuationToken`). The existing portal type uses a different name, which is why the token was never read; the candidate must notice and fix the type, not read both names.
- G03 The token is URL-encoded when sent; pageSize is set to the maximum allowed (100) or left to default, not removed from the contract.
- G04 A page that fails fails the whole load (no silent partial list), and the existing role-based `enabled` logic is unchanged.
- G05 Unit tests with mocked fetch: two pages, three pages, one page with null token, a failing second page, an empty list. The existing hook tests still pass or are updated with reason.
- G06 No new dependency; no infinite loop if the service repeats a token (a guard or a page limit with an error, not a silent stop).

Rules checked: CODE.7 (the portal type and the service contract are a linked pair: the candidate says where the pair is documented or adds a check where possible), CODE.2 (no silent truncation), T.4 (the escaped defect gets a test), T.2 (fetch and auth are injected as in the existing helpers).

Hard gates
- Typecheck, lint and unit tests pass (T.1).
- A test proves that a customer on page two is returned (T.4).

Regressions
- Raising pageSize beyond the documented maximum as the "fix".
- Fetching all pages in a component instead of in the api layer.
- Changing the query key shape without updating the invalidation calls.
