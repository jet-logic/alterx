# AlterX - The File Transformation Toolkit

<!-- [![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/) -->
<!-- [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) -->

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Tests Status](https://github.com/jet-logic/alterx/actions/workflows/tests.yml/badge.svg)](https://github.com/jet-logic/alterx/actions)
[![PyPI version fury.io](https://badge.fury.io/py/alterx.svg)](https://pypi.python.org/pypi/alterx/)

AlterX is a powerful command-line tool for batch processing and transforming files in various formats. It provides a consistent framework for modifying HTML, JSON, TOML, XML, and YAML files with custom Python logic.

## Features

- **Multi-format support**: Process HTML, JSON, TOML, XML, and YAML files
- **Extension system**: Define transformations in Python scripts
- **Smart modification**: Only changes files that need updates
- **Batch processing**: Recursively process entire directories
- **Dry run mode**: Test changes before applying them
- **Comprehensive logging**: Detailed output about modifications

## ☕ Support

If you find this project helpful, consider supporting me:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/B0B01E8SY7)

## Installation

```bash
pip install alterx
```

## Quick Start

1. Create a processing script (e.g., `transform.py`):

```python
def init(app):
    app.defs['VERSION'] = "2.0.0"

def process(doc, file_info, app):
    if 'version' in doc:
        doc['version'] = app.defs['VERSION']
        return True
```

2. Run AlterX:

```bash
# Process JSON files
alterx json -x transform.py path/to/files
```

### Example Use Cases Shown

- [JSON](Example-json.md) Updating API URLs across multiple JSON config files
- [TOML](Example-toml.md) Maintaining consistent Python project TOML files
- [HTML](Example-html.md) Standardizing HTML documents (adding missing tags, accessibility improvements)
- [XML](Example-xml.md) Processing XML sitemaps (adding/removing URLs, updating dates)
- [YAML](Example-yaml.md) Managing Kubernetes YAML manifests (adding labels, updating image tags)
