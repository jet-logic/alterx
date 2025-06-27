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
```

### 3. Run the Processor

```bash
# -m -m means modify if hash change
python -m alterx.yaml -mm -x k8s_updater.py k8s
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

### Key Features Demonstrated:

1. **YAML Structure Navigation**: Safely traverses nested Kubernetes manifests
2. **Conditional Modifications**: Only updates what's needed
3. **Multi-File Patterns**: Processes all matching YAML files
4. **Configuration Sharing**: Uses `app.defs` for shared parameters
5. **Change Detection**: Only modifies files that need updates

This example shows how to use `alterx` for maintaining Kubernetes manifests, but the same approach works for any YAML configuration files (Ansible, Docker Compose, CI/CD pipelines, etc.). The test case verifies both the transformation logic and the tool's change detection capabilities.
