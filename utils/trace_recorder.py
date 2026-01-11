import json
import time
import functools
import inspect
import threading
from collections import deque

class TraceRecorder:
    def __init__(self):
        self.traces = deque(maxlen=10000) # Circular buffer
        self.is_recording = False
        self.lock = threading.Lock()

    def start(self):
        self.is_recording = True
        self.traces.clear()

    def stop(self):
        self.is_recording = False

    def export(self, file_path="trace.json"):
        with self.lock:
            data = list(self.traces)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return file_path

    def trace(self, func):
        """Decorator to record function calls"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.is_recording:
                return func(*args, **kwargs)
            
            start_time = time.time()
            try:
                # Get caller info
                stack = inspect.stack()
                caller = stack[1]
                caller_name = caller.function
                # Ideally get full module path, but simple name for now
                
                result = func(*args, **kwargs)
                
                duration = (time.time() - start_time) * 1000 # ms
                
                with self.lock:
                    self.traces.append({
                        "source": caller_name,
                        "target": func.__name__,
                        "timestamp": start_time,
                        "duration": duration,
                        "args_summary": str(args)[:50] # Truncate
                    })
                
                return result
            except Exception as e:
                # Log error trace?
                raise e
        return wrapper

trace_recorder = TraceRecorder()
