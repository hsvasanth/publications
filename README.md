# Publications

Source for <https://hsvasanth.github.io/publications> — a crawlable landing page per paper, so Google Scholar has something to index that isn't the journal's own site.

**This repo is public.** Only published, open-access papers belong here. Unpublished drafts, Turnitin reports, and anything under `evidence/` in the private `research-papers` repo must never be added — public posting is prior disclosure at most venues, and the Turnitin PDFs carry live submission IDs.

## Why it exists

Scholar reads [Highwire Press `citation_*` meta tags](https://scholar.google.com/intl/en/scholar/inclusion.html) from a paper's landing page. Three fields are mandatory — `citation_title`, `citation_author`, `citation_publication_date` — and Scholar discards **every** tag on a page that omits any one of them. Each generated page carries the full set, plus `citation_pdf_url` pointing at a text-searchable PDF with no login or paywall.

## Editing

All content lives in [`publications.json`](publications.json). Nothing is hand-edited in HTML.

```bash
python3 build.py     # regenerates index.html and papers/<slug>/index.html
```

The build prints a `TODO` for any paper missing its PDF or abstract.

### Abstracts and keywords

All three are verbatim from the published papers, supplied by the author by hand. They were **not** machine-extracted: these PDFs set type in subset fonts with custom encodings, so automated extraction silently drops and mangles words — `scripts/pdftext.py` in the `research-papers` repo documents exactly how. Anything added here later should come from the paper the same way.

Keywords are the papers' own keyword lists, emitted as `citation_keywords`. They matter because they let a page rank for topic queries rather than only for its exact title.

### DOIs

`"doi": null` on all three. None of these papers has a Crossref DOI — checked against the Crossref API by title and by author, no matches. Set the field and rebuild once one exists; the page will emit `citation_doi` and link to `doi.org`.

## Adding the next paper

`publications.json` is the single source of truth. Add one entry, run two scripts, and the site, your BibTeX and your Zenodo payloads all follow from it — they cannot drift apart.

```bash
# 1. archive the PDF in the private repo (manifest-driven, dry run first)
cd ~/research/papers
#    add a line to scripts/manifest.txt, then:
./scripts/backup-papers.sh                  # review
./scripts/backup-papers.sh --apply --push

# 2. add the paper to publications.json, copy the PDF in, then:
cd ~/research/publications
python3 build.py                            # site pages + citation_* tags
python3 export.py                           # export/publications.bib + Zenodo payloads
git add -A && git commit && git push        # Pages redeploys automatically
```

Then the three things no script can do, because none of them has an API you can drive without a personal token:

| Step | Automatable? | How |
|---|---|---|
| Zenodo deposit → DOI | **yes, scripted** | `python3 zenodo_deposit.py <slug> --publish` |
| ORCID work entry | partly | ORCID → Works → Add → **Import BibTeX** → `export/publications.bib` |
| Google Scholar entry | **no** | no write API exists; add it by hand |

Finally, put the minted DOI back into `publications.json` and re-run both scripts. The paper page then emits `citation_doi` and links to `doi.org`, which is what lets a citation attach to you by exact match instead of by fuzzy title guessing.

### Transcribe abstracts by hand

Worth repeating because it is the one step that looks automatable and isn't. See the note in `publications.json`.

See [WORKFLOW.md](WORKFLOW.md) for the full process, including the mistakes the web forms invite and how each was caught.

## Publishing

GitHub Pages, served from the default branch root:

```bash
git remote add origin git@github.com-personal:hsvasanth/publications.git
git push -u origin main
# then: repo Settings → Pages → Source: main / (root)
```

The `github.com-personal` host alias is required — the plain `github.com` form offers the work-machine SSH keys.
