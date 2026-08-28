"""
zoom_client.py — Zoom Server-to-Server OAuth + meeting creation.

Requires in .env:
    ZOOM_ACCOUNT_ID
    ZOOM_CLIENT_ID
    ZOOM_CLIENT_SECRET
"""

import os
import httpx


def get_access_token() -> str:
    resp = httpx.post(
        "https://zoom.us/oauth/token",
        params={
            "grant_type": "account_credentials",
            "account_id": os.environ["ZOOM_ACCOUNT_ID"],
        },
        auth=(os.environ["ZOOM_CLIENT_ID"], os.environ["ZOOM_CLIENT_SECRET"]),
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_meeting(topic: str, start_time_iso: str, duration_minutes: int) -> dict:
    """Create a scheduled Zoom meeting and return {join_url, meeting_id}.

    start_time_iso should be an ISO 8601 string with timezone offset,
    e.g. "2026-05-07T10:00:00+10:00".
    """
    token = get_access_token()
    resp = httpx.post(
        "https://api.zoom.us/v2/users/me/meetings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "topic": topic,
            "type": 2,  # scheduled meeting
            "start_time": start_time_iso,
            "duration": duration_minutes,
            "settings": {
                "join_before_host": True,
                "waiting_room": False,
                "mute_upon_entry": False,
                "jbh_time": 0,
                "use_pmi": False,  # don't use your Personal Meeting ID
                "approval_type": 2,
            },
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "join_url": data["join_url"],
        "meeting_id": str(data["id"]),
    }


def end_meeting(meeting_id: str) -> None:
    """End a live Zoom meeting. Requires scope meeting:update:status:admin."""
    token = get_access_token()
    resp = httpx.put(
        f"https://api.zoom.us/v2/meetings/{meeting_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "end"},
    )
    resp.raise_for_status()
