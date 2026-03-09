# 20260309 video-download-mcp npm release

## Problem
- 需要让用户无需本地编译即可使用 MCP。
- 需要统一品牌命名为 `video-download-mcp`，并支持 `claude mcp add ... -- npx -y video-download-mcp`。

## Boundary & Ownership
- In scope:
  - 包名、服务名、文档名统一重命名
  - npm 打包配置与发布工作流
  - Claude 导入命令标准化
- Out of scope:
  - YouTube/Bilibili 实际下载能力实现
  - 完整平台风控兼容策略

## Options & Tradeoffs
- Option A: 仅 GitHub 源码分发
  - 优点: 维护简单
  - 缺点: 用户仍需本地构建，不满足“一键可用”
- Option B (Chosen): npm registry 分发 + npx 启动
  - 优点: 用户零编译接入，导入命令统一
  - 缺点: 需要维护 npm 版本与发布凭据

## Migration Plan
1. 重命名包目录与服务标识为 `video-download-mcp`。
2. 添加 npm 可执行入口（`bin`）和 `prepack` 构建钩子。
3. 补齐发布检查命令 `release:check`（`npm pack --dry-run`）。
4. 新增 GitHub Actions（release published 触发）自动发布 npm。
5. 更新 README/mcp.json，给出 `claude mcp add` 一键导入方式。

## Test Strategy
- `npm run typecheck`
- `npm run build`
- `npm_config_cache=/tmp/npm-cache-crawler npm run release:check`
- `claude mcp get video-download-mcp`（发布后验收）

## Acceptance Criteria
- AC1: npm 包可成功 `pack --dry-run`，包含 `dist` 与可执行入口。
- AC2: `claude mcp add ... npx -y video-download-mcp` 作为标准导入路径可用。
- AC3: GitHub Release（published）可触发自动发布工作流。

## Evidence Paths
- `packages/video-download-mcp/package.json`
- `packages/video-download-mcp/src/index.ts`
- `packages/video-download-mcp/src/cli.ts`
- `packages/video-download-mcp/README.md`
- `packages/video-download-mcp/mcp.json`
- `.github/workflows/publish-video-download-mcp.yml`
