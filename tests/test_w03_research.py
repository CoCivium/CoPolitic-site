#!/usr/bin/env python3
"""W03 static gate for CoPolitic research pages.

Reads repository text only. Checks: link back to the site index, no active
content, every cited href resolvable and recorded in research/citations.json,
explicit hypothesis/fiction labels on every CoScendence+/G_dSide+/mythos
passage, and the recorded noindex decision.
Passing proves structure, not that any claim is true.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
PAGES = [
    "research/reading-room/index.html",
    "research/beyond-legacy-ai-governance/index.html",
    "research/coscendence-synthetic-motives/index.html",
]
LEDGER = RESEARCH / "citations.json"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}
ACTIVE = {"script", "iframe", "form", "object", "embed", "frame", "frameset"}
MYTHOS = re.compile(r"coscendence|g_dside|mythos", re.I)
LABELS = {"hypothesis": "label: hypothesis", "fiction": "label: fiction"}


class Invalid(ValueError):
    pass


def need(ok, msg):
    if not ok:
        raise Invalid(msg)


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent = tag, attrs, parent
        self.children, self.text = [], []

    def all_text(self):
        out = list(self.text)
        for c in self.children:
            out.append(c.all_text())
        return " ".join(out)

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root
        self.issues, self.hrefs, self.robots = [], [], []
        self.chunks = []  # (text, node)

    def handle_starttag(self, tag, attrs):
        d = {k.lower(): (v or "") for k, v in attrs}
        if tag in ACTIVE:
            self.issues.append("ACTIVE_ELEMENT_" + tag)
        if any(k.startswith("on") for k in d):
            self.issues.append("INLINE_HANDLER_" + tag)
        for k in ("href", "src", "action"):
            if d.get(k, "").strip().lower().startswith("javascript:"):
                self.issues.append("JAVASCRIPT_URL")
        if tag == "meta" and d.get("name", "").lower() == "robots":
            self.robots.append(d.get("content", "").replace(" ", "").lower())
        if tag == "a" and "href" in d:
            self.hrefs.append(d["href"])
        n = Node(tag, d, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.cur = self.cur.parent

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.text.append(data)
            self.chunks.append((data, self.cur))


def parse(html):
    t = Tree()
    t.feed(html)
    t.close()
    return t


def ancestors(node):
    while node is not None:
        yield node
        node = node.parent


def resolve_local(page_rel, href):
    """Return repo path a relative href points to, or None if outside repo."""
    path = urlparse(href).path
    if not path:
        return ROOT / page_rel  # pure fragment
    base = (ROOT / page_rel).parent
    target = (base / path).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return None
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def check_page(page_rel, html, ledger):
    t = parse(html)
    need(not t.issues, "ACTIVE_CONTENT: " + ",".join(t.issues))
    need("<script" not in html.lower(), "SCRIPT_TEXT")

    # link back to the site index
    home = ROOT / "index.html"
    need(any(not urlparse(h).scheme and resolve_local(page_rel, h) == home.resolve()
             for h in t.hrefs), "NO_INDEX_BACKLINK")

    # every href resolvable; external ones recorded with a check result
    recorded = {c["href"]: c for c in ledger["citations"] if c["page"] == page_rel}
    for h in t.hrefs:
        u = urlparse(h)
        if u.scheme:
            need(u.scheme == "https" and u.hostname, "NON_HTTPS_HREF " + h)
            need(h in recorded, "UNRECORDED_CITATION " + h)
            c = recorded[h]
            need(c.get("direct_fetch") and c.get("existence"), "CITATION_WITHOUT_STATUS " + h)
            need(c["existence"].startswith(("CONFIRMED", "REPO_CONFIRMED")),
                 "CITATION_NOT_CONFIRMED " + h)
        else:
            target = resolve_local(page_rel, h)
            need(target is not None and target.is_file(), "BROKEN_LOCAL_HREF " + h)
            if u.fragment and target.resolve() == (ROOT / page_rel).resolve():
                need(f'id="{u.fragment}"' in html, "BROKEN_FRAGMENT " + h)
    need(set(recorded) <= set(t.hrefs), "STALE_LEDGER_ENTRY")

    # every listed source item carries a link
    for n in t.root.walk():
        if n.attrs.get("id") == "sources":
            items = [x for x in n.walk() if x.tag == "li"]
            need(items, "SOURCES_SECTION_EMPTY")
            for li in items:
                need(any(x.tag == "a" and x.attrs.get("href") for x in li.walk()),
                     "SOURCE_CLAIM_WITHOUT_HREF")

    # mythos / CoScendence passages carry an explicit, visible label
    for text, node in t.chunks:
        if not MYTHOS.search(text):
            continue
        if any(a.tag == "head" for a in ancestors(node)):
            continue
        holder = next((a for a in ancestors(node) if a.attrs.get("data-epistemic")), None)
        need(holder is not None and holder.tag not in ("main", "body", "html"),
             "UNLABELLED_MYTHOS: " + text.strip()[:50])
        kind = holder.attrs["data-epistemic"]
        need(kind in LABELS, "UNKNOWN_EPISTEMIC_KIND " + kind)
        labels = [x.all_text().strip().lower() for x in holder.walk()
                  if "epi" in x.attrs.get("class", "").split()]
        need(any(l.startswith(LABELS[kind]) for l in labels),
             "MISSING_VISIBLE_LABEL: " + text.strip()[:50])
        if holder.tag == "details":
            # A collapsed <details> renders only its <summary>; the label must live there.
            summ = next((x for x in holder.children if x.tag == "summary"), None)
            need(summ is not None and any(
                "epi" in x.attrs.get("class", "").split()
                and x.all_text().strip().lower().startswith(LABELS[kind])
                for x in summ.walk()), "LABEL_HIDDEN_IN_COLLAPSED_DETAILS: " + text.strip()[:50])

    # recorded decision: keep noindex,nofollow
    need(t.robots == ["noindex,nofollow"], "NOINDEX_DECISION_DRIFT")
    return {"page": page_rel, "hrefs": len(t.hrefs), "result": "PASS_STRUCTURE_ONLY"}


class W03ResearchTests(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.html = {p: (ROOT / p).read_text(encoding="utf-8") for p in PAGES}

    def run_all(self, override=None, ledger=None):
        for p in PAGES:
            h = override.get(p, self.html[p]) if override else self.html[p]
            check_page(p, h, ledger or self.ledger)

    # positive checks
    def test_01_all_pages_pass(self):
        for p in PAGES:
            self.assertEqual(check_page(p, self.html[p], self.ledger)["result"], "PASS_STRUCTURE_ONLY")

    def test_02_every_page_links_back_to_index(self):
        for p in PAGES:
            t = parse(self.html[p])
            self.assertTrue(any(resolve_local(p, h) == (ROOT / "index.html").resolve()
                                for h in t.hrefs if not urlparse(h).scheme), p)

    def test_03_no_script_or_active_content(self):
        for p in PAGES:
            self.assertEqual(parse(self.html[p]).issues, [], p)
            self.assertNotIn("<script", self.html[p].lower())

    def test_04_ledger_covers_every_external_href(self):
        ext = {(p, h) for p in PAGES for h in parse(self.html[p]).hrefs if urlparse(h).scheme}
        rec = {(c["page"], c["href"]) for c in self.ledger["citations"]}
        self.assertEqual(ext, rec)

    def test_05_mythos_sections_labelled(self):
        html = self.html["research/coscendence-synthetic-motives/index.html"]
        self.assertIn('data-epistemic="fiction"', html)
        self.assertIn("Label: Fiction / mythos", html)
        self.assertIn("Label: Hypothesis", html)

    def test_06_noindex_decision_recorded(self):
        d = self.ledger["noindex_decision"]
        self.assertTrue(d["decision"].startswith("KEEP"))
        self.assertGreaterEqual(len(d["reasons"]), 2)

    def test_07_front_door_untouched(self):
        # W03 may not alter index.html; PR #1 pins its blob.
        from hashlib import sha1
        data = (ROOT / "index.html").read_bytes()
        blob = sha1(b"blob %d\x00" % len(data) + data).hexdigest()
        self.assertEqual(blob, "1ae823ad0072cb310c2f30f7cb464c05b375a43f")

    # negative checks: the gate must reject these
    P = "research/coscendence-synthetic-motives/index.html"

    def test_10_reject_script(self):
        bad = self.html[self.P].replace("</main>", "<script>alert(1)</script></main>")
        with self.assertRaisesRegex(Invalid, "ACTIVE_CONTENT"):
            self.run_all({self.P: bad})

    def test_11_reject_inline_handler(self):
        bad = self.html[self.P].replace("<main>", '<main><a href="#idea" onclick="x()">x</a>', 1)
        with self.assertRaisesRegex(Invalid, "ACTIVE_CONTENT"):
            self.run_all({self.P: bad})

    def test_12_reject_missing_backlink(self):
        bad = self.html[self.P].replace('<a href="../../">CoPolitic home</a>', "")
        with self.assertRaisesRegex(Invalid, "NO_INDEX_BACKLINK"):
            self.run_all({self.P: bad})

    def test_13_reject_unrecorded_citation(self):
        bad = self.html[self.P].replace("</ul></section>",
            '<li><a href="https://example.org/made-up">Invented source</a></li></ul></section>')
        with self.assertRaisesRegex(Invalid, "UNRECORDED_CITATION"):
            self.run_all({self.P: bad})

    def test_14_reject_source_claim_without_href(self):
        bad = self.html[self.P].replace("</ul></section>", "<li>Smith (2026) proves it.</li></ul></section>")
        with self.assertRaisesRegex(Invalid, "SOURCE_CLAIM_WITHOUT_HREF"):
            self.run_all({self.P: bad})

    def test_15_reject_broken_local_href(self):
        bad = self.html[self.P].replace('href="../reading-room/"', 'href="../no-such-page/"')
        with self.assertRaisesRegex(Invalid, "BROKEN_LOCAL_HREF"):
            self.run_all({self.P: bad})

    def test_16_reject_unlabelled_mythos(self):
        bad = self.html[self.P].replace('<details data-epistemic="fiction">', "<details>")
        with self.assertRaisesRegex(Invalid, "UNLABELLED_MYTHOS"):
            self.run_all({self.P: bad})

    def test_17_reject_attribute_without_visible_label(self):
        bad = self.html[self.P].replace('<span class="epi">Label: Fiction / mythos</span>', "")
        with self.assertRaisesRegex(Invalid, "MISSING_VISIBLE_LABEL"):
            self.run_all({self.P: bad})

    def test_18_reject_page_wide_label_shortcut(self):
        bad = self.html[self.P].replace("<main>", '<main data-epistemic="hypothesis">', 1) \
                               .replace('<details data-epistemic="fiction">', "<details>")
        with self.assertRaisesRegex(Invalid, "UNLABELLED_MYTHOS"):
            self.run_all({self.P: bad})

    def test_19_reject_unconfirmed_citation(self):
        led = json.loads(json.dumps(self.ledger))
        led["citations"][0]["existence"] = "unreachable"
        with self.assertRaisesRegex(Invalid, "CITATION_NOT_CONFIRMED"):
            self.run_all(ledger=led)

    def test_20_reject_noindex_removal(self):
        bad = self.html[self.P].replace("noindex,nofollow", "index,follow")
        with self.assertRaisesRegex(Invalid, "NOINDEX_DECISION_DRIFT"):
            self.run_all({self.P: bad})

    def test_22_reject_label_hidden_in_collapsed_details(self):
        # Regression for R1 browser finding: label inside a closed <details> body is not visible.
        bad = self.html[self.P].replace(
            '<summary><span class="epi">Label: Fiction / mythos</span>G_dSide+ mythos</summary><p>',
            '<summary>G_dSide+ mythos</summary><p><span class="epi">Label: Fiction / mythos</span>')
        self.assertNotEqual(bad, self.html[self.P])
        with self.assertRaisesRegex(Invalid, "LABEL_HIDDEN_IN_COLLAPSED_DETAILS"):
            self.run_all({self.P: bad})

    def test_21_reject_http_citation(self):
        led = json.loads(json.dumps(self.ledger))
        h = led["citations"][3]["href"]
        led["citations"][3]["href"] = h.replace("https:", "http:")
        bad = self.html[self.P].replace(h, h.replace("https:", "http:"))
        with self.assertRaisesRegex(Invalid, "NON_HTTPS_HREF"):
            self.run_all({self.P: bad}, ledger=led)


if __name__ == "__main__":
    unittest.main(verbosity=2)
