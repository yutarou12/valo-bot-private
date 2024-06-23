import json

import discord
from discord import app_commands
from discord.ext import commands


class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='チーム分け')
    @app_commands.guild_only()
    async def cmd_team(self, interaction: discord.Interaction):
        """チーム分けを行います。"""

        red_embed = discord.Embed(title='アタッカー側', color=discord.Color.red())
        blue_embed = discord.Embed(title='ディフェンダー側', color=discord.Color.blue())

        view = MainView()
        await interaction.response.send_message(embeds=[red_embed, blue_embed], view=view)


class MainView(discord.ui.View):
    def __init__(self):
        self.team_list = {"red": [], "blue": []}
        with open('./data/player_name_list.json', 'r', encoding='utf-8') as d:
            valo_name_dict = json.load(d)
        self.valo_name_dict = valo_name_dict
        super().__init__()
        self.timeout = None

    @discord.ui.button(label='アタッカー側', style=discord.ButtonStyle.primary, custom_id='team_attack_button')
    async def team_attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.team_list["red"]:
            return await interaction.response.send_message('既にアタッカー側です。', ephemeral=True)
        self.team_list["red"].append(interaction.user)

        old_red_embed = interaction.message.embeds[0]
        old_blue_embed = interaction.message.embeds[1]

        old_red_embed.clear_fields()
        for user in self.team_list["red"]:
            old_red_embed.add_field(name=f'・{self.valo_name_dict.get(str(user.id))}', value=f'{user.mention}')

        if interaction.user in self.team_list["blue"]:
            old_blue_embed.clear_fields()
            self.team_list["blue"].remove(interaction.user)
            for user in self.team_list["blue"]:
                old_blue_embed.add_field(name=f'・{self.valo_name_dict.get(str(user.id))}', value=f'{user.mention}')

        await interaction.message.edit(embeds=[old_red_embed, old_blue_embed], view=self)
        return True

    @discord.ui.button(label='ディフェンダー側', style=discord.ButtonStyle.primary, custom_id='team_defend_button')
    async def team_defend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.team_list["blue"]:
            return await interaction.response.send_message('既にディフェンダー側です。', ephemeral=True)
        self.team_list["blue"].append(interaction.user)

        old_red_embed = interaction.message.embeds[0]
        old_blue_embed = interaction.message.embeds[1]

        old_blue_embed.clear_fields()
        for user in self.team_list["blue"]:
            old_blue_embed.add_field(name=f'・{self.valo_name_dict.get(str(user.id))}', value=f'{user.mention}')

        if interaction.user in self.team_list["red"]:
            old_red_embed.clear_fields()
            self.team_list["red"].remove(interaction.user)
            for user in self.team_list["red"]:
                old_red_embed.add_field(name=f'・{self.valo_name_dict.get(str(user.id))}', value=f'{user.mention}')

        await interaction.message.edit(embeds=[old_red_embed, old_blue_embed], view=self)
        return True

    @discord.ui.button(label='VCを分ける', style=discord.ButtonStyle.danger, custom_id='team_end_button')
    async def team_wakeru(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch_id = {"red": 1122211898398621770, "blue": 1122211898398621771}

        for color in ["red", "blue"]:
            for member in self.team_list[color]:
                vc_ch: discord.VoiceChannel = interaction.guild.get_channel(ch_id[color])
                if member.voice:
                    try:
                        await member.move_to(vc_ch)
                    except Exception:
                        await interaction.response.send_message(f'Error >> {member.mention} は移動できませんでした。')
                else:
                    await interaction.response.send_message(f'Warning >> {member.mention} は自分で{vc_ch.mention}に参加してください。')
        self.stop()
        red_context = "ㅤ・\n".join([self.valo_name_dict.get(str(m.id)) for m in self.team_list.get("red")]) if self.team_list.get("red") else "なし"
        blue_context = "ㅤ・\n".join([self.valo_name_dict.get(str(m.id)) for m in self.team_list.get("blue")]) if self.team_list.get("blue") else "なし"
        return await interaction.response.send_message(f'VCを分けました。\n\n>> **アタッカー側**\n{red_context}\n>> **ディフェンダー側**\n{blue_context}')


async def setup(bot):
    await bot.add_cog(Team(bot))
