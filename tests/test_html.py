import unittest
import tempfile
from pathlib import Path
from alterx.html import AlterHTML


class TestHTMLProcessing(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        # Create test HTML file
        self.test_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h2>Test Heading</h2>
    <img src="test.jpg" width="100">
</body>
</html>
"""
        (self.test_dir / "test.html").write_text(self.test_html.strip())

        # Create processor script
        self.script = self.test_dir / "html_processor.py"
        self.script.write_text(
            """
def init(app):
    app.defs['SITE_NAME'] = 'Test Site'

def process(doc, file_info, app):
    modified = False
    root = doc.getroot()
    
   
    # Head processing
    head = root.find('head')
    if head is not None:
        if not head.xpath('//meta[@charset]'):
            from lxml import html
            meta = html.Element('meta', charset='UTF-8')
            head.insert(0, meta)
            app.total.ImagesFixed += 1
            # modified = True
    
    # Body processing
    body = root.find('body')
    if body is not None:
        # Fix images
        for img in body.xpath('//img[not(@alt)]'):
            img.set('alt', f'location {img.get("src")}')
            app.total.MetaAdded += 1
            # modified = True
        
        # Fix headings
        first_h = next((e for e in body.iter() if e.tag.startswith('h')), None)
        # print('first_h', first_h, first_h.tag)
        if first_h is not None and first_h.tag != 'h1':
            first_h.tag = 'h1'
            # modified = True
    
    # return modified
"""
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir)

    def test_html_processing(self):
        # Run processor
        app = AlterHTML()
        app.main(["-mm", "--pretty", "-x", str(self.script), str(self.test_dir)])

        # Verify output
        with open(self.test_dir / "test.html") as f:
            content = f.read()
            self.assertIn('<meta charset="UTF-8">', content)
            self.assertIn("<h1>Test Heading</h1>", content)
            self.assertRegex(content, r'<img\s+src="test.jpg"\s+width="100"\s+alt="location test.jpg"')
            # self.assertIn('<img src="test.jpg" alt="">', content)

        # Verify stats
        self.assertEqual(app.total.MetaAdded, 1)
        self.assertEqual(app.total.ImagesFixed, 1)


if __name__ == "__main__":
    unittest.main()
