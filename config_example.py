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
    EXCLUDE_ROLES: List[Role.TYPING] = [922108075471687720, 922108199753089074]
    REVIEWER_ROLE: Snowflake.TYPING = 914163505966481438

    # Utils
    IMAGE_CHANNEL_ID: Snowflake.TYPING = 924280161413787668
    TEAM_ROLE: Role.TYPING = 914163148351766578
