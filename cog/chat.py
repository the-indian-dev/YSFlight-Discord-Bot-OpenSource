import asyncio
from asyncpg.exceptions import UniqueViolationError

import discord
from discord.ext import commands
from discord import Embed

import logging
import lib.ys_proto as ys_proto


class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.subscriber = ys_proto.Subscription()
        self.subscribers = []

        @self.subscriber.on_message
        def h(msg, server):
            self.bot.loop.create_task(self.chat_send(msg, server))

    @commands.Cog.listener()
    async def on_ready(self):
        a = await self.bot.db.fetch("SELECT * from chat")
        for server_info in list(a):
            server = ys_proto.Server(ip=server_info[2], port=server_info[3], version=server_info[4])
            self.subscribers.append([server, server_info[1]])
            self.subscriber.subscribe(server)

    @commands.slash_command(description="Setup Chat-sync for this channel")
    async def setup_chat_sync(self, ctx):
        await ctx.respond("Adding server for chat sync...")
        ip = await self.bot.db.fetch('SELECT ysf_server_ip FROM guilds WHERE guild_id = $1', ctx.guild.id)
        port = await self.bot.db.fetch('SELECT port FROM guilds WHERE guild_id = $1', ctx.guild.id)
        ver_number = await self.bot.db.fetch('SELECT version FROM guilds WHERE guild_id = $1', ctx.guild.id)
        ip = ip[0].get('ysf_server_ip')
        port = port[0].get('port')
        ver_number = ver_number[0].get('version')
        try:
            await self.bot.db.execute('INSERT INTO chat("server_id","channel_id") VALUES ($1, $2)', ctx.guild.id, ctx.channel.id)
            await self.bot.db.execute('UPDATE chat SET server_port = $1 WHERE "server_id" = $2', port, ctx.guild.id)
            await self.bot.db.execute('UPDATE chat SET server_ip = $1 WHERE "server_id" = $2', ip, ctx.guild.id)
            await self.bot.db.execute('UPDATE chat SET channel_id = $1 WHERE "server_id" = $2', int(ctx.channel.id), ctx.guild.id)
        except UniqueViolationError:
            await ctx.followup.send("""Cannot Add more than one YSFlight Server for one discord server!\n
Please use /linkserver to setup another server""")
            return -1

        self.subscriber.subscribe(server=ys_proto.Server(ip=ip, port=port, version=ver_number))
        await ctx.followup.send("Added server!")

    async def chat_send(self, msg, server):
        found = False
        for subscriber in self.subscribers:
            if subscriber[0] == server:
                found = True
                chnl_id = subscriber[1]
        if not found:
            print(server, self.subscribers)
            logging.warning("Server not found!")
            return -1
        channel = self.bot.get_channel(chnl_id)
        await channel.send(msg)

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.author.bot:
            return -1
        chnl_id = ctx.channel.id
        found_server = False
        for subscriber in self.subscribers:
            if chnl_id == subscriber[1]:
                server_snd = subscriber[0]
                self.subscriber.interact(server_snd, str(ctx.content), tag='[BOT]['+ctx.author.name+'#'+ctx.author.discriminator+']')
                found_server = True
                return 0
        if not found_server:
            await ctx.reply("Server linked not found! ")



def setup(bot):
    bot.add_cog(ChatCog(bot))
    logging.info("Succesfully loaded ChatCog")