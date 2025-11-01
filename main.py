import discord
from discord.ext import commands
from discord.ui import Button, View
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

# ----------- AYARLAR -----------
load_dotenv(".config")
token = os.getenv("dctoken")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

MODERATOR_ROLES = ["Mekanın Sahibi", "Yönetici", "Admin", "Moderatör", "Bot"]
CATEGORY_NAME = "|▬▬|TALEPLER|▬▬|"

# ----------- SQLITE DB -----------
DB_PATH = os.path.join(os.getcwd(), "Ticketler", "tickets.db")
os.makedirs("Ticketler", exist_ok=True)  # DB klasörü
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tickets
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user TEXT,
              reason TEXT,
              channel_name TEXT,
              opened_at TEXT,
              closed_at TEXT,
              closed_by TEXT)''')
conn.commit()

# ----------- DROPDOWN SEÇENEKLERİ -----------
class MySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Teknik Destek"),
            discord.SelectOption(label="Hesap Sorunları"),
            discord.SelectOption(label="Diğer")
        ]
        super().__init__(placeholder="Bir Seçim Yap 👇", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        reason = self.values[0]

        # Kanal adı
        channel_name = f"{user.name}-destek".lower()

        # Eğer kullanıcının eski ticketi varsa DB'den sil
        c.execute("DELETE FROM tickets WHERE LOWER(user) = ?", (user.name.lower(),))
        conn.commit()

        # Zaten açık ticket kanalı var mı kontrol et, varsa sil
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await existing_channel.delete()

        # Destek kategorisi
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if not category:
            category = await guild.create_category(CATEGORY_NAME)

        # Kanal izinleri
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False),
                      user: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        for role_name in MODERATOR_ROLES:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        overwrites[guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # Kanal oluştur
        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        # DB kaydı
        opened_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO tickets (user, reason, channel_name, opened_at) VALUES (?, ?, ?, ?)",
                  (user.name, reason, channel_name, opened_at))
        conn.commit()

        await interaction.response.send_message(f"Destek kanalın oluşturuldu: {channel.mention}", ephemeral=True)

        # Ticket mesajı ve buton
        button = Button(label="DESTEĞİ KAPAT", style=discord.ButtonStyle.red)

        async def close_ticket(interaction_button: discord.Interaction, ch_name=channel_name):
            closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("UPDATE tickets SET closed_at = ?, closed_by = ? WHERE LOWER(channel_name) = ?",
                      (closed_at, interaction_button.user.name, ch_name.lower()))
            conn.commit()
            await interaction_button.response.send_message("Ticket kapatılıyor...", ephemeral=True)
            await interaction_button.channel.delete()

        button.callback = close_ticket
        view = View()
        view.add_item(button)

        await channel.send(f"{user.mention} {reason} nedeniyle Talep Oluşturdu.", view=view)

# ----------- DROPDOWN VIEW -----------
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MySelect())   
        

# ----------- Komut -----------
@bot.command()
async def menü(ctx):
    await ctx.send("Hangi Konuda Yardıma İhtiyacın Var👇", view=MyView())

# ----------- Bot Başlat -----------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif: {bot.user}")

bot.run(token)
