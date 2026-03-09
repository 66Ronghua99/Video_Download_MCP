/**
 * URL classifier and candidate scorer
 */

import type { MediaKind, MediaSource, MediaCandidate, Platform } from '../types/index.js';

const MEDIA_EXTS = ['.mp4', '.m3u8', '.mpd', '.m4s', '.ts', '.webm'];

export function classifyUrl(url: string, contentType?: string): MediaKind | null {
  const u = url.toLowerCase();
  const ct = (contentType || '').toLowerCase();

  if (u.includes('.m3u8') || ct.includes('application/vnd.apple.mpegurl')) {
    return 'm3u8';
  }
  if (u.includes('.mpd') || ct.includes('application/dash+xml')) {
    return 'mpd';
  }
  if (u.includes('.mp4') || u.includes('.webm')) {
    return 'file';
  }
  if (u.includes('.m4s') || u.includes('.ts')) {
    return 'segment';
  }
  if (ct.startsWith('video/')) {
    return 'file';
  }
  if (ct.includes('json')) {
    return 'json_hint';
  }
  return null;
}

export function scoreCandidate(
  kind: MediaKind,
  url: string,
  contentType?: string,
  platform: Platform = 'unknown'
): number {
  let score = 0;

  if (kind === 'file') {
    score += 90;
  } else if (kind === 'm3u8') {
    score += 85;
  } else if (kind === 'mpd') {
    score += 80;
  } else if (kind === 'segment') {
    score += 30;
  } else if (kind === 'json_hint') {
    score += 10;
  }

  const u = url.toLowerCase();
  // Positive scoring
  if (u.includes('video') || u.includes('play')) {
    score += 10;
  }
  if (u.includes('aweme') || u.includes('playwm')) {
    // Douyin video
    score += 15;
  }
  if (u.includes('xhscdn') || u.includes('xiaohongshu')) {
    // Xiaohongshu video CDN
    score += 20;
  }
  if (u.includes('fe-video')) {
    // Xiaohongshu video
    score += 25;
  }
  if (u.includes('hd') || u.includes('1080') || u.includes('720')) {
    score += 5;
  }

  // Negative scoring
  if (u.includes('watermark')) {
    score -= 20;
  }
  if (u.includes('cover') || u.includes('poster')) {
    score -= 50;
  }
  if (u.includes('thumb')) {
    score -= 30;
  }
  if (u.includes('chrome-extension')) {
    score -= 100;
  }

  return score;
}

export function extractFromJson(
  body: string,
  url: string,
  platform: Platform = 'unknown'
): MediaCandidate[] {
  const candidates: MediaCandidate[] = [];

  let data: unknown;
  try {
    data = JSON.parse(body);
  } catch {
    return candidates;
  }

  const findVideoUrls = (obj: unknown, path = ''): void => {
    if (typeof obj === 'string') {
      // Check if it's a video URL
      const lower = obj.toLowerCase();
      if (MEDIA_EXTS.some(ext => lower.includes(ext))) {
        const kind = classifyUrl(obj, undefined);
        if (kind) {
          candidates.push({
            url: obj,
            kind,
            contentType: undefined,
            method: 'GET',
            headers: {},
            score: scoreCandidate(kind, obj, undefined, platform) + 5, // Bonus for JSON discovery
            source: 'api_json'
          });
        }
      }
    } else if (typeof obj === 'object' && obj !== null) {
      // Common Douyin video fields
      const objRecord = obj as Record<string, unknown>;
      const videoKeys = ['play_addr', 'video_url', 'url', 'url_list', 'download_addr'];
      // Xiaohongshu specific fields
      if (platform === 'xhs') {
        videoKeys.push('video_info', 'videoUrl', 'urlList', 'video', 'imageInfo');
      }
      for (const key of videoKeys) {
        if (key in objRecord && objRecord[key]) {
          findVideoUrls(objRecord[key], `${path}.${key}`);
        }
      }

      // Traverse all values
      for (const v of Object.values(objRecord)) {
        findVideoUrls(v, path);
      }
    } else if (Array.isArray(obj)) {
      for (const item of obj) {
        findVideoUrls(item, path);
      }
    }
  };

  findVideoUrls(data);
  return candidates;
}

// URL detection patterns
export const DOUYIN_URL_PATTERN = /https:\/\/v\.douyin\.com\/[a-zA-Z0-9]+/;
export const XHS_URL_PATTERN = /https:\/\/www\.xiaohongshu\.com\/(?:explore|discovery\/item)\/[a-zA-Z0-9]+(?:\?.*)?/;
export const YOUTUBE_URL_PATTERN = /https:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=[\w-]+|youtu\.be\/[\w-]+)/;
export const BILIBILI_URL_PATTERN = /https:\/\/(?:www\.)?bilibili\.com\/video\/[a-zA-Z0-9]+(?:\?.*)?/;

export function extractDouyinUrl(text: string): string | null {
  const match = text.match(DOUYIN_URL_PATTERN);
  if (match) {
    return match[0];
  }
  return null;
}

export function extractXhsUrl(text: string): string | null {
  const match = XHS_URL_PATTERN.exec(text);
  if (match) {
    return match[0];
  }
  return null;
}

export function extractYoutubeUrl(text: string): string | null {
  const match = text.match(YOUTUBE_URL_PATTERN);
  if (match) {
    return match[0];
  }
  return null;
}

export function extractBilibiliUrl(text: string): string | null {
  const match = text.match(BILIBILI_URL_PATTERN);
  if (match) {
    return match[0];
  }
  return null;
}

export function isValidUrl(text: string): boolean {
  return text.startsWith('http://') || text.startsWith('https://');
}

export function detectPlatform(url: string): Platform {
  if (url.includes('xiaohongshu.com') || url.includes('xhs.cn')) {
    return 'xhs';
  }
  if (url.includes('douyin.com')) {
    return 'douyin';
  }
  if (url.includes('youtube.com') || url.includes('youtu.be')) {
    return 'youtube';
  }
  if (url.includes('bilibili.com') || url.includes('b23.tv')) {
    return 'bilibili';
  }
  return 'unknown';
}

export function extractXhsNoteId(url: string): string | null {
  const match = url.match(/\/(?:explore|discovery\/item)\/([a-zA-Z0-9]+)/);
  return match ? match[1] : null;
}
