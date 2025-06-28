from contextlib import redirect_stdout
from subprocess import run
from sys import stderr
import unittest
import re
import tempfile
import xml.etree.ElementTree as ET
from io import StringIO
from pathlib import Path
from alterx.xml import AlterXML
from datetime import datetime
from lxml import etree


def canonicalize_xml(xml_string, **kwargs):
    parser = etree.XMLParser(remove_comments=True, remove_pis=True, compact=True, remove_blank_text=True)
    tree = etree.parse(StringIO(re.sub(r"\s+", " ", xml_string).strip()), parser)
    xml_tree = etree.ElementTree(tree.getroot())
    for element in xml_tree.iter():
        if element.text and element.text.strip():
            element.text = None
        if element.tail and element.tail.strip():
            element.tail = None
    return etree.canonicalize(etree.tostring(xml_tree, encoding="unicode", pretty_print=False))


class TestSitemapProcessing(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        self.files = (
            (
                self.test_dir.joinpath("sitemap_updater.py"),
                r"""
from datetime import datetime
from sys import stderr
def init(app):
    # Configuration
    app.defs.update({
        'DEPRECATED_PATHS': ['/old-page', '/temp'],
        'NEW_URLS': [
            {'loc': 'https://example.com/contact', 'priority': '0.8'},
            {'loc': 'https://example.com/about'}
        ],
        'DEFAULT_LASTMOD': datetime.now().strftime('%Y-%m-%d')
    })

def process(doc, file_info, app):
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    root = doc.getroot()
    
    # Remove deprecated URLs
    for url in root.findall('sm:url', ns):
        loc = url.find('sm:loc', ns)
        if any(path in loc.text for path in app.defs['DEPRECATED_PATHS']):
            root.remove(url)
    
    # Update lastmod dates
    for url in root.findall('sm:url', ns):
        lastmod = url.find('sm:lastmod', ns)
        if lastmod is None:
            lastmod = app.etree.SubElement(url, 'lastmod')
            lastmod.text = app.defs['DEFAULT_LASTMOD']
        elif lastmod.text < app.defs['DEFAULT_LASTMOD']:
            lastmod.text = app.defs['DEFAULT_LASTMOD']
    
    # Add new URLs
    existing_urls = {url.find('sm:loc', ns).text for url in root.findall('sm:url', ns)}
    for new_url in app.defs['NEW_URLS']:
        if new_url['loc'] not in existing_urls:
            url_elem = app.etree.SubElement(root, 'url')
            app.etree.SubElement(url_elem, 'loc').text = new_url['loc']
            app.etree.SubElement(url_elem, 'lastmod').text = app.defs['DEFAULT_LASTMOD']
            if 'priority' in new_url:
                app.etree.SubElement(url_elem, 'priority').text = new_url['priority']

def end(app):
    print(f"Processed {app.total.Files} sitemaps", file=stderr)
    print(f"Removed {getattr(app.total, 'Removed', 0)} deprecated URLs", file=stderr)
    print(f"Added {getattr(app.total, 'Added', 0)} new URLs", file=stderr)
            """,
            ),
            (
                self.test_dir.joinpath("websites/sitemap_old.xml"),
                r"""
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/home</loc>
    <lastmod>2022-01-01</lastmod>
  </url>
  <url>
    <loc>https://example.com/old-page</loc>
    <lastmod>2021-05-15</lastmod>
  </url>
</urlset>
        """,
            ),
            (
                self.test_dir.joinpath("websites/sitemap_new.xml"),
                r"""
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/blog</loc>
  </url>
</urlset>
                  """,
            ),
        )
        for path, content in self.files:
            path.parent.mkdir(exist_ok=True)
            path.write_text(content.strip())

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir)

    def test_sitemap_processing(self):
        # Run processor
        targets = ((path, path.stat().st_mtime) for path, content in self.files[1:])
        AlterXML().main(["-mm", "-x", str(self.files[0][0]), str(self.test_dir / "websites")])
        self.assertEqual(
            tuple(canonicalize_xml(path.read_text()) for path, mtime in targets),
            (
                canonicalize_xml(
                    r"""
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/home</loc>
    <lastmod>2023-11-15</lastmod>
  </url>
  <url>
    <loc>https://example.com/contact</loc>
    <lastmod>2023-11-15</lastmod>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2023-11-15</lastmod>
  </url>
</urlset>
               """
                ),
                canonicalize_xml(
                    r"""
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/blog</loc>
    <lastmod>2023-11-15</lastmod>
  </url>
  <url>
    <loc>https://example.com/contact</loc>
    <lastmod>2023-11-15</lastmod>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2023-11-15</lastmod>
  </url>
</urlset>
                """
                ),
            ),
        )
        self.assertTrue(all(path.stat().st_mtime > mtime for path, mtime in targets))

        # should be not modified
        targets = ((path, path.stat().st_mtime) for path, content in self.files[1:])
        AlterXML().main(["-mm", "-x", str(self.files[0][0]), str(self.test_dir / "websites")])
        self.assertTrue(all(path.stat().st_mtime == mtime for path, mtime in targets))

    def test_sink(self):
        out = self.test_dir / "out"
        with out.open("w") as f:
            with redirect_stdout(f):
                AlterXML().main(["-mm", "-x", str(self.files[0][0]), "-o", "-", str(self.files[1][0])])
        self.assertEqual(
            canonicalize_xml(out.read_text()),
            canonicalize_xml(
                r"""
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/home</loc>
    <lastmod>2023-11-15</lastmod>
  </url>
  <url>
    <loc>https://example.com/contact</loc>
    <lastmod>2023-11-15</lastmod>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2023-11-15</lastmod>
  </url>
</urlset>
               """
            ),
        )


if __name__ == "__main__":
    unittest.main()
