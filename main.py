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
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

MODERATOR_ROLES = ["Mekanın Sahibi", "Yönetici", "Admin", "Moderatör", "Bot"]
CATEGORY_NAME = "|▬▬|TALEPLER|▬▬|"

# ----------- SSS SİSTEMİ -----------
FAQ = {
    "nasıl alışveriş yapabilirim": "Alışveriş yapmak için, ilgilendiğiniz ürünü seçip 'Alışveriş Sepetine Ekle' butonuna tıklayın. Ardından sepete gidin ve satın alma işlemini tamamlayın.",
    "siparişimin durumunu nasıl öğrenebilirim": "Hesabınıza giriş yapın ve 'Siparişlerim' bölümünden durumunuzu görebilirsiniz.",
    "bir siparişi nasıl iptal edebilirim": "Siparişiniz gönderilmeden önce müşteri hizmetleriyle iletişime geçip iptal edebilirsiniz.",
    "siparişim hasarlı gelirse ne yapmalıyım": "Hasarlı ürün için müşteri hizmetleriyle iletişime geçin, fotoğraf gönderin, iade veya değişim yapılır.",
    "teknik destekle nasıl iletişime geçebilirim": "İnternet sitemizdeki telefon numarasını arayabilir veya sohbet robotu üzerinden ulaşabilirsiniz.",
    "teslimat yöntemini değiştirebilir miyim": "Evet, ödeme sayfasında teslimat bilgilerini değiştirebilirsiniz."
}

# ----------- SQLITE DB -----------
DB_PATH = os.path.join(os.getcwd(), "Ticketler", "tickets.db")
os.makedirs("Ticketler", exist_ok=True)
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
c.execute('''CREATE TABLE IF NOT EXISTS unanswered
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user TEXT,
              message TEXT,
              created_at TEXT)''')
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
        channel_name = f"{user.name}-destek".lower()

        # Eski ticket sil
        c.execute("DELETE FROM tickets WHERE LOWER(user) = ?", (user.name.lower(),))
        conn.commit()
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await existing_channel.delete()

        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if not category:
            category = await guild.create_category(CATEGORY_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for role_name in MODERATOR_ROLES:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        overwrites[guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        opened_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO tickets (user, reason, channel_name, opened_at) VALUES (?, ?, ?, ?)",
                  (user.name, reason, channel_name, opened_at))
        conn.commit()

        await interaction.response.send_message(f"✅ Destek kanalın oluşturuldu: {channel.mention}", ephemeral=True)

        button = Button(label="DESTEĞİ KAPAT", style=discord.ButtonStyle.red)

        async def close_ticket(interaction_button: discord.Interaction, ch_name=channel_name):
            closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("UPDATE tickets SET closed_at = ?, closed_by = ? WHERE LOWER(channel_name) = ?",
                      (closed_at, interaction_button.user.name, ch_name.lower()))
            conn.commit()
            await interaction_button.response.send_message("🚪 Ticket kapatılıyor...", ephemeral=True)
            await interaction_button.channel.delete()

        button.callback = close_ticket
        view = View()
        view.add_item(button)

        await channel.send(f"{user.mention} {reason} nedeniyle talep oluşturdu.", view=view)

# ----------- VIEW -----------
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MySelect())

# ----------- KOMUTLAR -----------
@bot.command()
async def menü(ctx):
    await ctx.send("Hangi konuda yardıma ihtiyacın var? 👇", view=MyView())

# ----------- MESAJ DİNLEYİCİ (SSS KONTROLÜ) -----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    msg = message.content.lower()
    found = False
    for soru, cevap in FAQ.items():
        if soru in msg:
            await message.channel.send(f"💡 {cevap}")
            found = True
            break

    # Eğer hiçbir eşleşme yoksa, veritabanına kaydet
    if not found:
        c.execute("INSERT INTO unanswered (user, message, created_at) VALUES (?, ?, ?)",
                  (str(message.author), message.content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

    await bot.process_commands(message)

# ----------- READY -----------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif: {bot.user}")

bot.run(token)
