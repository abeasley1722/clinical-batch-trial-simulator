""" 
============================================================
Author:         Zachary Kao
Date Created:   2026-03-12
Description:    Defines the Experiment object that represents a simulation request and its metadata
                including:
                - patient/patients
                - simulation duration
                - scenario/scenarios information
                - metrics needed
                - controller
                - events
                - vitals altered by the controller
============================================================ 
"""

from __future__ import annotations
import uuid
import json
from dataclasses import dataclass, asdict, field
        
@dataclass
class Patient:
    patient_id: str
    cohort_id: str | None
    sex: str | None
    age: float | None
    height: float | None
    weight: float | None
    json_file: str | None
    additional_descriptors: dict | None = None

    @staticmethod
    def create(
        sex=None,
        age=None,
        height=None,
        weight=None,
        json_file=None,
        cohort_id=None,
        additional_descriptors=None
    ):
        """
        Factory method to create a new patient with a generated ID
        """
        return Patient(
            patient_id=str(uuid.uuid4()),
            cohort_id=cohort_id,
            sex=sex,
            age=age,
            height=height,
            weight=weight,
            json_file=json_file,
            additional_descriptors=additional_descriptors or {}
        )

    def to_db_tuple(self):
        """
        Convert to tuple for DB insertion
        """
        return (
            self.patient_id,
            self.cohort_id,
            self.sex,
            self.age,
            self.height,
            self.weight,
            self.json_file,
            json.dumps(self.additional_descriptors) if self.additional_descriptors else None
        )

    @staticmethod
    def from_db_row(row):
        """
        Convert DB row → Patient object
        """
        return Patient(
            patient_id=row[0],
            cohort_id=row[1],
            sex=row[2],
            age=row[3],
            height=row[4],
            weight=row[5],
            json_file=row[6],
            additional_descriptors=json.loads(row[7]) if row[7] else {}
        )

    def to_dict(self):
        """
        Convert to dictionary (for API responses)
        """
        data = asdict(self)
        return data
    
    
    
@dataclass
class Batch:
    batch_id: str
    experiment_id: str
    patient_id: str
    status: str = "pending"
    raw_csv_path: str | None = None

    @staticmethod
    def create(experiment_id, patient_id):
        return Batch(
            batch_id=str(uuid.uuid4()),
            experiment_id=experiment_id,
            patient_id=patient_id,
            status="pending"
        )

    def to_db_tuple(self):
        return (
            self.batch_id,
            self.experiment_id,
            self.patient_id,
            self.raw_csv_path
        )        
        
@dataclass
class Scenario:
    type: str
    time: float | None = None
    trigger: dict | None = None
    params: dict = field(default_factory=dict)

    @staticmethod
    def from_dict(data):
        return Scenario(
            type=data.get("type"),
            time=data.get("time"),
            trigger=data.get("trigger"),
            params={k: v for k, v in data.items() if k not in ["type", "time", "trigger"]}
        )

    def to_dict(self):
        return {
            "type": self.type,
            "time": self.time,
            "trigger": self.trigger,
            **self.params
        }
    
@dataclass
class Metric:
    experiment_id: str
    mean_absolute_error: float
    controller_start_time: float
    mean: float
    std_dev: float
    time_within_target_range: float
    percent_time_within_target_range: float
    #TODO: varvel error measurement
    #TODO: user defined function comparison

    def create_metric(self, experiment: Experiment):
        self.experiment_id = experiment.experiment_id
        #TODO: Implement metric creation logic


@dataclass
class Experiment:
    name: str
    experiment_id: str
    patients: list[str]
    simulation_duration: int
    events: list[dict]
    output_columns: list[str] 
    output_dir: str
    analysis: Metric
    mean_csv_path: str | None = None

    @classmethod
    def from_json(cls, json_data, patient_list: list[str], file_path: str, experiment_id: str) -> 'Experiment':
        """
        Creates an Experiment instance from JSON data
        and a list of patient files described by the JSON request.
        """
        return cls(
            name = json_data.get("name"),
            experiment_id = experiment_id,
            patients = patient_list,
            simulation_duration = json_data.get("duration_s", 0),
            events = json_data.get("events", []), 
            output_columns = json_data.get("output_columns", []),
            output_dir = file_path,
            analysis = Metric(
                experiment_id=experiment_id,
                mean_absolute_error=0.0,  # Placeholder, to be calculated after simulation
                controller_start_time=0.0,  # Placeholder
                mean=0.0,  # Placeholder
                std_dev=0.0,  # Placeholder
                time_within_target_range=0.0,  # Placeholder
                percent_time_within_target_range=0.0  # Placeholder
            ),
            mean_csv_path=None
        )