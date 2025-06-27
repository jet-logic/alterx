### Example Scenario: HTML Content Processor

We'll process HTML files to:

1. Add missing meta tags
2. Improve image accessibility
3. Standardize heading structure
4. Inject analytics scripts

---

### 1. Create Sample HTML Files

```bash
mkdir -p website
cat > website/index.html <<EOF
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
EOF

cat > website/about.html <<EOF
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
EOF
```

### 2. Create Processing Script (`html_optimizer.py`)

```python
from lxml import html

def init(app):
    # Configuration parameters
    app.defs.update({
        'SITE_NAME': 'My Website',
        'ANALYTICS_ID': 'UA-1234567-1',
        'DEFAULT_META_DESC': 'Default description for pages without one'
    })

def process(doc, stat, app):
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
                              href=f"https://example.com/{stat.path.name}")
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
        if first_h and first_h.tag != 'h1':
            first_h.tag = 'h1'

        # Inject analytics before closing body
        if not body.xpath('//script[contains(text(), "GoogleAnalytics")]'):
            script = html.Element('script')
            script.text = f"""
                window.ga=window.ga||function(){{(ga.q=ga.q||[]).push(arguments)}};
                ga('create', '{app.defs['ANALYTICS_ID']}', 'auto');
                ga('send', 'pageview');
            """
            body.append(script)

def end(app):
    print(f"Optimized {app.total.Altered}/{app.total.Files} HTML files")
    print(f"Added {getattr(app.total, 'MetaTags', 0)} meta tags")
    print(f"Fixed {getattr(app.total, 'Images', 0)} images")
```

### 3. Run the Processor

```bash
# With HTML pretty printing
python -m alterx.html -mm -x html_optimizer.py website

# Alternative with more aggressive HTML cleaning
python -m alterx.html -mm --strip-comments --strip-pis -x html_optimizer.py website
```

### 4. Expected Output Files

**index.html**:

```html
<!DOCTYPE html>
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
```

**about.html**:

```html
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
```

---

### Key Features Demonstrated:

1. **HTML5 Structure**: Ensures proper document structure
2. **SEO Optimization**: Adds meta tags and canonical links
3. **Accessibility**: Handles image alt text and heading hierarchy
4. **Modern Practices**: Converts deprecated attributes to CSS
5. **Analytics Injection**: Adds tracking scripts non-invasively
6. **Change Tracking**: Detailed statistics about modifications

This example shows how to use `alterx` for professional HTML processing tasks, with specific optimizations for modern web development best practices. The same pattern can be adapted for other HTML processing needs like template injection, CSS/JS bundling, or content migration.
