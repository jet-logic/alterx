import unittest
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from alterx.xml import AlterXML
from datetime import datetime


class TestSitemapProcessing(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        # Create test sitemap
        self.sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://test.com/old</loc>
    <lastmod>2020-01-01</lastmod>
  </url>
  <url>
    <loc>https://test.com/current</loc>
  </url>
</urlset>"""

        (self.test_dir / "sitemap.xml").write_text(self.sitemap)

        # Create processor script
        self.script = self.test_dir / "sitemap_updater.py"
        self.script.write_text(
            """
from datetime import datetime

def init(app):
    app.defs.update({
        'DEPRECATED_PATHS': ['/old'],
        'NEW_URLS': [{'loc': 'https://test.com/new'}],
        'TODAY': datetime.now().strftime('%Y-%m-%d')
    })

def process(doc, stat, app):
    modified = False
    root = doc.getroot()
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    # Track changes for testing
    app.total.added = 0
    app.total.removed = 0
    
    # Remove old URLs
    for url in root.findall('sm:url', ns):
        loc = url.find('sm:loc', ns)
        if any(path in loc.text for path in app.defs['DEPRECATED_PATHS']):
            root.remove(url)
            app.total.removed += 1
            modified = True
    
    # Add lastmod if missing
    for url in root.findall('sm:url', ns):
        if url.find('sm:lastmod', ns) is None:
            app.etree.SubElement(url, 'lastmod').text = app.defs['TODAY']
            modified = True
    
    # Add new URLs
    existing = {u.find('sm:loc', ns).text for u in root.findall('sm:url', ns)}
    for new in app.defs['NEW_URLS']:
        if new['loc'] not in existing:
            url = app.etree.SubElement(root, 'url')
            app.etree.SubElement(url, 'loc').text = new['loc']
            app.etree.SubElement(url, 'lastmod').text = app.defs['TODAY']
            app.total.added += 1
            modified = True
    
    return modified

# def end(app):
#     app.total.Added = sum(hasattr(s, 'added') and s.added for s in app._stats)
#     app.total.Removed = sum(hasattr(s, 'removed') and s.removed for s in app._stats)
"""
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir)

    def test_sitemap_processing(self):
        # Run processor
        app = AlterXML()

        app.main(["-mm", "--pretty", "-x", str(self.script), str(self.test_dir)])

        # Verify output
        tree = ET.parse(self.test_dir / "sitemap.xml")
        root = tree.getroot()
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Check URLs
        urls = [url.find("sm:loc", ns).text for url in root.findall("sm:url", ns)]
        self.assertNotIn("https://test.com/old", urls)
        self.assertIn("https://test.com/current", urls)
        self.assertIn("https://test.com/new", urls)

        # Check lastmod dates
        today = datetime.now().strftime("%Y-%m-%d")
        for url in root.findall("sm:url", ns):
            lastmod = url.find("sm:lastmod", ns)
            self.assertIsNotNone(lastmod)
            self.assertEqual(lastmod.text, today)

        # Verify stats
        self.assertEqual(app.total.added, 1)
        self.assertEqual(app.total.removed, 1)


if __name__ == "__main__":
    unittest.main()
