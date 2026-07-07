"""
Stealth browser fallback for career pages without public APIs.

Uses Camoufox (primary), Nodriver, or SeleniumBase UC Mode with optional
rotating residential proxies. Never scrape behind login walls or extract PII.
"""
from __future__ import annotations

import os
from typing import Callable

HEADERS = {"User-Agent": "JobHunt/1.0 (personal job search)"}


def get_proxy() -> dict | None:
    proxy_url = os.environ.get("PROXY_URL")
    if not proxy_url:
        return None
    return {"server": proxy_url}


def fetch_with_camoufox(url: str) -> str | None:
    """Fetch page HTML using Camoufox anti-detect browser."""
    try:
        from camoufox.sync_api import Camoufox

        proxy = get_proxy()
        opts = {"headless": True}
        if proxy:
            opts["proxy"] = proxy
        with Camoufox(**opts) as browser:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            return page.content()
    except ImportError:
        print("  ! camoufox not installed — pip install 'jobhunt[stealth]'")
    except Exception as e:
        print(f"  ! Camoufox fetch failed: {e}")
    return None


def fetch_with_seleniumbase(url: str) -> str | None:
    """Fetch page HTML using SeleniumBase UC Mode."""
    try:
        from seleniumbase import SB

        proxy = os.environ.get("PROXY_URL")
        with SB(uc=True, headless=True, proxy=proxy) as sb:
            sb.open(url)
            return sb.get_page_source()
    except ImportError:
        print("  ! seleniumbase not installed — pip install 'jobhunt[stealth]'")
    except Exception as e:
        print(f"  ! SeleniumBase fetch failed: {e}")
    return None


def fetch_with_nodriver(url: str) -> str | None:
    """Fetch page HTML using Nodriver CDP."""
    try:
        import nodriver as uc

        async def _run():
            browser = await uc.start(headless=True)
            page = await browser.get(url)
            return await page.get_content()

        import asyncio
        return asyncio.run(_run())
    except ImportError:
        print("  ! nodriver not installed")
    except Exception as e:
        print(f"  ! Nodriver fetch failed: {e}")
    return None


FETCHERS: list[tuple[str, Callable[[str], str | None]]] = [
    ("camoufox", fetch_with_camoufox),
    ("seleniumbase", fetch_with_seleniumbase),
    ("nodriver", fetch_with_nodriver),
]


def stealth_fetch(url: str) -> str | None:
    """Try stealth fetchers in order until one succeeds."""
    for name, fn in FETCHERS:
        html = fn(url)
        if html:
            print(f"  stealth:{name} ok for {url[:60]}...")
            return html
    return None
