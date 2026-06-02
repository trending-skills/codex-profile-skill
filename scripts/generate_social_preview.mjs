import { createRequire } from "node:module";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const rootDir = process.cwd();
const inputPath = resolve(rootDir, process.argv[2] || "social-preview.html");
const outputPath = resolve(rootDir, process.argv[3] || "social-preview.png");

function loadPlaywright() {
  const candidates = [process.env.PLAYWRIGHT_MODULE_PATH, "playwright", "playwright-core"].filter(Boolean);

  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (error) {
      if (candidate === process.env.PLAYWRIGHT_MODULE_PATH) {
        console.warn(`Could not load PLAYWRIGHT_MODULE_PATH: ${candidate}`);
      }
    }
  }

  throw new Error(
    "Playwright is required to export the social preview image. Install it with `npm install -D playwright` and `npx playwright install chromium`, or set PLAYWRIGHT_MODULE_PATH to an existing Playwright module."
  );
}

if (!existsSync(inputPath)) {
  console.error(`Preview template not found: ${inputPath}`);
  process.exit(1);
}

const { chromium } = loadPlaywright();
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage({
    viewport: { width: 1200, height: 630 },
    deviceScaleFactor: 1,
  });

  await page.goto(pathToFileURL(inputPath).href, { waitUntil: "load" });
  await page.screenshot({
    path: outputPath,
    fullPage: false,
  });

  console.log(`Generated ${outputPath}`);
} finally {
  await browser.close();
}
