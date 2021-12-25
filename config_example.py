from typing import List

from dico import Snowflake, Role


class Config:
    # Bot
    TOKEN: str = ""
    GUILD_ID: Snowflake.TYPING = 911676954317582368

    # Vote
    IDEATHON_NAME: str = "아이디어톤"
    MAKETHON_NAME: str = "메이크톤"
    MAX_IDEATHON_VOTES: int = 2
    MAX_MAKETHON_VOTES: int = 2
    EXCLUDE_CATEGORIES: List[str] = ["메뉴얼"]

    # Utils
    IMAGE_CHANNEL_ID: Snowflake.TYPING = 924280161413787668
    TEAM_ROLE: Role.TYPING = 914163148351766578
