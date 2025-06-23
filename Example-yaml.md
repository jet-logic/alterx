### Example Scenario: Kubernetes Manifest Updates

We'll process Kubernetes YAML files to:

1. Update image tags
2. Add standard labels
3. Ensure resource limits exist

---

### 1. Create Sample YAML Files

```bash
mkdir -p k8s
cat > k8s/deployment.yaml <<EOF
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
EOF

cat > k8s/service.yaml <<EOF
apiVersion: v1
kind: Service
metadata:
  name: webapp
spec:
  ports:
  - port: 80
EOF
```

### 2. Create Processing Script (`k8s_updater.py`)

```python
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
    modified = False

    # Add standard labels
    if 'metadata' in doc and 'labels' not in doc['metadata']:
        doc['metadata']['labels'] = {
            'app.kubernetes.io/env': app.defs['ENVIRONMENT'],
            'app.kubernetes.io/managed-by': 'alterx'
        }
        modified = True

    # Update container images
    if doc.get('kind') == 'Deployment':
        for container in doc['spec']['template']['spec'].get('containers', []):
            if container['name'] == 'web':
                if not container['image'].endswith(app.defs['IMAGE_TAG']):
                    container['image'] = container['image'].rsplit(':', 1)[0] + ':' + app.defs['IMAGE_TAG']
                    modified = True

                # Add resource limits if missing
                if 'resources' not in container:
                    container['resources'] = {'limits': app.defs['RESOURCE_LIMITS']}
                    modified = True

    return modified

def end(app):
    print(f"Processed {app.total.Files} Kubernetes manifests")
    print(f"Updated {app.total.Altered} files")
```

### 3. Run the Processor

```bash
# Dry run first
python -m alterx.yaml --dry-run -m -x k8s_updater.py k8s/*.yaml

# Actual run (make changes)
python -m alterx.yaml -m -x k8s_updater.py k8s/*.yaml
```

### 4. Expected Output Files

**deployment.yaml**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  labels:
    app.kubernetes.io/env: production
    app.kubernetes.io/managed-by: alterx
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: web
          image: myrepo/webapp:1.3.0
          resources:
            limits:
              cpu: 500m
              memory: 512Mi
```

**service.yaml** (only labels added):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp
  labels:
    app.kubernetes.io/env: production
    app.kubernetes.io/managed-by: alterx
spec:
  ports:
    - port: 80
```

---

### Test Case

```python
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
            "deployment.yaml": """
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
            "service.yaml": """
                apiVersion: v1
                kind: Service
                metadata:
                  name: test-app
                """
        }

        for name, content in self.manifests.items():
            (self.test_dir / name).write_text(content.strip())

        # Create processor script
        self.script = self.test_dir / "k8s_updater.py"
        self.script.write_text("""
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
                    modified = True

                # Update image tags
                if doc.get('kind') == 'Deployment':
                    for container in doc['spec']['template']['spec'].get('containers', []):
                        if not container['image'].endswith(app.defs['IMAGE_TAG']):
                            container['image'] = container['image'].rsplit(':', 1)[0] + ':' + app.defs['IMAGE_TAG']
                            modified = True

                return modified
            """)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_yaml_processing(self):
        # Run processor
        app = AlterYAML()
        app.main([
            "-m",
            "-x", str(self.script),
            str(self.test_dir / "*.yaml")
        ])

        # Verify changes
        deployment = yaml.safe_load((self.test_dir / "deployment.yaml").read_text())
        service = yaml.safe_load((self.test_dir / "service.yaml").read_text())

        # Check labels
        self.assertEqual(deployment['metadata']['labels']['env'], 'staging')
        self.assertEqual(service['metadata']['labels']['env'], 'staging')

        # Check image tag
        self.assertTrue(deployment['spec']['template']['spec']['containers'][0]['image'].endswith(':2.0.0'))

        # Verify unchanged parts remain
        self.assertEqual(deployment['metadata']['name'], 'test-app')
        self.assertEqual(service['spec'], None)

    def test_idempotency(self):
        # First run should modify both files
        app = AlterYAML()
        app.main(["-m", "-x", str(self.script), str(self.test_dir / "*.yaml")])
        self.assertEqual(app.total.Altered, 2)

        # Second run should modify nothing
        app = AlterYAML()
        app.main(["-m", "-x", str(self.script), str(self.test_dir / "*.yaml")])
        self.assertEqual(app.total.Altered, 0)

if __name__ == "__main__":
    unittest.main()
```

### Key Features Demonstrated:

1. **YAML Structure Navigation**: Safely traverses nested Kubernetes manifests
2. **Conditional Modifications**: Only updates what's needed
3. **Multi-File Patterns**: Processes all matching YAML files
4. **Configuration Sharing**: Uses `app.defs` for shared parameters
5. **Change Detection**: Only modifies files that need updates

This example shows how to use `alterx` for maintaining Kubernetes manifests, but the same approach works for any YAML configuration files (Ansible, Docker Compose, CI/CD pipelines, etc.). The test case verifies both the transformation logic and the tool's change detection capabilities.
