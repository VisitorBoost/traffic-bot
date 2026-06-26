"""
Configuration Management Module
Loads and validates YAML configuration files, with support for
command-line argument overrides.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("traffic_bot.config")

# Default configuration values
DEFAULT_CONFIG = {
    "target": {
        "url": "https://example.com",
        "pages": [],
    },
    "sessions": {
        "total": 10,
        "concurrent": 5,
        "delay_min": 10,
        "delay_max": 60,
        "pages_per_session_min": 1,
        "pages_per_session_max": 4,
    },
    "browser": {
        "headless": True,
        "timeout": 30000,
    },
    "behavior": {
        "scroll": True,
        "scroll_speed": "random",
        "click_links": True,
        "mouse_movement": True,
        "random_pauses": True,
    },
    "referrers": {
        "organic_search_percent": 40,
        "social_percent": 25,
        "referral_percent": 20,
        "direct_percent": 15,
        "keywords": [
            "traffic bot",
            "website traffic generator",
            "web traffic tool",
        ],
    },
    "devices": {
        "desktop_percent": 60,
        "mobile_percent": 30,
        "tablet_percent": 10,
    },
    "geo": {
        "countries": ["US", "UK", "CA", "AU"],
    },
    "proxy": {
        "enabled": False,
        "file": "proxies.txt",
        "rotation": "per_session",
        "type": "residential",
    },
    "output": {
        "logging": True,
        "log_file": "traffic_bot.log",
        "log_level": "INFO",
        "report_file": "report.json",
        "dashboard": True,
    },
}


def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Load configuration from a YAML file with fallback to defaults.
    
    Args:
        config_path: Path to the YAML configuration file.
        
    Returns:
        A merged configuration dictionary.
    """
    config = DEFAULT_CONFIG.copy()

    if config_path:
        path = Path(config_path)
        if path.exists():
            try:
                with open(path, "r") as f:
                    user_config = yaml.safe_load(f)

                if user_config:
                    config = _deep_merge(config, user_config)
                    logger.info(f"Configuration loaded from: {config_path}")
                else:
                    logger.warning(
                        f"Config file {config_path} is empty. Using defaults."
                    )
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML config: {e}")
                logger.info("Using default configuration.")
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                logger.info("Using default configuration.")
        else:
            logger.warning(
                f"Config file not found: {config_path}. Using defaults."
            )

    # Validate configuration
    _validate_config(config)

    return config


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Deep merge two dictionaries. Override values take precedence.
    
    Args:
        base: The base dictionary with default values.
        override: The override dictionary with user values.
        
    Returns:
        A new merged dictionary.
    """
    result = base.copy()

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _validate_config(config: Dict):
    """Validate configuration values and log warnings for issues."""
    # Validate target URL
    target_url = config.get("target", {}).get("url", "")
    if not target_url or target_url == "https://example.com":
        logger.warning(
            "Target URL is not set or is still the default. "
            "Please update 'target.url' in your config."
        )

    # Validate session counts
    sessions = config.get("sessions", {})
    if sessions.get("total", 0) < 1:
        logger.warning("Total sessions must be at least 1.")
        config["sessions"]["total"] = 1

    if sessions.get("concurrent", 0) < 1:
        logger.warning("Concurrent sessions must be at least 1.")
        config["sessions"]["concurrent"] = 1

    if sessions.get("concurrent", 5) > sessions.get("total", 10):
        config["sessions"]["concurrent"] = sessions["total"]

    # Validate referrer percentages
    referrers = config.get("referrers", {})
    total_pct = (
        referrers.get("organic_search_percent", 0)
        + referrers.get("social_percent", 0)
        + referrers.get("referral_percent", 0)
        + referrers.get("direct_percent", 0)
    )
    if total_pct != 100:
        logger.warning(
            f"Referrer percentages sum to {total_pct}%, not 100%. "
            "Traffic distribution may be uneven."
        )

    # Validate device percentages
    devices = config.get("devices", {})
    device_total = (
        devices.get("desktop_percent", 0)
        + devices.get("mobile_percent", 0)
        + devices.get("tablet_percent", 0)
    )
    if device_total != 100:
        logger.warning(
            f"Device percentages sum to {device_total}%, not 100%. "
            "Device distribution may be uneven."
        )


def override_config(config: Dict, **kwargs) -> Dict:
    """
    Override specific configuration values from CLI arguments.
    
    Args:
        config: The base configuration dictionary.
        **kwargs: Key-value pairs to override.
        
    Returns:
        Updated configuration dictionary.
    """
    if kwargs.get("url"):
        config["target"]["url"] = kwargs["url"]

    if kwargs.get("sessions"):
        config["sessions"]["total"] = kwargs["sessions"]

    if kwargs.get("concurrent"):
        config["sessions"]["concurrent"] = kwargs["concurrent"]

    if kwargs.get("proxy_file"):
        config["proxy"]["enabled"] = True
        config["proxy"]["file"] = kwargs["proxy_file"]

    if kwargs.get("headless") is not None:
        config["browser"]["headless"] = kwargs["headless"]

    if kwargs.get("log_level"):
        config["output"]["log_level"] = kwargs["log_level"]

    return config
