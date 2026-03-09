const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const content = `
    <html>
      <head>
        <title>Test Items</title>
        <script>
          window.Telegram = { WebApp: { HapticFeedback: { impactOccurred: () => {}, selectionChanged: () => {} } } };
        </script>
      </head>
      <body>
        <div id="root"></div>
        <script type="module" src="./dist/assets/index.js"></script>
      </body>
    </html>
  `;

  await page.setContent(content);
  await page.screenshot({ path: 'test-results/items-test.png' });

  await browser.close();
})();
