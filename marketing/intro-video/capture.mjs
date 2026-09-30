import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const root = path.dirname(fileURLToPath(import.meta.url));
const mode = process.argv[2] || "preview";
const fps = 30;
const duration = 82.904;
const previewTimes = [2.8, 11.5, 18.6, 26.2, 37.4, 42.8, 53.2, 66.4, 78.6];
const chrome = process.env.CHROME_PATH || "/usr/bin/google-chrome";

const browser = await puppeteer.launch({
  executablePath: chrome,
  headless: "new",
  args: [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--force-color-profile=srgb",
    "--hide-scrollbars",
    "--font-render-hinting=none",
  ],
});
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
page.on("pageerror", (err) => console.error("PAGE", err.message));
await page.goto(pathToFileURL(path.join(root, "index.html")).href, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);
await new Promise((r) => setTimeout(r, 150));

async function shoot(t, file) {
  await page.evaluate((time) => window.seek(time), t);
  await page.screenshot({ path: file, type: "jpeg", quality: 92 });
}

if (mode === "preview") {
  const dir = path.join(root, "preview");
  fs.mkdirSync(dir, { recursive: true });
  for (const t of previewTimes) {
    const file = path.join(dir, `t${t.toFixed(1)}.jpg`);
    await shoot(t, file);
    console.log("wrote", file);
  }
} else if (mode === "one") {
  const t = parseFloat(process.argv[3] || "2.8");
  const file = process.argv[4] || path.join(root, "preview", "one.jpg");
  fs.mkdirSync(path.dirname(file), { recursive: true });
  await shoot(t, file);
} else {
  const dir = path.join(root, "frames");
  fs.mkdirSync(dir, { recursive: true });
  const n = Math.round(duration * fps);
  for (let i = 0; i < n; i++) {
    await shoot(i / fps, path.join(dir, `${String(i).padStart(5, "0")}.jpg`));
    if (i % 90 === 0) console.log(`${i}/${n}`);
  }
  console.log("frames", n);
}
await browser.close();
