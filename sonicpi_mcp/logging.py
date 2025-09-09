"""Logging system with ring buffer for tail_logs."""

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional

from .schemas import LogEntry


@dataclass
class LogRecord:
    """Internal log record structure."""
    ts: float
    level: str
    message: str


class RingLogger:
    """Ring buffer logger that maintains a fixed number of recent log entries."""
    
    def __init__(self, max_entries: int = 1000):
        """Initialize the logger with a maximum number of entries."""
        self.buffer: Deque[LogRecord] = deque(maxlen=max_entries)
    
    def log(self, level: str, message: str) -> None:
        """Add a new log entry."""
        self.buffer.append(LogRecord(
            ts=time.time() * 1000,  # Convert to milliseconds
            level=level,
            message=message
        ))
    
    def get_entries(self, since_ms: Optional[float] = None) -> List[LogEntry]:
        """Retrieve log entries, optionally filtered by timestamp."""
        entries = []
        
        for record in self.buffer:
            if since_ms is None or record.ts > since_ms:
                entries.append(LogEntry(
                    ts=record.ts,
                    level=record.level,
                    message=record.message
                ))
        
        return entries


# Global logger instance
logger = RingLogger()
