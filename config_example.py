from dico import Snowflake


class Config:
    # Bot
    TOKEN: str = ""
    GUILD_ID: Snowflake = Snowflake(911676954317582368)

    # Vote
    IDEATHON_NAME: str = "아이디어톤"
    MAKETHON_NAME: str = "메이크톤"
    MAX_IDEATHON_VOTES: int = 2
    MAX_MAKETHON_VOTES: int = 2
    EXCLUDE_CATEGORIES: str = ["메뉴얼"]
