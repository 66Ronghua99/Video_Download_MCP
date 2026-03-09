# 20260309 video-resolver MCP Claude Compatibility

## Problem
- 项目在 Claude Code 中导入后显示 `Failed to connect`，MCP 工具不可用。
- 当前代码在本地无法稳定重建，且运行时存在 ESM 导入与 stdio 污染风险。

## Boundary & Ownership
- In scope:
  - 修复 `packages/video-resolver` 的 MCP 启动与 SDK 兼容性
  - 修复 Claude Code 本地 MCP 注册命令
  - 保持既有工具名和功能语义不变
- Out of scope:
  - 抖音/XHS 反爬策略优化
  - 下载性能优化和并发调度
  - 完整自动化测试体系建设

## Options & Tradeoffs
- Option A: 继续 `node --import tsx src/index.ts`
  - 优点: 开发态改动无需构建
  - 缺点: 强依赖运行目录与 `tsx` 可见性；生产稳定性差
- Option B (Chosen): 固定为 `node dist/index.js`
  - 优点: 运行时依赖最小、路径确定、与 Claude MCP 健康检查一致
  - 缺点: 每次改动需先 build

## Migration Plan
1. 修复 SDK 导入路径为 `.js` 子路径，避免 Node ESM 解析失败。
2. MCP tool 输入 schema 改为 zod 形式，消除与 SDK 1.27 类型不兼容。
3. CLI `serve` 复用同一 `startMcpServer` 入口，防止双实现漂移。
4. resolver/downloader 内部日志改走 `stderr`，避免污染 MCP stdio 协议流。
5. 更新 `mcp.json` 与本地 `claude mcp` 配置，指向 `dist/index.js`。

## Test Strategy
- Static gates:
  - `npm run typecheck`
  - `npm run build`
- Runtime checks:
  - `npm run serve` 启动无异常
  - `claude mcp get video-resolver` 显示 `✓ Connected`
  - `claude mcp list` 显示 `video-resolver` 健康

## Acceptance Criteria
- AC1: MCP server 能在 Claude Code 中稳定连接。
- AC2: 项目可以在本地重新 typecheck/build 通过。
- AC3: MCP 运行时不向 stdout 打业务日志。

## Evidence Paths
- 代码变更:
  - `packages/video-resolver/src/index.ts`
  - `packages/video-resolver/src/cli.ts`
  - `packages/video-resolver/src/resolver/browser.ts`
  - `packages/video-resolver/src/downloader/index.ts`
  - `packages/video-resolver/mcp.json`
  - `packages/video-resolver/package.json`
- 验证命令:
  - `npm run typecheck`
  - `npm run build`
  - `npm run serve`
  - `claude mcp get video-resolver`
  - `claude mcp list`
