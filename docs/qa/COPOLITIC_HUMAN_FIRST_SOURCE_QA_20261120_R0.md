# CoPolitic human-first source QA R0
Observed 2026-11-20 UTC
Scope: GitHub review branch source, NOT a browser or public deployment test.

Repository: CoCivium/CoPolitic-site
Branch: review/copol-human-first-r0-20261117
Source path: index.html
Observed source blob SHA: 351a070ee2daec7aae9994080bdf17e9ef3a8ebb
Source character length: 11542

## Deterministic source checks
- Internal href="#id" references: 11
- Missing referenced ids: 0
- Duplicate ids: 0
- Journalist-facing section id=journalists: PRESENT
- noindex,nofollow: PRESENT
- Existing correction route: PRESENT
- External links: enumerated but not independently fetched or tested

## Comparison notes
- 2026-11-10 candidate source SHA 1ae823ad0072cb310c2f30f7cb464c05b375a43f: richer machine-readable navigation, ai/index.json and llms.txt.
- 2026-11-17 review source SHA before journalist section f9033cdef1389a775a481bba1ef94c5b8b4eb8d0: explicit noindex and restrained public-source claim.
- Review branch now adds an editor-facing explanation without claiming publication.
- No merge or supersession of the 2026-11-10 candidate is implied.

## Required acceptance before release
1. Browser render, keyboard focus, mobile readability and screenshot.
2. Fetch and verify external evidence links.
3. Verify public domain, DNS, HTTPS, serving commit and rollback.
4. Confirm authorized public release and contact/corrections route.
5. Independent external URL readback, deployment log and functional test.

Disposition: SOURCE_QA_PASS; UX_ACCEPTANCE_UNPROVEN; PUBLIC_HOLD.
Nonclaims: NOT_LIVE; NOT_DEPLOYED; NOT_RECEIVER_PICKUP; NOT_COEX; NOT_CANON; NOT_RUNTIME; NOT_EDITOR_ACK.
