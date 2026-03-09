# Checklist - video-resolver MCP Claude Compatibility

## Implementation
- [x] 修复 MCP SDK ESM 导入路径（`.js` 子路径）
- [x] 修复 MCP tool schema 兼容性（zod 输入）
- [x] CLI `serve` 与主 server 入口收敛为单实现
- [x] resolver/downloader 内部日志迁移到 `stderr`
- [x] 更新 `mcp.json` 默认启动命令为 `node dist/index.js`
- [x] 增加 `typecheck` 脚本

## Evidence
- [x] `npm run typecheck` 通过
- [x] `npm run build` 通过
- [x] `npm run serve` 可启动并输出 `Video Resolver MCP Server running on stdio`
- [x] `claude mcp get video-resolver` 显示 `✓ Connected`
- [x] `claude mcp list` 显示 `video-resolver` 健康

## Quality Gates
- [x] 类型检查通过
- [x] 构建通过
- [x] 文档同步完成（PROGRESS/MEMORY/NEXT_STEP/.plan）

## Docs Sync
- [x] `PROGRESS.md` 已更新
- [x] `MEMORY.md` 已更新
- [x] `NEXT_STEP.md` 已更新
