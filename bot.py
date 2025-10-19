import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ボタンクラス
class AuthView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.auth_role = role

    @discord.ui.button(label="認証開始", style=discord.ButtonStyle.green)
    async def auth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        guild_member = interaction.guild.get_member(member.id)

        # 既にそのロールを持っている場合は拒否
        if guild_member and self.auth_role in guild_member.roles:
            await interaction.response.send_message(
                f"あなたはすでに `{self.auth_role.name}` に認証済みです。",
                ephemeral=True
            )
            return

        # 数字生成
        number = str(random.randint(1000, 9999))

        # 画像作成
        img = Image.new('RGB', (200, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((50, 40), number, font=font, fill=(0, 0, 0))

        with BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="captcha.png")

        # ephemeral メッセージで送信（本人だけ）
        await interaction.response.send_message(
            "以下の数字を入力してください。",
            file=file,
            ephemeral=True
        )

        # モーダルで入力
        class AuthModal(discord.ui.Modal, title="認証フォーム"):
            input_number = discord.ui.TextInput(label="画像の数字を入力してください", style=discord.TextStyle.short)

            async def on_submit(self2, modal_interaction: discord.Interaction):
                if self2.input_number.value == number:
                    await modal_interaction.response.send_message(f"認証成功！ `{self.auth_role.name}` が付与されました", ephemeral=True)
                    if guild_member:
                        await guild_member.add_roles(self.auth_role)
                else:
                    await modal_interaction.response.send_message("数字が違います。もう一度試してください。", ephemeral=True)

        await interaction.followup.send_modal(AuthModal())

# /認証パネル コマンド（ユーザーがロールを選択可能）
@bot.tree.command(name="認証パネル", description="認証ボタンを設置します")
@discord.app_commands.describe(role="認証後に付与したいロールを選んでください")
async def auth_panel(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.send_message(
        f"以下のボタンを押すと `{role.name}` に認証されます。",
        view=AuthView(role),
        ephemeral=False  # チャンネル上に常時表示
    )

bot.run("MTQyOTA5MzM4NjAzOTcyNjEwMQ.GvTGzM.L6S_i9Jab_kVG2IF_EIareFuaSoDkQzpAzEsic")
