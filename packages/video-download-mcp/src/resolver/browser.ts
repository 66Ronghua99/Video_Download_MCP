/**
 * Browser-based resolver using Playwright
 */

import { chromium, type Browser, type BrowserContext, type Page } from 'playwright-core';
import { existsSync } from 'fs';
import type { ResolveResult, MediaCandidate, Platform } from '../types/index.js';
import {
  classifyUrl,
  scoreCandidate,
  extractFromJson,
  detectPlatform,
  extractXhsNoteId,
  extractDouyinUrl,
  extractXhsUrl,
  extractYoutubeUrl,
  extractBilibiliUrl,
  isValidUrl
} from './extractor.js';
import { HOOKS_SCRIPT } from './hooks.js';

const DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

const HEADLESS_ARGS = [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-blink-features=AutomationControlled',
  '--disable-dev-shm-usage',
  '--disable-gpu',
  '--window-size=1920,1080',
];

const HEADED_ARGS = [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-blink-features=AutomationControlled',
  '--disable-dev-shm-usage',
  '--start-maximized',
];

function detectBrowserPath(): string | undefined {
  // Check environment variable
  const envPath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
  if (envPath) {
    return envPath;
  }

  // Check common macOS Chrome paths
  const macChromePaths = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
  ];

  for (const p of macChromePaths) {
    if (existsSync(p)) {
      return p;
    }
  }

  return undefined;
}

async function resolveWithBrowser(
  url: string,
  platform: Platform,
  originalNoteId: string | null,
  headless: boolean,
  browserArgs: string[]
): Promise<{
  candidates: MediaCandidate[];
  logs: string[];
  title: string;
  finalPageUrl: string;
  success: boolean;
  error?: string;
}> {
  const candidates: MediaCandidate[] = [];
  const logs: string[] = [];

  const browserPath = detectBrowserPath();

  const browser = await chromium.launch({
    headless,
    args: browserArgs,
    executablePath: browserPath,
  });

  try {
    const context = await browser.newContext({
      userAgent: DEFAULT_USER_AGENT,
    });

    await context.addInitScript({ content: HOOKS_SCRIPT });

    const jsonResponses: Map<string, string> = new Map();

    context.on('response', async (resp) => {
      try {
        const ct = resp.headers()['content-type'] || '';
        const status = resp.status();
        if (status >= 200 && status < 400) {
          const respUrl = resp.url();
          const kind = classifyUrl(respUrl, ct);
          if (kind) {
            candidates.push({
              url: respUrl,
              kind,
              contentType: ct,
              method: 'GET',
              headers: {},
              score: scoreCandidate(kind, respUrl, ct, platform),
              source: 'network'
            });
          }
          if (ct.includes('json') && status === 200) {
            try {
              const body = await resp.text();
              jsonResponses.set(respUrl, body);
            } catch {
              // Ignore
            }
          }
        }
      } catch (e) {
        logs.push(`response parse error: ${e}`);
      }
    });

    const page = await context.newPage();

    const mode = headless ? 'headless' : 'headed';
    logs.push(`[${mode}] Navigating to: ${url}`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });

    logs.push(`[${mode}] Waiting 5 seconds for video to load...`);
    await page.waitForTimeout(5000);

    // Check for redirect (Xiaohongshu)
    const currentUrl = page.url();
    if (platform === 'xhs' && originalNoteId && currentUrl.includes('/explore/')) {
      const currentMatch = currentUrl.match(/\/explore\/([a-zA-Z0-9]+)/);
      const currentNoteId = currentMatch ? currentMatch[1] : null;

      if (currentNoteId && currentNoteId !== originalNoteId) {
        logs.push(`[${mode}] Redirect detected: ${currentNoteId} -> ${originalNoteId}`);
        candidates.length = 0;
        jsonResponses.clear();
        await context.close();

        const newContext = await browser.newContext({
          userAgent: DEFAULT_USER_AGENT,
        });
        await newContext.addInitScript({ content: HOOKS_SCRIPT });

        newContext.on('response', async (resp) => {
          try {
            const ct = resp.headers()['content-type'] || '';
            const status = resp.status();
            if (status >= 200 && status < 400) {
              const respUrl = resp.url();
              const kind = classifyUrl(respUrl, ct);
              if (kind) {
                candidates.push({
                  url: respUrl,
                  kind,
                  contentType: ct,
                  method: 'GET',
                  headers: {},
                  score: scoreCandidate(kind, respUrl, ct, platform),
                  source: 'network'
                });
              }
              if (ct.includes('json') && status === 200) {
                try {
                  const body = await resp.text();
                  jsonResponses.set(respUrl, body);
                } catch {
                  // Ignore
                }
              }
            }
          } catch (e) {
            logs.push(`response parse error: ${e}`);
          }
        });

        const newPage = await newContext.newPage();
        const newUrl = `https://www.xiaohongshu.com/explore/${originalNoteId}`;
        logs.push(`[${mode}] Re-navigating to: ${newUrl}`);
        await newPage.goto(newUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
        logs.push(`[${mode}] Waiting 5 seconds for video to load (retry)...`);
        await newPage.waitForTimeout(5000);
      }
    }

    const title = await page.title();
    const finalPageUrl = page.url();
    logs.push(`[${mode}] Page title: ${title}`);
    logs.push(`[${mode}] Final URL: ${finalPageUrl}`);

    // Extract from hook logs
    try {
      const hookLogs = await page.evaluate('window.__MEDIA_HOOK_LOGS__ || []') as Array<{ payload?: { url?: string; contentType?: string } }>;
      logs.push(`[${mode}] Hook logs count: ${hookLogs.length}`);
      for (const item of hookLogs) {
        const payload = item.payload || {};
        const hurl = payload.url;
        if (hurl) {
          const kind = classifyUrl(hurl, payload.contentType);
          if (kind) {
            candidates.push({
              url: hurl,
              kind,
              contentType: payload.contentType,
              method: 'GET',
              headers: {},
              score: scoreCandidate(kind, hurl, payload.contentType, platform) + 5,
              source: 'hook'
            });
          }
        }
      }
    } catch (e) {
      logs.push(`Hook logs error: ${e}`);
    }

    // Extract from JSON responses
    for (const [jsonUrl, jsonBody] of jsonResponses.entries()) {
      const jsonCandidates = extractFromJson(jsonBody, jsonUrl, platform);
      candidates.push(...jsonCandidates);
    }

    await browser.close();

    return {
      candidates,
      logs,
      title,
      finalPageUrl,
      success: true
    };
  } catch (e) {
    await browser.close();
    return {
      candidates: [],
      logs: [`Error in ${headless ? 'headless' : 'headed'} mode: ${e}`],
      title: '',
      finalPageUrl: '',
      success: false,
      error: String(e)
    };
  }
}

export async function resolveUrl(url: string, options: { headless?: boolean; timeout?: number } = {}): Promise<ResolveResult> {
  const { headless = true, timeout = 45000 } = options;

  // Extract URL from text if needed
  let extractedUrl = extractDouyinUrl(url)
    || extractXhsUrl(url)
    || extractYoutubeUrl(url)
    || extractBilibiliUrl(url);
  if (extractedUrl) {
    url = extractedUrl;
    console.error(`Extracted URL from text: ${url}`);
  } else if (!isValidUrl(url)) {
    throw new Error(`Invalid URL: ${url}`);
  }

  // Extract noteId for Xiaohongshu
  const originalNoteId = extractXhsNoteId(url);
  console.error(`Original noteId: ${originalNoteId}`);

  // Detect platform
  const platform = detectPlatform(url);
  console.error(`Detected platform: ${platform}`);

  // Try headless first
  console.error('Attempting with headless browser...');
  let result = await resolveWithBrowser(
    url,
    platform,
    originalNoteId,
    true,
    HEADLESS_ARGS
  );

  // Fallback to headed if headless fails
  if (!result.success || result.candidates.length === 0) {
    console.error('Headless failed or no candidates, falling back to headed browser...');
    result = await resolveWithBrowser(
      url,
      platform,
      originalNoteId,
      false,
      HEADED_ARGS
    );
  }

  const { candidates, logs, title, finalPageUrl } = result;

  // Deduplicate and sort by score
  const uniq: Map<string, MediaCandidate> = new Map();
  for (const c of candidates) {
    const key = `${c.url}::${c.kind}`;
    if (!uniq.has(key) || c.score > uniq.get(key)!.score) {
      uniq.set(key, c);
    }
  }

  const finalCandidates = Array.from(uniq.values()).sort((a, b) => b.score - a.score);
  const best = finalCandidates[0] || undefined;

  logs.push(`Total candidates: ${finalCandidates.length}`);
  if (best) {
    logs.push(`Best candidate: ${best.url} (score: ${best.score})`);
  }

  return {
    inputUrl: url,
    finalPageUrl,
    title,
    candidates: finalCandidates,
    best,
    logs,
    success: result.success,
    error: result.error
  };
}
