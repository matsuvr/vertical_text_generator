import asyncio
import os
from pathlib import Path

import requests

# PlaywrightでHTMLを画像化
from playwright.async_api import async_playwright


def fetch_html(url: str) -> str:
    token = os.getenv(
        "API_TOKEN", "d85e469dfe0551ae45cc90413ddf9b5923eb5761ec24cf49b799bd08f3d8e264"
    )
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text


async def html_to_png(html: str, out_path: str, width: int = 600, height: int = 800):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.set_content(html, wait_until="domcontentloaded")
        await page.wait_for_timeout(500)
        await page.screenshot(path=out_path, full_page=True)
        await browser.close()


def main():
    url = "http://192.168.1.45:8000/debug/html?text=%E3%81%93%E3%82%8C%E3%81%AF%E2%80%95%E2%80%95%E3%83%86%E3%82%B9%E3%83%88%E2%80%94%E2%80%94%E3%81%A7%E3%81%99%E3%80%82%E6%AC%A1%E3%81%AE%E8%A1%8C%E3%81%AF%E2%94%80%E2%94%80%E7%BD%AB%E7%B7%9A%E2%94%80%E2%94%80%E3%81%AE%E7%A2%BA%E8%AA%8D%E3%80%82&font_size=24"
    html = fetch_html(url)
    out_path = Path("test_output/debug_html_capture.png")
    out_path.parent.mkdir(exist_ok=True)
    asyncio.run(html_to_png(html, str(out_path)))
    print(f"画像を保存しました: {out_path}")


if __name__ == "__main__":
    main()
