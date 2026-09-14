from pathlib import Path

from celery.beat import PersistentScheduler

BEAT_HEARTBEAT_PATH = Path("/tmp/celery-beat-health")


class HealthCheckedScheduler(PersistentScheduler):
    def tick(self, *args, **kwargs):
        interval = super().tick(*args, **kwargs)
        BEAT_HEARTBEAT_PATH.touch()
        return interval
