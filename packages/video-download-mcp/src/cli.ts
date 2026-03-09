#!/usr/bin/env node
/**
 * CLI tool for video-download-mcp
 */

import { resolveUrl } from './resolver/browser.js';
import { downloadFromCandidate, downloadFile } from './downloader/index.js';
import { startMcpServer } from './index.js';

interface CliArgs {
  command: string;
  url?: string;
  outputDir?: string;
  filename?: string;
}

function parseArgs(args: string[]): CliArgs {
  const command = args[2] || 'help';

  if (command === 'help') {
    return { command: 'help' };
  }

  const urlIndex = args.findIndex((a, i) => i > 2 && (a.startsWith('http://') || a.startsWith('https://')));
  const url = urlIndex >= 0 ? args[urlIndex] : undefined;

  const outputIndex = args.indexOf('-o', 3);
  const outputDir = outputIndex >= 0 && args[outputIndex + 1] ? args[outputIndex + 1] : './downloads';

  const filenameIndex = args.indexOf('--filename', 3);
  const filename = filenameIndex >= 0 && args[filenameIndex + 1] ? args[filenameIndex + 1] : undefined;

  return { command, url, outputDir, filename };
}

function printHelp(): void {
  console.log(`
Video Download MCP CLI

Usage:
  video-download-cli resolve <url>              Resolve a URL and list candidates
  video-download-cli download <url> -o <dir>    Download a video from URL
  video-download-cli serve                      Start MCP Server

Examples:
  video-download-cli resolve "https://v.douyin.com/xxx"
  video-download-cli download "https://v.douyin.com/xxx" -o ./videos
  video-download-cli serve
`);
}

async function main() {
  const args = parseArgs(process.argv);

  if (args.command === 'help') {
    printHelp();
    process.exit(0);
  }

  if (args.command === 'serve') {
    await startMcpServer();
    return;
  }

  if (!args.url) {
    console.error('Error: URL is required');
    printHelp();
    process.exit(1);
  }

  if (args.command === 'resolve') {
    console.log(`Resolving: ${args.url}`);
    const result = await resolveUrl(args.url);

    console.log('\n=== Result ===');
    console.log(`Input URL: ${result.inputUrl}`);
    console.log(`Final URL: ${result.finalPageUrl}`);
    console.log(`Title: ${result.title}`);
    console.log(`Success: ${result.success}`);

    if (result.candidates.length > 0) {
      console.log('\n=== Candidates ===');
      result.candidates.forEach((c, i) => {
        console.log(`\n[${i + 1}] ${c.url}`);
        console.log(`    Kind: ${c.kind}, Score: ${c.score}, Source: ${c.source}`);
      });

      if (result.best) {
        console.log(`\n=== Best ===`);
        console.log(result.best.url);
      }
    }

    if (result.logs.length > 0) {
      console.log('\n=== Logs ===');
      result.logs.forEach(l => console.log(l));
    }
  }

  if (args.command === 'download') {
    console.log(`Resolving: ${args.url}`);
    const resolveResult = await resolveUrl(args.url);

    if (!resolveResult.best) {
      console.error('Error: No video candidate found');
      process.exit(1);
    }

    console.log(`Best candidate: ${resolveResult.best.url}`);
    console.log(`Downloading to: ${args.outputDir}`);

    const downloadResult = await downloadFromCandidate(resolveResult.best, {
      outputDir: args.outputDir,
      filename: args.filename,
    });

    if (downloadResult.success) {
      console.log(`Downloaded to: ${downloadResult.filepath}`);
    } else {
      console.error(`Download failed: ${downloadResult.error}`);
      process.exit(1);
    }
  }
}

main().catch((err) => {
  console.error('Error:', err);
  process.exit(1);
});
