"""
DICOM Client.

This module provides a clean interface to pynetdicom functionality,
abstracting the details of DICOM networking.
"""
import os
import time
import tempfile
from typing import Dict, List, Any, Tuple, Optional

from pydicom import dcmread
from pydicom.dataset import Dataset
from pynetdicom import AE, evt, build_role
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelGet,
    PatientRootQueryRetrieveInformationModelMove,  # For C-MOVE
    StudyRootQueryRetrieveInformationModelGet,
    StudyRootQueryRetrieveInformationModelMove,    # For C-MOVE
    Verification,
    EncapsulatedPDFStorage
)

from .attributes import get_attributes_for_level

class DicomClient:
    """DICOM networking client that handles communication with DICOM nodes."""
    
    def __init__(self, host: str, port: int, calling_aet: str, called_aet: str):
        """Initialize DICOM client.
        
        Args:
            host: DICOM node hostname or IP
            port: DICOM node port
            calling_aet: Local AE title (our AE title)
            called_aet: Remote AE title (the node we're connecting to)
        """
        self.host = host
        self.port = port
        self.called_aet = called_aet
        self.calling_aet = calling_aet
        
        # Create the Application Entity
        self.ae = AE(ae_title=calling_aet)
        
        # Add the necessary presentation contexts
        self.ae.add_requested_context(Verification)
        self.ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
        self.ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
        self.ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)
        self.ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
        self.ae.add_requested_context(StudyRootQueryRetrieveInformationModelGet)
        self.ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)
        
        # Add specific storage context for PDF - instead of adding all storage contexts
        self.ae.add_requested_context(EncapsulatedPDFStorage)
    
    def verify_connection(self) -> Tuple[bool, str]:
        """Verify connectivity to the DICOM node using C-ECHO.
        
        Returns:
            Tuple of (success, message)
        """
        # Associate with the DICOM node
        assoc = self.ae.associate(self.host, self.port, ae_title=self.called_aet)
        
        if assoc.is_established:
            # Send C-ECHO request
            status = assoc.send_c_echo()
            
            # Release the association
            assoc.release()
            
            if status and status.Status == 0:
                return True, f"Connection successful to {self.host}:{self.port} (Called AE: {self.called_aet}, Calling AE: {self.calling_aet})"
            else:
                return False, f"C-ECHO failed with status: {status.Status if status else 'None'}"
        else:
            return False, f"Failed to associate with DICOM node at {self.host}:{self.port} (Called AE: {self.called_aet}, Calling AE: {self.calling_aet})"
    
    def find(self, query_dataset: Dataset, query_model, attributes:List[str]) -> List[Dict[str, Any]]:
        """Execute a C-FIND request.
        
        Args:
            query_dataset: Dataset containing query parameters
            query_model: DICOM query model (Patient/StudyRoot)
        
        Returns:
            List of dictionaries containing query results
        
        Raises:
            Exception: If association fails
        """
        for attr in attributes:
            if not hasattr(query_dataset, attr):
                setattr(query_dataset, attr, "")

        # Associate with the DICOM node
        assoc = self.ae.associate(self.host, self.port, ae_title=self.called_aet)
        
        if not assoc.is_established:
            raise Exception(f"Failed to associate with DICOM node at {self.host}:{self.port} (Called AE: {self.called_aet}, Calling AE: {self.calling_aet})")
        
        results = []
        
        try:
            # Send C-FIND request
            responses = assoc.send_c_find(query_dataset, query_model)
            
            for (status, dataset) in responses:
                if status and status.Status == 0xFF00:  # Pending
                    if dataset:
                        results.append(self._dataset_to_dict(dataset,attributes))
        finally:
            # Always release the association
            assoc.release()
        
        return results
    
    def query_patients(self, patient_id: str = None, name_pattern: str = None, 
                     birth_date: str = None, attribute_preset: str = "standard",
                     additional_attrs: List[str] = []) -> List[Dict[str, Any]]:
        """Query for patients matching criteria.
        
        Args:
            patient_id: Patient ID
            name_pattern: Patient name pattern (can include wildcards * and ?)
            birth_date: Patient birth date (YYYYMMDD)
            attribute_preset: Attribute preset (minimal, standard, extended)
            additional_attrs: Additional attributes to include
            
        Returns:
            List of matching patient records
        """
        # Create query dataset
        ds = Dataset()
        ds.QueryRetrieveLevel = "PATIENT"
        
        # Add query parameters if provided
        if patient_id:
            ds.PatientID = patient_id
            
        if name_pattern:
            ds.PatientName = name_pattern
            
        if birth_date:
            ds.PatientBirthDate = birth_date
        
        # Add attributes based on preset
        attrs = get_attributes_for_level("patient", attribute_preset, additional_attrs)
        
        # Execute query
        return self.find(ds, PatientRootQueryRetrieveInformationModelFind, attrs)
    
    def query_studies(self, patient_id: str = None, study_date: str = None, 
                   modality: str = None, accession_number: str = None, 
                   attribute_preset: str = "standard", additional_attrs: List[str] = None) -> List[Dict[str, Any]]:
        """Query for studies matching criteria.
        
        Args:
            patient_id: Patient ID
            study_date: Study date or range (YYYYMMDD or YYYYMMDD-YYYYMMDD)
            modality: Modalities in study
            accession_number: Accession number
            attribute_preset: Attribute preset (minimal, standard, extended)
            additional_attrs: Additional attributes to include
            
        Returns:
            List of matching study records
        """
        # Create query dataset
        ds = Dataset()
        ds.QueryRetrieveLevel = "STUDY"
        
        # Add query parameters if provided
        if patient_id:
            ds.PatientID = patient_id
            
        if study_date:
            ds.StudyDate = study_date
            
        if modality:
            ds.ModalitiesInStudy = modality
            
        if accession_number:
            ds.AccessionNumber = accession_number
        
        # Add attributes based on preset
        attrs = get_attributes_for_level("study", attribute_preset, additional_attrs)
        
        # Execute query
        return self.find(ds, StudyRootQueryRetrieveInformationModelFind, attrs)
    
    def query_series(self, study_instance_uid: str, modality: str = None, attribute_preset: str = "standard", additional_attrs: List[str] = None) -> List[Dict[str, Any]]:
        """Query for series matching criteria.
        
        Args:
            study_instance_uid: Study Instance UID (required)
            modality: Modality (e.g. "CT", "MR")
            attribute_preset: Attribute preset (minimal, standard, extended)
            additional_attrs: Additional attributes to include
            
        Returns:
            List of matching series records
        """
        # Create query dataset
        ds = Dataset()
        ds.QueryRetrieveLevel = "SERIES"
        ds.StudyInstanceUID = study_instance_uid
        
        if modality:
            ds.Modality = modality

        # Add attributes based on preset
        attrs = get_attributes_for_level("series", attribute_preset, additional_attrs)
        
        # Execute query
        return self.find(ds, StudyRootQueryRetrieveInformationModelFind, attrs)
    
    def query_instance(self, series_instance_uid: str,
                      attribute_preset: str = "standard",
                      additional_attrs: List[str] = None) -> List[Dict[str, Any]]:
        """Query for instances matching criteria.
        
        Args:
            series_instance_uid: Series Instance UID (required)
            attribute_preset: Attribute preset (minimal, standard, extended)
            additional_attrs: Additional attributes to include
            
        Returns:
            List of matching instance records
        """
        # Create query dataset
        ds = Dataset()
        ds.QueryRetrieveLevel = "IMAGE"
        ds.SeriesInstanceUID = series_instance_uid
            
        # Add attributes based on preset
        attrs = get_attributes_for_level("instance", attribute_preset, additional_attrs)
        
        # Execute query
        return self.find(ds, StudyRootQueryRetrieveInformationModelFind,attrs)
    
    def move_series(
            self, 
            destination_ae: str,
            series_instance_uid: str
        ) -> dict:
        """Move a DICOM series to another DICOM node using C-MOVE.
        
        This method performs a simple C-MOVE operation to transfer a specific series
        to a destination DICOM node.
        
        Args:
            destination_ae: AE title of the destination DICOM node
            series_instance_uid: Series Instance UID to be moved
            
        Returns:
            Dictionary with operation status:
            {
                "success": bool,
                "message": str,
                "completed": int,  # Number of successful transfers
                "failed": int,     # Number of failed transfers
                "warning": int     # Number of warnings
            }
        """
        # Create query dataset for series level
        ds = Dataset()
        ds.QueryRetrieveLevel = "SERIES"
        ds.SeriesInstanceUID = series_instance_uid
        
        # Associate with the DICOM node
        assoc = self.ae.associate(self.host, self.port, ae_title=self.called_aet)
        
        if not assoc.is_established:
            return {
                "success": False,
                "message": f"Failed to associate with DICOM node at {self.host}:{self.port}",
                "completed": 0,
                "failed": 0,
                "warning": 0
            }
        
        result = {
            "success": False,
            "message": "C-MOVE operation failed",
            "completed": 0,
            "failed": 0,
            "warning": 0
        }
        
        try:
            # Send C-MOVE request with the destination AE title
            responses = assoc.send_c_move(
                ds, 
                destination_ae, 
                PatientRootQueryRetrieveInformationModelMove
            )
            
            # Process the responses
            for (status, dataset) in responses:
                if status:
                    # Record the sub-operation counts if available
                    if hasattr(status, 'NumberOfCompletedSuboperations'):
                        result["completed"] = status.NumberOfCompletedSuboperations
                    if hasattr(status, 'NumberOfFailedSuboperations'):
                        result["failed"] = status.NumberOfFailedSuboperations
                    if hasattr(status, 'NumberOfWarningSuboperations'):
                        result["warning"] = status.NumberOfWarningSuboperations
                    
                    # Check the status code
                    if status.Status == 0x0000:  # Success
                        result["success"] = True
                        result["message"] = "C-MOVE operation completed successfully"
                    elif status.Status == 0x0001 or status.Status == 0xB000:  # Success with warnings
                        result["success"] = True
                        result["message"] = "C-MOVE operation completed with warnings or failures"
                    elif status.Status == 0xA801:  # Refused: Move destination unknown
                        result["message"] = f"C-MOVE refused: Destination '{destination_ae}' unknown"
                    else:
                        result["message"] = f"C-MOVE failed with status 0x{status.Status:04X}"
                        
                    # If we got a dataset with an error comment, add it
                    if dataset and hasattr(dataset, 'ErrorComment'):
                        result["message"] += f": {dataset.ErrorComment}"
        
        finally:
            # Always release the association
            assoc.release()
        
        return result

    def move_study(
            self, 
            destination_ae: str,
            study_instance_uid: str
        ) -> dict:
        """Move a DICOM study to another DICOM node using C-MOVE.
        
        This method performs a simple C-MOVE operation to transfer a specific study
        to a destination DICOM node.
        
        Args:
            destination_ae: AE title of the destination DICOM node
            study_instance_uid: Study Instance UID to be moved
            
        Returns:
            Dictionary with operation status:
            {
                "success": bool,
                "message": str,
                "completed": int,  # Number of successful transfers
                "failed": int,     # Number of failed transfers
                "warning": int     # Number of warnings
            }
        """
        # Create query dataset for study level
        ds = Dataset()
        ds.QueryRetrieveLevel = "STUDY"
        ds.StudyInstanceUID = study_instance_uid
        
        # Associate with the DICOM node
        assoc = self.ae.associate(self.host, self.port, ae_title=self.called_aet)
        
        if not assoc.is_established:
            return {
                "success": False,
                "message": f"Failed to associate with DICOM node at {self.host}:{self.port}",
                "completed": 0,
                "failed": 0,
                "warning": 0
            }
        
        result = {
            "success": False,
            "message": "C-MOVE operation failed",
            "completed": 0,
            "failed": 0,
            "warning": 0
        }
        
        try:
            # Send C-MOVE request with the destination AE title
            responses = assoc.send_c_move(
                ds, 
                destination_ae, 
                PatientRootQueryRetrieveInformationModelMove
            )
            
            # Process the responses
            for (status, dataset) in responses:
                if status:
                    # Record the sub-operation counts if available
                    if hasattr(status, 'NumberOfCompletedSuboperations'):
                        result["completed"] = status.NumberOfCompletedSuboperations
                    if hasattr(status, 'NumberOfFailedSuboperations'):
                        result["failed"] = status.NumberOfFailedSuboperations
                    if hasattr(status, 'NumberOfWarningSuboperations'):
                        result["warning"] = status.NumberOfWarningSuboperations
                    
                    # Check the status code
                    if status.Status == 0x0000:  # Success
                        result["success"] = True
                        result["message"] = "C-MOVE operation completed successfully"
                    elif status.Status == 0x0001 or status.Status == 0xB000:  # Success with warnings
                        result["success"] = True
                        result["message"] = "C-MOVE operation completed with warnings or failures"
                    elif status.Status == 0xA801:  # Refused: Move destination unknown
                        result["message"] = f"C-MOVE refused: Destination '{destination_ae}' unknown"
                    else:
                        result["message"] = f"C-MOVE failed with status 0x{status.Status:04X}"
                        
                    # If we got a dataset with an error comment, add it
                    if dataset and hasattr(dataset, 'ErrorComment'):
                        result["message"] += f": {dataset.ErrorComment}"
        
        finally:
            # Always release the association
            assoc.release()
        
        return result
    def _retrieve_pdf_dataset(
            self,
            study_instance_uid: str,
            series_instance_uid: str,
            sop_instance_uid: str,
        ) -> Tuple[Optional[Dataset], str, str]:
        """C-GET a single Encapsulated PDF instance and validate it.

        Shared retrieval path for the PDF tools (text extraction and widget rendering).

        Returns a ``(dataset, message, file_path)`` tuple:
          - success: ``(<PDF dataset>, "", <temp .dcm path>)``
          - failure: ``(None, <human-readable reason>, <temp .dcm path or "">)``

        The reason string differentiates the common failure modes (no instance matched /
        stale UIDs, non-PDF instance that can't be transferred via the PDF-only role,
        unreadable DICOM, wrong SOP class) so callers can surface it directly.
        """
        # Create temporary directory for storing retrieved files
        temp_dir = tempfile.mkdtemp()

        # Create dataset for C-GET query
        ds = Dataset()
        ds.QueryRetrieveLevel = "IMAGE"
        ds.StudyInstanceUID = study_instance_uid
        ds.SeriesInstanceUID = series_instance_uid
        ds.SOPInstanceUID = sop_instance_uid

        # Collect instances pushed back to us via C-STORE during the C-GET.
        received_files = []

        def handle_store(event):
            """Handle C-STORE operations during C-GET"""
            ds = event.dataset
            sop_instance = ds.SOPInstanceUID if hasattr(ds, 'SOPInstanceUID') else "unknown"

            # Ensure we have file meta information
            if not hasattr(ds, 'file_meta') or not hasattr(ds.file_meta, 'TransferSyntaxUID'):
                from pydicom.dataset import FileMetaDataset
                if not hasattr(ds, 'file_meta'):
                    ds.file_meta = FileMetaDataset()

                if event.context.transfer_syntax:
                    ds.file_meta.TransferSyntaxUID = event.context.transfer_syntax
                else:
                    ds.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"

                if not hasattr(ds.file_meta, 'MediaStorageSOPClassUID') and hasattr(ds, 'SOPClassUID'):
                    ds.file_meta.MediaStorageSOPClassUID = ds.SOPClassUID

                if not hasattr(ds.file_meta, 'MediaStorageSOPInstanceUID') and hasattr(ds, 'SOPInstanceUID'):
                    ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID

            # Save the dataset to file
            file_path = os.path.join(temp_dir, f"{sop_instance}.dcm")
            ds.save_as(file_path, write_like_original=False)
            received_files.append(file_path)

            return 0x0000  # Success

        handlers = [(evt.EVT_C_STORE, handle_store)]

        # SCP/SCU Role Selection so our AE may act as the C-STORE receiver during C-GET.
        # Only the Encapsulated PDF storage role is negotiated (see __init__ context).
        role = build_role(EncapsulatedPDFStorage, scp_role=True)

        assoc = self.ae.associate(
            self.host,
            self.port,
            ae_title=self.called_aet,
            evt_handlers=handlers,
            ext_neg=[role],
        )

        if not assoc.is_established:
            return None, f"Failed to associate with DICOM node at {self.host}:{self.port}", ""

        message = "C-GET operation failed"
        final_status = None
        try:
            responses = assoc.send_c_get(ds, PatientRootQueryRetrieveInformationModelGet)
            for (status, dataset) in responses:
                if status:
                    final_status = status
                    status_int = status.Status if hasattr(status, "Status") else None
                    if status_int == 0xFF00:        # Pending - sub-operations running
                        message = "C-GET operation in progress"
                    elif status_int == 0x0000:      # Final success
                        message = "C-GET operation completed"
                else:
                    # An empty status means the peer aborted or the link timed out.
                    message = ("C-GET failed: no response from the peer "
                               "(association aborted or DIMSE timeout)")
        except Exception as exc:
            message = f"C-GET request raised an error: {exc}"
        finally:
            assoc.release()

        # No instance came back: differentiate "nothing matched" (stale UIDs) from
        # "matched but the transfer failed" (e.g. a non-PDF instance the PDF-only role
        # can't carry), using the C-GET sub-operation counts.
        if not received_files:
            status_hex = (f"0x{final_status.Status:04x}"
                          if final_status is not None and hasattr(final_status, "Status")
                          else "n/a")
            failed = getattr(final_status, "NumberOfFailedSuboperations", None)
            if failed:
                detail = (
                    f"C-GET matched the instance but the transfer failed (final status "
                    f"{status_hex}, {failed} failed sub-operation(s)). This tool only negotiates "
                    f"the Encapsulated PDF storage role, so a non-PDF instance - e.g. a Structured "
                    f"Report (SR) - cannot be retrieved with it. Verify the UIDs point to an "
                    f"Encapsulated PDF instance."
                )
            else:
                detail = (
                    f"C-GET returned no instances (final status {status_hex}). The requested UIDs "
                    f"were not found on '{self.called_aet}' - they may be stale (data deleted or "
                    f"re-imported). Re-run a query (C-FIND) to get current UIDs and try again."
                )
            return None, detail, ""

        # Read the received instance back and verify it really is an Encapsulated PDF.
        dicom_file = received_files[0]
        try:
            ds = dcmread(dicom_file)
        except Exception as exc:
            return None, f"Retrieved instance could not be read as DICOM: {exc}", dicom_file

        if not (hasattr(ds, "SOPClassUID")
                and ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.104.1"):
            return None, (
                "Retrieved DICOM instance is not an Encapsulated PDF "
                f"(SOP Class: {getattr(ds, 'SOPClassUID', 'unknown')}). "
                "A textual report may instead be stored as a Structured Report (SR)."
            ), dicom_file

        return ds, "", dicom_file

    def extract_pdf_text_from_dicom(
            self,
            study_instance_uid: str,
            series_instance_uid: str,
            sop_instance_uid: str
        ) -> Dict[str, Any]:
        """Retrieve a DICOM-encapsulated PDF via C-GET and extract its text (PyPDF2).

        Returns ``{success, message, text_content, file_path}``.
        """
        ds, error, dicom_file = self._retrieve_pdf_dataset(
            study_instance_uid, series_instance_uid, sop_instance_uid)
        if ds is None:
            return {"success": False, "message": error,
                    "text_content": "", "file_path": dicom_file}

        # A malformed/truncated PDF (e.g. missing xref/startxref) makes PyPDF2 raise -
        # catch it and report a clear cause rather than a raw traceback to the MCP client.
        try:
            pdf_data = ds.EncapsulatedDocument
            import io
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            extracted_text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        except Exception as exc:
            return {
                "success": False,
                "message": (
                    f"Instance retrieved, but the embedded PDF could not be parsed: {exc}. "
                    "The encapsulated document may be malformed or truncated."
                ),
                "text_content": "",
                "file_path": dicom_file,
            }

        return {
            "success": True,
            "message": "Successfully extracted text from PDF in DICOM",
            "text_content": extracted_text,
            "file_path": dicom_file,
        }

    @staticmethod
    def _dataset_to_dict(dataset: Dataset,attributes: List[str] = None) -> Dict[str, Any]:
        """Convert a DICOM dataset to a dictionary.
        
        Args:
            dataset: DICOM dataset
            
        Returns:
            Dictionary representation of the dataset
        """
        if hasattr(dataset, "is_empty") and dataset.is_empty():
            return {}
        
        result = {}
        for elem in dataset:
            if elem.VR == "SQ":
                # Handle sequences
                result[elem.keyword] = [DicomClient._dataset_to_dict(item, attributes) for item in elem.value]
            else:
                # Handle regular elements
                if hasattr(elem, "keyword"):
                    try:
                        if elem.VR == "PN":
                            # pydicom returns PersonName for PN elements, which is not
                            # JSON-serializable -> the MCP framework's json.dumps() fails
                            # downstream. Use the plain string form instead.
                            result[elem.keyword] = str(elem.value)
                        elif elem.VM > 1:
                            # Multiple values
                            result[elem.keyword] = list(elem.value)
                        else:
                            # Single value
                            result[elem.keyword] = elem.value
                    except Exception:
                        # Fall back to string representation
                        result[elem.keyword] = str(elem.value)

        result = {k: v for k, v in result.items() if k in attributes}

        return result