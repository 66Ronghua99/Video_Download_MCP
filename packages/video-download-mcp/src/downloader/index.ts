/**
 * Downloader module for media files
 */

import axios from 'axios';
import { createWriteStream, existsSync, mkdirSync, type WriteStream } from 'fs';
import { join, basename } from 'path';
import type { DownloadOptions, DownloadResult, MediaCandidate } from '../types/index.js';

export async function downloadFile(
  url: string,
  options: DownloadOptions = {}
): Promise<DownloadResult> {
  const { outputDir = './downloads', filename, headers = {} } = options;

  // Ensure output directory exists
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  // Determine filename
  const targetFilename = filename || getFilenameFromUrl(url);
  const filepath = join(outputDir, targetFilename);

  try {
    console.error(`Downloading: ${url}`);
    console.error(`To: ${filepath}`);

    const response = await axios({
      method: 'GET',
      url,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ...headers
      },
      responseType: 'stream',
      timeout: 300000, // 5 minutes
    });

    const totalLength = parseInt(response.headers['content-length'] || '0', 10);
    let downloaded = 0;

    const writer: WriteStream = createWriteStream(filepath);

    response.data.on('data', (chunk: Buffer) => {
      downloaded += chunk.length;
      if (totalLength > 0) {
        const progress = Math.round((downloaded / totalLength) * 100);
        process.stderr.write(`\rProgress: ${progress}%`);
      }
    });

    return new Promise((resolve, reject) => {
      response.data.pipe(writer);
      writer.on('finish', () => {
        console.error('\nDownload completed!');
        resolve({
          success: true,
          filepath,
        });
      });
      writer.on('error', (err) => {
        reject({
          success: false,
          filepath,
          error: err.message,
        });
      });
    });
  } catch (error) {
    return {
      success: false,
      filepath,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

export async function downloadFromCandidate(
  candidate: MediaCandidate,
  options: DownloadOptions = {}
): Promise<DownloadResult> {
  return downloadFile(candidate.url, {
    ...options,
    headers: {
      ...candidate.headers,
      ...options.headers,
    },
  });
}

function getFilenameFromUrl(url: string): string {
  try {
    const urlObj = new URL(url);
    const path = urlObj.pathname;
    const name = basename(path);

    if (name && name.includes('.')) {
      return name;
    }
  } catch {
    // Fallback
  }

  // Default filename with timestamp
  const timestamp = Date.now();
  return `video_${timestamp}.mp4`;
}

export function getDownloadStatus(id: string): { id: string; status: string } {
  // Placeholder for download status tracking
  return {
    id,
    status: 'completed'
  };
}
