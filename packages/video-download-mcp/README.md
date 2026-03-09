# video-download-mcp

MCP server for resolving and downloading videos from social/video share links.
Current production focus: Douyin and Xiaohongshu.

## Local Development

```bash
cd packages/video-download-mcp
npm install
npm run build
npm run serve
```

## Requirements

- Node.js 18+
- A local Chrome/Chromium installation (or set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`)

## CLI

```bash
# Resolve URL and list candidates
video-download-cli resolve "https://v.douyin.com/xxx"

# Resolve and download
video-download-cli download "https://v.douyin.com/xxx" -o ./videos
```

## Publish to npm

Trusted Publishing prerequisites:

- npm CLI >= 11.5.1
- Node.js >= 22.14.0
- npm package settings configured with GitHub Actions Trusted Publisher

Manual local publish (optional):

```bash
cd packages/video-download-mcp
npm run typecheck
npm run build
npm_config_cache=/tmp/npm-cache-crawler npm run release:check
npm publish --access public
```

Release-driven publish (recommended):

- Create a GitHub Release (`published`) and let workflow `.github/workflows/publish-video-download-mcp.yml` publish automatically.
- Workflow uses OIDC Trusted Publishing and `npm publish --provenance`, no `NPM_TOKEN` required.

## Import in Claude Code

After package is published:

```bash
claude mcp add video-download-mcp -- npx -y video-download-mcp
```

Equivalent MCP JSON:

```json
{
  "mcpServers": {
    "video-download-mcp": {
      "command": "npx",
      "args": ["-y", "video-download-mcp"]
    }
  }
}
```

## MCP Tools

- `resolve_url`: Resolve a share URL and return media candidates
- `download_video`: Download a video to target directory
- `resolve_and_download`: Resolve and download the best candidate

## Roadmap

- Add platform adapters for YouTube and Bilibili
- Add adapter-level tests for each platform
- Add smoke tests for MCP startup and tool discovery
