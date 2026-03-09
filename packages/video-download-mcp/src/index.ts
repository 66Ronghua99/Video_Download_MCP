#!/usr/bin/env node
/**
 * MCP Server for video-fetch-mcp
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { resolveUrl } from './resolver/browser.js';
import { downloadFromCandidate, downloadFile } from './downloader/index.js';

function createMcpServer(): McpServer {
  const mcpServer = new McpServer({
    name: 'video-fetch-mcp',
    version: '1.0.1',
  });

  (mcpServer as any).tool(
    'resolve_url',
    'Resolve a video URL (Douyin/Xiaohongshu) and return media candidates',
    {
      url: z.string().describe('The URL to resolve (Douyin or Xiaohongshu)'),
      headless: z.boolean().optional().describe('Use headless browser (default: true)'),
    },
    async ({ url, headless }: any) => {
      try {
        const result = await resolveUrl(url, { headless: headless ?? true });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                inputUrl: result.inputUrl,
                finalPageUrl: result.finalPageUrl,
                title: result.title,
                success: result.success,
                candidates: result.candidates.map(c => ({
                  url: c.url,
                  kind: c.kind,
                  score: c.score,
                  source: c.source,
                })),
                best: result.best ? {
                  url: result.best.url,
                  kind: result.best.kind,
                  score: result.best.score,
                } : null,
                logs: result.logs,
              }, null, 2),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
              }, null, 2),
            },
          ],
        };
      }
    }
  );

  (mcpServer as any).tool(
    'download_video',
    'Download a video from a URL or candidate',
    {
      url: z.string().describe('The video URL to download'),
      outputDir: z.string().optional().describe('Output directory (default: ./downloads)'),
      filename: z.string().optional().describe('Optional filename'),
    },
    async ({ url, outputDir, filename }: any) => {
      try {
        const result = await downloadFile(url, {
          outputDir: outputDir ?? './downloads',
          filename,
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
              }, null, 2),
            },
          ],
        };
      }
    }
  );

  (mcpServer as any).tool(
    'resolve_and_download',
    'Resolve URL and automatically download the best candidate',
    {
      url: z.string().describe('The URL to resolve and download'),
      outputDir: z.string().optional().describe('Output directory (default: ./downloads)'),
    },
    async ({ url, outputDir }: any) => {
      try {
        const resolveResult = await resolveUrl(url);
        if (!resolveResult.best) {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  success: false,
                  error: 'No video candidate found',
                }, null, 2),
              },
            ],
          };
        }

        const downloadResult = await downloadFromCandidate(resolveResult.best, {
          outputDir: outputDir ?? './downloads',
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                resolve: {
                  inputUrl: resolveResult.inputUrl,
                  best: resolveResult.best,
                },
                download: downloadResult,
              }, null, 2),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
              }, null, 2),
            },
          ],
        };
      }
    }
  );

  return mcpServer;
}

export async function startMcpServer(): Promise<void> {
  const mcpServer = createMcpServer();
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
  console.error('video-fetch-mcp server running on stdio');
}
