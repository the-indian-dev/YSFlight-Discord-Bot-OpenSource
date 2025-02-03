import discord
from discord.ext import commands, pages
from discord import Embed

import logging
import asyncio
import re
from lib.proto import Apps

async def get_player_list(ip, port, version):
    apps = Apps(ip, int(port), 5)
    apps.connect(b"YSF_Discord_tid", version)
    return apps.server.return_info()

#Local IP Regex
local_ip_reg = "(^127\.)|(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^192\.168\.)"


class YSFlightCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="See the credentials to join the YSFlight Server linked to this Discord Server", guild_only=True)
    async def serverinfo(self, ctx):
        """Shows the IP and port of the server"""
        logging.info("{} executed servershow command".format(ctx.author.name))
        await ctx.defer()
        ip = await self.bot.db.fetch('SELECT ysf_server_ip FROM guilds WHERE guild_id = $1', ctx.guild.id)
        port = await self.bot.db.fetch('SELECT port FROM guilds WHERE guild_id = $1', ctx.guild.id)
        ver_number = await self.bot.db.fetch('SELECT version FROM guilds WHERE guild_id = $1', ctx.guild.id)
        ip = ip[0].get('ysf_server_ip')
        port = port[0].get('port')
        ver_number = ver_number[0].get('version')
        embed = discord.Embed(title="Server Address", url="https://www.youtube.com/watch?v=qJRKedSUHg4",
                              description="Server Address", color=0x109319)
        embed.add_field(name="IP Address", value=ip, inline=True)
        embed.add_field(name="Port", value=port, inline=True)
        embed.add_field(name="YSFlight Version", value=ver_number, inline=False)
        embed.set_footer(text="Programmed By the_indian_dev#0148")
        await ctx.followup.send(embed=embed)

    @commands.slash_command(description="Link your YSFlight server with the Discord Server")
    @discord.default_permissions(manage_messages=True)
    async def linkserver(self, ctx,
                ip=discord.Option(str, required=True, description="IP Address of your YSFlight Server", default=""),
                port=discord.Option(int, required=False, description="Port of your YSFlight Server (Default : 7915)", default=7915),
                version=discord.Option(int, required=False, description="Version of YSFlight on your server(Default : 20150425)", default=20150425)):
        if ip=="" or ip==None:
            await ctx.respond("⚠️ ``ip`` field cannot be empty! Please Enter the IP Address of your YSFlight Server.")
            return -1
        try:
            port = int(port)
            version = int(version)
        except ValueError:
            await ctx.respond("⚠️ You may have entered incorrect details of port/version!")
            return -1

        local_ip=False
        if re.match(local_ip_reg, ip):
            local_ip=True
        await ctx.defer()
        await self.bot.db.execute('UPDATE guilds SET port = $1 WHERE "guild_id" = $2', port, ctx.guild.id)
        await self.bot.db.execute('UPDATE guilds SET ysf_server_ip = $1 WHERE "guild_id" = $2', ip, ctx.guild.id)
        await self.bot.db.execute('UPDATE guilds SET version = $1 WHERE "guild_id" = $2', version, ctx.guild.id)
        embed = discord.Embed(title="✅Succesful Setup", url="https://www.youtube.com/watch?v=qJRKedSUHg4",
                              description="🛫", color=0x109319)
        embed.add_field(name="IP Address", value=ip, inline=True)
        embed.add_field(name="Port", value=port, inline=True)
        embed.add_field(name="YSFlight Version", value=version, inline=False)
        if local_ip:
            embed.add_field(name="⚠️ Warning", value="You may have added the Local IP which will likely not work!", inline=False)
        embed.set_footer(text="Programmed By the_indian_dev#0148")
        await ctx.followup.send(embed=embed)

    @commands.slash_command(description="See current players in your YSFlight Server")
    async def showplayers(self, ctx):
        await ctx.defer()
        ip = await self.bot.db.fetch('SELECT ysf_server_ip FROM guilds WHERE guild_id = $1', ctx.guild.id)
        port = await self.bot.db.fetch('SELECT port FROM guilds WHERE guild_id = $1', ctx.guild.id)
        version = await self.bot.db.fetch('SELECT version FROM guilds WHERE guild_id = $1', ctx.guild.id)
        ip = ip[0].get('ysf_server_ip')
        port = port[0].get('port')
        version = version[0].get('version')
        players = await get_player_list(ip, port, version)
        if players["status"] == "online":
            players_list = ""
            player_online = len(players["userList"])
            for player in players["userList"]:
                to_be_joined = ""
                to_be_joined = player + "\n"
                players_list += to_be_joined
            page1 = discord.Embed(title="Server Online", url="https://www.youtube.com/watch?v=qJRKedSUHg4",
                                  description="{} Players Online".format(player_online), color=0x109319)
            page1.add_field(name="Players Online", value="``" + players_list + "``", inline=True)
            page1.add_field(name="Version", value="``" + str(version) + "``", inline=True)
            page1.set_footer(text="Programmed By the_indian_dev#0148")
            page2 = discord.Embed(title="Server Online", url="https://www.youtube.com/watch?v=qJRKedSUHg4",
                                  description="Advanced Info", color=0x109319)
            page2.add_field(name="Current Map", value="``" + players['map'] + "``", inline=True)
            page2.add_field(name="Blackout Enabled?", value="``" + str(players['blackout']) + "``", inline=True)
            page2.add_field(name="Weather", value="``" + str(players['weather']) + "``", inline=False)
            page2.add_field(name="Radar Altitude", value="``" + str(players["radar"]) + "``", inline=True)
            page2.add_field(name="Third Person View Enabled?", value="``" + str(players["f3"]) + "``", inline=True)
            page2.add_field(name="Missile Enabled?", value="``" + str(players["missileON"]) + "``", inline=True)
            page2.set_footer(text="Programmed By the_indian_dev#0148")

            views=[page1, page2]
            page_buttons = [
                pages.PaginatorButton("first", emoji="h", style=discord.ButtonStyle.green),
                pages.PaginatorButton("last", emoji="g", style=discord.ButtonStyle.green),
                pages.PaginatorButton("prev", emoji="⏪", style=discord.ButtonStyle.green),
                pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True),
                pages.PaginatorButton("next", emoji="⏩", style=discord.ButtonStyle.green),
            ]
            paginator = pages.Paginator(pages=views, loop_pages=True, disable_on_timeout=True, timeout=20, show_disabled=True,
                                        show_indicator=True,
                                        use_default_buttons=False,
                                        custom_buttons=page_buttons)
            paginator.remove_button("first")
            paginator.remove_button("last")
            await paginator.respond(ctx.interaction, ephemeral=False)
        else:
            embed = discord.Embed(title="Unable To Reach Server", url="https://www.youtube.com/watch?v=qJRKedSUHg4",
                                  description="🛫", color=0x109319)
            embed.add_field(name="⚠️ Error", value="Server is Offline/Bot is Banned from access!", inline=False)



def setup(bot):
    bot.add_cog(YSFlightCog(bot))
    logging.info("Succesfully loaded YSFlightCog")
