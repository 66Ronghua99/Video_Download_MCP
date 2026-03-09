# Memory

## 经验教训

### 2026-03-09
- **问题**: 项目初始化时未创建上下文文件
- **解决方案**: 先读取Python源码理解实现逻辑，再创建项目结构

- **问题**: MCP SDK版本 (1.27.1) 与文档中提到的包名不同
- **解决方案**: 使用 `@modelcontextprotocol/sdk` 而不是 `@modelcontextprotocol/server`
- **注意**: 在 ESM 项目中需使用带扩展名子路径（如 `@modelcontextprotocol/sdk/server/mcp.js`）

- **问题**: TypeScript模块解析问题
- **解决方案**: 保持 `type: module`，并统一 ESM 导入路径与运行方式

- **问题**: Playwright API使用问题
- **解决方案**: 使用playwright-core库，简化导入方式

### 2026-03-09（MCP兼容性修复）
- **问题**: Claude Code 中 MCP server 显示已导入但 `Failed to connect`
- **根因**:
  - 本地 `claude mcp` 注册命令指向 `node --import tsx src/index.ts`，在项目根目录找不到 `tsx`
  - MCP SDK 导入路径未带 `.js` 扩展，Node ESM 下触发 `ERR_MODULE_NOT_FOUND`
  - MCP 工具 schema 仍是旧 JSON Schema 风格，不符合当前 SDK 类型约束
- **修复**:
  - 统一使用构建产物启动：`node .../dist/index.js`
  - SDK 导入改为 `@modelcontextprotocol/sdk/server/mcp.js` 和 `stdio.js`
  - 工具输入 schema 改为 zod 形式；CLI `serve` 复用 `startMcpServer`
- **预防**:
  - MCP 场景禁止向 `stdout` 打日志（仅走 `stderr`）
  - 每次升级 SDK 后先执行 `npm run typecheck` + `npm run build` + `claude mcp list`

### 2026-03-09（npm打包发布）
- **问题**: `npm pack --dry-run` 因本机 `~/.npm` cache 权限异常失败
- **解决方案**: 使用临时 cache 目录执行命令：`npm_config_cache=/tmp/npm-cache-crawler npm run release:check`
- **预防**:
  - CI 中优先使用干净环境执行发布
  - 本地发布检查默认附带临时 cache 配置，避免被历史权限污染

### 2026-03-09（Trusted Publishing）
- **问题**: 传统 `NPM_TOKEN` 模式在安全与维护上成本较高
- **解决方案**: 切换到 npm Trusted Publishing（GitHub OIDC），workflow 需开启 `permissions.id-token: write`
- **预防**:
  - 发布触发采用 `release: published`，避免误触发
  - `npm publish` 使用 `--provenance` 保留供应链证明
