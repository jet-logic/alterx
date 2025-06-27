import unittest
import tempfile
import subprocess
from shutil import rmtree
from pathlib import Path


class Test1(unittest.TestCase):
    which = "alterx.xml"

    def _get_file_stats(self, f: Path):
        assert f.exists()
        stats = f.stat()
        return {
            "size": stats.st_size,
            "mtime": stats.st_mtime,
            "ctime": stats.st_ctime,
            "path": f,
        }

    def setUp(self):
        # Create a temporary directory with test files
        self.test_dir = Path(tempfile.mkdtemp())
        xml_samples = [
            ("test1.xml", "<data><id>1</id><value>X7f3n</value></data>", {}),
            ("test2.xml", "<items><a>q92L</a><b>k5TpP</b><c>true</c></items>", {}),
            ("test3.xml", '<root><x id="1">A1B</x><y id="2">C3D</y></root>', {}),
            (
                "test4.xml",
                "<test><name>sample</name><count>42</count><valid>yes</valid></test>",
                {},
            ),
            (
                "test5.xml",
                '<?xml version="1.0" encoding="utf-8" standalone="yes"?><config><setting>on</setting><timeout>30</timeout></config>',
                {},
            ),
        ]
        for filename, content, stat in xml_samples:
            f = self.test_dir.joinpath(filename)
            f.write_text(content)
            stat.update(self._get_file_stats(f))
        self.xml_samples = xml_samples
        self.test_dir.joinpath("dummy.txt").write_text(f"dummy/")

    def tearDown(self):
        for item in self.test_dir.glob("*"):
            item.unlink()
        rmtree(self.test_dir)
        pass

    def exec(self, args):
        print("RUN", args)
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        o = result.stdout + result.stderr
        print(o)
        return o

    def test_1(self):
        ext1 = self.test_dir.joinpath("ext1.py")
        ext1.write_text(
            r"""
def init(app):
    print("INIT")
def start(app):
    print(f"START {app.defs['VAR']}")
def process(doc, file_info, app):
    print(f"DATA {file_info.path}")
def end(app):
    print(f"END {app.defs['quiet']}")
        """.strip()
        )
        output = self.exec(f"python -B -m {self.which} -d VAR=foo -d quiet -x {ext1} {self.test_dir}".split())
        self.assertRegex(output, r"^INIT\s+")
        self.assertRegex(output, r"\s+START\sfoo\s+")
        self.assertRegex(output, r"\s+END\sTrue\s+")
        for i in range(5):
            self.assertRegex(output, rf"\s+DATA\s+[^\n]+\Wtest{i+1}\.xml\n")
        for filename, content, etc in self.xml_samples:
            st = self._get_file_stats(etc["path"])
            self.assertEqual(st, etc)

    # @unittest.skip
    def test_hash_modification(self):
        ext1 = self.test_dir.joinpath("ext1.py")
        ext1.write_text(
            r"""
def process(doc, file_info, app):
    for x in doc.iter('setting'):
        x.text = 'off'
        """.strip()
        )
        output = self.exec(f"python -B -m {self.which} -mm -x {ext1} {self.test_dir}".split())
        for filename, content, etc in self.xml_samples:
            st = self._get_file_stats(etc["path"])
            if "test5.xml" == st["path"].name:
                self.assertNotEqual(st, etc)
                self.assertEqual(
                    st["path"].read_text(),
                    "<config><setting>off</setting><timeout>30</timeout></config>",
                )

            else:
                self.assertEqual(st, etc)

    # @unittest.skip
    def test_output_to_stdout_or_file(self):
        ext1 = self.test_dir.joinpath("ext1.py")
        ext1.write_text(
            r"""
def process(doc, file_info, app):
    for x in doc.iter('x'):
        x.set("id", str(int(x.get("id"))+4) )
        """.strip()
        )
        output = self.exec(f"python -B -m {self.which} -mm -o - -x {ext1} {self.test_dir/'test3.xml'}".split())
        self.assertIn('<root><x id="5">A1B</x><y id="2">C3D</y></root>', output)

        ext2 = self.test_dir.joinpath("ext2.py")
        ext2.write_text(
            r"""
def process(doc, file_info, app):
    for x in doc.iter():
        x.text = "@"
        """.strip()
        )
        output = self.exec(
            f"python -B -m {self.which} -mm -o {self.test_dir/'test6.xml'} -x {ext2} {self.test_dir/'test1.xml'}".split()
        )

        for filename, content, etc in self.xml_samples:
            st = self._get_file_stats(etc["path"])
            self.assertEqual(st, etc)
        self.assertEqual(
            "<data>@<id>@</id><value>@</value></data>",
            (self.test_dir / "test6.xml").read_text(),
        )

    # @unittest.skip
    def test_extension_modification(self):
        ext1 = self.test_dir.joinpath("ext1.py")
        ext1.write_text(
            r"""
def process(doc, file_info, app):
    for x in doc.iter('name'):
        x.text = '@'
        return True
    for x in doc.iter('c'):
        x.text = 'true'
        return True
        """.strip()
        )
        output = self.exec(f"python -B -m {self.which} -m -x {ext1} {self.test_dir}".split())
        for filename, content, etc in self.xml_samples:
            st = self._get_file_stats(etc["path"])
            if st["path"].name in ("test2.xml", "test4.xml"):
                self.assertNotEqual(st, etc)
            else:
                self.assertEqual(st, etc)

    # @unittest.skip
    def test_extension_from_stdin(self):
        script = self.test_dir.joinpath("run.sh")
        script.write_text(
            rf"""
python -B -m {self.which} -m -x - {self.test_dir} << 'EOF'
def process(doc, file_info, app):
    for x in doc.iter('name'):
        x.text = '@'
        return True
EOF
        """.strip()
        )
        print(script.read_text())
        self.exec(f"sh {script}".split())
        for filename, content, etc in self.xml_samples:
            st = self._get_file_stats(etc["path"])
            if st["path"].name in ("test4.xml",):
                self.assertNotEqual(st, etc)
            else:
                self.assertEqual(st, etc)


class Test2(Test1):
    which = "alterx.xml.etree"


if __name__ == "__main__":
    unittest.main()
