"""Check inventory preservation, generated routes and internal references."""
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import json
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
from build_site import BASE, ORIGINAL, ROOT, route


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = []
        self.links = []
        self.copies = []
        self.h1 = 0
        self.rows = 0
        self.feed(path.read_text())

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])
        if "data-copy" in attrs:
            self.copies.append(attrs["data-copy"])
        self.h1 += tag == "h1"
        self.rows += "file-row" in attrs.get("class", "").split()


def json_data(path):
    return json.loads((ROOT / "data" / path).read_text())


def checked_link(source, href, pages):
    if href.startswith(BASE):
        parsed = urlsplit(href[len(BASE):])
        target = ROOT / unquote(parsed.path)
    else:
        parsed = urlsplit(href)
        if parsed.netloc or parsed.scheme:
            assert parsed.scheme in ("http", "https"), href
            return
        path = unquote(parsed.path)
        target = (source.parent / path).resolve() if path else source
    if target.is_dir():
        target /= "index.html"
    assert target.is_relative_to(ROOT) and target.is_file(), (source, href)
    if parsed.fragment and target in pages:
        assert unquote(parsed.fragment) in pages[target].ids, (source, href)


def main():
    inventory = json_data("catalog.json")
    evidence = json_data("package-evidence.json")
    research = json_data("research.json")
    items = inventory["items"]
    assert len(items) == inventory["package_count"] == 104
    assert Counter(item["collection"] for item in items) == {"brew2010": 84, "brew2018": 20}
    assert {item["id"] for item in items} == evidence.keys() == research["games"].keys()
    pages = {path: Page(path) for path in ROOT.rglob("*.html") if ".git" not in path.parts}
    site_map = ET.parse(ROOT / "sitemap.xml")
    assert len(site_map.getroot()) == len(pages) - 1
    for path, p in pages.items():
        assert len(set(p.ids)) == len(p.ids), (path, [i for i, n in Counter(p.ids).items() if n > 1])
        assert p.h1 == 1, path
        for link in p.links:
            checked_link(path, link, pages)

    quoted = Counter()
    images = set()
    for item in items:
        gid = item["id"]
        game = research["games"][gid]
        p = pages[ROOT / route(item)]
        assert p.rows == item["internal_file_count"] == len(evidence[gid]["members"]), gid
        assert set(p.copies) == {item["path"], item["sha256"]}, gid
        assert ORIGINAL in p.links
        assert all(q.get("speaker") and q.get("attribution") for q in game["quotes"]), gid
        for q in game["quotes"]:
            url = research["sources"][q["source"]]["url"]
            quoted[url] += sum(len((q.get(k) or "").split()) for k in ("text", "translation"))
        for m in game.get("media", []):
            verify_image(m, images)
    for m in research.get("platform_media", []):
        verify_image(m, images)
    assert all(n <= 25 for n in quoted.values())
    print(f"Verified {len(items)} package routes, {sum(len(row['members']) for row in evidence.values())} original member names, {len(pages)} HTML pages and {len(images)} archived image files.")


def verify_image(m, images):
    path = ROOT / m["path"]
    assert path.is_file()
    assert sha256(path.read_bytes()).hexdigest() == m["sha256"]
    assert m["width"] > 0 and m["height"] > 0
    assert all(m.get(k) for k in ("alt", "caption", "credit", "original_url", "platform", "kind"))
    images.add(path)


if __name__ == "__main__":
    main()
