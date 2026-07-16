import time
import threading
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any


class MetricsCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._latencies = defaultdict(list)
        self._errors = defaultdict(int)
        self._start_time = datetime.utcnow()

    def increment(self, metric: str, tags: dict = None):
        key = self._key(metric, tags)
        with self._lock:
            self._counters[key] += 1

    def gauge(self, metric: str, value: float, tags: dict = None):
        key = self._key(metric, tags)
        with self._lock:
            self._gauges[key] = value

    def record_latency(self, metric: str, duration_ms: float, tags: dict = None):
        key = self._key(metric, tags)
        with self._lock:
            self._latencies[key].append(duration_ms)
            if len(self._latencies[key]) > 1000:
                self._latencies[key] = self._latencies[key][-1000:]

    def record_error(self, metric: str, error_type: str, tags: dict = None):
        t = dict(tags or {})
        t['error_type'] = error_type
        key = self._key(metric, t)
        with self._lock:
            self._errors[key] += 1

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            now = datetime.utcnow()
            uptime = (now - self._start_time).total_seconds()
            snapshot = {
                'uptime_seconds': uptime,
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'errors': dict(self._errors),
                'latencies': {}
            }
            for key, values in self._latencies.items():
                if values:
                    sorted_vals = sorted(values)
                    n = len(sorted_vals)
                    snapshot['latencies'][key] = {
                        'count': n,
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / n,
                        'p50': sorted_vals[n // 2],
                        'p95': sorted_vals[int(n * 0.95)],
                        'p99': sorted_vals[int(n * 0.99)],
                    }
            return snapshot

    def _key(self, metric: str, tags: dict = None) -> str:
        if tags:
            tag_str = ','.join(f'{k}={v}' for k, v in sorted(tags.items()))
            return f'{metric}[{tag_str}]'
        return metric


metrics = MetricsCollector()


class timer:
    def __init__(self, metric: str, tags: dict = None):
        self.metric = metric
        self.tags = tags

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        duration_ms = (time.perf_counter() - self.start) * 1000
        metrics.record_latency(self.metric, duration_ms, self.tags)


def timed(metric: str = None, tags: dict = None):
    def decorator(func):
        name = metric or func.__name__
        def wrapper(*args, **kwargs):
            with timer(name, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator
