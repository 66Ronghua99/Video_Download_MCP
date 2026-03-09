# Progress

## 项目背景
- **项目名称**: @cory-ronghua/video-fetch-mcp
- **类型**: Node.js/TypeScript CLI + MCP Server
- **目标**: 实现可发布到 npm 并可被 Claude Code 一键导入的多平台视频下载 MCP

## 当前里程碑
- [x] 理解Python版本实现逻辑
- [x] Phase 1: 项目初始化
- [x] Phase 2: 核心功能实现
- [x] Phase 3: MCP Server实现
- [x] Phase 4: CLI工具
- [x] Phase 5: Claude Code MCP 兼容性修复
- [x] Phase 6: npm 打包与发布流水线配置
- [ ] Phase 7: 真实链接验收与平台扩展（YouTube/Bilibili）

## TODO
1. 真实链接验收
   - 使用抖音/XHS真实链接验证 `resolve_url`
   - 验证 `resolve_and_download` 下载路径和文件完整性
2. 平台扩展设计
   - 设计 YouTube/Bilibili 平台适配器接口
   - 明确平台能力边界（解析、下载、风控）
3. 自动化测试补齐
   - 增加最小 smoke test（MCP server 启动 + 工具 schema 可发现）
   - 增加 resolver/downloader 单元测试

## DONE
- 分析Python版本实现
- 创建项目结构 (packages/video-download-mcp/)
- 初始化 npm 项目，安装依赖
- 配置 TypeScript
- 实现类型定义 (types/index.ts)
- 实现浏览器解析 (resolver/browser.ts)
- 实现提取器 (resolver/extractor.ts)
- 实现下载模块 (downloader/index.ts)
- 实现MCP Server (src/index.ts)
- 实现CLI工具 (src/cli.ts)
- TypeScript 构建成功
- 修复 MCP SDK ESM 子路径导入：`@modelcontextprotocol/sdk/server/mcp.js` / `stdio.js`
- 修复 MCP 工具 schema 与 SDK 1.27 类型不兼容问题（改为 zod schema + 统一 server 注册）
- 消除 MCP stdio 污染（resolver/downloader 输出迁移到 stderr）
- 修复 claude mcp 本地注册命令，改为运行已构建产物 `dist/index.js`
- 质量门禁通过：`npm run typecheck`、`npm run build`
- 连通性验证通过：`claude mcp get video-fetch-mcp` / `claude mcp list` 均为 `✓ Connected`
- 包与服务统一重命名为 `video-download-mcp`
- 包发布名调整为 `@cory-ronghua/video-fetch-mcp`（规避 npm 命名过滤）
- 增加 npm 发布配置：`bin`、`files`、`prepack`、`release:check`
- 新增 GitHub Actions 发布流水线：`.github/workflows/publish-video-download-mcp.yml`
- 发布流水线已切换为 npm Trusted Publishing（OIDC + provenance，无需 NPM_TOKEN）
- 打包验证通过：`npm pack --dry-run`（使用临时 npm cache）
- 修复 npx 启动秒退问题：新增独立 bin 入口 `src/mcp-bin.ts`
- 发布版本提升到 `1.0.1`，用于修复后重新发布

## Reference List
- Python版本: media_resolver/resolver/
- MCP SDK: @modelcontextprotocol/sdk v1.x
- 设计文档: .plan/20260309_video_resolver_mcp_claude_compatibility.md
- 执行清单: .plan/checklist_video_resolver_mcp_claude_compatibility.md
- 发布设计: .plan/20260309_video_download_mcp_npm_release.md
- 发布清单: .plan/checklist_video_download_mcp_npm_release.md
