import json
from pathlib import Path

from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, ConnectEvent


def load_username_from_config(config_path: Path) -> str:
    """Load TikTok live username from config.json.

    Expects path at project root and field at `comment_source.live_username`.
    Returns a string like "@username" or raises ValueError if missing.
    """
    if not config_path.exists():
        raise ValueError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    src = data.get("comment_source", {})
    username = src.get("live_username")
    if not username or not isinstance(username, str):
        raise ValueError(
            "Missing 'comment_source.live_username' in config.json."
        )
    return username


# Resolve username from config (only this field is required)
CONFIG_PATH = Path(__file__).parent / "config.json"
UNIQUE_ID = load_username_from_config(CONFIG_PATH)

# Init connector using only the configured username
client = TikTokLiveClient(unique_id=UNIQUE_ID)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"Connected to @{event.unique_id} — room id: {client.room_id}")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    print(f"[Chat] {event.user.nickname}: {event.comment}")


@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    print(f"[Gift] {event.user.unique_id} sent \"{event.gift.name}\"")


if __name__ == "__main__":
    client.run()