#!/usr/bin/env python3
"""Add a published paper: one command, start to finish.

    python3 newpaper.py

Prompts for the paper's details, then does everything that can be done
without a browser:

    publications.json entry  ->  site pages + citation_* tags
                             ->  BibTeX for ORCID
                             ->  Zenodo deposit + DOI
                             ->  DOI written back, rebuilt, committed, pushed

and finally prints the short list of things that genuinely need a browser,
with the exact values to paste.

Nothing is irreversible until you confirm the Zenodo publish, which is the
only step that cannot be undone: it mints a DOI and freezes the uploaded file.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "publications.json"


def ask(label, default="", required=True):
    hint = f" [{default}]" if default else ""
    while True:
        v = input(f"  {label}{hint}: ").strip() or default
        if v or not required:
            return v
        print("    required")


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return "-".join(s.split("-")[:5])


def run(*cmd, check=True):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode and check:
        sys.exit(f"\n{' '.join(cmd)} failed:\n{r.stdout}{r.stderr}")
    return r.stdout.strip()


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    print("\nNew paper — details from the published PDF\n")

    title = ask("Title")
    slug = ask("Slug (folder name)", slugify(title))
    if any(p["slug"] == slug for p in d["papers"]):
        sys.exit(f"slug {slug!r} already exists in publications.json")

    journal = ask("Journal (full name)")
    short = ask("Journal abbreviation", "".join(w[0] for w in journal.split() if w[0].isupper()))
    issn = ask("ISSN")
    year = ask("Year")
    volume = ask("Volume", required=False)
    issue = ask("Issue", required=False)
    first = ask("First page", required=False)
    last = ask("Last page", required=False)
    issue_date = ask("Issue date YYYY-MM-DD (Zenodo needs a full date)", f"{year}-01-01")

    print("\n  Licence: check the journal's own site. Do not guess — depositing a")
    print("  publisher PDF under terms they never granted is an infringement.")
    print("  Both IJISAE and IJLRP are cc-by-sa-4.0. Blank = do not deposit.")
    lic = ask("Zenodo licence id", "cc-by-sa-4.0", required=False)

    print("\n  Abstract: paste it, then a blank line. Transcribe it BY HAND from the")
    print("  PDF — these journals use subset fonts and automated extraction")
    print("  silently drops words.")
    lines = []
    while (ln := input()) != "":
        lines.append(ln)
    abstract = " ".join(lines).strip()

    print("\n  Keywords, one per line, blank line to finish:")
    kws = []
    while (ln := input("    - ").strip()) != "":
        kws.append(ln)

    src = ask("\n  Path to the published PDF")
    src = pathlib.Path(os.path.expanduser(src))
    if not src.exists():
        sys.exit(f"no such file: {src}")

    dest_dir = ROOT / "papers" / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    pdf_name = f"{slug}.pdf"
    shutil.copy2(src, dest_dir / pdf_name)
    print(f"\n  copied -> papers/{slug}/{pdf_name} ({(dest_dir/pdf_name).stat().st_size} bytes)")

    d["papers"].append({
        "slug": slug, "title": title, "journal": journal, "journal_short": short,
        "issn": issn, "year": year, "volume": volume, "issue": issue,
        "firstpage": first, "lastpage": last,
        "publication_date": year, "issue_date": issue_date,
        "dates_note": "", "doi": None, "pdf": pdf_name,
        "license": lic or None,
        "bibtex_key": f"hosahalliseenappa{year}{slug.split('-')[0]}",
        "keywords": kws, "abstract": abstract,
    })
    DATA.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("  publications.json updated")

    print("\n" + run("python3", "build.py"))
    run("python3", "export.py")
    print("  exports regenerated")

    doi = None
    if lic and os.environ.get("ZENODO_TOKEN"):
        if ask("\n  Deposit to Zenodo and MINT A DOI? this cannot be undone (yes/no)",
               "no") == "yes":
            out = run("python3", "zenodo_deposit.py", slug, "--publish")
            print(out)
            m = re.search(r"doi:\s*(\S+)", out)
            doi = m.group(1) if m else None
            if doi:
                d = json.loads(DATA.read_text(encoding="utf-8"))
                for p in d["papers"]:
                    if p["slug"] == slug:
                        p["doi"] = doi
                DATA.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")
                run("python3", "build.py")
                run("python3", "export.py")
                print(f"  DOI {doi} recorded and site rebuilt")
    elif lic:
        print("\n  ZENODO_TOKEN not set — skipping the deposit.")
        print("  Get one at zenodo.org/account/settings/applications")
        print("  (scopes: deposit:write deposit:actions), then run:")
        print(f"      python3 zenodo_deposit.py {slug} --publish")
    else:
        print("\n  No licence recorded — deposit skipped deliberately.")

    run("git", "add", "-A")
    subprocess.run(["git", "commit", "-q", "-m", f"Add {slug}" + (f" ({doi})" if doi else "")],
                   cwd=ROOT)
    pushed = subprocess.run(["git", "push", "-q", "origin", "main"], cwd=ROOT).returncode == 0
    print(f"  committed{' and pushed' if pushed else ' (push failed — push manually)'}")

    url = f"{d['site']['base_url']}/papers/{slug}/"
    print(f"""
──────────────────────────────────────────────────────────────────────
 Done automatically: site page, citation_* tags, BibTeX, Zenodo{' + DOI' if doi else ''},
 commit{' and push' if pushed else ''}.

 LEFT FOR YOU — these three have no API you can drive:

 1. ORCID   orcid.org → Works → Add → Import BibTeX
            file: export/publications.bib
            (re-imports everything; delete any duplicate it creates)

 2. Scholar scholar.google.com → your profile → + → Add article manually
            There is NO DOI field. Enter:
              Title     {title}
              Authors   Hosahalli Seenappa, Vasantha Kumar
              Journal   {journal}
              Volume {volume}   Issue {issue}   Pages {first}-{last}
              Year      {year}
            Scholar will later crawl Zenodo and create a second entry —
            select both and Merge. Do not delete either.

 3. Zenodo  the ISSN field is not in the deposition API, so add it by hand:
              record → Edit → Journal → ISSN: {issn} → Publish
──────────────────────────────────────────────────────────────────────
 Page: {url}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
