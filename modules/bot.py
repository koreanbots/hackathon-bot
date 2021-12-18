import aiosqlite

from dico import Intents
from dico_command import Bot
from dico_interaction import InteractionClient

from config import Config


class HackathonBot(Bot):
    db: aiosqlite.Connection

    def __init__(self):
        super().__init__(Config.TOKEN, "!", intents=Intents.full())
        self.interaction = InteractionClient(client=self)
        self.on_ready = lambda ready: print(f"READY event dispatched.")
        self.load_module("dp")
        self.loop.create_task(self.init_bot())

    async def init_bot(self):
        await self.wait_ready()
        self.db = await aiosqlite.connect("vote.db")
        self.db.row_factory = aiosqlite.Row
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS vote 
                ("name" TEXT NOT NULL PRIMARY KEY,
                "idea_vote" TEXT NOT NULL DEFAULT '',
                "make_vote" TEXT NOT NULL DEFAULT '')"""
        )
        await self.db.commit()

    async def close(self):
        await self.db.close()
        await super().close()
