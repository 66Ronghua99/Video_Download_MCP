/**
 * Type definitions for video-download-mcp
 */

export type MediaKind = 'm3u8' | 'mpd' | 'file' | 'segment' | 'json_hint';

export type MediaSource = 'network' | 'hook' | 'dom' | 'api_json';

export interface MediaCandidate {
  url: string;
  kind: MediaKind;
  contentType?: string;
  score: number;
  source: MediaSource;
  method?: string;
  headers?: Record<string, string>;
}

export interface ResolveResult {
  inputUrl: string;
  finalPageUrl?: string;
  title?: string;
  candidates: MediaCandidate[];
  best?: MediaCandidate;
  logs: string[];
  success: boolean;
  error?: string;
}

export interface DownloadOptions {
  outputDir?: string;
  filename?: string;
  headers?: Record<string, string>;
}

export interface DownloadResult {
  success: boolean;
  filepath?: string;
  error?: string;
  candidate?: MediaCandidate;
}

export interface DownloadStatus {
  id: string;
  status: 'pending' | 'downloading' | 'completed' | 'failed';
  progress?: number;
  filepath?: string;
  error?: string;
}

export type Platform = 'douyin' | 'xhs' | 'youtube' | 'bilibili' | 'unknown';

export interface ResolverConfig {
  headless?: boolean;
  timeout?: number;
  userAgent?: string;
  cookies?: Record<string, string>;
}
