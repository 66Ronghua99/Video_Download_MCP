import subprocess
from pathlib import Path


def remux_stream(input_url: str, out_path: str, referer: str = "https://www.douyin.com/") -> bool:
    """
    使用 ffmpeg 封装 m3u8/mpd 流
    -codec copy 直接拷贝流而不重编码
    """
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",  # 覆盖输出文件
        "-headers", f"Referer: {referer}",
        "-i", input_url,
        "-codec", "copy",
        "-bsf:a", "aac_adtstoasc",  # 移除音频比特流过滤器
        out_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode == 0:
            print(f"Remux completed: {out_path}")
            return True
        else:
            print(f"FFmpeg error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("FFmpeg timeout")
        return False
    except FileNotFoundError:
        print("FFmpeg not found. Please install ffmpeg.")
        return False


def get_video_duration(input_path: str) -> float:
    """获取视频时长（秒）"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0
