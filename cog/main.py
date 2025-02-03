import discord
from discord.ext import commands
from discord import Embed

import cpuinfo
import logging


class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logging.info("[INFO] NEW SERVER! Guild Name : {} Guild ID : {}".format(guild.name, guild.id))
        channel = self.bot.get_channel(768027235470409771)
        await channel.send(
            "<@557467854266433537>!!! I got added to a new server\nGuild Name : {}\nGuild ID : {}".format(guild.name,
                                                                                                          guild.id))

        prefix = await self.bot.db.fetch('SELECT prefix FROM guilds WHERE guild_id = $1', guild.id)
        if len(prefix) == 0:
            await self.bot.db.execute('INSERT INTO guilds("guild_id",prefix) VALUES ($1, $2)', guild.id, "r")

        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    """Hello I am YSFlight Server Bot! I provide utility to connect your YSFlight Server with your Discord Server.\nIf you're an Adminstator of this server then use ``/linkserver`` to get started!""")
            break

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond("⚠️ Slow down buddy! Please wait a few seconds before trying again.")
        else:
            raise error

    @commands.slash_command(description="Know more about the developer of this bot")
    async def credits(self, ctx):
        """Shows credit nothing else"""
        embed_none = '\u200b'
        embed = Embed(title="Credits", url="https://github.com/the-indian-dev",
                      description="About the developer", color=0x109319)
        embed.add_field(name=embed_none, value="Hi, I am @the-indian-dev aka Ritabrata Das", inline=False)
        embed.add_field(name=embed_none,
                        value="<:github:928249835625250836> [Github Profile](https://github.com/the-indian-dev)",
                        inline=False)
        embed.add_field(name=embed_none, value="<:chrome:928251220529905695> [Website](https://theindiandev.in)",
                        inline=False)
        av_user = await self.bot.fetch_user(557467854266433537)
        av = av_user.avatar
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/927828410120687617/928187062291669002/durga-nft-2.jpg")
        embed.set_footer(text="Programmed By the_indian_dev#0148",
                         icon_url="https://avatars.githubusercontent.com/u/70189264")
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Ping the Discord API from the bot's servers")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        """Pings the discord api for average time taken to respond and sends the value to guild"""
        logging.info("{} executed ping command".format(ctx.author.name))
        embed = discord.Embed(title="Bot Info", url="https://www.youtube.com/watch?v=qJRKedSUHg4",
                              description="Current Bot Status", color=0x109319)
        cpu = cpuinfo.get_cpu_info()['brand_raw']
        ping = f'{round(self.bot.latency * 1000)}ms'
        embed.add_field(name="CPU", value=cpu, inline=True)
        embed.add_field(name="Ping", value=ping, inline=True)
        embed.set_footer(text="Programmed By the_indian_dev#0148")
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Add this awesome bot to your server")
    async def invite(self, ctx):
        """Sends invite link to the guild"""
        logging.info("{} executed invite command".format(ctx.author.name))
        embed = discord.Embed(title="Invite Me!", url="https://www.youtube.com/watch?v=qJRKedSUHg4",
                              description="Add me to your noice server", color=0x109319)
        embed.add_field(name="\u200b", value="[Click Here](https://forum.ysfhq.com/viewtopic.php?p=118432#p118432)",
                        inline=True)
        embed.set_footer(text="Thank you for inviting the Bot! ")
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Support development of this bot")
    async def donate(self, ctx):
        """Sends Donation Info guild"""
        logging.info("{} executed invite command".format(ctx.author.name))
        embed = discord.Embed(title="Donation", url="https://www.youtube.com/watch?v=qJRKedSUHg4",
                              description="Thank You!!!! OMG 😳", color=0x109319)
        embed.add_field(name="\u200b",
                        value="Thank You for donating!!! Even a small amount can help sustain the bot.[Click Here to Donate 😳](https://commerce.coinbase.com/checkout/59d0753a-055a-43c7-be2c-5d30ee0a6d63)",
                        inline=True)
        embed.set_footer(text="Thank you for the Donation")
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(MainCog(bot))
    logging.info("Succesfully loaded MainCog")
