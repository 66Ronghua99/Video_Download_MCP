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


async def _resolve_with_browser(
    p,
    url: str,
    platform: str,
    original_note_id: Optional[str],
    hooks_content: str,
    headless: bool,
    browser_args: List[str]
) -> Dict[str, Any]:
    """使用指定浏览器配置解析 URL"""
    candidates: List[Dict[str, Any]] = []
    logs: List[str] = []

    browser = await p.chromium.launch(
        headless=headless,
        args=browser_args
    )

    try:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await context.add_init_script(hooks_content)

        json_responses: Dict[str, str] = {}

        async def on_response(resp):
            try:
                ct = resp.headers.get("content-type", "")
                status = resp.status
                if status >= 200 and status < 400:
                    resp_url = resp.url
                    kind = classify_url(resp_url, ct)
                    if kind:
                        candidates.append({
                            "url": resp_url,
                            "kind": kind,
                            "content_type": ct,
                            "method": "GET",
                            "headers": {},
                            "score": score_candidate(kind, resp_url, ct, platform),
                            "source": "network"
                        })
                    if "json" in ct and status == 200:
                        try:
                            body = await resp.text()
                            json_responses[resp_url] = body
                        except Exception:
                            pass
            except Exception as e:
                logs.append(f"response parse error: {e}")

        context.on("response", on_response)
        page = await context.new_page()

        mode = "headless" if headless else "headed"
        logs.append(f"[{mode}] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)

        logs.append(f"[{mode}] Waiting 5 seconds for video to load...")
        await page.wait_for_timeout(5000)

        # 检查重定向
        current_url = page.url
        if platform == "xhs" and original_note_id and "/explore/" in current_url:
            current_match = re.search(r'/explore/([a-zA-Z0-9]+)', current_url)
            current_note_id = current_match.group(1) if current_match else None

            if current_note_id and current_note_id != original_note_id:
                logs.append(f"[{mode}] Redirect detected: {current_note_id} -> {original_note_id}")
                candidates.clear()
                json_responses.clear()
                await context.close()
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                await context.add_init_script(hooks_content)
                context.on("response", on_response)
                page = await context.new_page()
                new_url = f"https://www.xiaohongshu.com/explore/{original_note_id}"
                logs.append(f"[{mode}] Re-navigating to: {new_url}")
                await page.goto(new_url, wait_until="domcontentloaded", timeout=45000)
                logs.append(f"[{mode}] Waiting 5 seconds for video to load (retry)...")
                await page.wait_for_timeout(5000)

        title = await page.title()
        final_page_url = page.url
        logs.append(f"[{mode}] Page title: {title}")
        logs.append(f"[{mode}] Final URL: {final_page_url}")

        # 从 hook 日志中补充线索
        try:
            hook_logs = await page.evaluate("window.__MEDIA_HOOK_LOGS__ || []")
            logs.append(f"[{mode}] Hook logs count: {len(hook_logs)}")
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

        return {
            "candidates": candidates,
            "logs": logs,
            "title": title,
            "final_page_url": final_page_url,
            "success": True
        }
    except Exception as e:
        await browser.close()
        return {
            "candidates": [],
            "logs": [f"Error in {mode} mode: {e}"],
            "title": "",
            "final_page_url": "",
            "success": False,
            "error": str(e)
        }


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

    # 获取 hooks.js 的绝对路径
    hooks_path = Path(__file__).parent / "hooks.js"
    hooks_content = hooks_path.read_text()

    # 浏览器参数配置
    headless_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1920,1080',
    ]

    headed_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--start-maximized',
    ]

    async with async_playwright() as p:
        # 优先尝试无头模式
        print("Attempting with headless browser...")
        result = await _resolve_with_browser(
            p, url, platform, original_note_id,
            hooks_content, True, headless_args
        )

        # 如果无头模式失败或没有获取到候选，尝试有头模式
        if not result["success"] or (result["candidates"] and len(result["candidates"]) == 0):
            print("Headless failed or no candidates, falling back to headed browser...")
            result = await _resolve_with_browser(
                p, url, platform, original_note_id,
                hooks_content, False, headed_args
            )

        candidates = result["candidates"]
        logs = result["logs"]
        title = result["title"]
        final_page_url = result["final_page_url"]

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
