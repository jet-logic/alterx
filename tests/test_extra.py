import unittest
import tempfile
import subprocess
from shutil import rmtree
from pathlib import Path

from alterx.app import Counter, load_stdin_as_module


class Test1(unittest.TestCase):

    def new_temp_dir(self):
        d = Path(tempfile.mkdtemp())
        return d

    def setUp(self):
        # Create a temporary directory with test files
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        rmtree(self.test_dir)

    @unittest.skip
    def test_1(self):
        import xml.etree.ElementTree as etree

        kwargs = {}

        parser = etree.XMLParser(**kwargs)
        snk = self.test_dir / "snk.xml"
        src = self.test_dir / "src.xml"
        src.write_text('<?xml version="1.0" encoding="utf-8" standalone="no"?><config>1</config>')

        t = etree.parse(str(src), parser)

        kwargs = {"method": "xml"}
        with snk.open("wb") as h:
            t.write(h, **kwargs)
        print(etree.tostring(t.getroot()))

        self.assertEqual(
            snk.read_text(),
            '<?xml version="1.0" encoding="utf-8" standalone="no"?><config>1</config>',
        )

    @unittest.skip
    def test_lxml(self):
        from lxml import etree

        kwargs = {}

        parser = etree.XMLParser(**kwargs)
        snk = self.test_dir / "snk.xml"
        src = self.test_dir / "src.xml"
        src.write_text('<?xml version="1.1" encoding="us-ascii" standalone="no"?><config>1</config>')

        t = etree.parse(str(src), parser)
        self.assertFalse(t.docinfo.standalone)
        self.assertEqual(t.docinfo.encoding, "us-ascii")
        self.assertEqual(t.docinfo.xml_version, "1.1")
        # for x in t:
        #     print(x)
        kwargs = {"method": "xml"}
        with snk.open("wb") as h:
            t.write(h, **kwargs)

        self.assertEqual(
            snk.read_text(),
            '<?xml version="1.0" encoding="utf-8" standalone="no"?><config>1</config>',
        )


class Test2(unittest.TestCase):

    def exec(self, args):
        print("RUN", args)
        subprocess.run(args)

    @unittest.skip
    def test_git(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            print(f"Temporary directory created at: {temp_dir}")
            self.exec(f"git init {temp_dir}".split())
            self.exec(f"git init {temp_dir}".split())


class Test3(unittest.TestCase):

    def test_counter(self):
        total = Counter()
        total.lost = 4
        total["lives"] = 2
        self.assertEqual(total.win, 0)
        self.assertEqual(total["lost"], 4)
        self.assertIn("win", total)
        self.assertSetEqual(set(total), {"win", "lost", "lives"})
        self.assertDictEqual(dict(x.split() for x in str(total).split(";") if x), {"win": "0", "lost": "4", "lives": "2"})


if __name__ == "__main__":
    unittest.main()
# s = '<?xml version="1.0" encoding="utf-8" standalone="yes"?><config><setting>on</setting><timeout>30</timeout></config>'
