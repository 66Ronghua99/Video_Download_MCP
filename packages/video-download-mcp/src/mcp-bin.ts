#!/usr/bin/env node

import { startMcpServer } from './index.js';

startMcpServer().catch((error) => {
  console.error('MCP server failed to start:', error);
  process.exit(1);
});
