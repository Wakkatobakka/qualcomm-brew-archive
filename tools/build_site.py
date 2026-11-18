"""Render the archive from its immutable package inventory and editorial data."""
from collections import Counter, defaultdict
from html import escape
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://wakkatobakka.github.io/qualcomm-brew-archive/"
REPO = "https://github.com/Wakkatobakka/qualcomm-brew-archive"
ORIGINAL = "https://archive.org/details/qualcomm-brew-games"
NAV = [
    ("catalog", "Catalog", "index.html#catalog"),
    ("history", "Platform history", "history/index.html"),
    ("creators", "Creators", "creators/index.html"),
    ("sources", "Sources", "sources/index.html"),
]


def read(name):
    return json.loads((ROOT / "data" / name).read_text())


def h(value):
    return escape(str(value), quote=True)


def slug(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def route(item):
    return item["url"] + "index.html"


def brand(prefix, footer=False):
    mark = "" if footer else '<span class="brand-mark" aria-hidden="true"><span></span><span></span><span></span><span></span></span>'
    return f'<a class="brand" href="{prefix}index.html" aria-label="BREW Archive home">{mark}<span>BREW <span class="brand-slash">/</span> ARCHIVE</span></a>'


READABLE_TITLES = {
    "callofduty--callofduty": "Call of Duty",
    "crittercrunch--crittercrunch": "Critter Crunch",
    "jewelquest--jewelquest": "Jewel Quest",
    "massivesnowboarding--massivesnowboarding": "Massive Snowboarding",
    "pacman--pacman": "Pac-Man",
    "translator-utility-not-game--translator-net-ok": "Translator",
    "verizon-superpages-utility-not-game--vz-superpages-lg4400-net-ok": "Verizon SuperPages",
    "weatherbug-utility-not-game--weatherbug": "WeatherBug",
}


class Archive:
    def __init__(self):
        self.items = read("catalog.json")["items"]
        self.items_by_id = {item["id"]: item for item in self.items}
        self.package_evidence = read("package-evidence.json")
        self.research = read("research.json")
        self.games = self.research["games"]
        self.handset_metadata = read("handset-metadata.json")
        for item in self.items:
            game = self.games[item["id"]]
            item["display_title"] = game.get(
                "display_title", READABLE_TITLES.get(item["id"], item["title"])
            )
        self.sources = self.research["sources"]
        self.people = defaultdict(list)
        self.studios = defaultdict(list)
        self.pages = []
        for item in self.items:
            game = self.games[item["id"]]
            for credit in game["credits"]:
                self.people[credit["name"]].append((item, credit))
            for credit in game["studio_roles"]:
                self.studios[credit["name"]].append((item, credit))

    def save(self, path, title, description, body, active="", scripts=()):
        prefix = "../" * path.count("/")
        canonical = BASE + path.removesuffix("index.html")
        full_title = title + " | BREW Archive"
        top = "".join(
            f'<a href="{prefix}{url}"' + (' aria-current="page"' if key == active else '') + f'>{label}</a>'
            for key, label, url in NAV
        )
        sibling_links = "".join(
            f'<a href="https://wakkatobakka.github.io/{folder}/">{name} ↗</a>'
            for name, folder in [
                ("DoJa", "doja-archive"), ("ExEn", "exen-game-archive"),
                ("J2ME", "j2me-archive"), ("N-Gage", "ngage-archive"),
                ("Zeebo", "zeebo-archive"),
            ]
        )
        js = "".join(f'<script src="{prefix}assets/{name}" defer></script>' for name in scripts)
        doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0b1017">
<title>{h(full_title)}</title>
<meta name="description" content="{h(description)}">
<link rel="canonical" href="{h(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{h(full_title)}">
<meta property="og:description" content="{h(description)}">
<meta property="og:url" content="{h(canonical)}">
<meta property="og:image" content="{BASE}assets/social-preview.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/styles.css">
<link rel="stylesheet" href="{prefix}assets/history.css">
</head>
<body>
<div class="ambient" aria-hidden="true"></div>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="shell nav-shell">{brand(prefix)}<nav class="top-nav" aria-label="Main navigation">{top}</nav></div></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="shell"><div class="foot"><div>{brand(prefix, footer=True)}<p class="preservation-credit">Original files preserved by the contributors to the Internet Archive Qualcomm BREW Games collection.</p></div><div class="foot-links"><a href="{prefix}about/index.html">Methods &amp; credits</a><a href="{REPO}">GitHub ↗</a><a href="https://wakkatobakka.github.io/">Wakka’s Workshop ↗</a></div></div><nav class="archive-family" aria-label="Other game archives"><span>Other archives</span>{sibling_links}</nav></div></footer>
{js}
</body>
</html>
"""
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc)
        if path != "404.html":
            self.pages.append(canonical)

    def citations(self, ids, refs):
        if not ids:
            return ""
        links = "".join(
            f'<a href="#source-{h(sid)}" aria-label="Source {refs.index(sid) + 1}">[{refs.index(sid) + 1}]</a>'
            for sid in dict.fromkeys(ids)
        )
        return f'<span class="citations">{links}</span>'

    def paragraphs(self, items, refs):
        if not items:
            return ""
        body = "".join(f'<p>{h(p["text"])}{self.citations(p["sources"], refs)}</p>' for p in items)
        return f'<div class="entry-prose">{body}</div>'

    def quotes(self, items, refs, section):
        quotes = []
        for q in items:
            if q["section"] != section:
                continue
            lang = f' lang="{h(q["lang"])}"' if q.get("lang") else ""
            translation = f'<span class="translation-credit">{h(q["translation"])} <small>(English translation)</small></span>' if q.get("translation") else ""
            citation = self.citations([q["source"]], refs)
            quotes.append(
                f'<figure class="source-quote"><blockquote{lang}><p>“{h(q["text"])}”</p></blockquote>'
                f'<figcaption>{h(q["speaker"])} · {h(q["attribution"])}{citation}{translation}</figcaption></figure>'
            )
        return "".join(quotes)

    def gallery(self, items, refs, prefix):
        figures = []
        for m in items:
            url = prefix + m["path"]
            caption = h(m["caption"])
            credit_text = h(m["credit"])
            credit = f'<span class="image-credit">{credit_text} · <a href="{h(m["original_url"])}">Original image ↗</a></span>'
            wide = " wide-media" if m["kind"] in ("production", "document", "advertisement", "guide") else ""
            figures.append(
                f'<figure class="archive-figure{wide}"><div class="artifact" data-kind="{h(m["kind"])}">'
                f'<a class="image-open" href="{url}" data-image="{url}" data-caption="{caption}" aria-label="Enlarge image">'
                f'<img src="{url}" alt="{h(m["alt"])}" width="{m["width"]}" height="{m["height"]}" loading="lazy"></a></div>'
                f'<figcaption>{caption}{self.citations([m["source"]], refs)}{credit}</figcaption></figure>'
            )
        return "".join(figures)

    def bibliography(self, refs):
        rows = []
        for sid in refs:
            s = self.sources[sid]
            meta = " · ".join(h(s[key]) for key in ("published", "kind") if s.get(key))
            note = f'<p>{h(s["note"])}</p>' if s.get("note") else ""
            rows.append(f'<li id="source-{h(sid)}"><a href="{h(s["url"])}">{h(s["title"])} ↗</a><small>{meta}</small>{note}</li>')
        return '<section class="entry-section bibliography" id="sources"><h2>Sources</h2><ol>' + "".join(rows) + '</ol></section>'

    def refs(self, game, gid=None):
        ids = []
        for key in ("overview", "development", "release", "notes"):
            ids.extend(sid for p in game.get(key, []) for sid in p["sources"])
        for key in ("quotes", "credits", "studio_roles", "media"):
            ids.extend(p["source"] for p in game.get(key, []))
        if gid:
            ids.extend(game.get("previous_sources", []))
            ids.append("inventory-" + gid)
        return list(dict.fromkeys(ids))

    def viewer(self):
        return (
            '<dialog id="image-viewer" aria-labelledby="viewer-title"><div class="viewer-toolbar"><strong id="viewer-title">Archive image</strong>'
            '<div><button id="viewer-zoom" type="button" aria-pressed="false">Zoom in</button><button id="viewer-close" type="button">Close</button></div></div>'
            '<div id="viewer-canvas" class="viewer-canvas"><img id="viewer-image" alt=""></div></dialog>'
        )

    def card(self, item):
        game = self.games[item["id"]]
        search = [item[k] for k in ("display_title", "title", "original_inventory_label", "id", "filename", "path", "sha256")]
        search.extend(game.get("aliases", []))
        search.extend(c["name"] for c in game["credits"] + game["studio_roles"])
        search.extend(m["name"] for m in self.package_evidence[item["id"]]["members"])
        search.append(game["deck"])
        return (
            f'<a class="entry-card" href="{route(item)}" data-search="{h(" ".join(search))}" '
            f'data-type="{h(item["category"])}" data-collection="{h(item["collection"])}">'
            f'<div><span class="entry-sub">{h(item["category"])}</span>'
            f'<h3 class="entry-title">{h(item["display_title"])}</h3><p class="entry-description">{h(game["deck"])}</p></div>'
            f'<span class="card-bottom"><small>{h(item["filename"])} · {h(item["collection"])}</small><span aria-hidden="true">↗</span></span></a>'
        )

    def home(self):
        counts = Counter(item["category"] for item in self.items)
        chips = []
        for kind, label in [("All", "All packages"), ("Game", "Games"), ("Demo", "Demos"), ("Utility", "Utilities"), ("Add-on", "Add-ons")]:
            pressed = "true" if kind == "All" else "false"
            chips.append(f'<button class="chip" type="button" data-type="{kind}" aria-pressed="{pressed}">{label}</button>')
        featured = []
        for gid in ["bioshock-3d--bio3d", "shs-exact-game-title-unverified--shs", "aliens-vs-predator-3d--avp"]:
            item, game = self.items_by_id[gid], self.games[gid]
            art = next((m for m in game.get("media", []) if "dhams" in m["path"] or "kings" in m["path"]), None)
            if not art:
                art = next(iter(game.get("media", [])), None)
            preview = ""
            if art:
                preview = f'<div class="feature-image" aria-hidden="true"><img src="{h(art["path"])}" width="{art["width"]}" height="{art["height"]}" alt="" loading="lazy"></div>'
            featured.append(f'<a class="feature-card" href="{route(item)}">{preview}<div><h3>{h(item["display_title"])}</h3><p>{h(game["deck"])}</p></div></a>')
        body = f"""
<section class="shell brew-intro">
  <h1>Qualcomm <em>BREW</em> Archive</h1>
  <p class="hero-lede">Games downloaded to carrier phones, with the developers, reviews and original files behind them. Browse 104 preserved packages, including games, demos and utilities.</p>
  <div class="hero-actions"><a class="btn btn-primary" href="#catalog">Browse the catalog ↓</a><a class="btn btn-secondary" href="history/index.html">Platform history</a></div>
</section>
<section class="shell featured-section"><div class="section-heading"><h2>Start with a game</h2></div><div class="feature-grid">{"".join(featured)}</div></section>
<section class="catalog-wrap" id="catalog"><div class="shell">
  <div class="section-heading"><h2>Catalog</h2><p>{counts["Game"]} game packages, {counts["Demo"]} demos, {counts["Utility"]} utilities and {counts["Add-on"]} add-on.</p></div>
  <div class="catalog-controls">
    <label class="search-field"><span class="sr-only">Search by title, creator, filename or checksum</span><input id="search" type="search" autocomplete="off" placeholder="Title, creator, filename or checksum"><kbd aria-hidden="true">/</kbd></label>
    <div class="filter-group" role="group" aria-label="Package type">{"".join(chips)}</div>
    <div class="collection-picker"><label for="collection">Source subset</label><select id="collection"><option value="All">All subsets</option><option value="brew2010">brew2010</option><option value="brew2018">brew2018</option></select></div>
  </div>
  <div class="results-line"><span id="results-count" role="status">Showing {len(self.items)} of {len(self.items)} packages</span><a href="data/catalog.csv" download>Catalog CSV ↓</a></div>
  <div class="entry-grid">{"".join(self.card(item) for item in self.items)}</div>
  <div class="empty-results" id="no-results" hidden><h3>No matching packages</h3><p>Try another name or clear the filters.</p></div>
  <div class="catalog-bottom"><button class="btn btn-secondary" type="button" id="clear-search">Reset filters</button></div>
</div></section>"""
        self.save("index.html", "Qualcomm BREW games and their history", "The Qualcomm BREW game archive. Games, developers, period coverage, and 104 preserved packages.", body, "catalog", ("site.js",))

    def credit_rows(self, credits, kind, refs):
        grouped = defaultdict(list)
        for c in credits:
            grouped[c["name"]].append(c)
        rows = []
        for name, work in grouped.items():
            roles = " · ".join(dict.fromkeys(c["role"] + (f' ({c["scope"]})' if c.get("scope") else "") for c in work))
            teams = " · ".join(dict.fromkeys(c["team"] for c in work if c.get("team")))
            detail = f'<small>{h(teams)}</small>' if teams else ""
            rows.append(
                f'<div class="person-row"><h3><a href="../../creators/index.html#{kind}-{slug(name)}">{h(name)}</a></h3>'
                f'<div><p>{h(roles)}{self.citations([c["source"] for c in work], refs)}</p>{detail}</div></div>'
            )
        return '<div class="people-list">' + "".join(rows) + '</div>' if rows else ""

    def files(self, item, refs):
        evidence = self.package_evidence[item["id"]]
        members = "".join(f'<div class="file-row"><code>{h(m["name"])}</code><span>{h(m["size_display"])}</span></div>' for m in evidence["members"])
        facts = [
            ("Original inventory label", item["original_inventory_label"]),
            ("Filename", item["filename"]), ("Source subset", item["collection"]),
            ("Archive format", item["archive_format"]), ("Package size", f'{item["size_bytes"]:,} bytes'),
            ("Listing", f'{item["internal_file_count"]} files'), ("Inventory identification", item["identification"]),
        ]
        if item["variant_note"]:
            facts.append(("Display notation", item["variant_note"]))
        metadata = self.handset_metadata.get(item["id"])
        handset_html = ""
        if metadata:
            names = [
                ("title", "Title in descriptor"), ("version", "Version string"),
                ("credit", "Credit string"), ("other_credit", "Additional credit"),
                ("name", "Descriptor file"), ("sha256", "Descriptor SHA-256"),
            ]
            lines = "".join(
                f'<div><dt>{label}</dt><dd>{h(metadata[key])}</dd></div>'
                for key, label in names if key in metadata
            )
            handset_html = f'<details class="contents"><summary>Handset metadata</summary><dl class="package-dl handset-data">{lines}</dl></details>'
        facts_html = "".join(f'<div><dt>{label}</dt><dd>{h(value)}</dd></div>' for label, value in facts if value)
        related = "".join(
            f'<li><a href="../../{route(self.items_by_id[gid])}">{h(self.items_by_id[gid]["display_title"])} ↗</a></li>'
            for gid in evidence["related"]
        )
        related_html = f'<div class="related-packages"><h3>Related package records</h3><ul>{related}</ul></div>' if related else ""
        types = " ".join(f'<code>{h(t)}</code>' for t in item["types"])
        return f"""
<div class="package-facts"><p>In the Internet Archive item, open <strong>Qualcomm BREW Games.zip</strong> and look for the path below.{self.citations(["inventory-" + item["id"]], refs)}</p>
<div class="package-line"><code>{h(item["path"])}</code><button class="copy-button" type="button" data-copy="{h(item["path"])}">Copy path</button></div>
<a class="btn btn-secondary" href="{ORIGINAL}">Open original collection ↗</a>
<dl class="package-dl">{facts_html}</dl>
<div class="checksum"><span class="checksum-title">SHA-256 fingerprint</span><code id="hash-value">{item["sha256"]}</code><button class="copy-button" data-copy="{item["sha256"]}" type="button">Copy checksum</button></div>
<details class="contents"><summary>Inside the package · {item["internal_file_count"]} files</summary><p class="member-types">{types}</p><div class="file-list">{members}</div></details>
{handset_html}{related_html}</div>"""

    def game(self, item):
        gid = item["id"]
        game = self.games[gid]
        refs = self.refs(game, gid)
        sections, toc = [], []

        def add(key, title, content, alias=""):
            if content:
                toc.append((key, title))
                anchor = f'<span id="{alias}" class="legacy-anchor"></span>' if alias else ""
                sections.append(f'<section class="entry-section" id="{key}">{anchor}<h2>{title}</h2>{content}</section>')

        archive_only = game["coverage"]["status"] == "inventory"
        overview_title = "The package" if archive_only else {
            "Game": "The game", "Demo": "The sample", "Utility": "The application", "Add-on": "The add-on",
        }[item["category"]]
        placements = defaultdict(list)
        for media in game.get("media", []):
            placements[media.get("placement", "gallery")].append(media)
        add("the-game", overview_title, self.paragraphs(game["overview"], refs) + self.gallery(placements["game"], refs, "../../"), "historical-context")
        add("development", "Development",
            self.paragraphs(game["development"], refs) + self.quotes(game["quotes"], refs, "development") + self.gallery(placements["development"], refs, "../../"))
        add("creators", "People &amp; studios",
            self.credit_rows(game["credits"], "person", refs) + self.credit_rows(game["studio_roles"], "studio", refs))
        add("release", "Release &amp; reception",
            self.paragraphs(game["release"], refs) + self.quotes(game["quotes"], refs, "reception"))
        add("gallery", "Gallery", self.gallery(placements["gallery"], refs, "../../"))
        add("files", "Files &amp; versions", self.files(item, refs))
        limits = self.paragraphs(game["notes"], refs)
        gaps = game["coverage"].get("remaining_gaps", [])
        if gaps:
            limits += "<ul>" + "".join(f"<li>{h(gap)}</li>" for gap in gaps) + "</ul>"
        if limits:
            sections.append(f'<details class="edition-notes"><summary>Edition &amp; research notes</summary>{limits}</details>')
        toc.append(("sources", "Sources"))
        sections.append(self.bibliography(refs))
        jumps = "".join(f'<a href="#{key}">{title}</a>' for key, title in toc)
        year = f'<span class="chip">{h(game["year"])}</span>' if game["year"] else ""
        lead_refs = game["overview"][0]["sources"] if game["overview"] else []
        body = f"""
<header class="shell detail-hero">
<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../../index.html#catalog">Catalog</a><span aria-hidden="true">/</span><span aria-current="page">{h(item["display_title"])}</span></nav>
<div class="chips">{year}<span class="chip mint">{h(item["category"])}</span><a class="chip file-shortcut" href="#files">Files &amp; versions ↓</a></div>
<h1>{h(item["display_title"])}</h1><p class="detail-deck">{h(game["deck"])}{self.citations(lead_refs, refs)}</p>
</header>
<div class="shell entry-layout"><nav class="entry-contents" aria-label="In this entry"><h2>In this entry</h2><div>{jumps}</div></nav><article class="game-entry">{"".join(sections)}</article></div>
{self.viewer() if game.get("media") else ""}
"""
        self.save(route(item), item["display_title"], game["deck"], body, scripts=("site.js", "entry.js"))

    def platform(self):
        sections = self.research["platform"]
        images = self.research.get("platform_media", [])
        refs = list(dict.fromkeys(
            [sid for s in sections for p in s["paragraphs"] for sid in p["sources"]]
            + [m["source"] for m in images]
        ))
        body = '<article class="narrow article platform-history"><h1>Platform history</h1>'
        body += '<p class="lede">BREW reached players through phone carriers. Their storefronts, device lists and testing programs shaped which games a handset owner could download.</p>'
        for section in sections:
            cards = " · ".join(f'<a href="../{route(self.items_by_id[gid])}">{h(title)}</a>' for gid, title in section["links"])
            figures = [m for m in images if m.get("section") == section["id"]]
            body += (
                f'<section class="entry-section" id="{section["id"]}"><h2>{h(section["title"])}</h2>'
                + self.paragraphs(section["paragraphs"], refs)
                + self.gallery(figures, refs, "../")
                + f'<p class="platform-links">{cards}</p></section>'
            )
        figures = [m for m in images if not m.get("section")]
        if figures:
            body += '<section class="entry-section" id="platform-gallery"><h2>Platform documents</h2>' + self.gallery(figures, refs, "../") + '</section>'
        body += self.bibliography(refs) + '</article>'
        self.save("history/index.html", "Platform history", "How Qualcomm BREW reached carriers, developers and players.", body + (self.viewer() if images else ""), "history", ("entry.js",))

    def creator_index(self):
        body = """<header class="shell index-hero"><h1>People &amp; studios</h1>
<p class="lede">Browse credited work by person or studio. Each credit names the edition or release its source covers.</p>
<div class="creator-tools" hidden><label for="creator-search">Search by creator, studio or game</label><input type="search" id="creator-search" autocomplete="off">
<div id="creator-count" role="status"></div></div>
<p id="creator-empty" hidden>No matching people or studios.</p></header>"""
        for kind, label, index in [("person", "People", self.people), ("studio", "Studios &amp; organizations", self.studios)]:
            body += f'<section class="shell creator-index"><h2>{label}</h2><div class="creator-grid">'
            for name, work in sorted(index.items(), key=lambda group: group[0].casefold()):
                entries = []
                search = [name]
                for item, c in work:
                    search.extend((item["title"], item["display_title"], c["role"], c.get("scope", "")))
                    anchor = f'{route(item)}#source-{h(c["source"])}'
                    scope = f' · {h(c["scope"])}' if c.get("scope") else ""
                    entries.append(
                        f'<li><a href="../{route(item)}">{h(item["display_title"])}</a>'
                        f'<span>{h(c["role"])}{scope} · <a href="../{anchor}">Source</a></span></li>'
                    )
                body += (
                    f'<article class="creator-card" id="{kind}-{slug(name)}" data-search="{h(" ".join(search))}">'
                    f'<h3>{h(name)}</h3><details><summary>Credits</summary><ul>{"".join(entries)}</ul></details></article>'
                )
            body += "</div></section>"
        self.save("creators/index.html", "People & studios", "Developer, artist, designer and studio credits for BREW and related mobile editions.", body, "creators", ("creators.js",))

    def source_index(self):
        games_by_source = defaultdict(list)
        for item in self.items:
            gid = item["id"]
            for key in self.refs(self.games[gid]):
                games_by_source[key].append(item)
        platform_refs = {
            *(sid for section in self.research["platform"] for p in section["paragraphs"] for sid in p["sources"]),
            *(m["source"] for m in self.research.get("platform_media", [])),
        }
        entries = sorted(set(games_by_source) | platform_refs, key=lambda sid: (urlsplit(self.sources[sid]["url"]).hostname or "", self.sources[sid]["title"].casefold()))
        body = f"""<article class="narrow article source-index"><h1>Sources</h1><p class="lede">Developer accounts, period reviews, carrier announcements and preservation records used across the archive.</p>
<section class="entry-section"><h2>Original collection</h2><p><a href="{ORIGINAL}">Qualcomm BREW Games on the Internet Archive ↗</a></p><p>The catalog records the package paths, internal filenames and SHA-256 values from this collection.</p></section>
<section class="entry-section"><h2>Reading and research</h2><div class="source-register"><ul>"""
        for sid in entries:
            s = self.sources[sid]
            backrefs = [f'<a href="../{route(item)}">{h(item["display_title"])}</a>' for item in games_by_source[sid]]
            if sid in platform_refs:
                backrefs.append('<a href="../history/index.html">Platform history</a>')
            meta = " · ".join(h(s[k]) for k in ("published", "kind") if s.get(k))
            body += f'<li id="source-{h(sid)}"><a href="{h(s["url"])}">{h(s["title"])} ↗</a><small>{meta}</small><p class="source-backrefs">{" · ".join(backrefs)}</p></li>'
        body += """</ul></div></section><section class="entry-section"><h2>Catalog downloads</h2>
<ul><li><a href="../data/catalog.csv" download>Original catalog CSV ↓</a></li><li><a href="../data/catalog.json" download>Original catalog JSON ↓</a></li>
<li><a href="../data/package-evidence.json" download>Package listings JSON ↓</a></li><li><a href="../data/handset-metadata.json" download>Handset descriptor metadata JSON ↓</a></li><li><a href="../data/research.json" download>Histories, sources and credits JSON ↓</a></li></ul>
<p><a href="../about/index.html">Read the research and preservation methods</a></p></section></article>"""
        self.save("sources/index.html", "Sources", "The sources cited in the Qualcomm BREW Archive and the original collection inventory.", body, "sources")

    def about(self):
        body = f"""<article class="narrow article"><h1>About the archive</h1>
<p class="lede">Wakkatobakka maintains this independent reference for BREW software and the people who made it.</p>
<section class="entry-section"><h2>Collection</h2><p>The 104 records come from the <a href="{ORIGINAL}">Qualcomm BREW Games collection</a>. Its two subsets contain 84 RAR packages under <code>brew2010</code> and 20 ZIP packages under <code>brew2018</code>. The folder names are the collector’s groupings. A game may have more than one package, including a separate display build.</p><p>Each SHA-256 identifies the exact nested archive as cataloged. The inventory shows member filenames and their recorded display sizes. The original collection was checked against all 104 recorded fingerprints. Where handset descriptors contain titles, credit strings or versions, those values appear under Files &amp; versions. Handset compatibility and playability require separate evidence.</p></section>
<section class="entry-section"><h2>Editorial method</h2><p>Research starts with the original label, member paths and any edition clues. Period reviews, release announcements, developer accounts and surviving images are checked against that evidence. A source can establish who made a game, which build a reviewer played or what a carrier offered. Claims about a specific preserved build need a link to its own package evidence.</p><p>Where a title or edition is uncertain, the entry names the clue and what remains to be found. Quotes are given in the speaker’s original wording, with English translations when needed. Image captions identify the material, its origin and the edition it depicts.</p></section>
<section class="entry-section"><h2>Credits &amp; corrections</h2><p>Preservation credit goes to the original collectors and contributors to the Internet Archive item. Scans, period photographs and screenshots carry their own source credits. Copyright remains with the respective rights holders. The site is an independent archive.</p><p>To send a correction, <a href="{REPO}/issues">open a GitHub issue</a> with the entry and a supporting source.</p></section>
<p><a href="../sources/index.html">Browse the source register and catalog downloads ↗</a></p></article>"""
        self.save("about/index.html", "Methods & credits", "Scope, provenance and editorial methods for the Qualcomm BREW Archive.", body)
        self.save("404.html", "Page unavailable", "Find another page in the Qualcomm BREW Archive.",
                  f'<article class="narrow article"><h1>Page unavailable</h1><p><a href="{BASE}#catalog">Search the BREW catalog</a></p></article>')

    def render(self):
        self.home()
        for item in self.items:
            self.game(item)
        self.platform()
        self.creator_index()
        self.source_index()
        self.about()
        xml = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        for canonical in self.pages:
            ET.SubElement(ET.SubElement(xml, "url"), "loc").text = canonical
        ET.indent(xml, space="  ")
        ET.ElementTree(xml).write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)
        print(f"Built {len(self.pages)} indexed pages and a 404.")


if __name__ == "__main__":
    Archive().render()
