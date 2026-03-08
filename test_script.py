import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

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

        await page.goto("http://localhost:5000/inventory?uid=12345")

        await page.wait_for_selector("#nexus-grid-content", timeout=15000)
        # Skip video if still there
        if await page.is_visible("#eidos-loader"):
             await page.evaluate("window.forceCloseLoader()")

        await asyncio.sleep(2)

        await page.screenshot(path="test_nexus.png")
        print("Done")
        await browser.close()

asyncio.run(run())
