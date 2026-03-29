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

from datetime import datetime

from . import patient
from . import scenario
from . import metric
from dataclasses import dataclass

@dataclass
class Experiment:
    name: str
    experiment_id: str
    patients: list[str] #TODO: store patient as patient objects
    simulation_duration: int
    events: list[dict] #TODO: store as an object for better structure?
    output_columns: list[str] 
    #metrics: list[str] TODO: figure out how to represent the metrics. using metrics.py object?
    #scenarios: list[str] TODO: figure out how to represent the scenarios. list of events is already stored
    #controller TODO: figure out how to represent the controller
    #vitals TODO: figure out how to represent the vitals altered by the controller

    def __post_init__(self):
        #TODO: add validation for fields
        pass

    @classmethod
    def from_json(cls, json_data, patient_list: list[str]) -> 'Experiment':
        """
        Creates an Experiment instance from JSON data
        and a list of patient files described by the JSON request.
        """
        return cls(
            name = json_data.get("name"),
            experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S"),
            patients = patient_list,
            simulation_duration = json_data.get("duration_s", 0),
            events = json_data.get("events", []), 
            output_columns = json_data.get("output_columns", [])
            #TODO: add metrics, scenarios, controller, vitals
        )
        
