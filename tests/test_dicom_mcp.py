import os
import pytest
import requests
import time
import tempfile
import yaml
from pathlib import Path

from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import Verification

from dicom_mcp.config import DicomConfiguration, load_config
from dicom_mcp.dicom_client import DicomClient

        
# Configuration
ORTHANC_HOST = os.environ.get("ORTHANC_HOST", "localhost")
ORTHANC_PORT = int(os.environ.get("ORTHANC_PORT", "4242"))
ORTHANC_WEB_PORT = int(os.environ.get("ORTHANC_WEB_PORT", "8042"))
ORTHANC_AET = os.environ.get("ORTHANC_AET", "ORTHANC")
ORTHANC_USERNAME = os.environ.get("ORTHANC_USERNAME", "")
ORTHANC_PASSWORD = os.environ.get("ORTHANC_PASSWORD", "")

@pytest.fixture(scope="session")
def dicom_config():
    """Load the test configuration."""
    return load_config("tests/test_dicom_servers.yaml")


@pytest.fixture(scope="session")
def dicom_client(dicom_config):
    """Create a DICOM client from configuration."""
    node = dicom_config.nodes[dicom_config.current_node]
    aet = dicom_config.calling_aet
    
    client = DicomClient(
        host=node.host,
        port=node.port,
        calling_aet=aet,
        called_aet=node.ae_title
    )
    return client


def is_orthanc_ready():
    """Check if Orthanc is running and accessible"""
    try:
        if ORTHANC_USERNAME and ORTHANC_PASSWORD:
            response = requests.get(
                f"http://{ORTHANC_HOST}:{ORTHANC_WEB_PORT}/system",
                auth=(ORTHANC_USERNAME, ORTHANC_PASSWORD),
                timeout=2
            )
        else:
            response = requests.get(
                f"http://{ORTHANC_HOST}:{ORTHANC_WEB_PORT}/system",
                timeout=2
            )
        return response.status_code == 200
    except Exception:
        return False


def wait_for_orthanc(max_attempts=10, delay=2):
    """Wait for Orthanc to be ready"""
    for _ in range(max_attempts):
        if is_orthanc_ready():
            return True
        time.sleep(delay)
    return False


@pytest.fixture(scope="session")
def upload_test_data():
    """Upload a minimal test dataset to Orthanc"""
    # Import here to avoid circular imports
    from pydicom import dcmwrite
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid
    
    # Create a new SOP Instance UID
    sop_instance_uid = "1.2.3.4.5.6.7.8.9.2"
    sop_class_uid = "1.2.840.10008.5.1.4.1.1.1"  # CR Image Storage
    
    # Create the FileMetaDataset
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = sop_class_uid
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    
    # Simple dataset for testing
    ds = Dataset()
    # Set the file_meta attribute
    ds.file_meta = file_meta
    
    # Patient data
    ds.PatientName = "TEST^PATIENT"
    ds.PatientID = "TEST123"
    ds.PatientBirthDate = "19700101"
    ds.PatientSex = "O"
    
    # Study data
    ds.StudyInstanceUID = "1.2.3.4.5.6.7.8.9.0"
    ds.StudyDate = "20230101"
    ds.StudyTime = "120000"
    ds.StudyID = "TEST01"
    ds.StudyDescription = "Test Study"
    ds.AccessionNumber = "ACC123"
    
    # Series data
    ds.SeriesInstanceUID = "1.2.3.4.5.6.7.8.9.1"
    ds.SeriesNumber = 1
    ds.Modality = "CT"
    ds.SeriesDescription = "Test Series"
    
    # Instance data
    ds.SOPInstanceUID = sop_instance_uid
    ds.SOPClassUID = sop_class_uid
    ds.InstanceNumber = 1
    
    # Minimal image data
    ds.Rows = 16
    ds.Columns = 16
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelData = bytes([0] * (16 * 16))
    
    # Save to file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.dcm', delete=False) as temp:
        dcmwrite(temp.name, ds)
        temp_path = temp.name
    
    try:
        # Upload via HTTP
        with open(temp_path, 'rb') as f:
            dicom_data = f.read()
        
        # Try auth if credentials provided
        if ORTHANC_USERNAME and ORTHANC_PASSWORD:
            response = requests.post(
                f"http://{ORTHANC_HOST}:{ORTHANC_WEB_PORT}/instances",
                data=dicom_data,
                auth=(ORTHANC_USERNAME, ORTHANC_PASSWORD),
                headers={'Content-Type': 'application/dicom'}
            )
        else:
            response = requests.post(
                f"http://{ORTHANC_HOST}:{ORTHANC_WEB_PORT}/instances",
                data=dicom_data,
                headers={'Content-Type': 'application/dicom'}
            )
        
        assert response.status_code == 200, f"Failed to upload: {response.text}"
        
    finally:
        # Clean up
        os.unlink(temp_path)


@pytest.fixture(scope="session")
def dicom_echo():
    """Verify DICOM connectivity using C-ECHO"""
    ae = AE(ae_title="TESTCLIENT")
    ae.add_requested_context(Verification)
    
    assoc = ae.associate(ORTHANC_HOST, ORTHANC_PORT, ae_title=ORTHANC_AET)
    assert assoc.is_established, "Failed to establish association with Orthanc"
    
    status = assoc.send_c_echo()
    assoc.release()
    
    assert status and status.Status == 0, "C-ECHO failed"


def test_orthanc_connectivity():
    """Ensure Orthanc is running and ready for tests"""
    assert wait_for_orthanc(), "Orthanc is not available"


def test_dicom_config(dicom_config):
    """Test loading configuration"""
    assert dicom_config is not None
    assert "orthanc" in dicom_config.nodes
    assert dicom_config.current_node == "orthanc"
    
    # Check node details
    node = dicom_config.nodes["orthanc"]
    assert node.host == ORTHANC_HOST
    assert node.port == ORTHANC_PORT
    assert node.ae_title == ORTHANC_AET


def test_dicom_connectivity(dicom_echo):
    """Test DICOM connectivity to Orthanc"""
    # The fixture will fail if connectivity fails
    pass


def test_upload_data(upload_test_data):
    """Test uploading test data to Orthanc"""
    # The fixture will fail if upload fails
    pass


def test_verify_connection(dicom_client):
    """Test verify_connection using the DICOM client directly"""
    success, message = dicom_client.verify_connection()
    
    assert success, f"Connection verification failed: {message}"
    assert "successful" in message.lower() or "success" in message.lower()


def test_query_patients(dicom_client):
    """Test query_patients using the DICOM client directly"""
    result = dicom_client.query_patients()
    
    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0, "No patients found"
    
    # Verify the test patient
    patient_found = False
    for patient in result:
        if patient.get("PatientID") == "TEST123":
            patient_found = True
            break
    assert "ORTHANC" not in str(result)
    assert patient_found, "Test patient not found"

def test_query_studies(dicom_client):
    """Test query_studies using the DICOM client directly"""
    result = dicom_client.query_studies(patient_id="DLBCL2024")
    
    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0, "No studies found"
    
    # Verify the test study
    study_uid = None
    return study_uid


def test_query_series(dicom_client):
    """Test query_series using the DICOM client directly"""
    study_uid = test_query_studies(dicom_client)
    
    result = dicom_client.query_series(study_instance_uid=study_uid)
    
    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0, "No series found"
    
    # Verify the test series
    series_found = False
    series_uid = None
    
    for series in result:
        if series.get("SeriesNumber") == 1:
            series_found = True
            series_uid = series.get("SeriesInstanceUID")
            break
    
    assert series_found, "Test series not found"
    return series_uid


def test_query_instances(dicom_client):
    """Test query_instances using the DICOM client directly"""
    series_uid = test_query_series(dicom_client)
    
    result = dicom_client.query_instance(series_instance_uid=series_uid)
    
    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0, "No instances found"
    
    # Verify the test instance
    instance_found = False
    for instance in result:
        if instance.get("InstanceNumber") == 1:
            instance_found = True
            break
    
    assert instance_found, "Test instance not found"


def test_get_attribute_presets():
    """Test get_attribute_presets by importing directly"""
    from dicom_mcp.attributes import ATTRIBUTE_PRESETS
    
    assert ATTRIBUTE_PRESETS is not None
    assert isinstance(ATTRIBUTE_PRESETS, dict)
    assert "minimal" in ATTRIBUTE_PRESETS
    assert "standard" in ATTRIBUTE_PRESETS
    assert "extended" in ATTRIBUTE_PRESETS


def test_create_server():
    """Test creating the server"""
    # Import here to avoid circular import
    from dicom_mcp import create_dicom_mcp_server
    
    # Use temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as temp:
        config = {
            "nodes": {
                "test": {
                    "host": "localhost",
                    "port": 11112,
                    "ae_title": "TEST",
                    "description": "Test node"
                }
            },
            "calling_aets": {
                "default": {
                    "ae_title": "TESTCLIENT",
                    "description": "Test client"
                }
            },
            "current_node": "test",
            "calling_aet": "default"
        }
        yaml.dump(config, temp)
        temp.flush()
        
        # Should create a server without error
        server = create_dicom_mcp_server(temp.name)
        assert server is not None


if __name__ == "__main__":
    # If run directly, execute pytest
    import sys
    sys.exit(pytest.main(["-xvs", __file__]))