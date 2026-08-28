# test_dicom_client.py
from dicom_mcp.dicom_client import DicomClient
from dicom_mcp.config import load_config
import sys

def main():
    # Load the configuration
    try:
        config = load_config("configuration.yaml")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return
    
    # Get the current node and calling AE title
    node = config.nodes[config.current_node]
    aet = config.calling_aet
    
    # Create client
    client = DicomClient(
        host=node.host,
        port=node.port,
        calling_aet=aet.ae_title,
        called_aet=node.ae_title
    )
    
    print(f"Created DICOM client for {node.host}:{node.port}")
    print(f"Called AE: {node.ae_title}, Calling AE: {aet.ae_title}")
    
    # Test connection
    success, message = client.verify_connection()
    if not success:
        print(f"Connection failed: {message}")
        return
    print(f"Connection successful: {message}")
    
    # Query for patients
    print("\nQuerying patients...")
    patients = client.query_patients()
    if not patients:
        print("No patients found")
        return
    
    print(f"Found {len(patients)} patients")
    patient_id = patients[0]["PatientID"]
    print(f"Using patient ID: {patient_id}")
    
    # Query for studies
    print("\nQuerying studies...")
    studies = client.query_studies(patient_id=patient_id)
    if not studies:
        print(f"No studies found for patient {patient_id}")
        return
    
    print(f"Found {len(studies)} studies")
    study_uid = studies[0]["StudyInstanceUID"]
    print(f"Using study UID: {study_uid}")
    
    # Query for series
    print("\nQuerying series...")
    series = client.query_series(study_instance_uid=study_uid)
    if not series:
        print(f"No series found for study {study_uid}")
        return
    
    print(f"Found {len(series)} series")
    series_uid = series[0]["SeriesInstanceUID"]
    print(f"Using series UID: {series_uid}")
    
    # Query for instances
    print("\nQuerying instances...")
    instances = client.query_instance(series_instance_uid=series_uid)
    if not instances:
        print(f"No instances found for series {series_uid}")
        return
    
    print(f"Found {len(instances)} instances")
    instance_uid = instances[0]["SOPInstanceUID"]
    print(f"Using instance UID: {instance_uid}")
    
    # # Add the retrieve_instance method to DicomClient
    # # (Copy the method provided above to dicom_client.py first)
    
    # # Retrieve the instance
    # # test_dicom_client.py
    # # ... (keep everything else the same, just replace the retrieve_instance call)

    # Retrieve the instance using C-MOVE
    print("\nRetrieving instance using C-MOVE...")
    output_dir = "./dicom_test_download"
    result = client.retrieve_instance_move(
        study_instance_uid=study_uid,
        series_instance_uid=series_uid,
        sop_instance_uid=instance_uid,
        output_dir=output_dir
    )
    
    print(f"Retrieval success: {result['success']}")
    print(f"Message: {result['message']}")
    if result['success']:
        print(f"File saved to: {result['file_path']}")
    
    # print(f"Retrieval success: {result['success']}")
    # print(f"Message: {result['message']}")
    # if result['success']:
    #     print(f"File saved to: {result['file_path']}")


    # # After the C-MOVE test, add:
    # print("\nRetrying with movescu...")
    # result = client.retrieve_using_movescu(
    #     study_instance_uid=study_uid,
    #     series_instance_uid=series_uid,
    #     sop_instance_uid=instance_uid,
    #     output_dir="./dicom_movescu_download"
    # )

    # print(f"Retrieval success: {result['success']}")
    # print(f"Message: {result['message']}")
    # if result['success']:
    #     print(f"File saved to: {result['file_path']}")
    # else:
    #     print(f"Command output: {result.get('stdout', '')}")
    #     print(f"Command errors: {result.get('stderr', '')}")

    # # Retrieve the instance
    # print("\nRetrieving instance...")
    # output_dir = "./dicom_test_download"
    # result = client.retrieve_instance(
    #     study_instance_uid=study_uid,
    #     series_instance_uid=series_uid,
    #     sop_instance_uid=instance_uid,
    #     output_dir=output_dir
    # )
    
    # print(f"Retrieval success: {result['success']}")
    # print(f"Message: {result['message']}")
    # if result['success']:
    #     print(f"File saved to: {result['file_path']}")


if __name__ == "__main__":
    main()