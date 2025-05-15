from shutil import rmtree
import unittest
import tempfile
import subprocess
from pathlib import Path


class Test1(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory with test files
        self.test_dir = Path(tempfile.mkdtemp())
        xml_samples = [
            ("test1.xml", "<data><id>1</id><value>X7f3n</value></data>"),
            ("test2.xml", "<items><a>q92L</a><b>k5TpP</b><c>true</c></items>"),
            ("test3.xml", '<root><x id="1">A1B</x><y id="2">C3D</y></root>'),
            (
                "test4.xml",
                "<test><name>sample</name><count>42</count><valid>yes</valid></test>",
            ),
            (
                "test5.xml",
                "<config><setting>on</setting><timeout>30</timeout></config>",
            ),
        ]
        for filename, content in xml_samples:
            self.test_dir.joinpath(filename).write_text(content)

    def tearDown(self):
        for item in self.test_dir.glob("*"):
            item.unlink()
        # d = self.test_dir.joinpath(    '__pycache__')

        rmtree(self.test_dir)
        pass

    def exec(self, args):
        print("RUN", args)
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            # check=True,
            # stderr=subprocess.STDOUT,
            # stdin=subprocess.PIPE,
            # stdout=subprocess.PIPE,
            # stderr=subprocess.STDOUT,  # Merge stderr into stdout
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
def process(doc, stat, app):
    print(f"DATA {stat.path}")
def end(app):
    print(f"END {app.defs['quiet']}")
        """.strip()
        )
        output = self.exec(
            f"python -B -m alterx.xml -d VAR=foo -d quiet -x {ext1} {self.test_dir}".split()
        )
        self.assertRegex(output, r"^INIT\s+")
        self.assertRegex(output, r"\s+START\sfoo\s+")
        self.assertRegex(output, r"\s+END\sTrue\s+")
        for i in range(5):
            self.assertRegex(output, rf"\s+DATA\s+[^\n]+\Wtest{i+1}\.xml\n")


if __name__ == "__main__":
    unittest.main()
