# W03 research reconciliation (2026-11-18)

Base: PR #1 tested line `038a87a809f0b260aea8dc80cb92e085dcda4755`.
Research source: `candidate/copolitic-flagship-research-r0-20261118@431ca0f733e3f631d56859c9c03e0e1855670a65` (cut from main `0fb29d9`).

## What this branch does

1. Commit 1 imports the three research pages byte-for-byte (blobs `25a55aa9…`, `95daa9ee…`, `b7dfee0c…`).
2. Commit 2 edits only `research/**` and adds `tests/test_w03_research.py`:
   - adds a link back to the site root (`../../`) on every page, plus reading-room cross-links;
   - adds visible `Label: Hypothesis` / `Label: Fiction / mythos` markers and a `data-epistemic` attribute to every CoScendence+, G_dSide+ and mythos section;
   - expands citation link text with author, journal and identifiers (the PubMed link had no author before);
   - records every external href in `citations.json` with its check result;
   - keeps `noindex,nofollow`. The reasons are in `citations.json` → `noindex_decision`.

## Collision: index.html link NOT added

The brief asks for a link from `index.html` to the research. The existing PR #1 suite does not allow that within W03's write scope:

- `test_02_human_source_exact_blob` pins `index.html` to blob `1ae823ad…`, so any byte change fails;
- `test_01_structure` → `FRONT_DOOR_SOURCE_DRIFT` requires `ai/index.json` to carry the same blob, and W03 may not edit `ai/index.json`;
- `UNSAFE_EXTERNAL_LINK` rejects any href in `index.html` other than `#…`, `ai/index.json`, `llms.txt` or `https://github.com/…`, so a relative `research/reading-room/` link fails even with the hashes updated.

The rules say all existing tests must pass, so `index.html` is left unchanged.

To unblock, one change outside W03 scope must do all of the following: add the link, re-pin the blob in `tests/test_copolitic_site_r0.py` and `ai/index.json`, and either allow same-site relative `research/` hrefs in the link check or link via a `https://github.com/CoCivium/CoPolitic-site/blob/...` URL.

## Other notes

- The brief says PR #1 contains a CNAME. `038a87a` has no CNAME file.
- `.github/workflows/copolitic-first-use-r0.yml` runs only `test_copolitic_site_r0.py`, so CI will not run `test_w03_research.py` until someone widens the workflow, which is outside W03 scope.
