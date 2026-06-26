"""
Traffic Bot Core Engine
Handles browser session management, page navigation, and human behavior simulation.
"""

import asyncio
import random
import time
import logging
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from utils.user_agents import get_random_user_agent
from utils.referrers import get_random_referrer
from utils.proxies import ProxyManager

logger = logging.getLogger("traffic_bot.engine")


class HumanBehavior:
    """Simulates realistic human browsing behavior on a page."""

    def __init__(self, config: Dict):
        self.config = config
        self.behavior_config = config.get("behavior", {})

    async def random_delay(self, min_sec: float = None, max_sec: float = None):
        """Wait a random amount of time to simulate human reading/thinking."""
        min_sec = min_sec or self.config.get("sessions", {}).get("delay_min", 10)
        max_sec = max_sec or self.config.get("sessions", {}).get("delay_max", 60)
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
        return delay

    async def simulate_mouse_movement(self, page: Page):
        """Simulate natural mouse cursor movements across the page."""
        if not self.behavior_config.get("mouse_movement", True):
            return

        viewport = page.viewport_size
        if not viewport:
            return

        width = viewport["width"]
        height = viewport["height"]

        # Generate 3-7 random mouse movements
        num_movements = random.randint(3, 7)
        for _ in range(num_movements):
            x = random.randint(50, width - 50)
            y = random.randint(50, height - 50)
            # Move with slight delay to simulate natural movement
            await page.mouse.move(x, y, steps=random.randint(5, 15))
            await asyncio.sleep(random.uniform(0.1, 0.5))

    async def simulate_scroll(self, page: Page):
        """Simulate human-like scrolling behavior."""
        if not self.behavior_config.get("scroll", True):
            return

        scroll_speed = self.behavior_config.get("scroll_speed", "random")

        # Determine scroll parameters based on speed setting
        speed_map = {
            "slow": (100, 300, 0.5, 1.5),
            "medium": (200, 500, 0.3, 0.8),
            "fast": (400, 800, 0.1, 0.4),
            "random": (100, 800, 0.1, 1.5),
        }
        min_px, max_px, min_pause, max_pause = speed_map.get(
            scroll_speed, speed_map["random"]
        )

        # Get page height
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = page.viewport_size["height"] if page.viewport_size else 800
        max_scroll = page_height - viewport_height

        if max_scroll <= 0:
            return

        # Scroll down in increments (like a human reading)
        current_position = 0
        scroll_target = random.uniform(0.4, 0.95) * max_scroll

        while current_position < scroll_target:
            scroll_amount = random.randint(min_px, max_px)
            current_position += scroll_amount

            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(min_pause, max_pause))

            # Occasionally scroll up slightly (natural behavior)
            if random.random() < 0.15:
                scroll_back = random.randint(50, 150)
                await page.evaluate(f"window.scrollBy(0, -{scroll_back})")
                current_position -= scroll_back
                await asyncio.sleep(random.uniform(0.3, 1.0))

    async def simulate_click(self, page: Page):
        """Click on random internal links on the page."""
        if not self.behavior_config.get("click_links", True):
            return None

        try:
            # Find all clickable internal links
            links = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a[href]');
                    const internal = [];
                    const currentHost = window.location.hostname;
                    for (const link of links) {
                        try {
                            const url = new URL(link.href);
                            if (url.hostname === currentHost && 
                                !link.href.includes('#') &&
                                !link.href.includes('javascript:') &&
                                !link.href.includes('mailto:') &&
                                !link.href.includes('tel:') &&
                                link.offsetParent !== null) {
                                internal.push(link.href);
                            }
                        } catch(e) {}
                    }
                    return [...new Set(internal)];
                }
            """)

            if links:
                chosen_link = random.choice(links)
                logger.debug(f"Clicking internal link: {chosen_link}")
                return chosen_link
        except Exception as e:
            logger.debug(f"Could not find clickable links: {e}")

        return None

    async def random_pause(self):
        """Short random pause simulating thinking/reading."""
        if self.behavior_config.get("random_pauses", True):
            await asyncio.sleep(random.uniform(0.5, 3.0))


class BotSession:
    """Represents a single browser session with full lifecycle management."""

    def __init__(
        self,
        session_id: int,
        config: Dict,
        proxy_manager: Optional[ProxyManager] = None,
    ):
        self.session_id = session_id
        self.config = config
        self.proxy_manager = proxy_manager
        self.behavior = HumanBehavior(config)
        self.stats = {
            "pages_visited": 0,
            "total_time": 0,
            "start_time": None,
            "end_time": None,
            "referrer": None,
            "user_agent": None,
            "proxy": None,
            "status": "pending",
            "errors": [],
        }

    def _get_viewport_size(self) -> Dict[str, int]:
        """Get a realistic viewport size based on device configuration."""
        devices = self.config.get("devices", {})
        desktop_pct = devices.get("desktop_percent", 60)
        mobile_pct = devices.get("mobile_percent", 30)

        roll = random.randint(1, 100)

        if roll <= desktop_pct:
            # Desktop viewports
            viewports = [
                {"width": 1920, "height": 1080},
                {"width": 1366, "height": 768},
                {"width": 1536, "height": 864},
                {"width": 1440, "height": 900},
                {"width": 1280, "height": 720},
                {"width": 2560, "height": 1440},
            ]
        elif roll <= desktop_pct + mobile_pct:
            # Mobile viewports
            viewports = [
                {"width": 390, "height": 844},   # iPhone 14
                {"width": 393, "height": 852},   # iPhone 15
                {"width": 412, "height": 915},   # Samsung Galaxy S21
                {"width": 360, "height": 800},   # Generic Android
                {"width": 414, "height": 896},   # iPhone 11
                {"width": 375, "height": 812},   # iPhone X
            ]
        else:
            # Tablet viewports
            viewports = [
                {"width": 768, "height": 1024},  # iPad
                {"width": 820, "height": 1180},  # iPad Air
                {"width": 1024, "height": 1366}, # iPad Pro
                {"width": 800, "height": 1280},  # Android Tablet
            ]

        return random.choice(viewports)

    async def run(self) -> Dict:
        """Execute the full browser session."""
        self.stats["start_time"] = time.time()
        self.stats["status"] = "running"

        # Get session configuration
        user_agent = get_random_user_agent(self.config)
        referrer = get_random_referrer(self.config)
        proxy = self.proxy_manager.get_proxy() if self.proxy_manager else None
        viewport = self._get_viewport_size()

        self.stats["user_agent"] = user_agent
        self.stats["referrer"] = referrer
        self.stats["proxy"] = proxy.get("server", "direct") if proxy else "direct"

        target_url = self.config.get("target", {}).get("url", "")
        pages_min = self.config.get("sessions", {}).get("pages_per_session_min", 1)
        pages_max = self.config.get("sessions", {}).get("pages_per_session_max", 6)
        target_pages = random.randint(pages_min, pages_max)

        try:
            async with async_playwright() as p:
                # Launch browser with options
                launch_options = {
                    "headless": self.config.get("browser", {}).get("headless", True),
                }
                if proxy:
                    launch_options["proxy"] = proxy

                browser = await p.chromium.launch(**launch_options)

                # Create context with realistic settings
                context_options = {
                    "viewport": viewport,
                    "user_agent": user_agent,
                    "locale": random.choice(["en-US", "en-GB", "en-CA", "en-AU"]),
                    "timezone_id": random.choice([
                        "America/New_York", "America/Chicago",
                        "America/Los_Angeles", "Europe/London",
                        "Europe/Berlin", "Australia/Sydney",
                    ]),
                }

                # Add extra HTTP headers for referrer
                if referrer:
                    context_options["extra_http_headers"] = {
                        "Referer": referrer,
                    }

                context = await browser.new_context(**context_options)

                # Enable JavaScript and cookies
                page = await context.new_page()

                # Navigate to target URL
                logger.info(
                    f"Session {self.session_id}: Navigating to {target_url} "
                    f"(referrer: {referrer or 'direct'})"
                )

                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                self.stats["pages_visited"] += 1

                # Simulate human behavior on first page
                await self.behavior.random_pause()
                await self.behavior.simulate_mouse_movement(page)
                await self.behavior.simulate_scroll(page)
                await self.behavior.random_delay()

                # Navigate to additional pages
                for i in range(target_pages - 1):
                    next_url = await self.behavior.simulate_click(page)

                    if next_url:
                        try:
                            await page.goto(
                                next_url, wait_until="domcontentloaded", timeout=20000
                            )
                            self.stats["pages_visited"] += 1
                            logger.debug(
                                f"Session {self.session_id}: Visited page "
                                f"{self.stats['pages_visited']}: {next_url}"
                            )

                            # Simulate behavior on new page
                            await self.behavior.random_pause()
                            await self.behavior.simulate_mouse_movement(page)
                            await self.behavior.simulate_scroll(page)
                            await self.behavior.random_delay(
                                min_sec=5, max_sec=30
                            )
                        except Exception as e:
                            logger.debug(
                                f"Session {self.session_id}: "
                                f"Failed to navigate to {next_url}: {e}"
                            )
                            break
                    else:
                        # No internal links found, try configured pages
                        configured_pages = (
                            self.config.get("target", {}).get("pages", [])
                        )
                        if configured_pages:
                            next_path = random.choice(configured_pages)
                            full_url = target_url.rstrip("/") + next_path
                            try:
                                await page.goto(
                                    full_url,
                                    wait_until="domcontentloaded",
                                    timeout=20000,
                                )
                                self.stats["pages_visited"] += 1
                                await self.behavior.simulate_scroll(page)
                                await self.behavior.random_delay(
                                    min_sec=5, max_sec=30
                                )
                            except Exception as e:
                                logger.debug(
                                    f"Session {self.session_id}: "
                                    f"Failed to visit {full_url}: {e}"
                                )
                                break
                        else:
                            break

                # Close browser
                await context.close()
                await browser.close()

                self.stats["status"] = "completed"

        except Exception as e:
            self.stats["status"] = "failed"
            self.stats["errors"].append(str(e))
            logger.error(f"Session {self.session_id} failed: {e}")

        self.stats["end_time"] = time.time()
        self.stats["total_time"] = self.stats["end_time"] - self.stats["start_time"]

        logger.info(
            f"Session {self.session_id}: {self.stats['status']} - "
            f"{self.stats['pages_visited']} pages in "
            f"{self.stats['total_time']:.1f}s"
        )

        return self.stats


class TrafficBotEngine:
    """Main engine that orchestrates multiple browser sessions."""

    def __init__(self, config: Dict):
        self.config = config
        self.proxy_manager = None
        self.results: List[Dict] = []
        self.start_time = None
        self.end_time = None

        # Initialize proxy manager if proxies are configured
        proxy_config = config.get("proxy", {})
        if proxy_config.get("enabled", False):
            self.proxy_manager = ProxyManager(proxy_config)

    async def run(self) -> List[Dict]:
        """Run all sessions with configured concurrency."""
        session_config = self.config.get("sessions", {})
        total_sessions = session_config.get("total", 10)
        concurrent = session_config.get("concurrent", 5)

        logger.info(
            f"Starting Traffic Bot: {total_sessions} sessions, "
            f"{concurrent} concurrent"
        )
        self.start_time = time.time()

        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrent)

        async def run_session(session_id: int):
            async with semaphore:
                session = BotSession(
                    session_id=session_id,
                    config=self.config,
                    proxy_manager=self.proxy_manager,
                )
                result = await session.run()
                self.results.append(result)
                return result

        # Run all sessions
        tasks = [run_session(i + 1) for i in range(total_sessions)]
        await asyncio.gather(*tasks, return_exceptions=True)

        self.end_time = time.time()
        total_time = self.end_time - self.start_time

        logger.info(
            f"Traffic Bot completed: {len(self.results)} sessions in "
            f"{total_time:.1f}s"
        )

        return self.results

    def get_summary(self) -> Dict:
        """Get a summary of all session results."""
        if not self.results:
            return {"status": "no results"}

        completed = [r for r in self.results if r["status"] == "completed"]
        failed = [r for r in self.results if r["status"] == "failed"]

        total_pages = sum(r["pages_visited"] for r in self.results)
        total_time = sum(r["total_time"] for r in self.results)
        avg_time = total_time / len(self.results) if self.results else 0
        avg_pages = total_pages / len(self.results) if self.results else 0

        return {
            "total_sessions": len(self.results),
            "completed": len(completed),
            "failed": len(failed),
            "total_pages_visited": total_pages,
            "average_session_time": round(avg_time, 2),
            "average_pages_per_session": round(avg_pages, 2),
            "total_run_time": round(
                (self.end_time - self.start_time) if self.end_time else 0, 2
            ),
        }
