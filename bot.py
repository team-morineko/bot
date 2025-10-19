import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import random, string, io, os

intents = discord.Intents.default()  # 特権インテント不要
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 123456789012345678  # サーバーID
ROLE_ID = 987654321098765432   # 認証ロールID
active_verifications = {}  # user_id -> 認証データを保存


# 数字画像を生成する関数
def generate_code_image(code: str):
    img = Image.new("RGB", (200, 80), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 50)
    except:
        font = ImageFont.load_default()
    draw.text((50, 15), code, fill=(0, 255, 0), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ボタンUIを作成
class NumberButtonView(discord.ui.View):
    def __init__(self, user_id, code):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.code = code
        self.entered = ""

        # 0〜9ボタンを動的に追加
        for i in range(10):
            self.add_item(NumberButton(str(i), self))

    async def check_code(self, interaction: discord.Interaction):
        if self.entered == self.code:
            guild = bot.get_guild(GUILD_ID)
            member = guild.get_member(self.user_id)
            if member:
                role = guild.get_role(ROLE_ID)
                await member.add_roles(role)
                await interaction.response.edit_message(content="認証に成功しました。", attachments=[], view=None)
                active_verifications.pop(self.user_id, None)
            else:
                await interaction.response.send_message("サーバーに参加していないようです。", ephemeral=True)


class NumberButton(discord.ui.Button):
    def __init__(self, label, view):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.parent_view = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.user_id:
            await interaction.response.send_message("あなたの認証ではありません。", ephemeral=True)
            return

        self.parent_view.entered += self.label

        # 進捗表示
        display = "🔢 入力中: " + "•" * len(self.parent_view.entered)
        await interaction.response.edit_message(content=display, view=self.parent_view)

        # コードが完成したらチェック
        if len(self.parent_view.entered) == len(self.parent_view.code):
            await self.parent_view.check_code(interaction)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("スラッシュコマンド同期完了")
    except Exception as e:
        print(e)


@bot.tree.command(name="verify", description="認証を開始します（DMが届きます）")
async def verify(interaction: discord.Interaction):
    code = "".join(random.choices(string.digits, k=4))
    active_verifications[interaction.user.id] = code
    image = generate_code_image(code)
    file = discord.File(fp=image, filename="verify.png")

    try:
        view = NumberButtonView(interaction.user.id, code)
        await interaction.user.send("下の画像の数字を入力してください。", file=file, view=view)
        await interaction.response.send_message("DMを確認してください。", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("DMを開放してから再試行してください。", ephemeral=True)


bot.run(os.environ['DISCORD_TOKEN'])
