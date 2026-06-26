"""
Live Terminal Dashboard
Provides real-time visual feedback on traffic bot progress using the Rich library.
"""

import time
import threading
import logging
from typing import Dict

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

logger = logging.getLogger("traffic_bot.dashboard")


class LiveDashboard:
    """
    Real-time terminal dashboard showing bot progress, session stats,
    and proxy health information.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.console = Console()
        self.running = False
        self._thread = None
        self.stats = {
            "total_sessions": config.get("sessions", {}).get("total", 0),
            "completed": 0,
            "failed": 0,
            "in_progress": 0,
            "total_pages": 0,
            "start_time": None,
        }

    def start(self):
        """Start the dashboard display."""
        self.running = True
        self.stats["start_time"] = time.time()
        logger.debug("Dashboard started")

    def stop(self):
        """Stop the dashboard display."""
        self.running = False
        logger.debug("Dashboard stopped")

    def update(self, session_result: Dict):
        """Update dashboard with a completed session result."""
        if session_result.get("status") == "completed":
            self.stats["completed"] += 1
        elif session_result.get("status") == "failed":
            self.stats["failed"] += 1

        self.stats["total_pages"] += session_result.get("pages_visited", 0)

    def render_progress(self) -> str:
        """Render a simple progress indicator."""
        total = self.stats["total_sessions"]
        done = self.stats["completed"] + self.stats["failed"]
        pct = (done / total * 100) if total > 0 else 0

        elapsed = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        rate = done / elapsed if elapsed > 0 else 0

        bar_width = 40
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        return (
            f"\n  Progress: [{bar}] {pct:.1f}%\n"
            f"  Sessions: {done}/{total} | "
            f"Completed: {self.stats['completed']} | "
            f"Failed: {self.stats['failed']}\n"
            f"  Pages Visited: {self.stats['total_pages']} | "
            f"Rate: {rate:.1f} sessions/sec | "
            f"Elapsed: {elapsed:.0f}s\n"
        )
