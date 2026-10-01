# Publishing a paper: the whole process

Written after doing it three times by hand and getting something wrong every time. Every error came from a web form, not from the data — so the rule is: keep the data in `publications.json`, generate everything else, and hand-fill as little as possible.

## Where each system stands

| System | Write API? | What we do |
|---|---|---|
| Private archive (`research-papers`) | n/a | `backup-papers.sh`, manifest-driven, dry run by default |
| This site + Scholar meta tags | n/a | `build.py` |
| Zenodo → DOI | **yes** | `zenodo_deposit.py` — fully scripted |
| ORCID | read-only public API | `export.py` → BibTeX → one import action |
| Google Scholar | **none** | manual, permanently |

## The sequence

One command. It asks for the paper's details and does everything that does not
need a browser.

```bash
cd ~/research/publications
export ZENODO_TOKEN=...        # zenodo.org/account/settings/applications
                               # scopes: deposit:write deposit:actions
python3 newpaper.py
```

It will:

1. write the entry into `publications.json`
2. copy the PDF into `papers/<slug>/`
3. run `build.py` — site page with the full `citation_*` tag set
4. run `export.py` — BibTeX for ORCID, Zenodo payload, creators file
5. offer to deposit on Zenodo and mint the DOI
6. write the DOI back, rebuild, commit
7. print the three steps that need a browser, with the values to paste

Two confirmations are required and both default to **no**: minting the DOI
(irreversible — it freezes the file) and pushing (this repo is public).

Then separately, archive the PDF in the private repo:

```bash
cd ~/research/papers
#   add a line to scripts/manifest.txt
./scripts/backup-papers.sh                  # dry run, review
./scripts/backup-papers.sh --apply --push
```

### What still needs a browser, and why

| Step | Why not scripted |
|---|---|
| ORCID | writes need an OAuth token; BibTeX import is one action |
| Google Scholar | no write API exists at all, and no DOI field |
| Zenodo ISSN | not a field in the deposition API |

Everything else — including the related-work link back to this site, which is
how Scholar finds you — is set by the API deposit automatically.

## Checking it later

```bash
python3 audit.py            # report
python3 audit.py --strict   # exit 1 on any problem
```

Compares `publications.json`, Zenodo and ORCID and names anything that has
drifted. Read-only. Worth running after any manual edit in a web form, since
that is where every error so far has come from.

Things it has caught: a paper carrying another paper's DOI, which made ORCID
merge two works into one and hide a publication entirely; keywords silently
dropped because Zenodo's tag field needs Enter after each one; a DOI stored as
a full URL instead of a bare identifier.

## Transcribe the abstract by hand

The one step that looks automatable and isn't. These PDFs use subset fonts with custom encodings; automated extraction silently drops words. On NG-iRTS it lost the clause naming what the framework actually combines — the substance of the contribution. `scripts/pdftext.py` in the `research-papers` repo documents this and is good enough for checking metadata, not for quoting.

## Mistakes made, so they aren't made again

**Zenodo signup truncated the name.** It offered "Vasantha Kumar Hosahalli", dropping Seenappa, and that name pre-fills the creator on every deposit and lands in permanent DOI metadata. Upload `export/zenodo-creators.json` via *Add authors from file* rather than typing it.

**CC-BY was selected where the journal requires CC-BY-SA.** IJISAE publishes under Attribution-ShareAlike 4.0. Choosing plain CC-BY drops the ShareAlike condition — relicensing terms that are not yours to relicense. One wrong dropdown entry.

**Keywords collapsed into a single subject.** The form needs Enter after each tag; typing four and clicking away stores one long string, or nothing. The API takes a list and gets it right.

**ISSN was skipped.** Easy to miss in the Journal section, and it is how indexers tie the record to the journal.

**Edits were saved as a draft and never published.** On an already-published record, *Save draft* stores changes privately; only *Publish* makes them live. The giveaway is a "Discard changes" button appearing in the right-hand panel.

**A verification script read the wrong field paths.** `/api/records/<id>` returns the *legacy* serialisation — `metadata.license`, `metadata.journal`, flat `creators[].orcid`. Checking InvenioRDM paths (`metadata.rights`, `custom_fields['journal:journal']`) against it reports a complete record as entirely empty. `zenodo_deposit.py --verify` uses the right paths.

## Google Scholar

No API, and **no DOI field** — the manual entry form offers Title, Authors, Date, Journal, Volume, Issue, Pages, Publisher and nothing else. You cannot attach a DOI to a Scholar entry.

What happens instead: Scholar crawls Zenodo, finds the deposit, and creates its own entry beside your manual one. Select both and use **Merge**. That is the only route, and it is why the citation metadata on this site matters — it is the machine-readable copy Scholar can actually read.

## What none of this does

It removes the mechanical obstacles to a citation landing: no identifier, no crawlable page, inconsistent author name. It does not produce citations. That still comes from the work.
