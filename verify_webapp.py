import asyncio
from playwright.async_api import async_playwright
import os
import subprocess
import time

async def run():
    # Start the server in the background

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Mock Telegram WebApp
        await page.add_init_script("""
            window.Telegram = {
                WebApp: {
                    ready: () => {},
                    expand: () => {},
                    initDataUnsafe: { user: { id: 12345 } },
                    MainButton: { show: () => {}, hide: () => {}, onClick: () => {}, setText: () => {} },
                    showAlert: (msg) => console.log('ALERT:', msg),
                    showConfirm: (msg, cb) => cb(true),
                    HapticFeedback: { impactOccurred: () => {} }
                }
            };
        """)

        try:
            print("Navigating to WebApp...")
            await page.goto("http://localhost:5000/inventory?uid=12345")

            # Wait for loader to be removed (min 8s) or skip
            print("Waiting for data to load...")
            await page.wait_for_selector("#profile-name", timeout=15000)

            # Skip video if still there
            if await page.is_visible("#eidos-loader"):
                 await page.evaluate("window.forceCloseLoader()")

            await asyncio.sleep(2)
            await page.screenshot(path="webapp_inventory.png")
            print("Inventory screenshot taken.")

            # Navigate to Shop
            print("Navigating to Shop...")
            await page.click(".nexus-tile:nth-child(3)")
            await asyncio.sleep(1)
            await page.screenshot(path="webapp_shop.png")
            print("Shop screenshot taken.")

            # Navigate to Terminal (Social/AI)
            print("Navigating to Terminal...")
            await page.click(".nexus-tile:nth-child(6)")
            await asyncio.sleep(1)
            await page.screenshot(path="webapp_social.png")
            print("Social screenshot taken.")

            # Check for specific elements
            name = await page.inner_text("#profile-name")
            print(f"Profile Name found: {name}")

        except Exception as e:
            print(f"Error during verification: {e}")
            # Get page source for debugging
            # print(await page.content())
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
