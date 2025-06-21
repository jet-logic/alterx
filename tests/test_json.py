from shutil import rmtree
import unittest
import json
import tempfile
import os
from pathlib import Path
from alterx.json import AlterJSON


class TestJSONProcessing(unittest.TestCase):
    def setUp(self):
        # Create temporary directory
        self.test_dir = Path(tempfile.mkdtemp())

        # Create sample JSON files
        self.original_files = {
            "app1.json": {"app": "dashboard", "api_url": "http://old.example.com", "settings": {"debug": True, "timeout": 30}},
            "app2.json": {"app": "backend", "api_url": "http://old.api.example.com", "debug": True},
        }

        for filename, content in self.original_files.items():
            with open(self.test_dir / filename, "w") as f:
                json.dump(content, f)

        # Create our processing script
        self.script_path = self.test_dir / "update_configs.py"
        with open(self.script_path, "w") as f:
            f.write(
                """
def init(app):
    app.defs['NEW_API'] = "https://api.new.example.com/v2"

def process(doc, stat, app):
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
            """
            )

    def tearDown(self):
        # Clean up temporary directory
        rmtree(self.test_dir)

    def test_json_processing(self):
        # Expected results after processing
        expected_results = {
            "app1.json": {
                "app": "dashboard",
                "api_url": "https://api.new.example.com/v2",
                "settings": {"debug": False, "timeout": 30},
                "version": "2.0.0",
            },
            "app2.json": {"app": "backend", "api_url": "https://api.new.example.com/v2", "debug": False, "version": "2.0.0"},
        }

        # Run the processor (in-memory for testing)
        app = AlterJSON()
        app.main(["-m", "-x", str(self.script_path), str(self.test_dir)])

        # Verify results
        for filename, expected in expected_results.items():
            with open(self.test_dir / filename) as f:
                result = json.load(f)
                self.assertEqual(result, expected, f"{filename} not processed correctly")

    def test_dry_run(self):
        # Run in dry-run mode (no changes should be made)
        app = AlterJSON()
        app.main(["-m", "--dry-run", "-x", str(self.script_path), str(self.test_dir)])

        # Verify no files were changed
        for filename, original in self.original_files.items():
            with open(self.test_dir / filename) as f:
                result = json.load(f)
                self.assertEqual(result, original, f"{filename} was modified during dry run")

    def test_modification_detection(self):
        # First run - should modify both files
        app = AlterJSON()
        app.main(["-mm", "-x", str(self.script_path), str(self.test_dir)])

        self.assertEqual(app.total.Files, 2)
        self.assertEqual(app.total.Altered, 2)

        # Second run - should detect no changes needed
        app = AlterJSON()
        app.main(["-mm", "-x", str(self.script_path), str(self.test_dir)])

        self.assertEqual(app.total.Files, 2)
        self.assertEqual(app.total.Altered, 0)

    def test_script_from_stdin(self):
        # Test passing script via stdin
        import subprocess

        script_content = """
def process(doc, stat, app):
    doc['processed'] = True
    return True
"""

        cmd = ["python", "-m", "alterx.json", "-m", "-x", "-", str(self.test_dir)]

        result = subprocess.run(cmd, input=script_content, text=True, capture_output=True)

        # Verify the file was processed
        with open(self.test_dir / "app1.json") as f:
            content = json.load(f)
            self.assertTrue(content["processed"])


if __name__ == "__main__":
    unittest.main()
