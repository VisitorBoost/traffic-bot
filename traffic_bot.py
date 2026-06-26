#!/usr/bin/env python3
"""
Traffic Bot - Main Entry Point
A powerful, open-source traffic bot and website traffic generator.

Usage:
    python traffic_bot.py --url "https://your-website.com" --sessions 100
    python traffic_bot.py --config config.yaml
    python traffic_bot.py --url "https://your-website.com" --proxy-file proxies.txt --sessions 500
"""

import argparse
import asyncio
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import load_config, override_config
from core.engine import TrafficBotEngine
from reports.dashboard import LiveDashboard
from reports.reporter import SessionReporter


def setup_logging(config: dict):
    """Configure logging based on configuration."""
    output_config = config.get("output", {})
    log_level = getattr(logging, output_config.get("log_level", "INFO").upper())
    log_file = output_config.get("log_file", "traffic_bot.log")

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger
    root_logger = logging.getLogger("traffic_bot")
    root_logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    if output_config.get("logging", True):
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="traffic_bot",
        description=(
            "Traffic Bot - A powerful website traffic generator with "
            "realistic human behavior simulation, proxy rotation, and "
            "comprehensive analytics."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url "https://example.com" --sessions 50
  %(prog)s --config config.yaml
  %(prog)s --url "https://example.com" --proxy-file proxies.txt --sessions 200 --concurrent 20
  %(prog)s --url "https://example.com" --sessions 10 --no-headless
        """,
    )

    # Required arguments (one of url or config)
    parser.add_argument(
        "--url",
        type=str,
        help="Target website URL to generate traffic for",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)",
    )

    # Session settings
    parser.add_argument(
        "--sessions",
        type=int,
        help="Total number of sessions to generate",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        help="Maximum number of concurrent sessions",
    )

    # Proxy settings
    parser.add_argument(
        "--proxy-file",
        type=str,
        help="Path to proxy list file (one proxy per line)",
    )

    # Browser settings
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (not headless)",
    )

    # Output settings
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging verbosity level",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable live terminal dashboard",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Path to save the JSON session report",
    )

    return parser.parse_args()


async def main():
    """Main execution function."""
    args = parse_arguments()

    # Load configuration
    config = load_config(args.config)

    # Apply CLI overrides
    overrides = {}
    if args.url:
        overrides["url"] = args.url
    if args.sessions:
        overrides["sessions"] = args.sessions
    if args.concurrent:
        overrides["concurrent"] = args.concurrent
    if args.proxy_file:
        overrides["proxy_file"] = args.proxy_file
    if args.no_headless:
        overrides["headless"] = False
    if args.log_level:
        overrides["log_level"] = args.log_level

    config = override_config(config, **overrides)

    if args.no_dashboard:
        config["output"]["dashboard"] = False
    if args.report:
        config["output"]["report_file"] = args.report

    # Setup logging
    logger = setup_logging(config)

    # Validate that we have a target URL
    target_url = config.get("target", {}).get("url", "")
    if not target_url or target_url == "https://example.com":
        logger.error(
            "No target URL specified. Use --url or set target.url in config.yaml"
        )
        sys.exit(1)

    # Print banner
    print_banner(config)

    # Initialize and run the engine
    engine = TrafficBotEngine(config)

    # Run with or without dashboard
    if config.get("output", {}).get("dashboard", True):
        dashboard = LiveDashboard(config)
        dashboard.start()
        try:
            results = await engine.run()
        finally:
            dashboard.stop()
    else:
        results = await engine.run()

    # Generate report
    reporter = SessionReporter(config)
    summary = engine.get_summary()
    reporter.save_report(results, summary)
    reporter.print_summary(summary)

    return results


def print_banner(config: dict):
    """Print the traffic bot startup banner."""
    target = config.get("target", {}).get("url", "N/A")
    sessions = config.get("sessions", {}).get("total", 0)
    concurrent = config.get("sessions", {}).get("concurrent", 0)
    proxy_enabled = config.get("proxy", {}).get("enabled", False)

    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                     🚦 TRAFFIC BOT                          ║
║          Website Traffic Generator v1.0.0                   ║
╠══════════════════════════════════════════════════════════════╣
║  Target:      {target:<45}║
║  Sessions:    {sessions:<45}║
║  Concurrent:  {concurrent:<45}║
║  Proxies:     {"Enabled" if proxy_enabled else "Disabled":<45}║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


if __name__ == "__main__":
    asyncio.run(main())
