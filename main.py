import os
import logging

import dico
import dico_command
import dico_interaction

from config import Config

logging.basicConfig(level=logging.DEBUG)

bot = dico_command.Bot(Config.TOKEN, "!", intents=dico.Intents.full())
interaction = dico_interaction.InteractionClient(client=bot)
bot.on_ready = lambda ready: print(f"READY event dispatched.")
[bot.load_module(f"addons.{x.replace('.py', '')}") for x in os.listdir("addons") if x.endswith('.py') and not x.startswith("_")]
bot.load_module("dp")
bot.run()
