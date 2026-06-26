const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const APP_URL = process.env.STREAMLIT_URL || 'http://localhost:8501';
const ARTIFACTS = path.resolve('demo_artifacts');
const UPLOAD_FILE = path.resolve('demo_assets/invoice_demo.json');

fs.mkdirSync(ARTIFACTS, { recursive: true });

async function waitForText(page, text, timeout = 180000) {
  await page.getByText(text, { exact: false }).first().waitFor({ timeout });
}

async function clickByText(page, text) {
  await page.getByText(text, { exact: false }).first().click();
}

(async () => {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 350,
  });

  const context = await browser.newContext({
    viewport: { width: 1600, height: 950 },
    recordVideo: {
      dir: ARTIFACTS,
      size: { width: 1600, height: 950 },
    },
  });

  const page = await context.newPage();

  console.log(`[demo] opening ${APP_URL}`);
  await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 60000 });
  await page.screenshot({ path: path.join(ARTIFACTS, '01-home.png'), fullPage: true });

  console.log('[demo] looking for upload input');
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.waitFor({ state: 'attached', timeout: 30000 });
  await fileInput.setInputFiles(UPLOAD_FILE, { timeout: 30000 });

  await page.screenshot({ path: path.join(ARTIFACTS, '02-file-uploaded.png'), fullPage: true });

  console.log('[demo] clicking upload/analyze button');
  const uploadButtons = [
    'Upload & Analyze',
    'Analyze uploaded document',
    'Analyze document',
    'Assess uploaded document',
    'Run upload assessment',
    'Publish uploaded document',
    'Run agent + publish',
  ];

  let clicked = false;
  for (const label of uploadButtons) {
    const btn = page.getByText(label, { exact: false }).first();
    if (await btn.count().catch(() => 0)) {
      try {
        await btn.click({ timeout: 3000 });
        clicked = true;
        console.log(`[demo] clicked button: ${label}`);
        break;
      } catch (_) {}
    }
  }

  if (!clicked) {
    const buttons = await page.locator('button').allTextContents();
    console.log('[demo] visible buttons:', buttons);
    throw new Error('Could not find upload/analyze button. Update scripts/record_streamlit_demo.js with the exact button label.');
  }

  console.log('[demo] waiting for document hash / risk output');
  await Promise.race([
    waitForText(page, 'sha256:', 180000),
    waitForText(page, 'Risk score', 180000),
    waitForText(page, 'Evidence hash', 180000),
  ]);

  await page.screenshot({ path: path.join(ARTIFACTS, '03-risk-result.png'), fullPage: true });

  console.log('[demo] waiting for Casper result');
  await Promise.race([
    waitForText(page, 'Real Casper', 240000),
    waitForText(page, 'submitted', 240000),
    waitForText(page, 'Transaction hash', 240000),
    waitForText(page, 'Explorer', 240000),
  ]);

  await page.screenshot({ path: path.join(ARTIFACTS, '04-casper-result.png'), fullPage: true });

  const pageText = await page.locator('body').innerText();
  const txMatch = pageText.match(/[a-f0-9]{64}/i);
  const explorerMatch = pageText.match(/https:\/\/testnet\.cspr\.live\/deploy\/[a-f0-9]{64}/i);

  const summary = {
    detected_tx_hash: txMatch ? txMatch[0] : null,
    detected_explorer_url: explorerMatch ? explorerMatch[0] : null,
    recorded_at: new Date().toISOString(),
  };

  fs.writeFileSync(
    path.join(ARTIFACTS, 'demo-summary.json'),
    JSON.stringify(summary, null, 2)
  );

  console.log('[demo] summary:', summary);

  const explorerUrl =
    summary.detected_explorer_url ||
    (summary.detected_tx_hash ? `https://testnet.cspr.live/deploy/${summary.detected_tx_hash}` : null);

  if (explorerUrl) {
    console.log(`[demo] opening explorer ${explorerUrl}`);
    const explorer = await context.newPage();
    await explorer.goto(explorerUrl, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await explorer.waitForTimeout(8000);
    await explorer.screenshot({ path: path.join(ARTIFACTS, '05-explorer.png'), fullPage: true });
  } else {
    console.warn('[demo] no explorer URL detected in page text');
  }

  await page.waitForTimeout(3000);
  await context.close();
  await browser.close();

  const videos = fs.readdirSync(ARTIFACTS).filter((f) => f.endsWith('.webm'));
  console.log('[demo] video files:', videos.map((v) => path.join(ARTIFACTS, v)));
})();
