# Standard library
from logging import Logger
from typing import Dict, List, TypeAlias



import array
# Third party
from pydicom import Dataset

from .config import DicomConfiguration


SeriesDict: TypeAlias = Dict[str, List[Dataset]]
StudyDict: TypeAlias = Dict[str, SeriesDict]
PatientDict: TypeAlias = Dict[str, StudyDict]

UNORGANIZED_DATASETS_KEY = "unorganized"

def _get_key_from_dataset(dataset: Dataset, key: str) -> str:
    DE = dataset.get(key, None)

    if DE is not None:
        return str(DE.value)

    return UNORGANIZED_DATASETS_KEY


class DicomStorage():
    """In memory storage of dataset, that """
    def __init__(self, config: DicomConfiguration, logger: Logger) -> None:
        self.logger = logger
        self._internal_storage: PatientDict = {}

    def store(self, dataset_to_store: Dataset):
        patient_key = _get_key_from_dataset(dataset_to_store, 'PatientID')

        if patient_key not in dataset_to_store:
            self._internal_storage = {}
        patient_dict = self._internal_storage[patient_key]

        study_key = _get_key_from_dataset(dataset_to_store, 'StudyInstanceUID')
        if study_key not in patient_dict:
            patient_dict[study_key] = {}

        study_dict = patient_dict[study_key]

        series_key = _get_key_from_dataset(dataset_to_store,'SeriesInstanceUID')
        if series_key not in study_dict:
            study_dict = {}

        series = study_dict[series_key]
        series.append(dataset_to_store)

    def retrive(
            self,
            patient_id=UNORGANIZED_DATASETS_KEY,
            study_uid=UNORGANIZED_DATASETS_KEY,
            series_key=UNORGANIZED_DATASETS_KEY,
        ) -> List[Dataset]:

        if patient_id not in self._internal_storage:

            self.logger.info(f"Did not find any studies for {patient_id}")
            return []

        study_dict = self._internal_storage[patient_id]

        if study_uid not in study_dict:
            self.logger.info(f"Didn't find the study for {patient_id}")
            return []

        series_dict = study_dict[study_uid]

        if series_key not in series_dict:
            self.logger.info(f"Didn't find the series for {patient_id}")
            return []

        return series_dict[series_key]
