import os
import time
import json
from typing import Dict, Any, List, Optional

import requests


API_BASE = "https://open.tiktokapis.com/v2/research/video/comment/list/"


class TikTokAPIError(Exception):
    pass


def _get_token(config_source: Dict) -> str:
    token = config_source.get("access_token")
    if token:
        return token
    env_key = config_source.get("token_env")
    if env_key:
        env_val = os.environ.get(env_key)
        if env_val:
            return env_val
    raise TikTokAPIError("Missing TikTok access token. Set 'access_token' or 'token_env'.")


def fetch_video_comments(
    config_source: Dict,
    video_id: int,
    fields: str,
    max_count: int = 10,
    cursor: int = 0,
    timeout: int = 20,
) -> Dict[str, Any]:
    """
    Fetch comments for a TikTok video.

    Returns a dict with keys: 'comments' (list), 'cursor' (int), 'has_more' (bool)
    """
    token = _get_token(config_source)

    params = {"fields": fields}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "video_id": int(video_id),
        "max_count": int(max_count),
        "cursor": int(cursor),
    }

    try:
        resp = requests.post(API_BASE, params=params, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as e:
        raise TikTokAPIError(f"Network error: {e}")

    if resp.status_code != 200:
        raise TikTokAPIError(f"HTTP {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise TikTokAPIError("Invalid JSON response from TikTok API")

    err = data.get("error", {})
    if err and err.get("code") not in (None, "ok"):
        raise TikTokAPIError(f"API error: {err.get('code')} - {err.get('message')}")

    payload = data.get("data", {})
    comments = payload.get("comments", [])
    return {
        "comments": comments,
        "cursor": payload.get("cursor", 0),
        "has_more": bool(payload.get("has_more", False)),
    }
