from typing import List

import dico
import dico_command
import dico_interaction

from dico_command.utils import search

from config import Config


class Vote(dico_command.Addon):
    async def addon_check(self, ctx: dico_command.Context):
        return bool(search(ctx.member.roles, name="TEAM"))

    @staticmethod
    def split_vote(data: str) -> List[str]:
        return data.split(",")[:-1]

    @dico_interaction.component_callback("vote")  # Custom ID starts with "vote"
    async def vote_callback(self, ctx: dico_interaction.InteractionContext):
        await ctx.defer(ephemeral=True)
        parent = self.bot.get_channel(ctx.channel_id).parent_id
        name = self.bot.get_channel(parent).name

        author = ctx.author.id

        # Method 1
        async with self.bot.db.execute("SELECT * FROM vote") as cur:
            data = tuple(map(dict, await cur.fetchall()))
        vote_bot = list(filter(lambda d: d["name"] == name, data))[0]
        idea_voted = author in self.split_vote(vote_bot["idea_vote"])
        make_voted = author in self.split_vote(vote_bot["make_vote"])
        total_idea_votes = len(
            tuple(filter(lambda d: author in self.split_vote(d["idea_vote"]), data))
        )
        total_make_votes = len(
            tuple(filter(lambda d: author in self.split_vote(d["make_vote"]), data))
        )

        # Method 2
        """
        async with self.bot.db.execute("SELECT idea_vote, make_vote FROM vote WHERE name=?", (name,)) as cur:
            data = dict(await cur.fetchone())
        idea_voted = author in self.split_vote(data["idea_vote"])
        make_voted = author in self.split_vote(data["make_vote"])
        async with self.bot.db.execute("SELECT name FROM vote WHERE idea_vote LIKE ?", (f"%{author}%",)) as cur:
            total_idea_votes = len(await cur.fetchall())
        async with self.bot.db.execute("SELECT name FROM vote WHERE make_vote LIKE ?", (f"%{author}%",)) as cur:
            total_make_votes = len(await cur.fetchall())
        """

        if ctx.data.custom_id.endswith(Config.IDEATHON_NAME):
            if idea_voted:
                return await ctx.send("❌ 이미 해당 봇의 아이디어톤 분야에 투표했습니다.")
            elif total_idea_votes >= Config.MAX_IDEATHON_VOTES:
                return await ctx.send("❌ 투표 가능 횟수를 초과했습니다.")
            await self.bot.db.execute(
                "UPDATE vote SET idea_vote=idea_vote||? WHERE name=?",
                (f"{author},", name),
            )
        elif ctx.data.custom_id.endswith(Config.MAKETHON_NAME):
            if make_voted:
                return await ctx.send("❌ 이미 해당 봇의 메이크톤 분야에 투표했습니다.")
            elif total_make_votes >= Config.MAX_MAKETHON_VOTES:
                return await ctx.send("❌ 투표 가능 횟수를 초과했습니다.")
            await self.bot.db.execute(
                "UPDATE vote SET make_vote=make_vote||? WHERE name=?",
                (f"{author},", name),
            )
        await self.bot.db.commit()
        await ctx.send("✅ 해당 봇에 투표했습니다.")

    @dico_command.command("vote")
    async def vote(self, ctx: dico_command.Context):
        pass

    @vote.subcommand("start")
    async def vote_start(self, ctx: dico_command.Context):
        names = []
        for channel in await self.bot.request_guild_channels(ctx.guild_id):
            if channel.name in [Config.IDEATHON_NAME, Config.MAKETHON_NAME]:
                parent = self.bot.get_channel(channel.parent_id)
                if parent.name in Config.EXCLUDE_CATEGORIES:
                    continue
                button = dico.Button(
                    style=dico.ButtonStyles.SUCCESS,
                    label="투표하기",
                    custom_id=f"vote{channel.name}",
                    emoji="📥",
                )
                await channel.send("버튼을 눌러 투표하세요!", components=[dico.ActionRow(button)])
                await channel.modify(
                    permission_overwrites=[
                        dico.Overwrite(
                            role=ctx.guild_id,
                            deny=dico.PermissionFlags("SEND_MESSAGES"),
                        )
                    ],
                    reason="투표 시작",
                )
                if parent.name not in names:
                    names.append(parent.name)
        await self.bot.db.executemany(
            """INSERT INTO vote VALUES(?, '', '')""", [(x,) for x in names]
        )
        await self.bot.db.commit()
        await ctx.reply("✅ 세팅이 완료됐습니다.")

    @vote.subcommand("toggle")
    async def vote_toggle(self, ctx: dico_command.Context):
        for channel in await ctx.guild.request_channels():
            if channel.name in [Config.IDEATHON_NAME, Config.MAKETHON_NAME]:
                parent = self.bot.get_channel(channel.parent_id)
                if parent.name in Config.EXCLUDE_CATEGORIES:
                    continue
                msg = await self.bot.request_channel_message(channel, channel.last_message_id)
                # msg = self.bot.get_message(channel.last_message_id)
                msg.components[0].components[0].disabled = (
                    not msg.components[0].components[0].disabled
                )
                await msg.edit(components=msg.components)
        await ctx.reply("✅ 세팅이 완료됐습니다.")

    @vote.subcommand("status")
    async def vote_status(self, ctx: dico_command.Context):
        async with self.bot.db.execute("""SELECT * FROM vote""") as cur:
            data = map(dict, await cur.fetchall())
        text = ""
        for x in data:
            text += f"`{x['name']}`: 아이디어톤 `{len(self.split_vote(x['idea_vote']))}`표 | 메이크톤 `{len(self.split_vote(x['make_vote']))}`표\n"
        await ctx.reply(text)


def load(bot):
    bot.load_addons(Vote)


def unload(bot):
    bot.unload_addons(Vote)
