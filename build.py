#!/usr/bin/env python3
"""Generate the publications site from publications.json.

    python3 build.py

Writes index.html and papers/<slug>/index.html. Each paper page carries
Highwire Press citation_* meta tags, which is what Google Scholar actually
reads; citation_title, citation_author and citation_publication_date are
mandatory, and Scholar discards *all* tags on a page that omits any of them.
"""

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
DATA = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))

SITE = DATA["site"]
AUTHOR = DATA["author"]
BASE = SITE["base_url"].rstrip("/")

CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
    font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 46rem; margin: 0 auto; padding: 3rem 1.25rem 6rem;
    color: #1a1a1a; background: #fff;
}
@media (prefers-color-scheme: dark) { body { color: #e6e6e6; background: #111; } }
h1 { font-size: 1.6rem; line-height: 1.25; margin: 0 0 .35rem; }
h2 { font-size: 1.05rem; margin: 2.5rem 0 .75rem; text-transform: uppercase;
     letter-spacing: .08em; opacity: .55; font-weight: 600; }
a { color: #0b5fff; text-decoration-thickness: 1px; text-underline-offset: 2px; }
@media (prefers-color-scheme: dark) { a { color: #6ea8ff; } }
.sub { opacity: .7; margin: 0 0 1.5rem; }
.ids { font-size: .9rem; opacity: .75; }
article { padding: 1.1rem 0; border-top: 1px solid rgba(128,128,128,.25); }
article .title { font-weight: 600; }
article .venue { font-size: .92rem; opacity: .75; margin-top: .2rem; }
.meta { font-size: .92rem; opacity: .75; }
.meta dt { font-weight: 600; opacity: .8; }
.meta dd { margin: 0 0 .6rem; }
.back { font-size: .9rem; display: inline-block; margin-bottom: 2rem; }
footer { margin-top: 4rem; font-size: .85rem; opacity: .55; }
"""

E = html.escape


def meta(name, content):
    return f'    <meta name="{name}" content="{E(str(content), quote=True)}">' if content else None


def head(title, tags=()):
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '    <meta charset="utf-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"    <title>{E(title)}</title>",
    ]
    lines += [t for t in tags if t]
    lines += [f"    <style>{CSS}</style>", "</head>", "<body>"]
    return "\n".join(lines)


def paper_page(p):
    url = f"{BASE}/papers/{p['slug']}/"
    tags = [
        meta("citation_title", p["title"]),
        meta("citation_author", AUTHOR["citation_name"]),
        meta("citation_publication_date", p["publication_date"]),
        meta("citation_journal_title", p["journal"]),
        meta("citation_issn", p["issn"]),
        meta("citation_volume", p["volume"]),
        meta("citation_issue", p["issue"]),
        meta("citation_firstpage", p["firstpage"]),
        meta("citation_lastpage", p["lastpage"]),
        meta("citation_doi", p["doi"]),
        meta("citation_abstract_html_url", url),
        meta("citation_pdf_url", f"{url}{p['pdf']}"),
        # Scholar accepts semicolon-separated keywords; they help the page rank
        # for topic queries rather than only for the exact title.
        meta("citation_keywords", "; ".join(p.get("keywords", []))),
        meta("description", p["abstract"][:300] if p["abstract"] else p["title"]),
    ]

    rows = [("Journal", f"{E(p['journal'])} ({E(p['journal_short'])})"), ("ISSN", E(p["issn"]))]
    cite = ", ".join(x for x in [p["volume"] and f"vol. {E(p['volume'])}",
                                 p["issue"] and f"no. {E(p['issue'])}",
                                 p["firstpage"] and f"pp. {E(p['firstpage'])}–{E(p['lastpage'])}"] if x)
    if cite:
        rows.append(("Citation", f"{E(p['year'])}, {cite}"))
    else:
        rows.append(("Year", E(p["year"])))
    rows.append(("DOI", f'<a href="https://doi.org/{E(p["doi"])}">{E(p["doi"])}</a>' if p["doi"]
                 else "<em>not yet registered</em>"))
    if p.get("dates_note"):
        rows.append(("Dates", E(p["dates_note"])))

    body = [
        head(p["title"], tags),
        '<a class="back" href="../../">← All publications</a>',
        f"<h1>{E(p['title'])}</h1>",
        f'<p class="sub">{E(AUTHOR["display_name"])}</p>',
    ]
    if p["abstract"]:
        body.append(f"<p>{E(p['abstract'])}</p>")
    if p.get("keywords"):
        body.append(f'<p class="meta"><strong>Keywords:</strong> '
                    f'{E(", ".join(p["keywords"]))}</p>')
    body.append('<dl class="meta">')
    body += [f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows]
    body.append("</dl>")
    body.append(f'<p><a href="{E(p["pdf"])}">Download PDF</a></p>')
    body.append("</body>\n</html>")
    return "\n".join(body)


def index_page(papers, other):
    body = [
        head(SITE["title"], [meta("description", f"Publications of {AUTHOR['display_name']}.")]),
        f"<h1>{E(AUTHOR['display_name'])}</h1>",
        f'<p class="sub">{E(AUTHOR["role"])}</p>',
        '<p class="ids">'
        f'ORCID <a href="https://orcid.org/{E(AUTHOR["orcid"])}">{E(AUTHOR["orcid"])}</a>'
        f' · <a href="https://scholar.google.com/citations?user={E(AUTHOR["scholar_id"])}">Google Scholar</a>'
        "</p>",
        "<h2>Peer-reviewed publications</h2>",
    ]
    for p in papers:
        cite = ", ".join(x for x in [p["volume"] and f"vol. {E(p['volume'])}",
                                     p["issue"] and f"no. {E(p['issue'])}",
                                     p["firstpage"] and f"pp. {E(p['firstpage'])}–{E(p['lastpage'])}"] if x)
        venue = f"{E(p['journal_short'])}, {E(p['year'])}" + (f", {cite}" if cite else "")
        body.append(
            f'<article><div class="title">'
            f'<a href="papers/{E(p["slug"])}/">{E(p["title"])}</a></div>'
            f'<div class="venue">{venue}</div></article>'
        )
    if other:
        body.append("<h2>Registered designs</h2>")
        for o in other:
            body.append(
                f'<article><div class="title">{E(o["title"])}</div>'
                f'<div class="venue">{E(o["kind"])} {E(o["number"])} · '
                f'granted {E(o["granted"])} · {E(o["classification"])}</div></article>'
            )
    body.append("<footer>Metadata on each paper page follows the Google Scholar "
                "inclusion guidelines. Built from publications.json by build.py.</footer>")
    body.append("</body>\n</html>")
    return "\n".join(body)


def main():
    papers, missing = DATA["papers"], []
    (ROOT / "index.html").write_text(index_page(papers, DATA.get("other_work", [])), encoding="utf-8")
    for p in papers:
        d = ROOT / "papers" / p["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(paper_page(p), encoding="utf-8")
        if not (d / p["pdf"]).exists():
            missing.append(f"papers/{p['slug']}/{p['pdf']}")
        if not p["abstract"]:
            missing.append(f"abstract for {p['slug']}")
    print(f"built index.html + {len(papers)} paper pages")
    for m in missing:
        print(f"  TODO: {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
