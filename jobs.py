jobs: dict[str, tuple[str, float, float]] = {}

def update_job(id: str, status: tuple[str, float, float]):
    jobs[id] = status

def get_job(id: str):
    return jobs[id]
