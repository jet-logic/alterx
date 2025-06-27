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
  name: webapp
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: web
        image: myrepo/webapp:1.2.3
""",
            "service.yaml": r"""
apiVersion: v1
kind: Service
metadata:
  name: webapp
spec:
  ports:
  - port: 80
""",
        }

        for name, content in self.manifests.items():
            (self.test_dir / name).write_text(content.strip())

        # Create processor script
        self.script = self.test_dir / "k8s_updater.py"
        self.script.write_text(
            r"""
def init(app):
    # Configuration parameters
    app.defs.update({
        'ENVIRONMENT': 'production',
        'IMAGE_TAG': '1.3.0',
        'RESOURCE_LIMITS': {
            'cpu': '500m',
            'memory': '512Mi'
        }
    })

def process(doc, stat, app):

    # Add standard labels
    if 'metadata' in doc and 'labels' not in doc['metadata']:
        doc['metadata']['labels'] = {
            'app.kubernetes.io/env': app.defs['ENVIRONMENT'],
            'app.kubernetes.io/managed-by': 'alterx'
        }

    # Update container images
    if doc.get('kind') == 'Deployment':
        for container in doc['spec']['template']['spec'].get('containers', []):
            if container['name'] == 'web':
                if not container['image'].endswith(app.defs['IMAGE_TAG']):
                    container['image'] = container['image'].rsplit(':', 1)[0] + ':' + app.defs['IMAGE_TAG']

                # Add resource limits if missing
                if 'resources' not in container:
                    container['resources'] = {'limits': app.defs['RESOURCE_LIMITS']}


def end(app):
    print(f"Processed {app.total.Files} Kubernetes manifests")
    print(f"Updated {app.total.Altered} files")
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
        # self.assertEqual(deployment["metadata"]["labels"]["env"], "staging")
        # self.assertEqual(service["metadata"]["labels"]["env"], "staging")

        # Check image tag
        # self.assertTrue(deployment["spec"]["template"]["spec"]["containers"][0]["image"].endswith(":2.0.0"))

        # Verify unchanged parts remain
        # self.assertEqual(deployment["metadata"]["name"], "test-app")
        # self.assertEqual(service.get("spec"), None)

        self.assertDictEqual(
            service,
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "webapp",
                    "labels": {"app.kubernetes.io/env": "production", "app.kubernetes.io/managed-by": "alterx"},
                },
                "spec": {"ports": [{"port": 80}]},
            },
        )
        self.assertDictEqual(
            deployment,
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": "webapp",
                    "labels": {"app.kubernetes.io/env": "production", "app.kubernetes.io/managed-by": "alterx"},
                },
                "spec": {
                    "replicas": 3,
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": "web",
                                    "image": "myrepo/webapp:1.3.0",
                                    "resources": {"limits": {"cpu": "500m", "memory": "512Mi"}},
                                }
                            ]
                        }
                    },
                },
            },
        )

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
