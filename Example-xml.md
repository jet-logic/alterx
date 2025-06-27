### Example Scenario: Sitemap XML Processor

We'll process sitemap.xml files to:

1. Update lastmod dates
2. Remove deprecated URLs
3. Add new pages
4. Standardize formatting

---

### 1. Create Sample XML Files

```bash
mkdir -p websites
cat > websites/sitemap_old.xml <<EOF
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
EOF

cat > websites/sitemap_new.xml <<EOF
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/blog</loc>
  </url>
</urlset>
EOF
```

### 2. Create Processing Script (`sitemap_updater.py`)

```python
from datetime import datetime

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
    print(f"Processed {app.total.Files} sitemaps")
    print(f"Removed {getattr(app.total, 'Removed', 0)} deprecated URLs")
    print(f"Added {getattr(app.total, 'Added', 0)} new URLs")
```

### 3. Run the Processor

```bash
# Using the `-mm` flag, write only if modified
# With pretty printing and XML declaration
python -m alterx.xml -mm --pretty --xml-declaration -x sitemap_updater.py websites

# Alternative with lxml for better formatting
python -m alterx.xml -mm --pretty --ns-clean -x sitemap_updater.py websites
```

### 4. Expected Output Files

**sitemap_old.xml**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
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
```

**sitemap_new.xml**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
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
```

---

### Test Case

```python
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
        self.script.write_text("""
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
    stat.added = 0
    stat.removed = 0

    # Remove old URLs
    for url in root.findall('sm:url', ns):
        loc = url.find('sm:loc', ns)
        if any(path in loc.text for path in app.defs['DEPRECATED_PATHS']):
            root.remove(url)
            stat.removed += 1
            modified = True

    # Add lastmod if missing
    for url in root.findall('sm:url', ns):
        if url.find('sm:lastmod', ns) is None:
            ET.SubElement(url, 'lastmod').text = app.defs['TODAY']
            modified = True

    # Add new URLs
    existing = {u.find('sm:loc', ns).text for u in root.findall('sm:url', ns)}
    for new in app.defs['NEW_URLS']:
        if new['loc'] not in existing:
            url = ET.SubElement(root, 'url')
            ET.SubElement(url, 'loc').text = new['loc']
            ET.SubElement(url, 'lastmod').text = app.defs['TODAY']
            stat.added += 1

def end(app):
    app.total.Added = sum(hasattr(s, 'added') and s.added for s in app._stats)
    app.total.Removed = sum(hasattr(s, 'removed') and s.removed for s in app._stats)
""")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_sitemap_processing(self):
        # Run processor
        app = AlterXML()
        app.main([
            "-m",
            "--pretty",
            "-x", str(self.script),
            str(self.test_dir / "sitemap.xml")
        ])

        # Verify output
        tree = ET.parse(self.test_dir / "sitemap.xml")
        root = tree.getroot()
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Check URLs
        urls = [url.find('sm:loc', ns).text for url in root.findall('sm:url', ns)]
        self.assertNotIn('https://test.com/old', urls)
        self.assertIn('https://test.com/current', urls)
        self.assertIn('https://test.com/new', urls)

        # Check lastmod dates
        today = datetime.now().strftime('%Y-%m-%d')
        for url in root.findall('sm:url', ns):
            lastmod = url.find('sm:lastmod', ns)
            self.assertIsNotNone(lastmod)
            self.assertEqual(lastmod.text, today)

        # Verify stats
        self.assertEqual(app.total.Added, 1)
        self.assertEqual(app.total.Removed, 1)

if __name__ == "__main__":
    unittest.main()
```

### Key Features Demonstrated:

1. **Namespace Handling**: Proper XML namespace management
2. **Date Processing**: Automatic lastmod date updates
3. **Element Manipulation**: Adding, removing and modifying nodes
4. **Statistics Tracking**: Custom counters for added/removed URLs
5. **XML Declaration**: Preserving/adding XML declarations
6. **Pretty Printing**: Formatted output for readability

This example shows how to use `alterx` for professional XML processing tasks, with specific optimizations for sitemap files. The same pattern can be adapted for other XML formats like RSS feeds, configuration files, or data interchange formats.
