import discord
from discord.ext import commands
from discord import app_commands

from libs.database import Database


class Setting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db

    @app_commands.command(name="表示名設定")
    @app_commands.rename(display_name='valorant_name')
    async def setting_display_name(self, interaction: discord.Interaction, display_name: str | None = None):
        """コマンドを実行したときにでるValorantの表示名を設定します。"""
        db_display_name = await self.db.get_name_from_user(interaction.user.id, interaction.guild_id)

        if db_display_name:
            if display_name is None:
                embed = discord.Embed(title='Valorant表示名解除画面',
                                      description=f'登録を解除しますか？')
                embed.add_field(name='現在のValorant表示名', value=f'`{db_display_name}`', inline=False)
                ui_id = 0
            else:
                embed = discord.Embed(title='Valorant表示名変更画面',
                                      description=f'Valorant表示名を変更しますか？')
                embed.add_field(name='現在のValorant表示名', value=f'`{db_display_name}`', inline=False)
                embed.add_field(name='新しいValorant表示名', value=f'`{display_name}`', inline=False)
                ui_id = 1
        else:
            if display_name is None:
                return await interaction.response.send_message("Valorant表示名が登録されていません。Valorant表示名を入力してください。", ephemeral=True)
            else:
                check_text = f'DiscordID：{interaction.user.name}\nValorant表示名：{display_name}'
                embed = discord.Embed(title='Valorant表示名登録画面',
                                      description=f'以下の内容で登録しますか？\n```\n{check_text}\n```')
                ui_id = 1

        view = ValorantNameCheckView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()

        if view.value is None:
            return
        elif view.value:
            if ui_id == 0:
                await self.db.delete_name_for_user(interaction.user.id, interaction.guild_id)
            elif ui_id == 1:
                await self.db.set_name_for_user(interaction.user.id, interaction.guild_id, display_name)

    @app_commands.command(name="音声チャンネル設定")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(first_voice_channel='アタッカー側チャンネル', second_voice_channel='ディフェンダー側チャンネル')
    async def setting_voice_channel(self, interaction: discord.Interaction, first_voice_channel: discord.VoiceChannel, second_voice_channel: discord.VoiceChannel):
        """音声チャンネルを設定します。"""
        await self.db.set_guild_channel_data(interaction.guild_id, first_voice_channel.id, second_voice_channel.id)

        embed = discord.Embed(title='音声チャンネル設定完了',
                                description='音声チャンネルの設定が完了しました。')
        embed.add_field(name='アタッカー側', value=f'`{first_voice_channel.name}`', inline=False)
        embed.add_field(name='ディフェンダー側', value=f'`{second_voice_channel.name}`', inline=False)
        return await interaction.response.send_message("> それぞれのチャンネルをBotが見れるようにして下さい。", embed=embed, ephemeral=True)


class ValorantNameCheckView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 120
        self.value = None

    @discord.ui.button(label='OK', style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='完了しました', embed=None, view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='キャンセルしました', embed=None, view=None)
        self.value = False
        self.stop()


async def setup(bot):
    await bot.add_cog(Setting(bot))