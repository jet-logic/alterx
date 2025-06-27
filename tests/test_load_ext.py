import unittest
import tempfile
import sys
import hashlib
from pathlib import Path
from importlib import reload
from alterx.app import load_extension, load_stdin_as_module
from unittest.mock import patch, mock_open


class TestLoadExtension(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test modules
        self.test_dir = Path(tempfile.mkdtemp())

        # Create a valid test extension
        self.valid_ext = self.test_dir / "valid_ext.py"
        self.valid_ext.write_text(
            """
def init(app):
    app.defs['TEST'] = 'success'
            
def process(doc, stat, app):
    return True
"""
        )

        # Create an invalid test extension
        self.invalid_ext = self.test_dir / "invalid_ext.py"
        self.invalid_ext.write_text(
            """
1 / 0  # Will raise ZeroDivisionError when loaded
"""
        )

    def tearDown(self):
        # Clean up sys.modules
        for modname in list(sys.modules):
            if modname.startswith("ext_"):
                del sys.modules[modname]

        # Remove temp directory
        import shutil

        shutil.rmtree(self.test_dir)

    def test_load_valid_extension(self):
        """Test loading a valid extension file"""
        module = load_extension(str(self.valid_ext))

        # Verify module was loaded correctly
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, "init"))
        self.assertTrue(hasattr(module, "process"))

        # Verify module name follows expected pattern
        self.assertTrue(module.__name__.startswith("ext_"))

        # Verify the same module is returned on subsequent loads
        module2 = load_extension(str(self.valid_ext))
        self.assertEqual(module.__name__, module2.__name__)

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file"""
        with self.assertRaises(FileNotFoundError):
            load_extension(str(self.test_dir / "nonexistent.py"))

    def test_load_invalid_extension(self):
        """Test loading an invalid extension file"""
        with self.assertRaises(ImportError):
            load_extension(str(self.invalid_ext))

    def test_load_extension_with_special_chars(self):
        """Test loading a file with special characters in path"""
        special_path = self.test_dir / "test@ext.py"
        special_path.write_text("def init(app): pass")

        module = load_extension(str(special_path))
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, "init"))

    def test_load_stdin_extension(self):
        """Test loading an extension from stdin"""
        test_code = """
def init(app):
    app.defs['FROM_STDIN'] = True
"""

        with patch("sys.stdin.read", return_value=test_code):
            module = load_stdin_as_module()

            self.assertIsNotNone(module)
            self.assertTrue(hasattr(module, "init"))

            # Verify module name follows expected pattern
            self.assertTrue(module.__name__.startswith("stdin_module_"))

    def test_load_empty_stdin(self):
        """Test loading empty stdin"""
        with patch("sys.stdin.read", return_value=""):
            with self.assertRaises(ValueError):
                load_stdin_as_module()

    # def test_module_name_generation(self):
    #     """Test module name generation from path"""
    #     test_path = "/path/to/test_extension.py"
    #     module_name = load_extension.generate_module_name(test_path)

    #     # Should start with ext_
    #     self.assertTrue(module_name.startswith("ext_"))

    #     # Should include hash of path
    #     path_hash = hashlib.md5(Path(test_path).absolute().__str__().encode()).hexdigest()[:8]
    #     self.assertIn(path_hash, module_name)

    # def test_import_module_directly(self):
    #     """Test loading a module using import syntax"""
    #     # Create a package-like structure
    #     pkg_dir = self.test_dir / "testpkg"
    #     pkg_dir.mkdir()
    #     (pkg_dir / "__init__.py").touch()
    #     ext_file = pkg_dir / "module.py"
    #     ext_file.write_text("def init(app): app.defs['PKG'] = True")

    #     # Add to Python path
    #     import sys

    #     sys.path.append(str(self.test_dir))

    #     try:
    #         module = load_extension("testpkg.module")
    #         self.assertIsNotNone(module)
    #         self.assertTrue(hasattr(module, "init"))
    #     finally:
    #         sys.path.remove(str(self.test_dir))

    def test_reload_protection(self):
        """Test that modules aren't reloaded unnecessarily"""
        module1 = load_extension(str(self.valid_ext))
        module_id1 = id(module1)

        # Simulate file modification by changing content
        self.valid_ext.write_text("def init(app): pass")

        module2 = load_extension(str(self.valid_ext))
        module_id2 = id(module2)

        # Should return same module object despite content change
        self.assertEqual(module_id1, module_id2)

    def test_error_cleanup(self):
        """Test that failed imports are cleaned up from sys.modules"""
        initial_modules = set(sys.modules.keys())

        with self.assertRaises(ImportError):
            load_extension(str(self.invalid_ext))

        # Check no leftover modules
        new_modules = set(sys.modules.keys()) - initial_modules
        ext_modules = [m for m in new_modules if m.startswith("ext_")]
        self.assertEqual(len(ext_modules), 0)

    def test_load_extension_with_syntax_error(self):
        """Test that loading a script with invalid syntax raises ImportError with proper message"""
        # Create a temporary Python file with invalid syntax
        invalid_syntax_file = self.test_dir / "syntax_error.py"
        invalid_syntax_file.write_text(
            """
    def init(app):
        app.defs['TEST'] = 'success'
        
    # Missing colon and indentation - invalid syntax
    def process(doc, stat app)
        return True
    """
        )

        with self.assertRaises(ImportError) as cm:
            load_extension(str(invalid_syntax_file))

        # Verify the error message contains useful information
        self.assertIn("Error loading extension", str(cm.exception))
        self.assertIn("syntax_error.py", str(cm.exception))
        # self.assertIn("invalid syntax", str(cm.exception).lower())

        # Verify the bad module was cleaned from sys.modules
        module_name = f"ext_{hashlib.md5(str(invalid_syntax_file.absolute()).encode()).hexdigest()[:8]}"
        self.assertNotIn(module_name, sys.modules)


if __name__ == "__main__":
    unittest.main()
