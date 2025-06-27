from io import StringIO
import re
import unittest
import tempfile
from pathlib import Path
from alterx.html import AlterHTML
from lxml import html, etree


def canonicalize_html(html_string, **kwargs):
    parser = html.HTMLParser(remove_comments=True, remove_pis=True, compact=True, remove_blank_text=True)
    tree = html.parse(StringIO(re.sub(r"\s+", " ", html_string).strip()), parser)
    xml_tree = etree.ElementTree(tree.getroot())
    for element in xml_tree.iter():
        if element.text and element.text.strip():
            element.text = None
        if element.tail and element.tail.strip():
            element.tail = None
    return etree.canonicalize(etree.tostring(xml_tree, encoding="unicode", pretty_print=False))


class TestHTMLProcessing(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        self.files = (
            (
                self.test_dir.joinpath("html_optimizer.py"),
                r"""
from lxml import html
from pathlib import Path

def init(app):
    # Configuration parameters
    app.defs.update({
        'SITE_NAME': 'My Website',
        'ANALYTICS_ID': 'UA-1234567-1',
        'DEFAULT_META_DESC': 'Default description for pages without one'
    })

def process(doc, file_info, app):
    root = doc.getroot()

    # Ensure proper HTML structure
    if root.tag != 'html':
        return False

    # HEAD section processing
    head = root.find('head')
    if head is not None:
        # Add missing charset meta
        if not head.xpath('//meta[@charset]'):
            meta = html.Element('meta', charset='UTF-8')
            head.insert(0, meta)

        # Add missing viewport meta
        if not head.xpath('//meta[@name="viewport"]'):
            meta = html.Element('meta', name='viewport',
                              content='width=device-width, initial-scale=1')
            head.insert(1, meta)


        # Add default description if missing
        if not head.xpath('//meta[@name="description"]'):
            meta = html.Element('meta', name='description',
                              content=app.defs['DEFAULT_META_DESC'])
            head.append(meta)

        # Add canonical link if missing
        if not head.xpath('//link[@rel="canonical"]'):
            link = html.Element('link', rel='canonical',
                              href=f"https://example.com/{Path(file_info.path).name}")
            head.append(link)


    # BODY section processing
    body = root.find('body')
    if body is not None:
        # Add alt text to images
        for img in body.xpath('//img[not(@alt)]'):
            img.set('alt', '')

        # Convert width/height attributes to CSS
        for img in body.xpath('//img[@width or @height]'):
            style = img.get('style', '')
            if img.get('width'):
                style += f"width: {img.get('width')}px;"
                del img.attrib['width']
            if img.get('height'):
                style += f"height: {img.get('height')}px;"
                del img.attrib['height']
            img.set('style', style)

        # Standardize heading hierarchy
        first_h = next((e for e in body.iter() if e.tag in ('h1','h2','h3','h4','h5','h6')), None)
        if first_h is not None and first_h.tag != 'h1':
            first_h.tag = 'h1'

        # Inject analytics before closing body
        if not body.xpath('//script[contains(text(), "GoogleAnalytics")]'):
            script = html.Element('script')
            script.text = "\n".join(['window.ga=window.ga||function(){{(ga.q=ga.q||[]).push(arguments)}};',
 "ga('create', '{app.defs['ANALYTICS_ID']}', 'auto');",
 "ga('send', 'pageview');"])
            body.append(script)

def end(app):
    print(f"Optimized {app.total.Altered}/{app.total.Files} HTML files")
    print(f"Added {getattr(app.total, 'MetaTags', 0)} meta tags")
    print(f"Fixed {getattr(app.total, 'Images', 0)} images")
            """,
            ),
            (
                self.test_dir.joinpath("website/index.html"),
                r"""
<!DOCTYPE html>
<html>
<head>
    <title>Home Page</title>
</head>
<body>
    <h2>Welcome</h2>
    <img src="logo.png">
    <div class="content">
        <p>Main page content</p>
    </div>
</body>
</html>
        """,
            ),
            (
                self.test_dir.joinpath("website/about.html"),
                r"""
<!DOCTYPE html>
<html>
<head>
    <title>About Us</title>
    <meta name="description" content="Learn about our company">
</head>
<body>
    <h3>Our Story</h3>
    <img src="team.jpg" width="300">
</body>
</html>
                  """,
            ),
        )
        for path, content in self.files:
            path.parent.mkdir(exist_ok=True)
            path.write_text(content.strip())

    def tearDown(self):
        import shutil

        # shutil.rmtree(self.test_dir)
        print(self.test_dir)

    def test_html_processing(self):
        # Run processor
        app = AlterHTML()
        targets = ((path, path.stat().st_mtime) for path, content in self.files[1:])
        app.main(["-mm", "-x", str(self.files[0][0]), str(self.test_dir / "website")])
        self.assertEqual(
            tuple(canonicalize_html(path.read_text()) for path, mtime in targets),
            (
                canonicalize_html(
                    r"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Home Page</title>
    <meta
      name="description"
      content="Default description for pages without one"
    />
    <link rel="canonical" href="https://example.com/index.html" />
  </head>
  <body>
    <h1>Welcome</h1>
    <img src="logo.png" alt="" />
    <div class="content">
      <p>Main page content</p>
    </div>
    <script>
      window.ga =
        window.ga ||
        function () {
          (ga.q = ga.q || []).push(arguments);
        };
      ga("create", "UA-1234567-1", "auto");
      ga("send", "pageview");
    </script>
  </body>
</html>
               """
                ),
                canonicalize_html(
                    r"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>About Us</title>
    <meta name="description" content="Learn about our company" />
    <link rel="canonical" href="https://example.com/about.html" />
  </head>
  <body>
    <h1>Our Story</h1>
    <img src="team.jpg" style="width: 300px;" alt="" />
    <script>
      window.ga =
        window.ga ||
        function () {
          (ga.q = ga.q || []).push(arguments);
        };
      ga("create", "UA-1234567-1", "auto");
      ga("send", "pageview");
    </script>
  </body>
</html>
                """
                ),
            ),
        )
        self.assertTrue(all(path.stat().st_mtime > mtime for path, mtime in targets))

        targets = ((path, path.stat().st_mtime) for path, content in self.files[1:])
        app.main(["-mm", "-x", str(self.files[0][0]), str(self.test_dir / "website")])
        self.assertTrue(all(path.stat().st_mtime == mtime for path, mtime in targets))


if __name__ == "__main__":
    unittest.main()
