from typing import Optional, List, Dict, Any


MEDIA_EXTS = (".mp4", ".m3u8", ".mpd", ".m4s", ".ts", ".webm")


def classify_url(url: str, content_type: Optional[str]) -> Optional[str]:
    """根据 URL 和 content-type 分类媒体类型"""
    u = url.lower()
    ct = (content_type or "").lower()

    if ".m3u8" in u or "application/vnd.apple.mpegurl" in ct:
        return "m3u8"
    if ".mpd" in u or "application/dash+xml" in ct:
        return "mpd"
    if any(ext in u for ext in [".mp4", ".webm"]):
        return "file"
    if any(ext in u for ext in [".m4s", ".ts"]):
        return "segment"
    if ct.startswith("video/"):
        return "file"
    if "json" in ct:
        return "json_hint"
    return None


def score_candidate(kind: str, url: str, content_type: Optional[str], platform: str = "unknown") -> int:
    """对候选媒体源进行评分"""
    score = 0

    if kind == "file":
        score += 90
    elif kind == "m3u8":
        score += 85
    elif kind == "mpd":
        score += 80
    elif kind == "segment":
        score += 30
    elif kind == "json_hint":
        score += 10

    u = url.lower()
    # 正面加分
    if "video" in u or "play" in u:
        score += 10
    if "aweme" in u or "playwm" in u:  # 抖音视频
        score += 15
    if "xhscdn" in u or "xiaohongshu" in u:  # 小红书视频CDN
        score += 20
    if "fe-video" in u:  # 小红书视频
        score += 25
    if "hd" in u or "1080" in u or "720" in u:
        score += 5

    # 负面减分
    if "watermark" in u:
        score -= 20
    if "cover" in u or "poster" in u:
        score -= 50
    if "thumb" in u:
        score -= 30
    if "chrome-extension" in u:
        score -= 100

    return score


def extract_from_json(body: str, url: str, platform: str = "unknown") -> List[Dict[str, Any]]:
    """从 JSON 响应中提取可能的视频链接"""
    import json
    candidates = []

    try:
        data = json.loads(body)
    except:
        return candidates

    def find_video_urls(obj, path=""):
        if isinstance(obj, str):
            # 检查是否是视频URL
            if any(ext in obj.lower() for ext in MEDIA_EXTS):
                kind = classify_url(obj, None)
                if kind:
                    candidates.append({
                        "url": obj,
                        "kind": kind,
                        "content_type": None,
                        "method": "GET",
                        "headers": {},
                        "score": score_candidate(kind, obj, None, platform) + 5,  # 从JSON中发现，加分
                        "source": "api_json"
                    })
        elif isinstance(obj, dict):
            # 常见抖音视频字段
            video_keys = ["play_addr", "video_url", "url", "url_list", "download_addr"]
            # 小红书特定字段
            if platform == "xhs":
                video_keys.extend(["video_info", "videoUrl", "urlList", "video", "imageInfo"])
            for key in video_keys:
                if key in obj and obj[key]:
                    find_video_urls(obj[key], f"{path}.{key}")

            # 遍历所有值
            for v in obj.values():
                find_video_urls(v, path)
        elif isinstance(obj, list):
            for item in obj:
                find_video_urls(item, path)

    find_video_urls(data)
    return candidates
