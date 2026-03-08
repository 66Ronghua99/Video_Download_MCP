import httpx
import json
from pathlib import Path
from typing import Optional, Dict
from pathlib import Path as PathLib


# Cookie 目录
COOKIE_DIR = PathLib(__file__).parent.parent / "cookies"


def get_platform_from_url(url: str) -> str:
    """根据 URL 判断平台"""
    if "xiaohongshu.com" in url or "xhscdn" in url:
        return "xhs"
    elif "douyin.com" in url or "douyinvod" in url:
        return "douyin"
    return "unknown"


def load_cookies_for_download(platform: str) -> Dict[str, str]:
    """为下载请求加载 Cookie"""
    cookie_file = COOKIE_DIR / f"{platform}.json"
    if cookie_file.exists():
        try:
            with open(cookie_file) as f:
                cookies = json.load(f)
            # 转换为 Cookie 字符串
            return {c["name"]: c["value"] for c in cookies}
        except Exception:
            pass
    return {}


async def download_file(url: str, out_path: str, headers: Optional[Dict[str, str]] = None):
    """直链文件下载"""
    platform = get_platform_from_url(url)

    # 根据平台设置默认 Referer
    if platform == "xhs":
        default_referer = "https://www.xiaohongshu.com/"
    else:
        default_referer = "https://www.douyin.com/"

    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": default_referer
    }

    # 添加 Cookie
    cookies = load_cookies_for_download(platform)
    cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
    if cookie_str:
        default_headers["Cookie"] = cookie_str

    if headers:
        default_headers.update(headers)

    async with httpx.AsyncClient(follow_redirects=True, timeout=300) as client:
        async with client.stream("GET", url, headers=default_headers) as resp:
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            Path(out_path).parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        progress = downloaded / total * 100
                        print(f"\rDownloading: {progress:.1f}%", end="", flush=True)

            print()  # 换行
            return out_path
