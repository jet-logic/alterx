import unittest
import tempfile
import tomlkit
from pathlib import Path
from alterx.toml import AlterToml


class TestTOMLProcessing(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        # Create test files
        self.files = {
            "project_a.toml": """
                [build-system]
                requires = ["setuptools>=61.0.0"]
                build-backend = "setuptools.build_meta"
            """,
            "project_b.toml": """
                [project]
                name = "test-project"
            """,
        }

        for name, content in self.files.items():
            (self.test_dir / name).write_text(content.strip())

        # Create processor script
        self.script = self.test_dir / "processor.py"
        self.script.write_text(
            """
def init(app):
    app.defs['PYTHON_REQUIRES'] = ">=3.9"
    
def process(doc, file_info, app):
    if 'project' in doc:
        doc['project']['requires-python'] = app.defs['PYTHON_REQUIRES']
        # return True
"""
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir)

    def test_toml_processing(self):
        # Run processor
        app = AlterToml()
        app.main(["-mm", "-x", str(self.script), str(self.test_dir)])

        # Verify changes
        for name in self.files:
            content = tomlkit.loads((self.test_dir / name).read_text())
            if "project" in content:
                self.assertEqual(content["project"]["requires-python"], ">=3.9", f"{name} not processed correctly")

    def test_no_unnecessary_changes(self):
        # First run should modify files
        app = AlterToml()
        app.main(["-mm", "-x", str(self.script), str(self.test_dir)])
        self.assertEqual(app.total.Altered, 1)  # Only project_b.toml has [project]

        # Second run should make no changes
        app = AlterToml()
        app.main(["-mm", "-x", str(self.script), str(self.test_dir)])
        self.assertEqual(app.total.Altered, 0)


if __name__ == "__main__":
    unittest.main()
