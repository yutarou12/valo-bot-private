import json
import os

import cv2
from PIL import Image, ImageFilter
import pytesseract

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

    @app_commands.command(name='チーム分け2')
    @app_commands.guild_only()
    async def cmd_team_2(self, interaction: discord.Interaction, input_image: discord.Attachment):
        """画像によるチーム分けを行います。"""
        await interaction.response.defer(ephemeral=True)

        ch_id = 1378713691578699837
        second_id = 1378713734624841889

        blue_ch: discord.VoiceChannel = interaction.guild.get_channel(ch_id)
        red_ch: discord.VoiceChannel = interaction.guild.get_channel(second_id)

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

        with open('./data/player_name_list.json', 'r', encoding='utf-8') as d:
            valo_name_dict = json.load(d)

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
                text = pytesseract.image_to_string(resized_image, lang='jpn')
                print(f"Text from {filename}: {text.strip()}")
                for user_id, name in valo_name_dict.items():
                    if name in text:
                        member = interaction.guild.get_member(int(user_id))
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
        """VCを終了"""

        ch_id = 1378713691578699837
        second_id = 1378713734624841889

        vc_ch: discord.VoiceChannel = interaction.guild.get_channel(ch_id)
        second_id_ch: discord.VoiceChannel = interaction.guild.get_channel(second_id)

        for member in second_id_ch.members:
            if member.voice:
                try:
                    await member.move_to(vc_ch)
                except Exception:
                    await interaction.message.channel.send(f'Error >> {member.mention} は移動できませんでした。')
            else:
                await interaction.message.channel.send(f'Warning >> {member.mention} は自分で{vc_ch.mention}に参加してください。')

        return await interaction.response.send_message('集合！！！！！')


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
            old_red_embed.add_field(name=f'・{self.valo_name_dict.get(str(user.id))}', value=f'{user.mention}', inline=False)

        if interaction.user in self.team_list["blue"]:
            old_blue_embed.clear_fields()
            self.team_list["blue"].remove(interaction.user)
            for user in self.team_list["blue"]:
                old_blue_embed.add_field(name=f'・{self.valo_name_dict.get(str(user.id))}', value=f'{user.mention}', inline=False)

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
            old_blue_embed.add_field(name=f'・{self.valo_name_dict.get(str(user.id))}', value=f'{user.mention}', inline=False)

        if interaction.user in self.team_list["red"]:
            old_red_embed.clear_fields()
            self.team_list["red"].remove(interaction.user)
            for user in self.team_list["red"]:
                old_red_embed.add_field(name=f'・{self.valo_name_dict.get(str(user.id))}', value=f'{user.mention}', inline=False)

        await interaction.message.edit(embeds=[old_red_embed, old_blue_embed], view=self)
        return True

    @discord.ui.button(label='VCを分ける', style=discord.ButtonStyle.danger, custom_id='team_end_button')
    async def team_wakeru(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch_id = {"red": 1378713691578699837, "blue": 1378713734624841889}

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
        red_context = "ㅤ\n".join([self.valo_name_dict.get(str(m.id)) for m in self.team_list.get("red")]) if self.team_list.get("red") else "なし"
        blue_context = "ㅤ\n".join([self.valo_name_dict.get(str(m.id)) for m in self.team_list.get("blue")]) if self.team_list.get("blue") else "なし"
        return await interaction.response.send_message(f'VCを分けました。\n\n>> **アタッカー側**\n{red_context}\n>> **ディフェンダー側**\n{blue_context}')


async def setup(bot):
    await bot.add_cog(Team(bot))
