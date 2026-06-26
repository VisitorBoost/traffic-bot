"""
Referrer Management Module
Generates realistic HTTP Referer headers to simulate traffic from various sources
including organic search, social media, referral sites, and direct visits.
"""

import random
from typing import Dict, Optional

# Search engine referrer templates
SEARCH_REFERRERS = {
    "google": [
        "https://www.google.com/",
        "https://www.google.com/search?q={keyword}",
        "https://www.google.co.uk/search?q={keyword}",
        "https://www.google.ca/search?q={keyword}",
        "https://www.google.com.au/search?q={keyword}",
        "https://www.google.de/search?q={keyword}",
    ],
    "bing": [
        "https://www.bing.com/",
        "https://www.bing.com/search?q={keyword}",
    ],
    "duckduckgo": [
        "https://duckduckgo.com/",
        "https://duckduckgo.com/?q={keyword}",
    ],
    "yahoo": [
        "https://search.yahoo.com/",
        "https://search.yahoo.com/search?p={keyword}",
    ],
    "yandex": [
        "https://yandex.com/",
        "https://yandex.com/search/?text={keyword}",
    ],
}

# Social media referrer templates
SOCIAL_REFERRERS = {
    "facebook": [
        "https://www.facebook.com/",
        "https://l.facebook.com/",
        "https://lm.facebook.com/",
        "https://m.facebook.com/",
    ],
    "twitter": [
        "https://t.co/",
        "https://twitter.com/",
        "https://x.com/",
    ],
    "linkedin": [
        "https://www.linkedin.com/",
        "https://www.linkedin.com/feed/",
        "https://lnkd.in/",
    ],
    "reddit": [
        "https://www.reddit.com/",
        "https://old.reddit.com/",
    ],
    "pinterest": [
        "https://www.pinterest.com/",
        "https://pin.it/",
    ],
    "youtube": [
        "https://www.youtube.com/",
        "https://youtu.be/",
    ],
    "instagram": [
        "https://www.instagram.com/",
        "https://l.instagram.com/",
    ],
    "tiktok": [
        "https://www.tiktok.com/",
    ],
}

# Generic referral site templates
REFERRAL_SITES = [
    "https://www.medium.com/",
    "https://www.quora.com/",
    "https://news.ycombinator.com/",
    "https://www.producthunt.com/",
    "https://www.techcrunch.com/",
    "https://www.forbes.com/",
    "https://www.entrepreneur.com/",
    "https://www.inc.com/",
    "https://www.mashable.com/",
    "https://www.wired.com/",
    "https://www.theverge.com/",
    "https://www.businessinsider.com/",
    "https://www.huffpost.com/",
    "https://www.buzzfeed.com/",
    "https://www.cnet.com/",
    "https://www.zdnet.com/",
    "https://www.arstechnica.com/",
    "https://www.engadget.com/",
    "https://www.lifehacker.com/",
    "https://www.makeuseof.com/",
]

# Default search keywords (used when no custom keywords are provided)
DEFAULT_KEYWORDS = [
    "traffic bot",
    "website traffic generator",
    "web traffic bot",
    "increase website traffic",
    "traffic generation tool",
    "automated traffic",
    "website visitors",
    "organic traffic",
    "boost website traffic",
    "web automation",
    "SEO traffic",
    "buy website traffic",
    "traffic software",
    "website traffic tool",
    "generate web traffic",
]


def get_random_referrer(config: Dict) -> Optional[str]:
    """
    Generate a random referrer URL based on the configured distribution.
    
    Args:
        config: The full bot configuration dictionary.
        
    Returns:
        A referrer URL string, or None for direct traffic.
    """
    referrer_config = config.get("referrers", {})

    # Get distribution percentages
    organic_pct = referrer_config.get("organic_search_percent", 40)
    social_pct = referrer_config.get("social_percent", 25)
    referral_pct = referrer_config.get("referral_percent", 20)
    # direct_pct is the remainder (no referrer)

    # Get custom keywords if provided
    keywords = referrer_config.get("keywords", DEFAULT_KEYWORDS)

    roll = random.randint(1, 100)

    if roll <= organic_pct:
        return _generate_search_referrer(keywords)
    elif roll <= organic_pct + social_pct:
        return _generate_social_referrer()
    elif roll <= organic_pct + social_pct + referral_pct:
        return _generate_referral()
    else:
        # Direct traffic - no referrer
        return None


def _generate_search_referrer(keywords: list) -> str:
    """Generate a search engine referrer with a random keyword."""
    # Weight Google more heavily (realistic distribution)
    engine_weights = {
        "google": 75,
        "bing": 12,
        "duckduckgo": 5,
        "yahoo": 5,
        "yandex": 3,
    }

    engine = random.choices(
        list(engine_weights.keys()),
        weights=list(engine_weights.values()),
        k=1,
    )[0]

    templates = SEARCH_REFERRERS[engine]
    template = random.choice(templates)

    if "{keyword}" in template:
        keyword = random.choice(keywords)
        # URL-encode the keyword (basic encoding)
        keyword_encoded = keyword.replace(" ", "+")
        return template.format(keyword=keyword_encoded)

    return template


def _generate_social_referrer() -> str:
    """Generate a social media referrer."""
    # Weight platforms by realistic traffic share
    platform_weights = {
        "facebook": 30,
        "twitter": 20,
        "linkedin": 15,
        "reddit": 15,
        "pinterest": 8,
        "youtube": 7,
        "instagram": 3,
        "tiktok": 2,
    }

    platform = random.choices(
        list(platform_weights.keys()),
        weights=list(platform_weights.values()),
        k=1,
    )[0]

    templates = SOCIAL_REFERRERS[platform]
    return random.choice(templates)


def _generate_referral() -> str:
    """Generate a referral site URL."""
    return random.choice(REFERRAL_SITES)
