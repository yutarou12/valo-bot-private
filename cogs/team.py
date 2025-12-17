import os

import cv2
from PIL import Image, ImageFilter
import pytesseract
import pyocr

import discord
from discord import app_commands
from discord.ext import commands

from libs.database import Database

arr_ocr_tool = pyocr.get_available_tools()
if len(arr_ocr_tool) == 0:
    print("No OCR tool found")
ocr_tool = arr_ocr_tool[0]


class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db

    @app_commands.command(name='チーム分け')
    @app_commands.guild_only()
    async def cmd_team(self, interaction: discord.Interaction):
        """チーム分けを行います。"""

        red_embed = discord.Embed(title='アタッカー側', color=discord.Color.red())
        blue_embed = discord.Embed(title='ディフェンダー側', color=discord.Color.blue())

        guild_valo_name_list = await self.db.get_all_names_in_guild(interaction.guild_id)
        first_ch_id, second_ch_id = await self.db.get_guild_channel_data(interaction.guild_id)

        view = MainView(guild_valo_name_list=guild_valo_name_list, guild_ch_id=(first_ch_id, second_ch_id))
        return await interaction.response.send_message(embeds=[red_embed, blue_embed], view=view)

    @app_commands.command(name='チーム分け2')
    @app_commands.guild_only()
    async def cmd_team_2(self, interaction: discord.Interaction, input_image: discord.Attachment):
        """画像によるチーム分けを行います。"""
        await interaction.response.defer()

        first_ch_id, second_ch_id = await self.db.get_guild_channel_data(interaction.guild_id)
        if not first_ch_id or not second_ch_id:
            return await interaction.followup.send('> 音声チャンネルの設定がされていません。サーバー管理者に問い合わせてください。', ephemeral=True)

        red_ch: discord.VoiceChannel = interaction.guild.get_channel(first_ch_id)
        blue_ch: discord.VoiceChannel = interaction.guild.get_channel(second_ch_id)

        red_embed = discord.Embed(title='アタッカー側', color=discord.Color.red())
        blue_embed = discord.Embed(title='ディフェンダー側', color=discord.Color.blue())

        if input_image.content_type not in ['image/png', 'image/jpeg']:
            return await interaction.response.send_message('画像ファイルをアップロードしてください。', ephemeral=True)

        if input_image.content_type == 'image/png':
            await input_image.save('./images/input_image.png')
        else:
            await input_image.save('./images/input_image.jpg')
            image = cv2.imread('./images/input_image.jpg')
            cv2.imwrite('./images/input_image.png', image, [int(cv2.IMWRITE_PNG_COMPRESSION), 1])

        guild_valo_name_list = await self.db.get_all_names_in_guild(interaction.guild_id)

        img = Image.open('./images/input_image.png')
        im_crop = img.crop((245, 462, 1160, 786))
        im_crop.save('images/new_input_image.png', quality=95)
        img = cv2.imread('./images/new_input_image.png', cv2.IMREAD_COLOR)
        h, w = img.shape[:2]
        split_x = 2
        split_y = 5

        cx = 0
        cy = 0
        for j in range(split_x):
            for i in range(split_y):
                split_pic = img[cy:cy + int(h / split_y), cx:cx + int(w / split_x), :]
                cv2.imwrite('./images/split_pic/split_y' + str(i) + '_x' + str(j) + '.jpg', split_pic)
                cy = cy + int(h / split_y)
            cy = 0
            cx = cx + int(w / split_x)

        for filename in os.listdir('./images/split_pic/'):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg',)):
                image_path = os.path.join('./images/split_pic/', filename)
                image_b = Image.open(image_path)
                image = image_b.crop((67, 0, image_b.width, image_b.height))
                gray_image = image.convert('L')
                denoised_image = gray_image.filter(ImageFilter.GaussianBlur(radius=1))
                resized_image = denoised_image.resize((600, int(denoised_image.height * (600 / denoised_image.width))))
                text = ocr_tool.image_to_string(
                    resized_image,
                    lang="jpn"
                )
                # text = pytesseract.image_to_string(resized_image, lang='jpn')
                print(f"Text from {filename}: {text.strip()}")
                for user_id, name in guild_valo_name_list.items():
                    if name in text:
                        member = interaction.guild.get_member(user_id)
                        if filename.endswith('x0.jpg'):
                            blue_embed.add_field(name=f'・{name}', value=f'{member.mention}', inline=False)
                            if member.voice:
                                try:
                                    await member.move_to(blue_ch)
                                except Exception:
                                    await interaction.followup.send(
                                        f'Error >> {member.mention} は移動できませんでした。')
                            else:
                                await interaction.followup.send(
                                    f'Warning >> {member.mention} は自分で{blue_ch.mention}に参加してください。')

                        elif filename.endswith('x1.jpg'):
                            red_embed.add_field(name=f'・{name}', value=f'{member.mention}', inline=False)
                            if member.voice:
                                try:
                                    await member.move_to(red_ch)
                                except Exception:
                                    await interaction.followup.send(
                                        f'Error >> {member.mention} は移動できませんでした。')
                            else:
                                await interaction.followup.send(
                                    f'Warning >> {member.mention} は自分で{red_ch.mention}に参加してください。')

        return await interaction.followup.send(embeds=[red_embed, blue_embed])

    @app_commands.command(name='ゲーム終了')
    @app_commands.guild_only()
    async def cmd_end(self, interaction: discord.Interaction):
        """1つのチャンネルに全員戻ってきます。"""
        first_ch_id, second_ch_id = await self.db.get_guild_channel_data(interaction.guild_id)
        if not first_ch_id or not second_ch_id:
            return await interaction.followup.send(
                '> 音声チャンネルの設定がされていません。サーバー管理者に問い合わせてください。', ephemeral=True)

        red_ch: discord.VoiceChannel = interaction.guild.get_channel(first_ch_id)
        blue_ch: discord.VoiceChannel = interaction.guild.get_channel(second_ch_id)

        for member in blue_ch.members:
            if member.voice:
                try:
                    await member.move_to(red_ch)
                except Exception:
                    await interaction.message.channel.send(f'Error >> {member.mention} は移動できませんでした。')
            else:
                await interaction.message.channel.send(f'Warning >> {member.mention} は自分で{red_ch.mention}に参加してください。')

        return await interaction.response.send_message('集合！！！！！')


class MainView(discord.ui.View):
    def __init__(self, guild_valo_name_list, guild_ch_id):
        self.team_list = {"red": [], "blue": []}
        self.guild_valo_name_list = guild_valo_name_list
        self.guild_ch_id = guild_ch_id
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
            user_valo_name = self.guild_valo_name_list.get(user.id)
            old_red_embed.add_field(name=f'・{user_valo_name if user_valo_name else "登録なし"}', value=f'{user.mention}', inline=False)

        if interaction.user in self.team_list["blue"]:
            old_blue_embed.clear_fields()
            self.team_list["blue"].remove(interaction.user)
            for user in self.team_list["blue"]:
                user_valo_name = self.guild_valo_name_list.get(user.id)
                old_blue_embed.add_field(name=f'・{user_valo_name if user_valo_name else "登録なし"}', value=f'{user.mention}', inline=False)

        return await interaction.response.edit_message(embeds=[old_red_embed, old_blue_embed], view=self)

    @discord.ui.button(label='ディフェンダー側', style=discord.ButtonStyle.primary, custom_id='team_defend_button')
    async def team_defend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.team_list["blue"]:
            return await interaction.response.send_message('既にディフェンダー側です。', ephemeral=True)
        self.team_list["blue"].append(interaction.user)

        old_red_embed = interaction.message.embeds[0]
        old_blue_embed = interaction.message.embeds[1]

        old_blue_embed.clear_fields()
        for user in self.team_list["blue"]:
            user_valo_name = self.guild_valo_name_list.get(user.id)
            old_blue_embed.add_field(name=f'・{user_valo_name if user_valo_name else "登録なし"}', value=f'{user.mention}', inline=False)

        if interaction.user in self.team_list["red"]:
            old_red_embed.clear_fields()
            self.team_list["red"].remove(interaction.user)
            for user in self.team_list["red"]:
                user_valo_name = self.guild_valo_name_list.get(user.id)
                old_red_embed.add_field(name=f'・{user_valo_name if user_valo_name else "登録なし"}', value=f'{user.mention}', inline=False)

        return await interaction.response.edit_message(embeds=[old_red_embed, old_blue_embed], view=self)

    @discord.ui.button(label='VCを分ける', style=discord.ButtonStyle.danger, custom_id='team_end_button')
    async def team_wakeru(self, interaction: discord.Interaction, button: discord.ui.Button):
        first_ch_id, second_ch_id = self.guild_ch_id
        if not first_ch_id or not second_ch_id:
            return await interaction.response.send_message(
                '> 音声チャンネルの設定がされていません。サーバー管理者に問い合わせてください。', ephemeral=True)

        ch_id = {"red": first_ch_id, "blue": second_ch_id}

        for color in ["red", "blue"]:
            for member in self.team_list[color]:
                vc_ch: discord.VoiceChannel = interaction.guild.get_channel(ch_id[color])
                if member.voice:
                    try:
                        await member.move_to(vc_ch)
                    except Exception:
                        await interaction.message.channel.send(f'Error >> {member.mention} は移動できませんでした。')
                else:
                    await interaction.message.channel.send(f'Warning >> {member.mention} は自分で{vc_ch.mention}に参加してください。')
        self.stop()
        red_context = "ㅤ\n".join([self.guild_valo_name_list.get(m.id) if self.guild_valo_name_list.get(m.id) else "登録なし" for m in self.team_list.get("red")]) if self.team_list.get("red") else "なし"
        blue_context = "ㅤ\n".join([self.guild_valo_name_list.get(m.id) if self.guild_valo_name_list.get(m.id) else "登録なし" for m in self.team_list.get("blue")]) if self.team_list.get("blue") else "なし"
        return await interaction.response.edit_message(content=f'VCを分けました。\n\n>> **アタッカー側**\n{red_context}\n>> **ディフェンダー側**\n{blue_context}', view=None, embed=None)


async def setup(bot):
    await bot.add_cog(Team(bot))
