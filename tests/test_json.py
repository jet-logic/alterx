import contextlib
from shutil import rmtree
import unittest
import json
import tempfile
import os
from pathlib import Path
from alterx.json import AlterJSON


class CD(contextlib.AbstractContextManager):
    """Non thread-safe context manager to change the current working directory."""

    def __init__(self, path):
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(os.getcwd())
        os.chdir(self.path)

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())


class TestJSONProcessing(unittest.TestCase):
    def setUp(self):
        # Create temporary directory
        self.test_dir = Path(tempfile.mkdtemp())

        # Create sample JSON files
        self.original_files = (
            (
                self.test_dir / "configs/app1.json",
                {
                    "app": "dashboard",
                    "api_url": "http://old.example.com",
                    "settings": {"debug": True, "timeout": 30},
                },
            ),
            (self.test_dir / "configs/app2.json", {"app": "backend", "api_url": "http://old.api.example.com", "debug": True}),
        )

        for p, content in self.original_files:
            p.parent.mkdir(exist_ok=True)
            with p.open("w") as f:
                json.dump(content, f)

        # Create our processing script
        self.script_path = self.test_dir / "update_configs.py"
        with open(self.script_path, "w") as f:
            f.write(
                """
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
            """
            )

    def tearDown(self):
        # Clean up temporary directory
        rmtree(self.test_dir)

    def _test_json_processing(self, m="-m"):
        # Expected results after processing
        expected_results = tuple(
            zip(
                [x[0] for x in self.original_files],
                (
                    {
                        "app": "dashboard",
                        "api_url": "https://api.new.example.com/v2",
                        "settings": {"debug": False, "timeout": 30},
                        "version": "2.0.0",
                    },
                    {
                        "app": "backend",
                        "api_url": "https://api.new.example.com/v2",
                        "debug": False,
                        "version": "2.0.0",
                    },
                ),
            )
        )

        # Run the processor (in-memory for testing)
        app = AlterJSON()
        with CD(self.test_dir):
            app.main([m, "-x", "./update_configs.py", "configs"])

        # Verify results
        for filename, expected in expected_results:
            with filename.open() as f:
                self.assertEqual(json.load(f), expected, f"{filename} not processed correctly")

    # @unittest.skip
    def test_json_processing(self, m="-m"):
        self._test_json_processing("-mm")

    # @unittest.skip
    def test_dry_run(self):
        # Run in dry-run mode (no changes should be made)
        with CD(self.test_dir):
            app = AlterJSON()
            app.main(["-n", "-x", "./update_configs.py", "configs"])

        # Verify no files were changed
        for filename, original in self.original_files:
            with filename.open() as f:
                self.assertEqual(json.load(f), original, f"{filename} was modified during dry run")

    # @unittest.skip
    def test_modification_detection(self):
        times = [(filename, filename.stat().st_mtime) for filename, _ in self.original_files]

        # First run - should modify both files
        with CD(self.test_dir):
            app = AlterJSON()
            app.main(["-m", "-x", "./update_configs.py", "configs"])

        self.assertEqual(app.total.Files, 2)
        self.assertEqual(app.total.Altered, 2)
        self.assertTrue(all(p.stat().st_mtime > m for p, m in times))
        times = [(filename, filename.stat().st_mtime) for filename, _ in self.original_files]

        # Second run - should detect no changes needed
        with CD(self.test_dir):
            app = AlterJSON()
            app.main(["-mm", "-x", str(self.script_path), str(self.test_dir)])

        self.assertEqual(app.total.Files, 2)
        self.assertEqual(app.total.Altered, 0)
        self.assertTrue(all(p.stat().st_mtime == m for p, m in times))

    # @unittest.skip
    def test_script_from_stdin(self):
        # Test passing script via stdin
        import subprocess

        script_content = """
def process(doc, file_info, app):
    doc['processed'] = True
    return True
"""
        with CD(self.test_dir):
            cmd = ["python", "-m", "alterx.json", "-m", "-x", "-", "configs"]
            subprocess.run(cmd, input=script_content, text=True, capture_output=True)
        for k, v in self.original_files:
            # Verify the file was processed
            with k.open() as f:
                content = json.load(f)
                self.assertTrue(content["processed"])

    def test_hash_check_modification(self):
        # Test passing script via stdin
        import re
        from tempfile import gettempdir

        tmp = Path(gettempdir())

        content = re.sub(r"(?m)^(\s+)([\w\s]*modified)", r"\1### \2", self.script_path.read_text().strip())
        with self.test_dir.joinpath("update_configs.py").open("w") as w:
            w.write(content)

        with tmp.joinpath("update_configs_new.py").open("w") as w:
            w.write(content)
        self._test_json_processing("-mm")


if __name__ == "__main__":
    unittest.main()
