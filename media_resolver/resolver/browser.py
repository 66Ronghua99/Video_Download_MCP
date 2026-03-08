import asyncio
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .extractor import classify_url, score_candidate, extract_from_json


# 抖音链接正则
DOUYIN_URL_PATTERN = re.compile(r'https://v\.douyin\.com/[a-zA-Z0-9]+')

# 小红书链接正则 - 支持带查询参数的完整URL
# 匹配 /explore/ 或 /discovery/item/ 后面的 noteId 及其查询参数 (支持跨行)
XHS_URL_PATTERN = re.compile(r"https://www\.xiaohongshu\.com/(?:explore|discovery/item)/[a-zA-Z0-9]+(?:\?.*)?", re.DOTALL)


def extract_douyin_url(text: str) -> Optional[str]:
    """从文本中提取抖音链接"""
    match = DOUYIN_URL_PATTERN.search(text)
    if match:
        return match.group(0)
    return None


def extract_xhs_url(text: str) -> Optional[str]:
    """从文本中提取小红书链接，保留查询参数"""
    match = XHS_URL_PATTERN.search(text)
    if match:
        url = match.group(0)
        # 保留原始文本中的查询参数
        # 找到 URL 结束位置，获取后面的查询参数
        url_end = match.end()
        if url_end < len(text):
            query = text[url_end:]
            # 只保留查询参数部分（从 ? 开始）
            if query.startswith('?'):
                url = url + query
            elif query.startswith('&'):
                # 处理没有 ? 只有 & 的情况
                url = url + '?' + query[1:]
        return url
    return None


def is_valid_url(text: str) -> bool:
    """检查是否是有效的 URL"""
    return text.startswith("http://") or text.startswith("https://")


def detect_platform(url: str) -> str:
    """检测链接平台: douyin 或 xhs (小红书)"""
    if "xiaohongshu.com" in url or "xhs.cn" in url:
        return "xhs"
    elif "douyin.com" in url:
        return "douyin"
    return "unknown"


def extract_xhs_note_id(url: str) -> Optional[str]:
    """从小红书 URL 中提取 noteId"""
    import re
    # 匹配 /explore/ 或 /discovery/item/ 两种格式
    match = re.search(r'/(?:explore|discovery/item)/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None


async def resolve_url(url: str) -> Dict[str, Any]:
    # 支持从文本中提取 URL
    extracted_url = extract_douyin_url(url) or extract_xhs_url(url)
    if extracted_url:
        url = extracted_url
        print(f"Extracted URL from text: {url}")
    elif not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")

    # 提前提取 noteId，用于后续验证是否发生重定向
    original_note_id = extract_xhs_note_id(url)
    print(f"Original noteId: {original_note_id}")

    # 检测平台
    platform = detect_platform(url)
    print(f"Detected platform: {platform}")

    """解析 URL，返回媒体候选列表和最佳下载源"""
    candidates: List[Dict[str, Any]] = []
    logs: List[str] = []

    # 获取 hooks.js 的绝对路径
    hooks_path = Path(__file__).parent / "hooks.js"
    hooks_content = hooks_path.read_text()

    async with async_playwright() as p:
        # 启动 Chromium 浏览器 - 使用更真实的浏览器环境
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--start-maximized',
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 注入 hooks.js
        await context.add_init_script(hooks_content)

        # 存储响应的 JSON 数据
        json_responses: Dict[str, str] = {}

        async def on_response(resp):
            try:
                ct = resp.headers.get("content-type", "")
                status = resp.status

                # 只关注成功的响应
                if status >= 200 and status < 400:
                    url = resp.url

                    # 分类 URL
                    kind = classify_url(url, ct)

                    if kind:
                        candidates.append({
                            "url": url,
                            "kind": kind,
                            "content_type": ct,
                            "method": "GET",
                            "headers": {},
                            "score": score_candidate(kind, url, ct, platform),
                            "source": "network"
                        })

                    # 如果是 JSON，保存下来后面解析
                    if "json" in ct and status == 200:
                        try:
                            body = await resp.text()
                            json_responses[url] = body
                        except Exception:
                            pass

            except Exception as e:
                logs.append(f"response parse error: {e}")

        context.on("response", on_response)

        # 创建页面
        page = await context.new_page()

        # 打开目标 URL
        logs.append(f"Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)

        # 等待页面加载 5 秒
        logs.append("Waiting 5 seconds for video to load...")
        await page.wait_for_timeout(5000)

        # 检查是否发生了重定向
        current_url = page.url
        if platform == "xhs" and original_note_id and "/explore/" in current_url:
            # 提取当前 URL 中的 noteId
            import re
            current_match = re.search(r'/explore/([a-zA-Z0-9]+)', current_url)
            current_note_id = current_match.group(1) if current_match else None

            # 如果发生了重定向（noteId 不匹配），则使用原始 noteId 重新访问
            if current_note_id and current_note_id != original_note_id:
                logs.append(f"Redirect detected: {current_note_id} -> {original_note_id}")
                # 清除旧的 candidates 和 json_responses
                candidates.clear()
                json_responses.clear()
                # 重建 context 和 page
                await context.close()
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                await context.add_init_script(hooks_content)
                context.on("response", on_response)
                page = await context.new_page()
                new_url = f"https://www.xiaohongshu.com/explore/{original_note_id}"
                logs.append(f"Re-navigating to: {new_url}")
                await page.goto(new_url, wait_until="domcontentloaded", timeout=45000)
                logs.append("Waiting 5 seconds for video to load (retry)...")
                await page.wait_for_timeout(5000)

        # 获取页面标题和最终 URL
        title = await page.title()
        final_page_url = page.url

        logs.append(f"Page title: {title}")
        logs.append(f"Final URL: {final_page_url}")

        # 从 hook 日志中补充线索
        try:
            hook_logs = await page.evaluate("window.__MEDIA_HOOK_LOGS__ || []")
            logs.append(f"Hook logs count: {len(hook_logs)}")

            for item in hook_logs:
                payload = item.get("payload", {})
                hurl = payload.get("url")
                if hurl:
                    kind = classify_url(hurl, payload.get("contentType"))
                    if kind:
                        candidates.append({
                            "url": hurl,
                            "kind": kind,
                            "content_type": payload.get("contentType"),
                            "method": "GET",
                            "headers": {},
                            "score": score_candidate(kind, hurl, payload.get("contentType"), platform) + 5,
                            "source": "hook"
                        })
        except Exception as e:
            logs.append(f"Hook logs error: {e}")

        # 从 JSON 响应中提取视频链接
        for json_url, json_body in json_responses.items():
            json_candidates = extract_from_json(json_body, json_url, platform)
            candidates.extend(json_candidates)

        await browser.close()

    # 去重并按分数排序
    uniq: Dict[tuple, Dict[str, Any]] = {}
    for c in candidates:
        k = (c["url"], c["kind"])
        if k not in uniq or c["score"] > uniq[k]["score"]:
            uniq[k] = c

    final_candidates = sorted(uniq.values(), key=lambda x: x["score"], reverse=True)
    best = final_candidates[0] if final_candidates else None

    logs.append(f"Total candidates: {len(final_candidates)}")
    if best:
        logs.append(f"Best candidate: {best['url']} (score: {best['score']})")

    return {
        "input_url": url,
        "final_page_url": final_page_url,
        "title": title,
        "candidates": final_candidates,
        "best": best,
        "logs": logs
    }
