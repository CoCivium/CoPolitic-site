# CoPolitic.org launch rail R1

**State:** `CANDIDATE_TESTED` (source only). Not `AUTHORIZED`, not `DEPLOYED`, not `PUBLIC_VERIFIED`.
**Base:** PR #1, `candidate/copolitic-first-use-source-site-r0-20261110` at `038a87a809f0b260aea8dc80cb92e085dcda4755`. Prior work is preserved. R1 adds only a domain declaration, a source lock, a verifier and tests.

## 1. What R1 adds
- `CNAME` = `copolitic.org`. This is inert until a Pages admin points Pages at a branch that contains it.
- `ai/sources.lock.json` pins all 8 external sources the page links to, each to an exact commit and blob. All 8 were verified unchanged upstream at 2026-11-18T15:5xZ.
- `tools/verify_sources_lock.py` re-verifies the lock with plain git, read-only, and reports drift.
- `tests/test_copolitic_r1_rail.py` (6 tests) covers: a single CNAME equal to the planned host, every human and machine source pinned, human links being a subset of machine sources, and no "live" claims.
- The CI path filter now covers `tests/**`, `tools/**`, `CNAME` and the lock.

## 2. Observed boundary (inherited, not re-observed by R1)
PR #1 records two different observations of `www.copolitic.org`, and both are kept:
- `docs/COPOLITIC_RELEASE_GATE_R0_20261117.md` records a TLS name/SNI failure.
- `ai/index.json` records `APEX_404_WWW_502`.

Both sources record `https://copolitic.org/` as 404. R1 could not reach either host: this session's egress proxy refused them. `copolitic.org` is **not** among the six Active Cloudflare zones in the starting evidence. Its DNS provider is therefore unknown, and it may be the GoDaddy DNS default.

## 3. Release steps (each needs the named authority; none was taken here)
| # | Step | Authority | Reversible by |
|---|---|---|---|
| 1 | Read-only: record `dig copolitic.org A AAAA CAA NS`, `dig www.copolitic.org CNAME`, and the registrar of record. Keep any MX/TXT/SPF/DKIM records exactly as found. | none (observation) | n/a |
| 2 | Choose the canonical host. R1 assumes the **apex** `copolitic.org`, which matches the plan. `www` redirects to it. | steward | edit CNAME |
| 3 | Merge PR #1 + R1 to `main`. Before merging, replace the candidate-branch URLs in `ai/index.json` and `llms.txt` with `main` URLs and update the matching R0 assertions. | repo admin + CoGuardian | `git revert` |
| 4 | Pages: Settings → Pages → Deploy from branch `main` / root. Custom domain `copolitic.org`. Verify the domain for the CoCivium org (TXT record). | repo admin | Pages: unpublish or clear the domain |
| 5 | DNS at the actual authority: apex A records `185.199.108.153`, `.109`, `.110`, `.111`; AAAA `2606:50c0:8000::153` to `8003::153`; `www` CNAME `cocivium.github.io`. Do **not** touch NS, DNSSEC or mail records. If the zone is on Cloudflare, use DNS-only (grey cloud) until the certificate is issued. | DNS owner, with a change envelope | Restore the recorded prior records from step 1 |
| 6 | Wait for the certificate, then enable "Enforce HTTPS". | repo admin | Toggle off |

## 4. Acceptance (PUBLIC_VERIFIED needs all of these, recorded with a timestamp)
1. `curl -sSI https://copolitic.org/` returns 200 with a valid certificate for `copolitic.org`.
2. `curl -sSI https://www.copolitic.org/` returns a 301 to `https://copolitic.org/` with a valid certificate for `www`.
3. `curl -sSI http://copolitic.org/` returns a 301 to https.
4. The sha256 of the served `/` equals the sha256 of `main:index.html` at the deployed commit. Same check for `/ai/index.json` and `/llms.txt`.
5. Every link on the page returns 200. `tools/verify_sources_lock.py` exits 0.
6. Desktop and 320 px mobile screenshots. A keyboard-only path: skip link → "Explore one civic question" → a source link → the corrections issue page.
7. Page claims are updated from "not verified at copolitic.org" to match observed reality, in a **separate** reviewed commit after verification, never before.
8. A receipt with the URL, the HTTP/TLS log, screenshots, the commit and the rollback pointer.

## 5. Rollback
- **Site:** revert the merge commit on `main`, or unpublish Pages.
- **DNS:** restore the records captured in step 1. Because step 1 runs before any change, the prior state is always known.

## 6. Open UX defect (HOLD, not fixed in R1)
The three primary cards link to GitHub **source views** of HTML pages, so a visitor sees code, not the page. CoAcademy's own source names rendered URLs at `https://cocivium.github.io/CoAcademy/...`, but they were **not reachable for verification** from this session. Swap the card links to the rendered URLs only after acceptance check 5 passes for them. Keep the source links as secondary.

`SOURCE_READY → CANDIDATE_TESTED (here) → AUTHORIZED → DEPLOYED → PUBLIC_VERIFIED`
