"""
DICOM attribute presets for different query levels.
"""

from typing import Dict, List, Optional

# Dictionary of attribute presets for each query level
ATTRIBUTE_PRESETS = {
    # Minimal attribute set - just essential identifiers
    "minimal": {
        "patient": [
            "PatientID",
            "PatientName",
        ],
        "study": [
            "StudyInstanceUID",
            "PatientID",
            "StudyDate",
            "StudyDescription",
        ],
        "series": [
            "SeriesInstanceUID",
            "StudyInstanceUID",
            "Modality",
            "SeriesNumber",
        ],
        "instance": [
            "SOPInstanceUID",
            "SeriesInstanceUID",
            "InstanceNumber",
        ],
    },
    
    # Standard attribute set - common clinical attributes
    "standard": {
        "patient": [
            "PatientID",
            "PatientName",
            "PatientBirthDate",
            "PatientSex",
            "PatientAge",
        ],
        "study": [
            "StudyInstanceUID",
            "StudyDate",
            "StudyTime",
            "StudyDescription",
            "AccessionNumber",
            "NumberOfStudyRelatedSeries",
            "ModalitiesInStudy",
        ],
        "series": [
            "SeriesInstanceUID",
            "Modality",
            "SeriesNumber",
            "SeriesDescription",
        ],
        "instance": [
            "SOPInstanceUID",
            "InstanceNumber",
            "ContentDate",
            "ContentTime",
            "ImageType",
            "NumberOfFrames",
        ],
    },
    
    # Extended attribute set - comprehensive information
    "extended": {
        "patient": [
            "PatientID",
            "PatientName",
            "PatientBirthDate",
            "PatientSex",
            "PatientAge",
            "PatientWeight",
            "PatientAddress",
            "PatientComments",
            "IssuerOfPatientID",
            "EthnicGroup",
        ],
        "study": [
            "StudyInstanceUID",
            "PatientID",
            "StudyDate",
            "StudyTime",
            "StudyDescription",
            "AccessionNumber",
            "ReferringPhysicianName",
            "StudyID",
            "ProcedureCodeSequence",
            "NumberOfStudyRelatedSeries",
            "NumberOfStudyRelatedInstances",
            "StudyComments",
            "AdmissionID",
            "ModalitiesInStudy",
            "RequestingPhysician",
            "RequestedProcedureDescription",
        ],
        "series": [
            "SeriesInstanceUID",
            "StudyInstanceUID",
            "Modality",
            "SeriesNumber",
            "SeriesDescription",
            "BodyPartExamined",
            "PatientPosition",
            "NumberOfSeriesRelatedInstances",
            "SeriesDate",
            "SeriesTime",
            "PerformingPhysicianName",
            "ProtocolName",
            "OperatorsName",
            "PerformedProcedureStepDescription",
            "AnatomicalOrientationType",
            "InstitutionName",
        ],
        "instance": [
            "SOPInstanceUID",
            "SeriesInstanceUID",
            "SOPClassUID",
            "InstanceNumber",
            "ContentDate",
            "ContentTime",
            "ImageType",
            "AcquisitionDate",
            "AcquisitionTime",
            "ImageComments",
            "NumberOfFrames",
            "BurnedInAnnotation",
            "WindowCenter",
            "WindowWidth",
            "ImagePositionPatient",
            "ImageOrientationPatient",
            "SliceLocation",
            "PixelSpacing",
            "PhotometricInterpretation",
            "BitsAllocated",
            "BitsStored",
        ],
    },
}


def get_attributes_for_level(
    level: str, 
    preset: str = "standard", 
    additional_attrs: Optional[List[str]] = None, 
    exclude_attrs: Optional[List[str]] = None
) -> List[str]:
    """Get the list of attributes for a specific query level and preset.
    
    Args:
        level: Query level (patient, study, series, instance)
        preset: Attribute preset name (minimal, standard, extended)
        additional_attrs: Additional attributes to include
        exclude_attrs: Attributes to exclude
        
    Returns:
        List of DICOM attribute names
    """
    # Start with the preset attributes
    if preset in ATTRIBUTE_PRESETS and level in ATTRIBUTE_PRESETS[preset]:
        attr_list = ATTRIBUTE_PRESETS[preset][level].copy()
    elif preset in ATTRIBUTE_PRESETS and level not in ATTRIBUTE_PRESETS[preset]:
        # If preset exists but doesn't have this level, fall back to standard
        attr_list = ATTRIBUTE_PRESETS["standard"][level].copy()
    else:
        # If preset doesn't exist, fall back to standard
        attr_list = ATTRIBUTE_PRESETS["standard"][level].copy()
    
    # Add additional attributes
    if additional_attrs:
        for attr in additional_attrs:
            if attr not in attr_list:
                attr_list.append(attr)
    
    # Remove excluded attributes
    if exclude_attrs:
        attr_list = [attr for attr in attr_list if attr not in exclude_attrs]
    
    return attr_list