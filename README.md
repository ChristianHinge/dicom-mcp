# dicom-mcp: A DICOM Model Context Protocol Server
[![smithery badge](https://smithery.ai/badge/@ChristianHinge/dicom-mcp)](https://smithery.ai/server/@ChristianHinge/dicom-mcp)

This repo is part of a blog post: [Agentic Healthcare LLMs](https://www.christianhinge.com/projects/dicom-mcp/)

## Overview

A Model Context Protocol server for DICOM (Digital Imaging and Communications in Medicine) interactions. This server provides tools to query and interact with DICOM servers, enabling Large Language Models to access and analyze medical imaging metadata.

dicom-mcp allows AI assistants to query patient information, studies, series, and instances from DICOM servers using standard DICOM networking protocols. It also supports extracting text from encapsulated PDF documents stored in DICOM format, making it possible to analyze clinical reports. It's built on pynetdicom and follows the Model Context Protocol specification.

### Tools

1. `list_dicom_nodes`
   - Lists all configured DICOM nodes and calling AE titles
   - Inputs: None
   - Returns: Current node, available nodes, current calling AE title, and available calling AE titles

2. `switch_dicom_node`
   - Switches to a different configured DICOM node
   - Inputs:
     - `node_name` (string): Name of the node to switch to
   - Returns: Success message

3. `switch_calling_aet`
   - Switches to a different configured calling AE title
   - Inputs:
     - `aet_name` (string): Name of the calling AE title to switch to
   - Returns: Success message

4. `verify_connection`
   - Tests connectivity to the configured DICOM node using C-ECHO
   - Inputs: None
   - Returns: Success or failure message with details

5. `query_patients`
   - Search for patients matching specified criteria
   - Inputs:
     - `name_pattern` (string, optional): Patient name pattern (can include wildcards)
     - `patient_id` (string, optional): Patient ID
     - `birth_date` (string, optional): Patient birth date (YYYYMMDD)
     - `attribute_preset` (string, optional): Preset level of detail (minimal, standard, extended)
     - `additional_attributes` (string[], optional): Additional DICOM attributes to include
     - `exclude_attributes` (string[], optional): DICOM attributes to exclude
   - Returns: Array of matching patient records

6. `query_studies`
   - Search for studies matching specified criteria
   - Inputs:
     - `patient_id` (string, optional): Patient ID
     - `study_date` (string, optional): Study date or range (YYYYMMDD or YYYYMMDD-YYYYMMDD)
     - `modality_in_study` (string, optional): Modalities in study
     - `study_description` (string, optional): Study description (can include wildcards)
     - `accession_number` (string, optional): Accession number
     - `study_instance_uid` (string, optional): Study Instance UID
     - `attribute_preset` (string, optional): Preset level of detail
     - `additional_attributes` (string[], optional): Additional DICOM attributes to include
     - `exclude_attributes` (string[], optional): DICOM attributes to exclude
   - Returns: Array of matching study records

7. `query_series`
   - Search for series within a study
   - Inputs:
     - `study_instance_uid` (string): Study Instance UID (required)
     - `modality` (string, optional): Modality (e.g., "CT", "MR")
     - `series_number` (string, optional): Series number
     - `series_description` (string, optional): Series description
     - `series_instance_uid` (string, optional): Series Instance UID
     - `attribute_preset` (string, optional): Preset level of detail
     - `additional_attributes` (string[], optional): Additional DICOM attributes to include
     - `exclude_attributes` (string[], optional): DICOM attributes to exclude
   - Returns: Array of matching series records

8. `query_instances`
   - Search for instances within a series
   - Inputs:
     - `series_instance_uid` (string): Series Instance UID (required)
     - `instance_number` (string, optional): Instance number
     - `sop_instance_uid` (string, optional): SOP Instance UID
     - `attribute_preset` (string, optional): Preset level of detail
     - `additional_attributes` (string[], optional): Additional DICOM attributes to include
     - `exclude_attributes` (string[], optional): DICOM attributes to exclude
   - Returns: Array of matching instance records

9. `get_attribute_presets`
   - Lists available attribute presets for queries
   - Inputs: None
   - Returns: Dictionary of available presets and their attributes by level

10. `retrieve_instance`
    - Retrieves a specific DICOM instance and saves it to the local filesystem
    - Inputs:
      - `study_instance_uid` (string): Study Instance UID
      - `series_instance_uid` (string): Series Instance UID
      - `sop_instance_uid` (string): SOP Instance UID
      - `output_directory` (string, optional): Directory to save the retrieved instance to (default: "./retrieved_files")
    - Returns: Dictionary with information about the retrieval operation

11. `extract_pdf_text_from_dicom`
    - Retrieves a DICOM instance containing an encapsulated PDF and extracts its text content
    - Inputs:
      - `study_instance_uid` (string): Study Instance UID
      - `series_instance_uid` (string): Series Instance UID
      - `sop_instance_uid` (string): SOP Instance UID
    - Returns: Dictionary with extracted text information and status
    
## Installation

### Installing via Smithery

To install DICOM Model Context Protocol Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@ChristianHinge/dicom-mcp):

```bash
npx -y @smithery/cli install @ChristianHinge/dicom-mcp --client claude
```

### Prerequisites

- Python 3.12 or higher
- A DICOM server to connect to (e.g., Orthanc, dcm4chee, etc.)

### Using pip

Install via pip:

```bash
pip install dicom-mcp
```

## Configuration

dicom-mcp requires a YAML configuration file that defines the DICOM nodes and calling AE titles. Create a configuration file with the following structure:

```yaml
# DICOM nodes configuration
nodes:
  orthanc:
    host: "localhost"
    port: 4242
    ae_title: "ORTHANC"
    description: "Local Orthanc DICOM server"
  
  clinical:
    host: "pacs.hospital.org"
    port: 11112
    ae_title: "CLIN_PACS"
    description: "Clinical PACS server"

# Local calling AE titles
calling_aets:
  default:
    ae_title: "MCPSCU"
    description: "Default calling AE title"
  
  modality:
    ae_title: "MODALITY"
    description: "Simulating a modality"

# Currently selected node
current_node: "orthanc"

# Currently selected calling AE title
current_calling_aet: "default"
```

## Usage

### Command Line

Run the server using the script entry point:

```bash
dicom-mcp /path/to/configuration.yaml
```

If using uv:

```bash
uv run dicom-mcp /path/to/configuration.yaml
```

### Configuration with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
"mcpServers": {
  "dicom": {
    "command": "uv",
    "args": ["--directory", "/path/to/dicom-mcp", "run", "dicom-mcp", "/path/to/configuration.yaml"]
  }
}
```

### Usage with Zed

Add to your Zed settings.json:

```json
"context_servers": [
  "dicom-mcp": {
    "command": {
      "path": "uv",
      "args": ["--directory", "/path/to/dicom-mcp", "run", "dicom-mcp", "/path/to/configuration.yaml"]
    }
  }
],
```

## Example Queries

### List available DICOM nodes

```python
list_dicom_nodes()
```

### Switch to a different node

```python
switch_dicom_node(node_name="clinical")
```

### Switch to a different calling AE title

```python
switch_calling_aet(aet_name="modality")
```

### Verify connection

```python
verify_connection()
```

### Search for patients

```python
# Search by name pattern (using wildcard)
patients = query_patients(name_pattern="SMITH*")

# Search by patient ID
patients = query_patients(patient_id="12345678")

# Get detailed information
patients = query_patients(patient_id="12345678", attribute_preset="extended")
```

### Search for studies

```python
# Find all studies for a patient
studies = query_studies(patient_id="12345678")

# Find studies within a date range
studies = query_studies(study_date="20230101-20231231")

# Find studies by modality
studies = query_studies(modality_in_study="CT")
```

### Search for series in a study

```python
# Find all series in a study
series = query_series(study_instance_uid="1.2.840.10008.5.1.4.1.1.2.1.1")

# Find series by modality and description
series = query_series(
    study_instance_uid="1.2.840.10008.5.1.4.1.1.2.1.1",
    modality="CT",
    series_description="CHEST*"
)
```

### Search for instances in a series

```python
# Find all instances in a series
instances = query_instances(series_instance_uid="1.2.840.10008.5.1.4.1.1.2.1.2")

# Find a specific instance by number
instances = query_instances(
    series_instance_uid="1.2.840.10008.5.1.4.1.1.2.1.2",
    instance_number="1"
)
```

### Retrieve a DICOM instance

```python
# Retrieve a specific instance
result = retrieve_instance(
    study_instance_uid="1.2.840.10008.5.1.4.1.1.2.1.1",
    series_instance_uid="1.2.840.10008.5.1.4.1.1.2.1.2",
    sop_instance_uid="1.2.840.10008.5.1.4.1.1.2.1.3",
    output_directory="./dicom_files"
)
```

### Extract text from a DICOM encapsulated PDF

```python
# Extract text from an encapsulated PDF
result = extract_pdf_text_from_dicom(
    study_instance_uid="1.2.840.10008.5.1.4.1.1.104.1.1",
    series_instance_uid="1.2.840.10008.5.1.4.1.1.104.1.2",
    sop_instance_uid="1.2.840.10008.5.1.4.1.1.104.1.3"
)
```


## Debugging

You can use the MCP inspector to debug the server:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/dicom-mcp run dicom-mcp /path/to/configuration.yaml
```

## Development

### Setup Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/dicom-mcp.git
   cd dicom-mcp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

### Running Tests

The tests require a running Orthanc server. You can start one using Docker:

```bash
cd tests
docker-compose up -d
```

Then run the tests:

```bash
pytest tests/test_dicom_mcp.py
```

To test PDF extraction functionality:

```bash
pytest tests/test_dicom_pdf.py
```

### Project Structure

- `src/dicom_mcp/`: Main package
  - `__init__.py`: Package initialization
  - `__main__.py`: Entry point
  - `server.py`: MCP server implementation
  - `dicom_client.py`: DICOM client implementation
  - `attributes.py`: DICOM attribute presets
  - `config.py`: Configuration management with Pydantic

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on [pynetdicom](https://github.com/pydicom/pynetdicom)
- Follows the [Model Context Protocol](https://modelcontextprotocol.io) specification
- Uses [PyPDF2](https://pythonhosted.org/PyPDF2/) for PDF text extraction
