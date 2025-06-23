import unittest
import tempfile
import tomlkit
from pathlib import Path
from alterx.toml import AlterToml


class TestTOMLProcessing(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        # Create test files
        self.files = (
            (
                self.test_dir / "project_a.toml",
                r"""
[build-system]
requires = ["setuptools>=61.0.0"]
build-backend = "setuptools.build_meta"

[tool.poetry]
name = "project-a"
version = "1.0.0"
            """,
            ),
            (
                self.test_dir / "project_b.toml",
                r"""
[project]
name = "project-b"
dynamic = ["version"]
            """,
            ),
        )

        for path, content in self.files:
            path.write_text(content.strip())

        # Create processor script
        self.script = self.test_dir / "processor.py"
        self.script.write_text(
            r"""
def init(app):
    # Define our standard versions
    app.defs.update({
        'SETUPTOOLS_VERSION': ">=68.0.0",
        'PYTHON_REQUIRES': ">=3.8"
    })

def process(doc, stat, app):
    modified = False

    # Update setuptools version
    if 'build-system' in doc and 'requires' in doc['build-system']:
        reqs = doc['build-system']['requires']
        for i, req in enumerate(reqs):
            if req.startswith('setuptools'):
                reqs[i] = f"setuptools{app.defs['SETUPTOOLS_VERSION']}"
                modified = True

    # Add python requires if missing
    if 'project' in doc and 'requires-python' not in doc['project']:
        doc['project']['requires-python'] = app.defs['PYTHON_REQUIRES']
        modified = True

    # Add description if missing
    if 'project' in doc and 'description' not in doc['project']:
        doc['project']['description'] = ""
        modified = True

    return modified

def end(app):
    print(f"Updated {app.total.Altered}/{app.total.Files} TOML files")
"""
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir)

    def _test_toml_processing(self, m="-m"):
        # Run processor
        app = AlterToml()
        app.main([m, "-x", str(self.script), str(self.test_dir)])

        self.assertEqual(
            tuple(tomlkit.loads(path.read_text()) for path, content in self.files),
            (
                {
                    "build-system": {"requires": ["setuptools>=68.0.0"], "build-backend": "setuptools.build_meta"},
                    "tool": {"poetry": {"name": "project-a", "version": "1.0.0"}},
                },
                {"project": {"name": "project-b", "dynamic": ["version"], "requires-python": ">=3.8", "description": ""}},
            ),
        )

    # @unittest.skip
    def test_toml_processing(self):
        self._test_toml_processing()

    # @unittest.skip
    def test_no_unnecessary_changes(self):
        self._test_toml_processing("-mm")

        times = [(filename, filename.stat().st_mtime) for filename, _ in self.files]

        self._test_toml_processing("-mm")
        self.assertTrue(all(p.stat().st_mtime == m for p, m in times))


if __name__ == "__main__":
    unittest.main()
