from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from resolver.browser import resolve_url
from downloader import download_video
from models import ResolveResult, DownloadRequest
from pydantic import BaseModel


class ResolveRequest(BaseModel):
    url: str


app = FastAPI(title="Media Resolver API")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Media Resolver API"}


@app.post("/resolve")
async def resolve(req: ResolveRequest):
    """
    解析 URL，返回媒体候选列表
    """
    try:
        result = await resolve_url(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download")
async def download(req: DownloadRequest):
    """
    解析并下载视频
    """
    try:
        result = await download_video(
            url=req.url,
            output_dir=req.output_path or "./downloads"
        )
        if result.get("success"):
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Download failed")
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CLI 入口
if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python app.py <url>")
            return

        url = sys.argv[1]
        print(f"Downloading: {url}")

        result = await download_video(url)
        if result.get("success"):
            print(f"Success! Saved to: {result['output_path']}")
        else:
            print(f"Failed: {result.get('error')}")
            print("\nCandidates:")
            for c in result.get("result", {}).get("candidates", []):
                print(f"  [{c['score']}] {c['kind']}: {c['url'][:100]}")

    asyncio.run(main())
