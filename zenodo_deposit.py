#!/usr/bin/env python3
"""Deposit a paper on Zenodo through the API instead of the web form.

    export ZENODO_TOKEN=...                       # zenodo.org/account/settings/applications
    python3 zenodo_deposit.py <slug>              # create draft, upload, set metadata
    python3 zenodo_deposit.py <slug> --publish     # ... and publish (mints the DOI)
    python3 zenodo_deposit.py <slug> --verify <id> # read back a record and diff it

Why bother: every mistake made filling this in by hand came from the form, not
from the data. A truncated surname at signup, CC-BY selected where the journal
requires CC-BY-SA, four keywords collapsing into one string because Enter was
not pressed, a missing ISSN, and edits saved as a draft that never published.
The payload from export.py has none of those failure modes, because it is the
same data that drives the site.

--publish is deliberately separate. Publishing mints a DOI and freezes the
files; there is no undo and you cannot delete a published record yourself.
"""

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).parent
API = "https://zenodo.org/api"


def load(slug: str) -> dict:
    data = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
    for p in data["papers"]:
        if p["slug"] == slug:
            return data, p
    sys.exit(f"no paper with slug {slug!r} in publications.json")


def request(method: str, url: str, token: str, body=None, content_type="application/json"):
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(f"{url}{sep}access_token={token}", method=method)
    if body is not None and content_type == "application/json":
        body = json.dumps(body).encode()
    if body is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, body) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        sys.exit(f"{method} {url} -> HTTP {e.code}\n{detail}")


def payload(slug: str) -> dict:
    """The deposition metadata, read from what export.py already generated."""
    f = ROOT / "export" / f"zenodo-{slug}.json"
    if not f.exists():
        sys.exit(f"missing {f} -- run: python3 export.py")
    return json.loads(f.read_text(encoding="utf-8"))


def verify(record_id: str, slug: str) -> int:
    """Read a record back and report fields that did not land.

    Note the endpoint returns the *legacy* serialisation: metadata.license,
    metadata.journal, and flat creators[].orcid. Checking InvenioRDM paths
    against it reports everything as empty even when the record is complete.
    """
    d = request("GET", f"{API}/records/{record_id}", os.environ.get("ZENODO_TOKEN", ""))
    m = d.get("metadata", {})
    _, paper = load(slug)
    want_kw = paper.get("keywords", [])
    got_kw = m.get("keywords") or []
    lic = m.get("license")
    lic = lic.get("id") if isinstance(lic, dict) else lic
    j = m.get("journal") or {}
    c = (m.get("creators") or [{}])[0]

    checks = [
        ("doi", d.get("doi")),
        ("orcid", c.get("orcid")),
        ("affiliation", c.get("affiliation")),
        ("licence", lic),
        ("licence matches journal", lic == paper.get("license")),
        ("language", m.get("language")),
        ("journal title", j.get("title")),
        ("journal issn", j.get("issn")),
        ("journal volume", j.get("volume")),
        ("journal issue", j.get("issue")),
        ("journal pages", j.get("pages")),
        ("abstract", bool(m.get("description"))),
        (f"keywords ({len(want_kw)} expected)", len(got_kw) == len(want_kw) or got_kw),
    ]
    bad = 0
    for name, val in checks:
        ok = bool(val) and val is not False
        bad += not ok
        print(f"  {'ok ' if ok else 'MISSING'}  {name}: {val if val not in (True,) else ''}")
    if len(got_kw) == 1 and want_kw and len(want_kw) > 1:
        print(f"\n  keywords collapsed into one entry: {got_kw[0]!r}")
        print("  the web form needs Enter after each tag; the API does not.")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--publish", action="store_true",
                    help="publish after upload: mints the DOI, freezes files, no undo")
    ap.add_argument("--verify", metavar="RECORD_ID",
                    help="read back an existing record and report gaps")
    a = ap.parse_args()

    if a.verify:
        return verify(a.verify, a.slug)

    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        sys.exit("set ZENODO_TOKEN (zenodo.org/account/settings/applications, "
                 "scopes: deposit:write deposit:actions)")

    data, paper = load(a.slug)
    if not paper.get("license"):
        sys.exit(f"{a.slug} has no licence in publications.json. The journal states none "
                 "publicly -- confirm the terms in writing before depositing its PDF.")

    pdf = ROOT / "papers" / a.slug / paper["pdf"]
    if not pdf.exists():
        sys.exit(f"missing {pdf}")

    meta = payload(a.slug)
    dep = request("POST", f"{API}/deposit/depositions", token, meta)
    dep_id, bucket = dep["id"], dep["links"]["bucket"]
    print(f"draft {dep_id}  {dep['links'].get('html','')}")

    request("PUT", f"{bucket}/{pdf.name}", token, pdf.read_bytes(),
            content_type="application/octet-stream")
    print(f"uploaded {pdf.name} ({pdf.stat().st_size} bytes)")

    if not a.publish:
        print("\nDraft only. Review it in the browser, then re-run with --publish, "
              "or publish from the web UI.")
        return 0

    rec = request("POST", f"{API}/deposit/depositions/{dep_id}/actions/publish", token)
    doi = rec.get("doi")
    print(f"\npublished  doi: {doi}")
    print(f'Now set "doi": "{doi}" for {a.slug} in publications.json, '
          "then re-run build.py and export.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
