from datetime import datetime
from typing import Dict, List

import reflex as rx


class LoggerState(rx.State):
    entries: List[Dict[str, str]] = []

    @rx.event
    def add_log(self, message: str, level: str = "info"):
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message,
        }
        self.entries = [entry, *self.entries[:299]]

    @rx.event
    def clear(self):
        self.entries = []
