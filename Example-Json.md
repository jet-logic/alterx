### Example Scenario

Let's say we have a directory of JSON configuration files that need:

1. All values under "api_url" keys updated
2. All "debug" flags set to `false`
3. A new "version" field added

### Step 1: Create Sample JSON Files

```bash
mkdir -p configs
cat > configs/app1.json <<EOF
{
    "app": "dashboard",
    "api_url": "http://old.example.com",
    "settings": {
        "debug": true,
        "timeout": 30
    }
}
EOF

cat > configs/app2.json <<EOF
{
    "app": "backend",
    "api_url": "http://old.api.example.com",
    "debug": true
}
EOF
```

### Step 2: Create Processing Script (`update_configs.py`)

```python
def init(app):
    app.defs['NEW_API'] = "https://api.new.example.com/v2"

def process(doc, file_info, app):
    modified = False

    if 'api_url' in doc:
        doc['api_url'] = app.defs['NEW_API']
        modified = True

    def disable_debug(obj):
        nonlocal modified
        if isinstance(obj, dict):
            if 'debug' in obj and obj['debug']:
                obj['debug'] = False
                modified = True
            for v in obj.values():
                disable_debug(v)

    disable_debug(doc)

    if 'version' not in doc:
        doc['version'] = "2.0.0"
        modified = True

    return modified

def end(app):
    print(f"Processed {app.total.Files} files, modified {app.total.Altered}")
```

### Step 3: Run the Processor

```bash
# Dry run first (no modification allowed)
python -m alterx.json -x update_configs.py configs

# Actual run (write changes if *process* returns True)
python -m alterx.json -m -x update_configs.py configs
```

### Sample Output

```
INFO: Module 'ext_8c567255' './update_configs.py'
INFO: JSON [#1] configs/app1.json
WARN: Altered?
INFO: JSON [#2] configs/app2.json
WARN: Altered?
Processed 2 files, modified 2
INFO: Total Altered 2; Files 2;

INFO: Module 'ext_e881a06c' './update_configs.py'
INFO: JSON [#1] configs/app1.json
WARN: Altered!
INFO: JSON [#2] configs/app2.json
WARN: Altered!
Processed 2 files, modified 2
INFO: Total Altered 2; Files 2;
```

### Key Features Demonstrated:

1. **Modification Detection**: Only writes files that actually changed (`-m` flag)
2. **Extension Script**: Custom Python logic in `update_configs.py`
3. **Variable Passing**: Using `app.defs` to share data
4. **Nested JSON Handling**: Recursive debug flag disabling
5. **Reporting**: Clean output showing changes

### Advanced Usage Example:

Using the `-mm` flag, no need to tell modification

#### Modify (`update_configs.py`)

```python
def init(app):
    app.defs['NEW_API'] = "https://api.new.example.com/v2"

def process(doc, file_info, app):
    ### modified = False

    if 'api_url' in doc:
        doc['api_url'] = app.defs['NEW_API']
        ### modified = True

    def disable_debug(obj):
        ### nonlocal modified
        if isinstance(obj, dict):
            if 'debug' in obj and obj['debug']:
                obj['debug'] = False
                ### modified = True
            for v in obj.values():
                disable_debug(v)

    disable_debug(doc)

    if 'version' not in doc:
        doc['version'] = "2.0.0"
        ### modified = True

    ### return modified

def end(app):
    print(f"Processed {app.total.Files} files, modified {app.total.Altered}")
```

#### Run the Processor

```bash
# Actual run (write changes, if document hash changes)
python -m alterx.json -mm -x update_configs.py configs
```

#### Sample Output

```
INFO: Module 'ext_070705d5' './update_configs.py'
INFO: JSON [#1] configs/app1.json
WARN: Altered!
INFO: JSON [#2] configs/app2.json
WARN: Altered!
Processed 2 files, modified 2
INFO: Total Altered 2; Files 2;
```

This shows how _alterx_ provides a powerful framework for batch JSON processing while keeping the actual transformation logic clean and Pythonic.
