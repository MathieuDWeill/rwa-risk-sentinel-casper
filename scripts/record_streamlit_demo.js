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

  console.log('[demo] clicking ASSESS RWA DOCUMENT');
  const assessButton = page.getByRole('button', { name: /ASSESS RWA DOCUMENT/i });
  await assessButton.scrollIntoViewIfNeeded({ timeout: 30000 });
  await assessButton.click({ timeout: 30000, force: true });
  console.log('[demo] clicked ASSESS RWA DOCUMENT');

  // Streamlit reruns after click. Give it time to start and finish.
  await page.waitForTimeout(3000);

  console.log('[demo] waiting for upload assessment output');

  try {
    await Promise.race([
      waitForText(page, 'ON-CHAIN PROOF REGISTERED', 300000),
      waitForText(page, 'Transaction Hash', 300000),
      waitForText(page, 'SHA-256 Document Hash', 300000),
      waitForText(page, 'Document Risk Profiling', 300000),
      waitForText(page, 'Casper Attestation Status', 300000),
      waitForText(page, 'Traceback', 300000),
      waitForText(page, 'Exception', 300000),
      waitForText(page, 'Error', 300000),
    ]);
  } catch (err) {
    const bodyText = await page.locator('body').innerText();
    fs.writeFileSync(path.join(ARTIFACTS, 'debug-body-timeout.txt'), bodyText);
    await page.screenshot({ path: path.join(ARTIFACTS, 'debug-timeout.png'), fullPage: true });
    throw err;
  }

  await page.screenshot({ path: path.join(ARTIFACTS, '03-risk-result.png'), fullPage: true });

  console.log('[demo] waiting specifically for Casper transaction hash');
  try {
    await waitForText(page, 'Transaction Hash', 300000);
  } catch (err) {
    const bodyText = await page.locator('body').innerText();
    fs.writeFileSync(path.join(ARTIFACTS, 'debug-no-transaction.txt'), bodyText);
    await page.screenshot({ path: path.join(ARTIFACTS, '04-no-transaction.png'), fullPage: true });
    throw err;
  }

  await page.screenshot({ path: path.join(ARTIFACTS, '04-casper-result.png'), fullPage: true });

  const pageText = await page.locator('body').innerText();

  const explorerMatch = pageText.match(/https:\/\/testnet\.cspr\.live\/deploy\/[a-f0-9]{64}/i);

  let txHash = null;

  const txLabelMatch = pageText.match(/Transaction Hash:\\s*([a-f0-9]{64})/i);
  if (txLabelMatch) {
    txHash = txLabelMatch[1];
  }

  if (!txHash) {
    const hashes = [...pageText.matchAll(/[a-f0-9]{64}/gi)].map((m) => m[0]);
    const uniqueHashes = [...new Set(hashes)];

    // Avoid picking the document SHA-256 shown under Cryptographic Verification.
    const documentHashMatch = pageText.match(/SHA-256 Document Hash:\\s*([a-f0-9]{64})/i);
    const documentHash = documentHashMatch ? documentHashMatch[1] : null;

    txHash = uniqueHashes.find((h) => h !== documentHash) || null;
  }

  const summary = {
    detected_tx_hash: txHash,
    detected_explorer_url: explorerMatch ? explorerMatch[0] : (txHash ? `https://testnet.cspr.live/deploy/${txHash}` : null),
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

  if (!explorerUrl) {
    const bodyText = await page.locator('body').innerText();
    fs.writeFileSync(path.join(ARTIFACTS, 'debug-no-explorer-url.txt'), bodyText);
    throw new Error('No explorer URL or transaction hash detected; refusing to open explorer.');
  }

  console.log(`[demo] opening CSPR.live search for tx ${summary.detected_tx_hash}`);

  const explorer = await context.newPage();
  await explorer.goto('https://testnet.cspr.live/', { waitUntil: 'domcontentloaded', timeout: 90000 });
  await explorer.waitForTimeout(5000);

  // Handle cookie banner if present.
  const accept = explorer.getByText('Accept', { exact: false }).first();
  if (await accept.count().catch(() => 0)) {
    try { await accept.click({ timeout: 3000 }); } catch (_) {}
  }

  const searchBox = explorer.locator('input[placeholder*="Search"], input[type="text"]').first();
  await searchBox.waitFor({ state: 'visible', timeout: 30000 });
  await searchBox.fill(summary.detected_tx_hash);
  await explorer.keyboard.press('Enter');

  await explorer.waitForTimeout(15000);
  await explorer.screenshot({ path: path.join(ARTIFACTS, '05-explorer.png'), fullPage: true });

  await page.waitForTimeout(3000);
  await context.close();
  await browser.close();

  const videos = fs.readdirSync(ARTIFACTS).filter((f) => f.endsWith('.webm'));
  console.log('[demo] video files:', videos.map((v) => path.join(ARTIFACTS, v)));
})();
