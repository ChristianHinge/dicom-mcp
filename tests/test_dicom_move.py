import pytest
from dicom_mcp.dicom_client import DicomClient

# Import test fixtures
from tests.test_dicom_mcp import dicom_client, upload_test_data, dicom_config

# def test_move_series(dicom_client):
#     """Test the move_series method"""
#     # Make sure we have test data  
      
#     # First query to get a series UID
#     studies = dicom_client.query_studies(patient_id="Anon001")
#     assert len(studies) > 0
    
#     study_uid = studies[0]["StudyInstanceUID"]
    
#     series = dicom_client.query_series(study_instance_uid=study_uid)
#     assert len(series) > 0
    
#     series_uid = series[0]["SeriesInstanceUID"]
    
#     # Attempt to move the series to the same Orthanc server (self-move)
#     # In a real scenario, you would move to a different destination
#     result = dicom_client.move_series(
#         destination_ae="MONAI-DEPLOY",
#         series_instance_uid=series_uid
#     )
    
#     # Verify the response structure
#     assert isinstance(result, dict)
#     assert "success" in result and result["success"]
#     assert "message" in result
#     assert "completed" in result
#     assert "failed" in result
#     assert "warning" in result
#     print(result)
#     # The actual result may vary depending on how Orthanc is configured
#     # but we're just testing the API works

# def test_move_study(dicom_client):
#     """Test the move_study method"""
#     # Make sure we have test data
    
#     # Query to get a study UID
#     studies = dicom_client.query_studies(patient_id="TEST123")
#     assert len(studies) > 0
    
#     study_uid = studies[0]["StudyInstanceUID"]
    
#     # Attempt to move the study
#     result = dicom_client.move_study(
#         destination_ae="ORTHANC",
#         study_instance_uid=study_uid
#     )
    
#     # Verify the response structure
#     assert isinstance(result, dict)
#     assert "success" in result
#     assert "message" in result
#     assert "completed" in result
#     assert "failed" in result
#     assert "warning" in result