# Checklist - video-fetch-mcp npm release

## Implementation
- [x] 包目录重命名为 `packages/video-download-mcp`
- [x] MCP server 名称重命名为 `video-fetch-mcp`
- [x] `package.json` 增加 `bin/files/prepack/release:check`
- [x] MCP bin 入口独立化（`mcp-bin`）以兼容 npx 启动
- [x] 入口文件加 shebang，支持 npm bin 直接执行
- [x] README 更新为 npm 发布与 `claude mcp add` 接入
- [x] `mcp.json` 更新为 `npx -y @cory-ronghua/video-fetch-mcp`
- [x] 新增 GitHub Actions 发布工作流

## Evidence
- [x] `npm run typecheck` 通过
- [x] `npm run build` 通过
- [x] `npm_config_cache=/tmp/npm-cache-crawler npm run release:check` 通过

## Quality Gates
- [x] 类型检查通过
- [x] 构建通过
- [x] 打包检查通过
- [x] 文档同步完成（PROGRESS/MEMORY/NEXT_STEP/.plan）

## Follow-up
- [ ] 在 npm 网站绑定 Trusted Publisher（GitHub Actions）
- [ ] 发布 GitHub Release 并观察发布工作流
- [ ] 发布后在干净环境验证 `claude mcp add video-fetch-mcp -- npx -y @cory-ronghua/video-fetch-mcp`
- [ ] 验证 `@cory-ronghua/video-fetch-mcp@1.0.1` 可通过 npx 稳定启动
- [ ] 规划 YouTube/Bilibili adapter 设计文档
