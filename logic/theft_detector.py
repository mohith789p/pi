import numpy as np
import time
import json
import os

class TheftDetector:
    def __init__(self, cfg, persist_path=None, save_interval=5, stale_timeout=60):
        self.tracks = {}
        self.cfg = cfg
        self.pixel_threshold = cfg.get('pixel_threshold', 120)
        self.persist_path = persist_path
        self.last_save_time = time.time()
        self.save_interval = save_interval  # seconds
        self.stale_timeout = stale_timeout  # seconds
        if self.persist_path and os.path.exists(self.persist_path):
            self._load_tracks()

    def update_track(self, tid, x, y):
        now = time.time()
        self.tracks.setdefault(tid, []).append((now, x, y))
        self.tracks[tid] = self.tracks[tid][-5:]
        self._cleanup_stale_tracks()
        if self.persist_path and (time.time() - self.last_save_time) > self.save_interval:
            self._save_tracks()
            self.last_save_time = time.time()

    def detect(self, humans, hens):
        for tid, (hx, hy) in humans:
            track = self.tracks.get(tid, [])
            if len(track) < 2:
                continue
            t0, x0, y0 = track[0]
            t1, x1, y1 = track[-1]
            dt = max(t1 - t0, 1e-3)
            velocity = np.linalg.norm([x1-x0, y1-y0]) / dt
            nearby = sum(1 for x, y in hens if np.linalg.norm([hx-x, hy-y]) < self.pixel_threshold)
            if velocity > self.cfg['velocity_threshold'] and nearby >= self.cfg['theft_hens']:
                return True
        return False

    def _cleanup_stale_tracks(self):
        now = time.time()
        stale_tids = [tid for tid, positions in self.tracks.items()
                      if positions and now - positions[-1][0] > self.stale_timeout]
        for tid in stale_tids:
            del self.tracks[tid]

    def _save_tracks(self):
        try:
            with open(self.persist_path, 'w') as f:
                json.dump({tid: track[-5:] for tid, track in self.tracks.items()}, f)
        except Exception:
            pass

    def _load_tracks(self):
        try:
            with open(self.persist_path, 'r') as f:
                self.tracks = json.load(f)
                self.tracks = {int(tid): [tuple(pos) for pos in track] for tid, track in self.tracks.items()}
        except Exception:
            self.tracks = {}
