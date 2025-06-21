import unittest
import tempfile
import yaml
from pathlib import Path
from alterx.yaml import AlterYAML


class TestK8sYAMLProcessing(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        # Create test files
        self.manifests = {
            "deployment.yaml": r"""
apiVersion: apps/v1
kind: Deployment
metadata:
    name: test-app
spec:
    template:
        spec:
            containers:
            - name: app
              image: test/app:1.0.0
""",
            "service.yaml": r"""
apiVersion: v1
kind: Service
metadata:
    name: test-app
""",
        }

        for name, content in self.manifests.items():
            (self.test_dir / name).write_text(content.strip())

        # Create processor script
        self.script = self.test_dir / "k8s_updater.py"
        self.script.write_text(
            """
def init(app):
    app.defs.update({
        'ENVIRONMENT': 'staging',
        'IMAGE_TAG': '2.0.0'
    })

def process(doc, stat, app):
    modified = False
    
    # Add labels
    if 'metadata' in doc:
        doc['metadata']['labels'] = {
            'env': app.defs['ENVIRONMENT'],
            'processed': 'true'
        }
        # modified = True
    
    # Update image tags
    if doc.get('kind') == 'Deployment':
        for container in doc['spec']['template']['spec'].get('containers', []):
            if not container['image'].endswith(app.defs['IMAGE_TAG']):
                container['image'] = container['image'].rsplit(':', 1)[0] + ':' + app.defs['IMAGE_TAG']
                # modified = True
    
    return modified
            """
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir)

    def test_yaml_processing(self):
        # Run processor
        app = AlterYAML()
        app.main(["-mm", "-x", str(self.script), str(self.test_dir)])

        # Verify changes
        deployment = yaml.safe_load((self.test_dir / "deployment.yaml").read_text())
        service = yaml.safe_load((self.test_dir / "service.yaml").read_text())

        # Check labels
        self.assertEqual(deployment["metadata"]["labels"]["env"], "staging")
        self.assertEqual(service["metadata"]["labels"]["env"], "staging")

        # Check image tag
        self.assertTrue(deployment["spec"]["template"]["spec"]["containers"][0]["image"].endswith(":2.0.0"))

        # Verify unchanged parts remain
        self.assertEqual(deployment["metadata"]["name"], "test-app")
        self.assertEqual(service.get("spec"), None)

    def test_idempotency(self):
        # First run should modify both files
        app = AlterYAML()
        app.main(["-mm", "-x", str(self.script), str(self.test_dir)])
        self.assertEqual(app.total.Altered, 2)

        # Second run should modify nothing
        app = AlterYAML()
        app.main(["-mm", "-x", str(self.script), str(self.test_dir)])
        self.assertEqual(app.total.Altered, 0)


if __name__ == "__main__":
    unittest.main()
