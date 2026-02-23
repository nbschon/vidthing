from dataclasses import dataclass

@dataclass
class JobInfo:
    step: str
    percent: float
    src_duration: float
    filename: str

jobs: dict[str, JobInfo] = {}

def update_job(id: str, new_info: JobInfo):
    jobs[id] = new_info 

def get_job(id: str):
    return jobs[id]
