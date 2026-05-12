from __future__ import annotations

from threading import Lock

from app.schemas import GardenProfile


class GardenProfileStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._profile = GardenProfile()

    def get(self) -> GardenProfile:
        with self._lock:
            return self._profile.model_copy()

    def update(self, profile: GardenProfile) -> GardenProfile:
        with self._lock:
            self._profile = profile
            return self._profile.model_copy()


garden_profile_store = GardenProfileStore()
