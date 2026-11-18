# Qualcomm BREW Archive

[Browse the archive](https://wakkatobakka.github.io/qualcomm-brew-archive/) ·
[Platform history](https://wakkatobakka.github.io/qualcomm-brew-archive/history/) ·
[People and studios](https://wakkatobakka.github.io/qualcomm-brew-archive/creators/) ·
[Sources](https://wakkatobakka.github.io/qualcomm-brew-archive/sources/)

Wakkatobakka’s independent archive of Qualcomm BREW games. The catalog connects game histories, developer accounts and period materials to the packages preserved by the [Internet Archive collection](https://archive.org/details/qualcomm-brew-games).

## Collection

The catalog covers 104 package records, including display variants, demos and utilities. The source collection groups 84 RAR files under `brew2010` and 20 ZIP files under `brew2018`. Release dates come from historical sources where available.

| Data | Contents |
| --- | --- |
| [Catalog CSV](data/catalog.csv) and [catalog JSON](data/catalog.json) | Original inventory, paths, categories and package SHA-256 values |
| [Package evidence](data/package-evidence.json) | Original member filenames and recorded display sizes |
| [Handset metadata](data/handset-metadata.json) | Titles, versions and credit strings from preserved descriptors |
| [Research data](data/research.json) | Histories, edition-scoped credits, quotations, images and sources |

Preservation credit goes to the original collectors and contributors to the Internet Archive item. Images, quotations and supporting documents have individual credits. Copyright remains with the respective rights holders. Game packages can be found through the original collection.

## Maintenance

The committed HTML is ready for GitHub Pages at the repository root. For local review, open `index.html` in a browser. Run the following from the repository root to regenerate and validate the pages after editing the research data.

```sh
python3 tools/build_site.py
python3 tools/verify.py
```

Read [AGENTS.md](AGENTS.md), the [archive standard](ARCHIVE_STANDARD.md) and the [research status](research/STATUS.md) before starting another pass. To report a correction, open a [GitHub issue](https://github.com/Wakkatobakka/qualcomm-brew-archive/issues) with the entry ID and supporting source.
