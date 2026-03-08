import asyncio
from pathlib import Path
from typing import Optional, Dict

from resolver.browser import resolve_url
from resolver.extractor import classify_url
from downloader.http_download import download_file
from remux.ffmpeg import remux_stream


async def download_video(
    url: str,
    output_dir: str = "./downloads",
    title: Optional[str] = None
) -> Dict:
    """
    主下载流程：
    1. 解析 URL 获取媒体候选
    2. 选择最佳候选
    3. 根据类型下载或转码
    """
    print(f"[1/3] Resolving: {url}")

    # 解析 URL
    result = await resolve_url(url)

    if not result.get("best"):
        return {
            "success": False,
            "error": "No media candidate found",
            "result": result
        }

    best = result["best"]
    print(f"[2/3] Best candidate: {best['url']}")
    print(f"       Kind: {best['kind']}, Score: {best['score']}")

    # 准备输出路径
    video_title = title or result.get("title", "video") or "video"
    # 清理文件名 - 只保留合法字符并截断
    video_title = "".join(c for c in video_title if c.isalnum() or c in " -_").strip()[:30]
    if not video_title:
        video_title = "video"

    # 从URL中提取一个唯一标识
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    video_title = f"{video_title}_{url_hash}"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 根据类型选择下载策略
    kind = best["kind"]

    print(f"[3/3] Downloading...")

    if kind == "file":
        # 直链文件，直接下载
        # 从 URL 中提取扩展名
        url_path = best["url"].split("?")[0]
        ext = Path(url_path).suffix
        if not ext or ext not in [".mp4", ".webm", ".m4v"]:
            ext = ".mp4"
        out_path = output_dir / f"{video_title}{ext}"

        await download_file(best["url"], str(out_path))

        return {
            "success": True,
            "output_path": str(out_path),
            "result": result
        }

    elif kind in ("m3u8", "mpd"):
        # 流媒体，使用 ffmpeg 转码
        out_path = output_dir / f"{video_title}.mp4"

        success = remux_stream(best["url"], str(out_path))

        return {
            "success": success,
            "output_path": str(out_path) if success else None,
            "result": result
        }

    else:
        return {
            "success": False,
            "error": f"Unsupported media kind: {kind}",
            "result": result
        }
