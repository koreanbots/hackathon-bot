import asyncio

from typing import List

import dico
import dico_command
import dico_interaction

from dico.exception import HTTPError
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

        # author = ctx.author.id
        if not ctx.member.role_ids:
            return await ctx.send("❌ 해커톤에 참여하지 않으신 경우 투표하실 수 없습니다.")
        if (
            Config.TEAM_ROLE in ctx.member.role_ids
            or Config.REVIEWER_ROLE in ctx.member.role_ids
        ):
            return await ctx.send("❌ 한디리 TEAM 분들과 심사위원분들은 투표하실 수 없습니다.")
        team_role = [
            x
            for x in ctx.member.roles
            if x.id not in Config.EXCLUDE_ROLES and x.id != 918472234069286953
        ]
        if not team_role:
            return await ctx.send("❌ 해커톤에 참여하지 않으신 경우 투표하실 수 없습니다.")
        team_role = team_role[0]
        if team_role.name == name:
            return await ctx.send("❌ 자신의 봇에는 투표하실 수 없습니다.")

        async with self.bot.db.execute("SELECT * FROM vote") as cur:
            data = tuple(map(dict, await cur.fetchall()))
        vote_bot = list(filter(lambda d: d["name"] == name, data))[0]
        idea_voted = team_role.id in self.split_vote(vote_bot["idea_vote"])
        make_voted = team_role.id in self.split_vote(vote_bot["make_vote"])
        total_idea_votes = len(
            tuple(
                filter(lambda d: team_role.id in self.split_vote(d["idea_vote"]), data)
            )
        )
        total_make_votes = len(
            tuple(
                filter(lambda d: team_role.id in self.split_vote(d["make_vote"]), data)
            )
        )

        if ctx.data.custom_id.endswith(Config.IDEATHON_NAME):
            if idea_voted:
                return await self.cancel_vote(ctx, "아이디어톤", team_role, name)
                # return await ctx.send("❌ 이미 해당 봇의 아이디어톤 분야에 투표했습니다.")
            elif total_idea_votes >= Config.MAX_IDEATHON_VOTES:
                return await ctx.send("❌ 투표 가능 횟수를 초과했습니다.")
            await self.bot.db.execute(
                "UPDATE vote SET idea_vote=idea_vote||? WHERE name=?",
                (f"{team_role.id},", name),
            )
        elif ctx.data.custom_id.endswith(Config.MAKETHON_NAME):
            if make_voted:
                return await self.cancel_vote(ctx, "메이크톤", team_role, name)
                # return await ctx.send("❌ 이미 해당 봇의 메이크톤 분야에 투표했습니다.")
            elif total_make_votes >= Config.MAX_MAKETHON_VOTES:
                return await ctx.send("❌ 투표 가능 횟수를 초과했습니다.")
            await self.bot.db.execute(
                "UPDATE vote SET make_vote=make_vote||? WHERE name=?",
                (f"{team_role.id},", name),
            )
        await self.bot.db.commit()
        await ctx.send("✅ 해당 봇에 투표했습니다.")

    async def cancel_vote(
        self,
        ctx: dico_interaction.InteractionContext,
        was_from: str,
        team_role: dico.Role,
        name: str,
    ):
        yes_button = dico.Button(
            style=dico.ButtonStyles.SUCCESS, emoji="⭕", custom_id=f"confy{ctx.id}"
        )
        no_button = dico.Button(
            style=dico.ButtonStyles.DANGER, emoji="❌", custom_id=f"confn{ctx.id}"
        )
        await ctx.send(
            f"⚠ 이미 해당 봇의 {was_from} 분야에 투표했습니다. 투표를 취소할까요?",
            components=[dico.ActionRow(yes_button, no_button)],
        )
        yes_button.disabled = True
        no_button.disabled = True

        def check(inter: dico_interaction.InteractionContext):
            return (
                inter.type.message_component
                and inter.data.custom_id.startswith("conf")
                and inter.data.custom_id.endswith(str(ctx.id))
            )

        try:
            resp = await self.bot.interaction.wait_interaction(check=check, timeout=30)
            await resp.send(update_message=True)
            if resp.data.custom_id.startswith("confy"):
                vote = "make_vote" if was_from == Config.MAKETHON_NAME else "idea_vote"
                await self.bot.db.execute(
                    f"UPDATE vote SET {vote}=REPLACE({vote}, ?, '') WHERE name=?",
                    (f"{team_role.id},", name),
                )
                await self.bot.db.commit()
                await ctx.edit_original_response(
                    content="✅ 성공적으로 투표를 취소했습니다.",
                    components=[dico.ActionRow(yes_button, no_button)],
                )
            else:
                await ctx.edit_original_response(
                    content="✅ 투표 취소를 취소했습니다.",
                    components=[dico.ActionRow(yes_button, no_button)],
                )
        except asyncio.TimeoutError:
            await ctx.edit_original_response(
                content="❌ 시간이 초과됐습니다. 아무것도 변경되지 않았습니다.",
                components=[dico.ActionRow(yes_button, no_button)],
            )

    @dico_command.command("vote")
    async def vote(self, ctx: dico_command.Context):
        pass

    @vote.subcommand("start")
    async def vote_start(self, ctx: dico_command.Context, to_open: str):
        names = []
        for channel in await self.bot.request_guild_channels(ctx.guild_id):
            if channel.name in [to_open]:
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
        if to_open == Config.IDEATHON_NAME:
            await self.bot.db.executemany(
                """INSERT INTO vote VALUES(?, '', '')""", [(x,) for x in names]
            )
        await self.bot.db.commit()
        await ctx.reply("✅ 세팅이 완료됐습니다.")

    @vote.subcommand("toggle")
    async def vote_toggle(self, ctx: dico_command.Context, to_lock: str = None):
        if not to_lock:
            lock = [Config.IDEATHON_NAME, Config.MAKETHON_NAME]
        else:
            lock = [to_lock]
        for channel in await ctx.guild.request_channels():
            if channel.name in lock:
                parent = self.bot.get_channel(channel.parent_id)
                if parent.name in Config.EXCLUDE_CATEGORIES:
                    continue
                try:
                    msg = await self.bot.request_channel_message(
                        channel, channel.last_message_id
                    )
                except HTTPError:
                    await ctx.reply(f"{channel.mention} 실패")
                    continue
                # msg = self.bot.get_message(channel.last_message_id)
                msg.components[0].components[0].disabled = (
                    not msg.components[0].components[0].disabled
                )
                await msg.edit(components=msg.components)
        await ctx.reply("✅ 세팅이 완료됐습니다.")

    @vote.subcommand("status")
    async def vote_status(
        self, ctx: dico_command.Context, to_show: str = None, clean: str = None
    ):
        async with self.bot.db.execute("""SELECT * FROM vote""") as cur:
            data = map(dict, await cur.fetchall())
        text = ""
        clean = bool(clean == "clean")
        if to_show == Config.IDEATHON_NAME:
            data = sorted(
                data, key=lambda n: len(self.split_vote(n["idea_vote"])), reverse=True
            )
        elif to_show == Config.MAKETHON_NAME:
            data = sorted(
                data, key=lambda n: len(self.split_vote(n["make_vote"])), reverse=True
            )
        for i, x in enumerate(data):
            i += 1
            if i == 1:
                emoji = "🥇 "
            elif i == 2:
                emoji = "🥈 "
            elif i == 3:
                emoji = "🥉 "
            else:
                emoji = ""
            if not to_show:
                text += f"`{x['name']}`: 아이디어톤 `{len(self.split_vote(x['idea_vote']))}`표 | 메이크톤 `{len(self.split_vote(x['make_vote']))}`표\n"
            elif to_show == Config.IDEATHON_NAME:
                vote_count = len(self.split_vote(x["idea_vote"]))
                if clean and not vote_count:
                    continue
                text += f"{emoji}#{i} `{x['name']}`: 아이디어톤 `{vote_count}`표\n"
            elif to_show == Config.MAKETHON_NAME:
                vote_count = len(self.split_vote(x["make_vote"]))
                if clean and not vote_count:
                    continue
                text += f"{emoji}#{i} `{x['name']}`: 메이크톤 `{vote_count}`표\n"
        await ctx.reply(text)

    @vote.subcommand("voters")
    async def vote_voters(self, ctx: dico_command.Context, to_show: str = None):
        async with self.bot.db.execute("SELECT * FROM vote") as cur:
            data = tuple(map(dict, await cur.fetchall()))
        members = await ctx.guild.list_members(limit=200)
        text = ""
        for member in members:
            if (
                not member.roles
                or Config.TEAM_ROLE in member.role_ids
                or Config.REVIEWER_ROLE in member.role_ids
                or 923940331152629771 in member.role_ids
                or 918472234069286953 in member.role_ids
            ):
                continue
            team_role = [x for x in member.roles if x.id not in Config.EXCLUDE_ROLES][0]
            total_idea_votes = len(
                tuple(
                    filter(
                        lambda d: team_role.id in self.split_vote(d["idea_vote"]), data
                    )
                )
            )
            total_make_votes = len(
                tuple(
                    filter(
                        lambda d: team_role.id in self.split_vote(d["make_vote"]), data
                    )
                )
            )
            if not to_show:
                text += f"<@&{team_role.id}>: 아이디어톤 `{total_idea_votes}`표 | 메이크톤 `{total_make_votes}`표\n"
            elif to_show == Config.IDEATHON_NAME:
                text += f"<@&{team_role.id}>: 아이디어톤 `{total_idea_votes}`표\n"
            elif to_show == Config.MAKETHON_NAME:
                text += f"<@&{team_role.id}>: 메이크톤 `{total_make_votes}`표\n"
        await ctx.reply(text)


def load(bot):
    bot.load_addons(Vote)


def unload(bot):
    bot.unload_addons(Vote)
