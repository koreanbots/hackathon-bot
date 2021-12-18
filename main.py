import os
import logging

from modules.bot import HackathonBot

logging.basicConfig(level=logging.DEBUG)

bot = HackathonBot()
[
    bot.load_module(f"addons.{x.replace('.py', '')}")
    for x in os.listdir("addons")
    if x.endswith(".py") and not x.startswith("_")
]
bot.run()
