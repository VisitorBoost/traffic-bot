"""
Session Reporter Module
Generates detailed JSON reports and formatted terminal summaries
of traffic bot session results.
"""

import json
import time
import logging
from typing import Dict, List
from pathlib import Path
from collections import Counter

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

logger = logging.getLogger("traffic_bot.reporter")


class SessionReporter:
    """
    Generates comprehensive reports from traffic bot session data.
    Outputs JSON files and formatted terminal summaries.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.console = Console()
        self.output_config = config.get("output", {})

    def save_report(self, results: List[Dict], summary: Dict):
        """
        Save a detailed JSON report of all session results.
        
        Args:
            results: List of individual session result dictionaries.
            summary: Aggregated summary statistics.
        """
        report_file = self.output_config.get("report_file", "report.json")

        report = {
            "metadata": {
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "target_url": self.config.get("target", {}).get("url", ""),
                "total_sessions_configured": self.config.get("sessions", {}).get("total", 0),
                "concurrent_limit": self.config.get("sessions", {}).get("concurrent", 0),
                "proxy_enabled": self.config.get("proxy", {}).get("enabled", False),
            },
            "summary": summary,
            "referrer_distribution": self._calculate_referrer_distribution(results),
            "device_distribution": self._calculate_device_distribution(results),
            "session_details": [
                {
                    "session_id": i + 1,
                    "status": r.get("status", "unknown"),
                    "pages_visited": r.get("pages_visited", 0),
                    "total_time": round(r.get("total_time", 0), 2),
                    "referrer": r.get("referrer", "direct"),
                    "user_agent": r.get("user_agent", "")[:80] + "...",
                    "proxy": r.get("proxy", "direct"),
                    "errors": r.get("errors", []),
                }
                for i, r in enumerate(results)
            ],
        }

        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to: {report_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    def print_summary(self, summary: Dict):
        """Print a formatted summary table to the terminal."""
        self.console.print()

        # Main summary panel
        table = Table(
            title="Traffic Bot - Session Summary",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total Sessions", str(summary.get("total_sessions", 0)))
        table.add_row(
            "Completed",
            f"[green]{summary.get('completed', 0)}[/green]",
        )
        table.add_row(
            "Failed",
            f"[red]{summary.get('failed', 0)}[/red]",
        )
        table.add_row(
            "Total Pages Visited",
            str(summary.get("total_pages_visited", 0)),
        )
        table.add_row(
            "Avg Session Time",
            f"{summary.get('average_session_time', 0):.2f}s",
        )
        table.add_row(
            "Avg Pages/Session",
            f"{summary.get('average_pages_per_session', 0):.2f}",
        )
        table.add_row(
            "Total Run Time",
            f"{summary.get('total_run_time', 0):.2f}s",
        )

        # Calculate success rate
        total = summary.get("total_sessions", 1)
        completed = summary.get("completed", 0)
        success_rate = (completed / total * 100) if total > 0 else 0
        table.add_row("Success Rate", f"{success_rate:.1f}%")

        self.console.print(table)
        self.console.print()

    def _calculate_referrer_distribution(self, results: List[Dict]) -> Dict:
        """Calculate the distribution of referrer sources across sessions."""
        referrers = []
        for r in results:
            ref = r.get("referrer")
            if ref is None:
                referrers.append("direct")
            elif "google" in ref:
                referrers.append("google")
            elif "bing" in ref:
                referrers.append("bing")
            elif "duckduckgo" in ref:
                referrers.append("duckduckgo")
            elif "yahoo" in ref:
                referrers.append("yahoo")
            elif "facebook" in ref or "fb.com" in ref:
                referrers.append("facebook")
            elif "twitter" in ref or "t.co" in ref or "x.com" in ref:
                referrers.append("twitter")
            elif "linkedin" in ref:
                referrers.append("linkedin")
            elif "reddit" in ref:
                referrers.append("reddit")
            elif "pinterest" in ref:
                referrers.append("pinterest")
            elif "youtube" in ref:
                referrers.append("youtube")
            else:
                referrers.append("other_referral")

        counter = Counter(referrers)
        total = len(referrers) or 1

        return {
            source: {
                "count": count,
                "percentage": round(count / total * 100, 1),
            }
            for source, count in counter.most_common()
        }

    def _calculate_device_distribution(self, results: List[Dict]) -> Dict:
        """Calculate the distribution of device types across sessions."""
        devices = []
        for r in results:
            ua = r.get("user_agent", "").lower()
            if "ipad" in ua or "tablet" in ua:
                devices.append("tablet")
            elif "mobile" in ua or "android" in ua or "iphone" in ua:
                devices.append("mobile")
            else:
                devices.append("desktop")

        counter = Counter(devices)
        total = len(devices) or 1

        return {
            device: {
                "count": count,
                "percentage": round(count / total * 100, 1),
            }
            for device, count in counter.most_common()
        }
