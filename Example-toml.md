### Example Scenario: Updating Project Configuration Files

We'll process TOML files (like Python's `pyproject.toml`) to:

1. Update dependency versions
2. Add missing sections
3. Standardize formatting

---

### 1. Create Sample TOML Files

```bash
mkdir -p projects
cat > projects/project_a.toml <<EOF
[build-system]
requires = ["setuptools>=61.0.0"]
build-backend = "setuptools.build_meta"

[tool.poetry]
name = "project-a"
version = "1.0.0"
EOF

cat > projects/project_b.toml <<EOF
[project]
name = "project-b"
dynamic = ["version"]
EOF
```

### 2. Create Processing Script (`update_toml.py`)

```python
def init(app):
    # Define our standard versions
    app.defs.update({
        'SETUPTOOLS_VERSION': ">=68.0.0",
        'PYTHON_REQUIRES': ">=3.8"
    })

def process(doc, stat, app):
    # Update setuptools version
    if 'build-system' in doc and 'requires' in doc['build-system']:
        reqs = doc['build-system']['requires']
        for i, req in enumerate(reqs):
            if req.startswith('setuptools'):
                reqs[i] = f"setuptools{app.defs['SETUPTOOLS_VERSION']}"

    # Add python requires if missing
    if 'project' in doc and 'requires-python' not in doc['project']:
        doc['project']['requires-python'] = app.defs['PYTHON_REQUIRES']

    # Add description if missing
    if 'project' in doc and 'description' not in doc['project']:
        doc['project']['description'] = ""

def end(app):
    print(f"Updated {app.total.Altered}/{app.total.Files} TOML files")
```

### 3. Run the Processor

Using `-mm` flag to modify only if changed.

```bash
> python -m alterx.toml -mm -x update_toml.py projects

INFO: Module 'ext_e9cb3fe6' '/tmp/tmpxoe8wqsr/processor.py'
INFO: TOML [#1] /tmp/tmpxoe8wqsr/project_a.toml
WARN: Altered!
INFO: TOML [#2] /tmp/tmpxoe8wqsr/project_b.toml
WARN: Altered!
Updated 2/2 TOML files
INFO: Total Altered 2; Files 2;
```

If you run it agian, nothing is modified!

```bash
> python -m alterx.toml -mm -x update_toml.py projects
INFO: Module 'ext_e9cb3fe6' '/tmp/tmpxoe8wqsr/processor.py'
INFO: TOML [#1] /tmp/tmpxoe8wqsr/project_a.toml
INFO: TOML [#2] /tmp/tmpxoe8wqsr/project_b.toml
Updated 0/2 TOML files
INFO: Total Altered 0; Files 2;
```

### 4. Expected Output Files

**project_a.toml**:

```toml
[build-system]
requires = ["setuptools>=68.0.0"]
build-backend = "setuptools.build_meta"

[tool.poetry]
name = "project-a"
version = "1.0.0"
```

**project_b.toml**:

```toml
[project]
name = "project-b"
dynamic = ["version"]
requires-python = ">=3.8"
description = ""
```

### Key Features Demonstrated:

- **TOML-Specific Handling**: Uses `tomlkit` for parsing/preserving formatting
- **Conditional Modifications**: Only makes changes when needed
- **Variable Passing**: Shares configuration through `app.defs`
- **Change Detection**: Only modifies files that need updates

This example shows how to use `alterx` for maintaining consistency across TOML configuration files in a project repository. The test case verifies both the transformation logic and the tool's change detection capabilities.
