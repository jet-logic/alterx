### Overview

AlterX is a modular file processing framework that supports multiple formats:

- XML/HTML (via lxml or built-in ElementTree)
- JSON
- YAML
- TOML

### Key Features

1. **File Processing Capabilities**:

   - Batch processing of files with glob patterns
   - Modification detection via hashing
   - Dry-run mode for testing changes
   - Supports both in-place modification and output to different files

2. **Extension System**:

   - Loadable Python modules/scripts to customize processing
   - Lifecycle hooks (init, start, process, end)
   - Can load extensions from files or stdin

3. **Core Components**:

   - `App` class - Base application framework
   - `FindSkel` - File traversal and filtering system
   - Format-specific subclasses (AlterXML, AlterJSON, etc.)
   - Command-line argument parsing via `Main` base class

4. **Advanced Features**:
   - File glob filtering (include/exclude patterns)
   - Size and depth filters
   - Variable definitions
   - Encoding handling
   - XML-specific features like pretty printing, namespace cleaning

### Example Use Cases

- Batch modification of XML/HTML files
- Transforming configuration files (JSON/YAML/TOML)
- Automated content updates across multiple files
- File validation and reporting
