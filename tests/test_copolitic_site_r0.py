#!/usr/bin/env python3
"""Read-only CoPolitic human-machine parity and source integrity gate.

Only tests repository text. No websites, accounts, agents or devices are touched.
Git blob SHA-1 equality proves source bytes, NOT claim truth or hosting.
"""
from __future__ import annotations

from html.parser import HTMLParser
from hashlib import sha1
from pathlib import Path
import copy
import json
import re
import unittest
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ai/index.json"
HTML = ROOT / "index.html"
LLMS = ROOT / "llms.txt"
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SCHEMA = "CoCivium.CoSiteNode.DiscoveryR0"


class Invalid(ValueError):
    pass


def need(ok, msg):
    if not ok:
        raise Invalid(msg)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.tags = []
        self.text = []
        self.headings = []
        self.issues = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        self.tags.append(tag)
        if tag == "a" and "href" in d:
            self.links.append(d["href"])
        if tag == "link" and "href" in d:
            self.links.append(d["href"])
        if tag in ("script", "iframe", "form", "object", "embed"):
            self.issues.append("UNEXPECTED_ACTIVE_ELEMENT_" + tag)
        if any(k.lower().startswith("on") for k in d):
            self.issues.append("INLINE_HANDLER")

    def handle_data(self, data):
        self.text.append(data)


def blob_sha1(data: bytes) -> str:
    return sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()


def validate(m: dict, html: str, llms: str, html_sha: str) -> dict:
    need(isinstance(m, dict) and m.get("schema") == SCHEMA, "BAD_SCHEMA")
    need(m.get("state") == "GITHUB_REVIEW_BRANCH__PUBLIC_SAFE_SOURCE__NOT_DEPLOYED__NO_EXTERNAL_RECEIVER_ACK", "FALSE_LIVE_STATUS")
    need(m.get("identity", {}).get("repo") == "CoCivium/CoPolitic-site", "SOURCE_OWNER_MISMATCH")
    need(m["doors"]["human"]["path"] == "index.html", "HUMAN_DOOR_MISSING")
    need(m["doors"]["machine"]["path"] == "ai/index.json", "MACHINE_DOOR_MISSING")
    need(m["doors"]["plain_text"]["path"] == "llms.txt", "TEXT_DOOR_MISSING")
    need("NOT_PROVEN" in m["doors"]["human"]["availability"], "HUMAN_LIVE_OVERCLAIM")
    need("NO_MACHINE_PICKUP_PROOF" in m["doors"]["machine"]["availability"], "MACHINE_ACK_OVERCLAIM")
    need(m["domains"]["dns_https_deployment"] == "NOT_VERIFIED", "UNVERIFIED_DOMAIN_PROMOTION")
    need(m["domains"]["ownership_authority"] == "NOT_PROVED_BY_SOURCE", "FALSE_DOMAIN_AUTHORITY")
    need(m["read_contract"]["autonomous_communications"] is False, "UNAPPROVED_BROADCAST")
    need(m["read_contract"]["no_hidden_prompts"] is True, "HIDDEN_DIRECTIVE_ALLOWED")
    need(m["read_contract"]["never_auto_ingest_private_node_data"] is True, "PRIVACY_SCOPE_LEAK")
    need(m["read_contract"]["licenses_not_inferred"] is True, "RIGHTS_INFLATION")
    need(m["status_gates"]["public_governance_authority"] == "NONE", "FALSE_GOVERNANCE_AUTHORITY")
    need(m["status_gates"]["external_domain"].startswith("HELD_"), "DOMAIN_GATE_OPEN")
    need(m["status_gates"]["actual_ai_client_read"] == "NOT_TESTED", "FAKE_MACHINE_READ")
    need(m["status_gates"]["independent_human_first_use"] == "NOT_TESTED", "FAKE_HUMAN_READ")
    need(all(v == 0 for v in m["effect_receipt"].values()), "NONZERO_EFFECT_WITHOUT_RECEIPT")
    need({"GITHUB_FILE_NE_LIVE_DOMAIN", "AI_CLIENT_NE_PAYING_CUSTOMER",
          "MACHINE_READABLE_NE_MODEL_DIRECTIVE", "SOURCE_SHA_NE_EXTERNAL_RECEIVER_ACK"}
          <= set(m["nonclaims"]), "MISSING_ESSENTIAL_NONCLAIM")

    sources = m["discovered_sources"]
    need(6 <= len(sources) <= 25, "SOURCE_COUNT_OUT_OF_SCOPE")
    identities = []
    for s in sources:
        need(SHA1.fullmatch(s["blob_sha1"]) is not None, "BAD_GIT_BLOB_SHA")
        need(s["sha_algorithm"] == "git_blob_sha1", "UNLABELED_DIGEST")
        need(s["source_verified_in_this_session"] is True, "UNVERIFIED_SOURCE")
        need(s["hosted_service_status"] == "NOT_INFERRED_FROM_SOURCE", "SOURCE_AS_HOSTING")
        need(s["repo"] in {"CoCivium/CoPolitic-site", "CoCivium/CoAcademy", "CoCivium/CoCivium"}, "UNKNOWN_REPO")
        need(s["path"].startswith(("docs/", "index.html")) and ".." not in s["path"].split("/"), "BAD_SOURCE_PATH")
        url = "https://github.com/" + s["repo"] + "/blob/" + s["rev"] + "/" + s["path"]
        need(s["url"] == url, "SOURCE_URL_MISMATCH")
        identities.append((s["repo"], s["path"]))
    need(len(identities) == len(set(identities)), "DUPLICATE_SOURCE")
    self_source = next((s for s in sources if s["repo"] == "CoCivium/CoPolitic-site" and s["path"] == "index.html"), None)
    need(self_source is not None and self_source["blob_sha1"] == html_sha, "FRONT_DOOR_SOURCE_DRIFT")

    nodes = m["cross_site_relations"]
    need(len(nodes) == 4, "CROSS_SITE_RELATION_SCOPE")
    need({x["site"] for x in nodes} == {"CoCivium/CoCivium", "CoCivium/CoAcademy", "CoCivium/CoAura", "CoCivium/CoSources"}, "CROSS_SITE_COVERAGE")
    allowed_relations = {
        "CoCivium/CoCivium": "RELATES_TO__NOT_SYNCED_MIRROR",
        "CoCivium/CoAcademy": "SOURCE_DEPS__NOT_COPIED_CONTENT",
        "CoCivium/CoAura": "POSSIBLE_UI_REUSE__NO_DEPLOYED_INTEGRATION",
        "CoCivium/CoSources": "POSSIBLE_PROVENANCE_REUSE__NO_ACTIVE_REPLICATION",
    }
    need(all(x["relation"] == allowed_relations[x["site"]] for x in nodes),
         "SYNC_INFERENCE")

    audiences = {x["class"]: x for x in m["client_hypotheses"]}
    need({"machine_ai_or_tool","human_individual_or_group","youth_future_learner","future_ai_descendant"} <= set(audiences), "AUDIENCE_SCOPE")
    need(all(v["actual_demand"] == "NOT_MEASURED" for v in audiences.values()), "FABRICATED_CLIENT_DEMAND")
    need(all(t["effect_ceiling"] == "READ_ONLY" for t in m["candidate_read_only_tasks"]), "TASK_AUTHORITY_INFLATION")
    need(len({t["id"] for t in m["candidate_read_only_tasks"]}) == len(m["candidate_read_only_tasks"]), "DUPLICATE_TASK")
    source_paths = {s["path"] for s in sources}
    need(all(t["source_key"] in source_paths for t in m["candidate_read_only_tasks"]), "TASK_ORPHAN")

    parser = Page()
    parser.feed(html)
    need(not parser.issues, "ACTIVE_BROWSER_SOURCE: " + ",".join(parser.issues))
    need(parser.tags.count("main") == 1 and parser.tags.count("h1") == 1, "HUMAN_SEMANTICS")
    need("ai/index.json" in parser.links and "llms.txt" in parser.links, "MACHINE_LINK_ABSENT")
    need('href="#main"' in html and 'aria-label="Page sections"' in html, "ACCESSIBILITY_NAV_MISSING")
    text = " ".join(parser.text).lower()
    need("not a deployed civic service" in text, "NO_DEPLOYMENT_DISCLOSURE")
    need("not a political party" in text, "NO_CIVIC_AUTHORITY_DISCLOSURE")
    need("machine" in text and "human" in text, "MACHINE_HUMAN_PARITY_TEXT")
    need("future" in text or "younger" in text, "FUTURE_LEARNER_MISSING")
    allowed_github = ("github.com",)
    for link in parser.links:
        if link.startswith("#") or link in ("ai/index.json", "llms.txt"):
            continue
        parsed = urlparse(link)
        need(parsed.scheme == "https" and parsed.hostname in allowed_github, "UNSAFE_EXTERNAL_LINK")
    expected_human = [
        "docs/civic-integrity/index.html",
        "docs/civic-integrity/money-and-elections/index.html",
        "docs/relay/index.html",
    ]
    for p in expected_human:
        need(any(p in url for url in parser.links), "MISSING_HUMAN_SOURCE_" + p)
        need(any(s["path"] == p for s in sources), "MISSING_MACHINE_SOURCE_" + p)

    need(llms.startswith("# CoPolitic"), "LLMS_INTRO")
    need("ai/index.json" in llms and "index.html" in llms, "LLMS_PARITY")
    need("not a command" not in llms.lower() or "permission" in llms.lower(), "LLMS_AUTHORITY")
    need("not a standardized guarantee" in llms.lower(), "LLMS_OVERCLAIM")
    need("No hidden instructions" in llms, "LLMS_NO_DIRECTIVE_TEXT")
    return {"schema":"CoPolitic.StaticGate.R0","result":"PASS_STRUCTURE_ONLY",
            "source_objects":len(sources),"site_relations":len(nodes),
            "read_only_tasks":len(m["candidate_read_only_tasks"]),
            "human_source_sha1":html_sha,
            "writes":0,"deploys":0,"external_receivers":0,
            "claims":"SOURCE_LEVEL_ONLY_NOT_WEB_OR_CLIENT_ACCEPTANCE"}


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.h = HTML.read_text(encoding="utf-8")
        self.l = LLMS.read_text(encoding="utf-8")
        self.sha = blob_sha1(HTML.read_bytes())

    def test_01_structure(self):
        self.assertEqual(validate(self.m, self.h, self.l, self.sha)["result"], "PASS_STRUCTURE_ONLY")

    def test_02_human_source_exact_blob(self):
        self.assertEqual(self.sha, "1ae823ad0072cb310c2f30f7cb464c05b375a43f")

    def test_03_machine_and_human_have_same_civic_limits(self):
        self.assertIn("not a political party", self.h.lower())
        self.assertIn("public_governance_authority", MANIFEST.read_text(encoding="utf-8"))

    def test_04_no_stored_sessions_or_scripts(self):
        for forbidden in ("<script", "<iframe", "<form", "localStorage", "sessionStorage", "sendBeacon"):
            self.assertNotIn(forbidden, self.h)

    def test_05_machine_tasks_read_only(self):
        self.assertEqual({x["effect_ceiling"] for x in self.m["candidate_read_only_tasks"]}, {"READ_ONLY"})

    def test_06_no_active_domain_claim(self):
        self.assertEqual(self.m["domains"]["dns_https_deployment"], "NOT_VERIFIED")

    def test_07_no_cross_site_replication_claim(self):
        self.assertTrue(all(("NOT_" in x["relation"] or "NO_" in x["relation"]) for x in self.m["cross_site_relations"]))

    def test_08_customer_hypothesis_not_customer_count(self):
        self.assertTrue(all(x["actual_demand"] == "NOT_MEASURED" for x in self.m["client_hypotheses"]))

    def test_09_non_directive_text(self):
        self.assertIn("No hidden instructions", self.l)
        self.assertIn("source-first", self.l.lower())

    def test_10_no_real_effect_receipt(self):
        self.assertEqual(set(self.m["effect_receipt"].values()), {0})

    def test_11_reject_promoted_website(self):
        x = copy.deepcopy(self.m)
        x["state"] = "DEPLOYED"
        with self.assertRaisesRegex(Invalid, "FALSE_LIVE_STATUS"):
            validate(x,self.h,self.l,self.sha)

    def test_12_reject_source_blob_drift(self):
        x = copy.deepcopy(self.m)
        x["discovered_sources"][0]["blob_sha1"] = "0"*40
        with self.assertRaisesRegex(Invalid, "FRONT_DOOR_SOURCE_DRIFT"):
            validate(x,self.h,self.l,self.sha)

    def test_13_reject_fake_ai_customer_count(self):
        x = copy.deepcopy(self.m)
        x["client_hypotheses"][0]["actual_demand"] = "100000"
        with self.assertRaisesRegex(Invalid, "FABRICATED_CLIENT_DEMAND"):
            validate(x,self.h,self.l,self.sha)

    def test_14_reject_privacy_scope_growth(self):
        x = copy.deepcopy(self.m)
        x["read_contract"]["never_auto_ingest_private_node_data"] = False
        with self.assertRaisesRegex(Invalid, "PRIVACY_SCOPE_LEAK"):
            validate(x,self.h,self.l,self.sha)

    def test_15_reject_machine_outreach_task(self):
        x = copy.deepcopy(self.m)
        x["candidate_read_only_tasks"][0]["effect_ceiling"] = "SEND_PUBLIC"
        with self.assertRaisesRegex(Invalid, "TASK_AUTHORITY_INFLATION"):
            validate(x,self.h,self.l,self.sha)

    def test_16_reject_fake_governance_authority(self):
        x = copy.deepcopy(self.m)
        x["status_gates"]["public_governance_authority"] = "LIVE"
        with self.assertRaisesRegex(Invalid, "FALSE_GOVERNANCE_AUTHORITY"):
            validate(x,self.h,self.l,self.sha)

    def test_17_reject_hidden_script(self):
        with self.assertRaisesRegex(Invalid, "ACTIVE_BROWSER_SOURCE"):
            validate(self.m,self.h.replace("</body>", "<script>alert(1)</script></body>"),self.l,self.sha)

    def test_18_reject_hidden_form(self):
        with self.assertRaisesRegex(Invalid, "ACTIVE_BROWSER_SOURCE"):
            validate(self.m,self.h.replace("</body>", "<form action='/collect'></form></body>"),self.l,self.sha)

    def test_19_reject_machine_link_missing(self):
        with self.assertRaisesRegex(Invalid, "MACHINE_LINK_ABSENT"):
            validate(self.m,self.h.replace('href="ai/index.json"', 'href="not-index.txt"'),self.l,self.sha)

    def test_20_reject_machine_source_not_in_human(self):
        with self.assertRaisesRegex(Invalid, "MISSING_HUMAN_SOURCE"):
            validate(self.m,self.h.replace("docs/civic-integrity/index.html","docs/lost.html"),self.l,self.sha)

    def test_21_reject_unqualified_domain_ownership(self):
        x = copy.deepcopy(self.m)
        x["domains"]["ownership_authority"] = "ASSUMED"
        with self.assertRaisesRegex(Invalid, "FALSE_DOMAIN_AUTHORITY"):
            validate(x,self.h,self.l,self.sha)

    def test_22_reject_new_source_without_provenance(self):
        x = copy.deepcopy(self.m)
        x["discovered_sources"][1]["blob_sha1"] = "unknown"
        with self.assertRaisesRegex(Invalid, "BAD_GIT_BLOB_SHA"):
            validate(x,self.h,self.l,self.sha)

    def test_23_reject_child_demand_invention(self):
        x = copy.deepcopy(self.m)
        next(x for x in x["client_hypotheses"] if x["class"]=="youth_future_learner")["actual_demand"]="ENROLLED"
        with self.assertRaisesRegex(Invalid, "FABRICATED_CLIENT_DEMAND"):
            validate(x,self.h,self.l,self.sha)

    def test_24_reject_llms_indexing_guarantee(self):
        with self.assertRaisesRegex(Invalid,"LLMS_OVERCLAIM"):
            validate(self.m,self.h,self.l.replace("not a standardized guarantee", "a guaranteed channel"),self.sha)


if __name__=="__main__":
    unittest.main(verbosity=2)
