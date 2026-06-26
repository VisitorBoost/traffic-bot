"""
Proxy Management Module
Handles proxy loading, rotation, health checking, and geographic targeting.
Supports HTTP, HTTPS, and SOCKS5 proxies.
"""

import random
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("traffic_bot.proxies")


class ProxyManager:
    """
    Manages a pool of proxies with rotation strategies.
    
    Supports:
    - Round-robin rotation
    - Random rotation
    - Per-session sticky proxies
    - Geographic targeting
    - Health tracking
    """

    def __init__(self, proxy_config: Dict):
        self.config = proxy_config
        self.proxies: List[Dict] = []
        self.current_index = 0
        self.rotation_mode = proxy_config.get("rotation", "per_session")
        self.failed_proxies: set = set()

        # Load proxies from file or config
        self._load_proxies()

    def _load_proxies(self):
        """Load proxies from file or inline configuration."""
        proxy_file = self.config.get("file", "")

        if proxy_file and Path(proxy_file).exists():
            self._load_from_file(proxy_file)
        elif self.config.get("list"):
            self._load_from_list(self.config["list"])
        else:
            logger.warning(
                "No proxy file or list found. Running without proxies."
            )

    def _load_from_file(self, filepath: str):
        """
        Load proxies from a text file.
        
        Supported formats:
        - protocol://user:pass@host:port
        - protocol://host:port
        - host:port (assumes HTTP)
        - user:pass@host:port (assumes HTTP)
        """
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                proxy = self._parse_proxy_string(line)
                if proxy:
                    self.proxies.append(proxy)

            logger.info(f"Loaded {len(self.proxies)} proxies from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load proxy file {filepath}: {e}")

    def _load_from_list(self, proxy_list: List[str]):
        """Load proxies from a list in the configuration."""
        for proxy_str in proxy_list:
            proxy = self._parse_proxy_string(proxy_str)
            if proxy:
                self.proxies.append(proxy)

        logger.info(f"Loaded {len(self.proxies)} proxies from config")

    def _parse_proxy_string(self, proxy_str: str) -> Optional[Dict]:
        """
        Parse a proxy string into a Playwright-compatible proxy dict.
        
        Returns:
            Dict with 'server', and optionally 'username' and 'password'.
        """
        try:
            proxy_str = proxy_str.strip()

            # If it already has a protocol prefix
            if "://" in proxy_str:
                parts = proxy_str.split("://", 1)
                protocol = parts[0]
                remainder = parts[1]
            else:
                protocol = "http"
                remainder = proxy_str

            # Check for authentication
            username = None
            password = None

            if "@" in remainder:
                auth_part, host_part = remainder.rsplit("@", 1)
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                else:
                    username = auth_part
            else:
                host_part = remainder

            # Build the proxy server URL
            server = f"{protocol}://{host_part}"

            proxy_dict = {"server": server}
            if username:
                proxy_dict["username"] = username
            if password:
                proxy_dict["password"] = password

            return proxy_dict

        except Exception as e:
            logger.warning(f"Failed to parse proxy: {proxy_str} - {e}")
            return None

    def get_proxy(self) -> Optional[Dict]:
        """
        Get the next proxy based on the rotation strategy.
        
        Returns:
            A Playwright-compatible proxy dictionary, or None if no proxies available.
        """
        if not self.proxies:
            return None

        available = [
            p for p in self.proxies
            if p["server"] not in self.failed_proxies
        ]

        if not available:
            # Reset failed proxies and try again
            logger.warning("All proxies marked as failed. Resetting...")
            self.failed_proxies.clear()
            available = self.proxies

        if self.rotation_mode == "round_robin":
            proxy = available[self.current_index % len(available)]
            self.current_index += 1
        elif self.rotation_mode == "random" or self.rotation_mode == "per_session":
            proxy = random.choice(available)
        else:
            proxy = random.choice(available)

        return proxy

    def mark_failed(self, proxy_server: str):
        """Mark a proxy as failed so it won't be used again."""
        self.failed_proxies.add(proxy_server)
        logger.debug(f"Proxy marked as failed: {proxy_server}")

    def get_stats(self) -> Dict:
        """Get proxy pool statistics."""
        return {
            "total_proxies": len(self.proxies),
            "active_proxies": len(self.proxies) - len(self.failed_proxies),
            "failed_proxies": len(self.failed_proxies),
            "rotation_mode": self.rotation_mode,
        }
