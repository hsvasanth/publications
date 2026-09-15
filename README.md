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

### Abstracts are deliberately empty

The published PDFs are letter-spaced and extract as garbled text, so nothing was auto-filled rather than risk publishing a mangled abstract under your name. Paste each real abstract into `publications.json` and re-run the build. Until then the pages carry verified bibliographic metadata only — enough for Scholar, but the abstract is what makes a page findable by topic rather than by title.

### DOIs

`"doi": null` on all three. None of these papers has a Crossref DOI — checked against the Crossref API by title and by author, no matches. Set the field and rebuild once one exists; the page will emit `citation_doi` and link to `doi.org`.

## Publishing

GitHub Pages, served from the default branch root:

```bash
git remote add origin git@github.com-personal:hsvasanth/publications.git
git push -u origin main
# then: repo Settings → Pages → Source: main / (root)
```

The `github.com-personal` host alias is required — the plain `github.com` form offers the work-machine SSH keys.
