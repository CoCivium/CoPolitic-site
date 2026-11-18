# CoPolitic public-domain release gate R0

**Date:** 2026-11-17 UTC. **State:** HOSTING_HELD | SOURCE_CANDIDATE_NOT_DEPLOYED | OWNER_UNVERIFIED. Review-branch-only source. No DNS, TLS, registrar, certificate, server, site, account or public messaging action is authorized here.

## What one direct HTTPS route observed
- `https://copolitic.org/`: HTTP **404**, TLS handshake accepted.
- `https://www.copolitic.org/`: certificate name/SNI verification **failed**; no trusted HTTPS page body was retrieved. Never bypass TLS verification to manufacture a PASS.
- The present GitHub `main` branch is a source pointer, not the candidate `index.html`.
- The existing [draft source PR #1](https://github.com/CoCivium/CoPolitic-site/pull/1) has a human-first civic-learning page, a typed read-only machine source index, and passing source-only CI at commit `5abfa9c378ca6ef9bedd9e306b47cc536dc82cc3`.
- A single route's HTTP/TLS evidence cannot assign a registrar owner, diagnose the exact hosting misconfiguration, prove private metadata safety, or count as independent user acceptance.

## CoRelShock+ as a testable trust hypothesis, not a diagnosis
Interconnected political, institutional and AI-mediated systems can leave ordinary people unsure which claims to trust and which authority can be challenged. CoPolitic should help a visitor **check a claim, compare competing interpretations, find the official record, understand legitimate authority, and correct a mistake** without demanding political alignment or personal disclosure.

An evidence source is not a vote, and three AI outputs sharing a common source are not three independent verifications. AI must not silently assign civic authority, target political opinions, or erase rights, ambiguity and dissent.

## Minimum release election
1. **Owner:** record the actual registrar/account/hosting owner and authorized release principal; inspect DNS/CAA/cert chain read-only with exact timestamp. GitHub repository write access does not grant control over a domain.
2. **Serving:** establish a chosen canonical hostname and tested 301/308 behavior, working A/AAAA or DNS records, matching TLS certificates for both apex and `www`, and accurate static hosting binding to a reviewed exact commit.
3. **Privacy and rights:** clear the serving origin and any previous or exposed metadata. Publish only rights-reviewed civic material, with no collection of beliefs, allegation forms, third-party private details, or invented election findings.
4. **Human first-use:** ask one consenting unfamiliar person to complete a question-to-source-to-correction path using keyboard and mobile; preserve what fails and fix it.
5. **Machine parity:** ensure `ai/index.json` and `llms.txt` provide optional navigation, not imperative hidden commands; source paths and versioned data must be current.
6. **Independent acceptance:** at least three genuinely independent qualifications where policy requires; explicit receiver identity, authority, source and observed effect, not three copies of one provider's tests.
7. **Release receipt:** authorized actor and exact source revision, URL + HTTP/TLS log + desktop/mobile screenshot + content digest + rollback pointer. Keep an independent master. Do not count draft PR or a 200 response alone as release proof.

## Current boundary and next CoNod
`SITE_DOMAIN_UNREADY | PRIVACY_CLASSIFICATION_HELD | MERGE_HELD | EXT_VER_NOT_SATISFIED | KEEP_MASTER`.

**Next safe deed:** In the incumbent site/domain owner lane, identify actual DNS and serving owner, then propose a reversible binding and TLS repair with no live changes until reviewed. Continue the existing candidate PR; do not create a second web framework or scheduler.

**Nonclaims:** `SOURCE_NE_SITE`, `HTTPS_200_NE_CIVIC_BENEFIT`, `REPO_ACCESS_NE_DOMAIN_AUTHORITY`, `AI_PARITY_NE_AI_RECEIVER_ACK`, `CIVIC_LEARNING_NE_PARTISAN_AUTHORITY`, `HOLD_NE_DONE`.
