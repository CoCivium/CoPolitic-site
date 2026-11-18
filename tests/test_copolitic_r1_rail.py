#!/usr/bin/env python3
"""CoPolitic R1 launch-rail checks (offline, standard library only).

Adds to test_copolitic_site_r0.py:
  * exactly one custom-domain declaration, matching the planned canonical host;
  * every external CoCivium source linked from the human page or the machine
    index is pinned in ai/sources.lock.json to an exact commit and blob;
  * human page and machine index link the same external source set;
  * the page does not claim the domain is live.
Passing proves source properties only. It does not prove DNS, HTTPS or serving.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
INDEX = json.loads((ROOT / "ai" / "index.json").read_text(encoding="utf-8"))
LOCK = json.loads((ROOT / "ai" / "sources.lock.json").read_text(encoding="utf-8"))
SHA = re.compile(r"^[0-9a-f]{40}$")
GH = re.compile(r'href="https://github\.com/(CoCivium/[^/"]+)/blob/([^/"]+)/([^"#?]+)"')


def locked():
    return {(s["repo"], s["path"]) for s in LOCK["sources"]}


class LaunchRail(unittest.TestCase):
    def test_single_cname_is_planned_canonical_host(self):
        cnames = [p for p in ROOT.rglob("CNAME") if ".git" not in p.parts]
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in cnames], ["CNAME"])
        host = (ROOT / "CNAME").read_text(encoding="utf-8").strip()
        self.assertEqual(host, "copolitic.org")
        self.assertIn(host, INDEX["domains"]["planned"])

    def test_lock_entries_are_exact(self):
        self.assertTrue(LOCK["sources"])
        for s in LOCK["sources"]:
            with self.subTest(path=s["path"]):
                self.assertRegex(s["commit"], SHA)
                self.assertRegex(s["blob"], SHA)
                self.assertTrue(s["repo"].startswith("CoCivium/"))

    def test_every_external_human_link_is_locked(self):
        missing = [(r, p) for r, _ref, p in GH.findall(HTML)
                   if r != "CoCivium/CoPolitic-site" and (r, p) not in locked()]
        self.assertEqual(missing, [], "HOLD_UNPINNED_HUMAN_SOURCE")

    def test_every_external_machine_source_is_locked(self):
        missing = [(s["repo"], s["path"]) for s in INDEX["discovered_sources"]
                   if s["repo"] != "CoCivium/CoPolitic-site" and (s["repo"], s["path"]) not in locked()]
        self.assertEqual(missing, [], "HOLD_UNPINNED_MACHINE_SOURCE")

    def test_human_external_links_subset_of_machine_sources(self):
        machine = {(s["repo"], s["path"]) for s in INDEX["discovered_sources"]}
        human = {(r, p) for r, _ref, p in GH.findall(HTML) if r != "CoCivium/CoPolitic-site"}
        self.assertLessEqual(human, machine, "HUMAN_MACHINE_SOURCE_DIVERGENCE")

    def test_cname_does_not_turn_into_a_live_claim(self):
        text = re.sub(r"<[^>]+>", " ", HTML).lower()
        for claim in ("now live", "is live", "launched", "deployed at copolitic.org", "verified at copolitic.org"):
            self.assertNotIn(claim, text, claim)
        self.assertEqual(INDEX["domains"]["dns_https_deployment"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
