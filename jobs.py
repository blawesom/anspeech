import json
import os
from datetime import datetime
from threading import Lock

class JobTracker:
    def __init__(self, jobs_file='jobs.json'):
        self.jobs_file = jobs_file
        self.lock = Lock()
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.jobs_file):
            with open(self.jobs_file, 'w') as f:
                json.dump([], f)

    def add_job(self, stream_url, segment_duration):
        with self.lock:
            jobs = self._read_jobs()
            job = {
                'id': len(jobs) + 1,
                'stream_url': stream_url,
                'segment_duration': segment_duration,
                'status': 'processing',
                'created_at': datetime.now().isoformat(),
                'completed_at': None,
                'error': None
            }
            jobs.append(job)
            self._write_jobs(jobs)
            return job

    def update_job(self, job_id, status, error=None):
        with self.lock:
            jobs = self._read_jobs()
            for job in jobs:
                if job['id'] == job_id:
                    job['status'] = status
                    if status in ['completed', 'failed']:
                        job['completed_at'] = datetime.now().isoformat()
                    if error:
                        job['error'] = error
                    break
            self._write_jobs(jobs)

    def get_active_jobs(self):
        jobs = self._read_jobs()
        return [j for j in jobs if j['status'] == 'processing']

    def get_recent_jobs(self, limit=20):
        jobs = self._read_jobs()
        return sorted(jobs, key=lambda x: x['created_at'], reverse=True)[:limit]

    def _read_jobs(self):
        with open(self.jobs_file, 'r') as f:
            return json.load(f)

    def _write_jobs(self, jobs):
        with open(self.jobs_file, 'w') as f:
            json.dump(jobs, f, indent=2)
