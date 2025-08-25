import requests

from app.core.config import settings
from app.models.models import Post


def print_post(post: Post):
    if (not settings.USE_SRPRINT) or settings.SRPRINT_BASE_URL is None:
        print("print post guard failed")
        return

    job = {
        "parts": [
            {
                "cmd": "mode",
                "double_height_mode": True,
                "double_width_mode": True,
                "inverse_printing_mode": True,
            },
            {"cmd": "text", "text": "MEGAFON!"},
            {"cmd": "CR"},
            {"cmd": "LF"},
            {
                "cmd": "mode",
                "double_height_mode": False,
                "double_width_mode": False,
                "inverse_printing_mode": False,
            },
            {"cmd": "text", "text": f"New Post from {post.created_by_name}\n"},
            {
                "cmd": "text",
                "text": f"Posted {post.created_at.strftime('%d.%m.%Y %H:%M:%S')}\n",
            },
            {"cmd": "text", "text": f"---\n{post.content}\n---\n\n"},
            {"cmd": "feed"},
        ]
    }

    requests.post(f"{settings.SRPRINT_BASE_URL}/schedule", json=job)
    print("Scheduled print job for SRPRINT")
