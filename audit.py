#!/usr/bin/env python3
"""Check that publications.json, Zenodo and ORCID still agree.

    python3 audit.py          # report
    python3 audit.py --strict # exit 1 on any problem (for a cron or pre-push hook)

These three drift silently and in ways nothing warns you about. Real examples
from this record: a paper carried another paper's DOI, which made ORCID merge
two works into one and hid a publication; keywords typed into Zenodo's web
form vanished because the field needs Enter after each tag; a DOI entered as a
full URL instead of a bare identifier broke matching.

Read-only. Nothing here changes any system.
"""

import argparse
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).parent
ORCID = "0009-0009-4836-5205"


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r)
    except Exception as exc:
        print(f"  ! fetch failed {url}: {exc}", file=sys.stderr)
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    data = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
    # ORCID's public API serves XML unless you ask for JSON. Forgetting this
    # header makes every DOI look missing.
    orcid = get(f"https://pub.orcid.org/v3.0/{ORCID}/works",
                {"Accept": "application/json"})
    groups = orcid.get("group", [])
    odois = {e.get("external-id-value", "").replace("https://doi.org/", "")
             for g in groups for s in g.get("work-summary", [])
             for e in ((s.get("external-ids") or {}).get("external-id") or [])
             if e.get("external-id-type") == "doi"}

    problems = []
    for g in groups:
        if len(g.get("work-summary", [])) > 1:
            t = ((g["work-summary"][0].get("title") or {}).get("title") or {}).get("value", "?")
            problems.append(f"ORCID has merged >1 work into one group: {t[:60]} "
                            f"-- almost always two papers sharing a DOI")

    print(f"{'paper':<34}{'zenodo':<9}{'orcid':<8}{'issn':<9}{'keywords':<10}{'site link'}")
    for p in data["papers"]:
        doi = p.get("doi") or ""
        name = p["slug"][:33]
        if not doi:
            print(f"{name:<34}{'no DOI':<9}{'-':<8}{'-':<9}{'-':<10}-")
            problems.append(f"{p['slug']}: no DOI recorded")
            continue
        rec = get(f"https://zenodo.org/api/records/{doi.rsplit('.', 1)[-1]}")
        m = rec.get("metadata", {})
        j = m.get("journal") or {}
        nkw, want = len(m.get("keywords") or []), len(p.get("keywords") or [])
        ok_z, ok_o = rec.get("doi") == doi, doi in odois
        issn, links = j.get("issn"), len(m.get("related_identifiers") or [])
        print(f"{name:<34}{'ok' if ok_z else 'MISMATCH':<9}{'ok' if ok_o else 'MISSING':<8}"
              f"{(issn or 'blank'):<9}{f'{nkw}/{want}':<10}{links}")
        if not ok_z:
            problems.append(f"{p['slug']}: Zenodo record does not report this DOI")
        if not ok_o:
            problems.append(f"{p['slug']}: DOI {doi} is not on the ORCID record")
        if not issn:
            problems.append(f"{p['slug']}: Zenodo ISSN blank (set it in the web UI; "
                            f"the deposition API has no field for it)")
        if nkw != want:
            problems.append(f"{p['slug']}: Zenodo has {nkw} keywords, expected {want} "
                            f"(the form needs Enter after each tag)")
        if not links:
            problems.append(f"{p['slug']}: no related-work link back to the site -- "
                            f"this is the path Scholar follows to find you")

    print()
    if problems:
        print(f"{len(problems)} problem(s):")
        for x in problems:
            print(f"  - {x}")
    else:
        print("all three systems agree")
    return 1 if (problems and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
