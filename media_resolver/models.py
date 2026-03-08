from pydantic import BaseModel
from typing import Optional, List, Dict


class MediaCandidate(BaseModel):
    url: str
    kind: str                   # mp4, m3u8, mpd, segment, json_hint
    content_type: Optional[str] = None
    method: str = "GET"
    headers: Dict[str, str] = {}
    score: int = 0
    source: str = "network"     # network / hook / dom / api_json
    note: Optional[str] = None


class ResolveResult(BaseModel):
    input_url: str
    final_page_url: Optional[str] = None
    title: Optional[str] = None
    candidates: List[MediaCandidate] = []
    best: Optional[MediaCandidate] = None
    logs: List[str] = []


class DownloadRequest(BaseModel):
    url: str
    output_path: Optional[str] = None
