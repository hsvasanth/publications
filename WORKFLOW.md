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

```bash
# 1. archive the PDF privately
cd ~/research/papers
#    add a line to scripts/manifest.txt
./scripts/backup-papers.sh                    # dry run, review
./scripts/backup-papers.sh --apply --push

# 2. add the paper to publications.json, copy the PDF into papers/<slug>/
cd ~/research/publications
python3 build.py                              # site + citation_* tags
python3 export.py                             # BibTeX + Zenodo payloads

# 3. mint the DOI
export ZENODO_TOKEN=...                       # zenodo.org/account/settings/applications
python3 zenodo_deposit.py <slug>              # draft — review in browser
python3 zenodo_deposit.py <slug> --publish    # mints the DOI

# 4. put the DOI back in publications.json, then
python3 build.py && python3 export.py
git add -A && git commit && git push

# 5. verify the record actually matches what you sent
python3 zenodo_deposit.py <slug> --verify <record_id>
```

Then two manual steps: import `export/publications.bib` into ORCID, and add the paper to Google Scholar by hand.

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
