import os
import sys

# Tambahkan direktori project ke sys.path agar modul core bisa di-import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.licensing import LicenseManager

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("[Discord Bot] Error: Package 'discord.py' belum terinstall.")
    sys.exit(1)

# DISCORD_BOT_TOKEN & DISCORD_SERVER_ID dari Environment Variable Render / OS
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID", "")  # ID Server Discord kamu (misal: 123456789012345678)
DISCORD_INVITE_LINK = os.getenv("DISCORD_INVITE_LINK", "https://discord.gg/JdZ8Td3r8")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"==================================================")
    print(f"🤖 SA-RP Linggo Token Bot Ready!")
    print(f"Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"==================================================")

async def check_user_in_server(user_id: int) -> bool:
    """Mengecek apakah user dengan ID tertentu adalah member di Server Discord."""
    guild = None
    if DISCORD_SERVER_ID:
        try:
            guild_id = int(DISCORD_SERVER_ID)
            guild = bot.get_guild(guild_id)
            if not guild:
                guild = await bot.fetch_guild(guild_id)
        except Exception as e:
            print(f"[Bot Warning] Gagal fetch guild by ID: {e}")
    
    # Auto-detect guild pertama tempat bot bergabung jika DISCORD_SERVER_ID kosong
    if not guild and bot.guilds:
        guild = bot.guilds[0]

    if not guild:
        # Jika bot belum masuk server manapun, izinkan sementara
        return True

    try:
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound:
                return False
            except Exception as e:
                print(f"[Bot Warning] Error fetch_member: {e}")
                return False
        return member is not None
    except Exception as e:
        print(f"[Bot Warning] Gagal mengecek keanggotaan member: {e}")
        return False

@bot.command(name="token", aliases=["gettoken", "lisensi"])
async def give_token(ctx, hwid: str = None, days: int = 30):
    """Command untuk member Discord mengambil token activation SA-RP Linggo. Contoh: !token AB43"""
    # 1. Cek apakah user adalah member di Server Discord kita
    is_member = await check_user_in_server(ctx.author.id)
    if not is_member:
        embed_not_member = discord.Embed(
            title="🚫 Akses Ditolak!",
            description=f"Halo **{ctx.author.name}**!\nKamu harus menjadi **member resmi Server Discord SA-RP Linggo** terlebih dahulu untuk mendapatkan token aktivasi gratis.",
            color=0xEF4444
        )
        embed_not_member.add_field(
            name="Silakan Bergabung Dulu di Server Kami:",
            value=f"👉 [**Klik Di Sini Untuk Join Discord**]({DISCORD_INVITE_LINK})",
            inline=False
        )
        embed_not_member.set_footer(text="SA-RP Linggo • Access Restricted")
        await ctx.reply(embed=embed_not_member)
        return

    # 2. Cek parameter HWID
    if not hwid or hwid.upper() in ["GLOB", "NONE", "HELP"]:
        embed_error = discord.Embed(
            title="⚠️ HWID Diperlukan!",
            description="Untuk keamanan lisensi, token harus dikunci ke **HWID (Hardware ID)** komputer kamu.",
            color=0xEF4444
        )
        embed_error.add_field(
            name="Cara Mengetahui HWID Kamu:",
            value="1. Buka aplikasi **SA-RP Linggo**\n2. Klik **Settings ⚙️**\n3. Lihat **Device HWID** kamu (Contoh: `6F54` atau `AB43`)\n4. Jalankan perintah: `!token <HWID_KAMU>` (Contoh: `!token 6F54`)",
            inline=False
        )
        await ctx.reply(embed=embed_error)
        return

    days_clamped = max(1, min(days, 90))
    hwid_clean = hwid.strip().upper()[:4]
    token_code = LicenseManager.generate_token_raw(days=days_clamped, hwid=hwid_clean)

    embed = discord.Embed(
        title="🔑 SA-RP Linggo License Token",
        description=f"Halo **{ctx.author.name}**! Ini token aktivasi aplikasi SA-RP Linggo kamu (Locked to Device HWID: `{hwid_clean}`):",
        color=0x38BDF8
    )
    embed.add_field(name=f"Kode Token (Valid {days_clamped} Hari)", value=f"```\n{token_code}\n```", inline=False)
    embed.add_field(
        name="Cara Pakai", 
        value="1. Buka aplikasi **SA-RP Linggo**\n2. Buka **Settings** -> **🔑 Offline License Token**\n3. Paste kode di atas lalu klik **Activate Token**!",
        inline=False
    )
    embed.set_footer(text="SA-RP Linggo • Created by yambuttt")

    try:
        await ctx.author.send(embed=embed)
        if ctx.guild:
            await ctx.reply("📩 Token aktivasi telah dikirimkan ke **Pesan Pribadi (DM)** kamu! Cek DM ya bro.", mention_author=True)
    except discord.Forbidden:
        await ctx.reply(embed=embed)

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("[Warning] Silakan atur DISCORD_BOT_TOKEN di Environment Variable terlebih dahulu!")
    else:
        bot.run(DISCORD_BOT_TOKEN)
