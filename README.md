# Qualcomm BREW Archive — The Lost Catalog

**A complete, static GitHub Pages site built from the actual archived files.**

The website catalogs **104 surviving packages** from the Internet Archive item [Qualcomm BREW Games](https://archive.org/details/qualcomm-brew-games): 84 RAR files in `brew2010`, 20 ZIP files in `brew2018`, plus an archive readme. Each package has its own indexable page with exact source path, package size, original contents, and SHA-256 fingerprint. The homepage is searchable and supports type and collection filters. There are no game binaries in this project.

## Publish this site

1. Create a **public** GitHub repository called **`qualcomm-brew-archive`** under `Wakkatobakka`.
2. Upload the **contents** of this folder to the repository root (the `index.html`, `games`, `assets`, `data`, `about`, and other files), then commit. Don't upload the ZIP as one file expecting GitHub to unpack it.
3. In your repository's **Settings → Pages**, choose **Deploy from a branch**, branch **main**, folder **/(root)**, and save.

Expected site address after publication: **https://wakkatobakka.github.io/qualcomm-brew-archive/**

This website is static: no server, API key, paid service, or build step is necessary. It also works locally by opening `index.html` in a browser. If the repository name or username changes, update the absolute URLs in `sitemap.xml`, `robots.txt`, and the SEO metadata in each HTML page; the navigation links remain relative.

## What is indexed

- All **104 original archive packages**; also included are demos, non-game utilities, alternate display builds, and add-ons.
- **One detail page for every package** under `games/`.
- A searchable, source-grounded index with names labeled as tentative where appropriate.
- A `data/catalog.csv` and `data/catalog.json` dataset (metadata only).
- A sitemap covering all **106 HTML pages** (home, about, and 104 package pages).

**Archive folder names `brew2010` and `brew2018` are not verified release years.** Likewise, a preserved package does not establish device support or playability. The about page cites Qualcomm's 2001/2003 history and the original archive provenance. Game content and protected assets are not republished here.


## Researched history layer (October 2026)

This edition enriches **all 104 archive pages** and the searchable homepage with short descriptive introductions. It adds sourced histories and studio context where independent historical records were found, while preserving the original archive provenance and file listings. Historical annotations are also available as `history_*` fields in `data/catalog.json` and `data/catalog.csv`.

Research labels and their counts in this edition:

- **Documented game history:** 14 entries. Contemporary/retrospective sources discuss the named mobile game; an archived binary's exact revision may still be unverified.
- **Related mobile history:** 61 entries. The sources document a related franchise, platform edition or publisher; they do **not** prove authorship of that particular BREW binary.
- **Archive evidence only:** 29 entries. No adequate independent evidence was found; only surviving package facts are stated.

Individual source links are visible under each detail page's **Behind the game / History & context** section. The `/about/` page explains the labeling standard. Descriptions are independently written summaries, not copied press releases. **Neither public game ROMs nor private Android bridge sources, checkpoints, or signing material are included.**

If a studio credit cannot be tied to the exact BREW edition, it is shown as an associated or related credit, not an unqualified developer claim. The site intentionally leaves some mysteries unresolved.

## Why the hashes?

The SHA-256 for every package was calculated from the original nested archive entry bytes. This allows later researchers to identify an identical package even if the copy has been renamed.

## Updating the catalogue

Edit HTML pages and/or `data/catalog.csv` as verified new information is discovered. Avoid turning guesses into historical facts. The initial set of details was generated from the supplied archive's actual RAR/ZIP member listings, not manually invented.

---
Independent archival index. No affiliation with Qualcomm or any original game rights holder.
