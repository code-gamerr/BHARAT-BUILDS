const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  const logs = [];
  page.on("console", (msg) => logs.push(`[${msg.type()}] ${msg.text()}`));
  page.on("pageerror", (err) => errors.push(String(err)));
  page.on("requestfailed", (req) => errors.push(`REQFAIL ${req.url()} ${req.failure()?.errorText}`));

  await page.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2000);
  const body = await page.locator("body").innerText().catch(() => "");
  const html = await page.content();
  console.log("TITLE", await page.title());
  console.log("BODY_SNIP", body.slice(0, 800));
  console.log("HAS_ROOT", html.includes('id="root"'));
  console.log("ROOT_CHILDREN", await page.locator("#root > *").count());
  console.log("ERRORS", JSON.stringify(errors, null, 2));
  console.log("LOGS", JSON.stringify(logs.filter((l) => l.includes("error") || l.includes("Error") || l.startsWith("[error]")).slice(0, 30), null, 2));
  await page.screenshot({ path: "debug-ui.png", fullPage: true });
  console.log("SCREENSHOT debug-ui.png");
  await browser.close();
})().catch((e) => {
  console.error("SCRIPT_FAIL", e);
  process.exit(1);
});
