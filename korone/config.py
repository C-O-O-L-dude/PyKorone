from typing import List

# Bot token from Bot Father
TOKEN: str = "1924336789:AAGHCcmrWb3M0gWEjCGZUFX4LqDTYVovNuU"

# Your API ID and API HASH
# Get it from https://my.telegram.org/apps
API_ID: int = 2712818
API_HASH: str = "fda406cc4f648c303a0fb77255f2a026"

# Sudoers IDs (to use some special commands)
OWNER: int = 1517181772
SUDOERS: List[int] = [1517181772]
SUDOERS.append(OWNER)

# Prefixes for commands, e.g: /start and !start
PREFIXES: List[str] = ["/", "!"]

# SpamWatch API used for automatic bans
# Get it from https:/t.me/SpamWatchBot
SW_API: str = "WtVoY5eIvpIqakuWsHiMU29C1Xsjcqj3SpMLfldZ3u8zKshloS0meZAPy~ourVt1"

# Required to use Reddit-related commands
# Get it from https://www.reddit.com/prefs/apps
REDDIT_SECRET: str = ""
REDDIT_ID: str = ""
