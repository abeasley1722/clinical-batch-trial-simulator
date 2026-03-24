
# ============================================================
# Author:        Zachary Kao & Anointiyae Beasley
# Date Created:  2026-03-19
# Description:   A class meant to handle running a full experiment
# ============================================================ 

class ExperimentExecutor:
    def __init__(self, experiment: Experiment):
        #Unpack each experiment into new variables [unfinished]
        self.id = experiment.id
        
        self.pulse = None
        self.results = [] #May just be one csv file
        
    def initialize_engine(self):
        pass

    def build_data_requests(self):
        pass

    def load_patient(self):
        pass

    def apply_event(self, event):
        pass

    def step(self):
        pass

    def collect_results(self):
        pass

    def run(self):
        pass