# -*- coding: utf-8 -*-
import io
import time
import datetime
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont

# ==========================
# CONFIG
# ==========================

TOKEN = "change me"

GUILD_ID = 1443741698227179734

# Welcome
WELCOME_CHANNEL_ID   = 1444785317075878009
RULES_CHANNEL_ID     = 1444764542805737563
WHITELIST_CHANNEL_ID = 1444768331289591931
AUTO_ROLE_ID         = 1443773432654204979

JOIN_SERVER_URL = "https://cfx.re/join/pbabqy"
SERVER_NAME = "Codexia Roleplay"
WELCOME_BG_FILE = "codexia_welcome_bg.png"

# Tickets
TICKET_PANEL_CHANNEL_ID = 1444792903527432302
TICKET_CATEGORY_ID      = 1444769930200219791
STAFF_ROLE_IDS = [
    1443768827212071012,
    1443773202915659866,
    1443771529409204355,
    1443772176141516831,
    1443772639637274884,
    1443772839625752606,
]

# DM Notifications
DM_NOTIFY_ROLE_IDS = [
    1443771529409204355,
    1443772176141516831,
    1443772639637274884,
]

WAITING_SUPPORT_VC_ID = 1444770686995529769

# Logging
MOD_LOG_CHANNEL_ID        = 1444769242279968871
ALL_MEMBERS_CHANNEL_ID    = 1445134359702147185
ONLINE_MEMBERS_CHANNEL_ID = 1445134530930282616

# Anti-spam
SPAM_WINDOW_SECONDS = 5
SPAM_MAX_MESSAGES   = 5
SPAM_PUNISH_DELETE  = True
SPAM_PUNISH_WARN    = True

# ==========================
# PREMIUM THEME
# ==========================

class Theme:
    # Colors - Clean & Professional
    PRIMARY   = 0x5865F2  # Blurple
    SUCCESS   = 0x2ECC71  # Green
    WARNING   = 0xF39C12  # Orange
    ERROR     = 0xE74C3C  # Red
    INFO      = 0x3498DB  # Blue
    PREMIUM   = 0x9B59B6  # Purple
    DARK      = 0x2C2F33  # Dark
    TICKET    = 0x00AFF4  # Cyan
    GOLD      = 0xF1C40F  # Gold

    # Minimal Icons (less emoji, more professional)
    ICON_SUCCESS = "✓"
    ICON_ERROR   = "✗"
    ICON_WARNING = "!"
    ICON_INFO    = "i"

# ==========================
# BOT SETUP
# ==========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Storage
user_message_times: dict[int, list[float]] = {}
ticket_dm_messages: dict[int, list[tuple[int, int]]] = {}
aio_session: aiohttp.ClientSession = None

# ==========================
# UTILITIES
# ==========================

def load_ticket_number() -> int:
    try:
        with open("ticket_counter.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_ticket_number(num: int) -> None:
    try:
        with open("ticket_counter.txt", "w") as f:
            f.write(str(num))
    except:
        pass

def get_main_guild() -> discord.Guild | None:
    return bot.get_guild(GUILD_ID)

def get_mod_log_channel() -> discord.TextChannel | None:
    g = get_main_guild()
    if not g:
        return None
    ch = g.get_channel(MOD_LOG_CHANNEL_ID)
    return ch if isinstance(ch, discord.TextChannel) else None

async def get_aio_session() -> aiohttp.ClientSession:
    global aio_session
    if aio_session is None or aio_session.closed:
        aio_session = aiohttp.ClientSession()
    return aio_session

def staff_only(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in getattr(interaction.user, "roles", []))

# ==========================
# PREMIUM EMBED BUILDER
# ==========================

def create_embed(
    title: str = None,
    description: str = None,
    color: int = Theme.PRIMARY,
    thumbnail: str = None,
    image: str = None,
    footer: str = None,
    footer_icon: str = None,
    author: str = None,
    author_icon: str = None,
    fields: list = None,
    timestamp: bool = True
) -> discord.Embed:
    
    embed = discord.Embed(color=color)
    
    if title:
        embed.title = title
    if description:
        embed.description = description
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    if author:
        embed.set_author(name=author, icon_url=author_icon)
    if footer:
        embed.set_footer(text=footer, icon_url=footer_icon)
    if timestamp:
        embed.timestamp = discord.utils.utcnow()
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    
    return embed

# ==========================
# DM & LOG HELPERS
# ==========================

async def notify_staff_dm(guild: discord.Guild, embed: discord.Embed, ticket_id: str = None) -> list:
    notified = set()
    dm_messages = []
    
    for role_id in DM_NOTIFY_ROLE_IDS:
        role = guild.get_role(role_id)
        if not role:
            continue
        
        for member in role.members:
            if member.id in notified or member.bot:
                continue
            
            try:
                msg = await member.send(embed=embed)
                notified.add(member.id)
                if ticket_id:
                    dm_messages.append((member.id, msg.id))
            except:
                pass
    
    return dm_messages

async def delete_ticket_dms(channel_id: int) -> None:
    if channel_id not in ticket_dm_messages:
        return
    
    for user_id, msg_id in ticket_dm_messages[channel_id]:
        try:
            user = await bot.fetch_user(user_id)
            dm_channel = await user.create_dm()
            msg = await dm_channel.fetch_message(msg_id)
            await msg.delete()
        except:
            pass
    
    del ticket_dm_messages[channel_id]

async def log_action(title: str, description: str, color: int = Theme.DARK, fields: list = None, thumbnail: str = None) -> None:
    log = get_mod_log_channel()
    if not log:
        return
    
    embed = create_embed(
        title=title,
        description=description,
        color=color,
        thumbnail=thumbnail,
        footer=SERVER_NAME
    )
    
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    
    try:
        await log.send(embed=embed)
    except:
        pass

# ==========================
# VIEWS
# ==========================

class WelcomeButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        if JOIN_SERVER_URL:
            self.add_item(discord.ui.Button(
                label="Connect to Server",
                style=discord.ButtonStyle.link,
                url=JOIN_SERVER_URL
            ))

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        member = interaction.user

        is_staff = any(r.id in STAFF_ROLE_IDS for r in getattr(member, "roles", []))
        is_creator = False
        if isinstance(channel, discord.TextChannel) and channel.topic:
            if str(member.id) in channel.topic:
                is_creator = True

        if not (is_staff or is_creator):
            return await interaction.response.send_message(
                embed=create_embed(
                    title="Access Denied",
                    description="Only staff or ticket creator can close this.",
                    color=Theme.ERROR
                ),
                ephemeral=True
            )

        button.disabled = True
        button.label = "Closing..."
        await interaction.response.edit_message(view=self)

        close_embed = create_embed(
            title="Ticket Closing",
            description=f"This ticket will be deleted in 5 seconds.\n\n**Closed by:** {member.mention}",
            color=Theme.ERROR
        )

        await channel.send(embed=close_embed)
        await delete_ticket_dms(channel.id)
        await asyncio.sleep(5)
        
        try:
            await channel.delete(reason=f"Closed by {member}")
        except:
            pass

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        if guild is None:
            return await interaction.response.send_message(
                embed=create_embed(title="Error", description="Server not found.", color=Theme.ERROR),
                ephemeral=True
            )

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if category is None or not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                embed=create_embed(title="Error", description="Ticket system not configured.", color=Theme.ERROR),
                ephemeral=True
            )

        for ch in category.text_channels:
            if ch.topic and str(member.id) in ch.topic:
                return await interaction.response.send_message(
                    embed=create_embed(
                        title="Ticket Exists",
                        description=f"You already have an open ticket: {ch.mention}",
                        color=Theme.WARNING
                    ),
                    ephemeral=True
                )

        await interaction.response.defer(ephemeral=True)

        current_number = load_ticket_number()
        ticket_number = current_number + 1
        save_ticket_number(ticket_number)

        ticket_name = f"ticket-{ticket_number:04d}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
        }

        for role_id in STAFF_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True
                )

        ticket_channel = await guild.create_text_channel(
            name=ticket_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket by {member} ({member.id})"
        )

         # Premium ticket embed
        ticket_embed = discord.Embed(
            title=f"Ticket #{ticket_number:04d}",
            description=(
                f"Welcome {member.mention}\n\n"
                f"Please describe your issue and wait for a staff member!\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=Theme.TICKET
        )

        ticket_embed.add_field(
            name="Guidelines",
            value="• Be patient for a response\n• Provide clear details\n• One issue per ticket",
            inline=False
        )

        ticket_embed.set_author(
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None
        )

        ticket_embed.set_footer(
            text=f"{SERVER_NAME} • Support",
            icon_url=guild.icon.url if guild.icon else None
        )

        ticket_embed.timestamp = discord.utils.utcnow()

        # Custom staff roles to mention
        CUSTOM_TICKET_ROLES = [
            1443768827212071012,  # Admin
            1443771529409204355,  # Moderator
            1443772176141516831   # Support
        ]

        staff_mentions = " ".join(f"<@&{role_id}>" for role_id in CUSTOM_TICKET_ROLES)

        await ticket_channel.send(
            content=f"{member.mention} {staff_mentions}",
            embed=ticket_embed,
            view=TicketCloseView()
        )


        # DM notification
        dm_embed = create_embed(
            title="New Ticket",
            description="A support ticket has been opened.",
            color=Theme.SUCCESS,
            thumbnail=member.display_avatar.url,
            fields=[
                ("User", f"{member.mention}\n`{member}`", True),
                ("Ticket", f"{ticket_channel.mention}\n`{ticket_name}`", True)
            ],
            footer=f"{SERVER_NAME} • Support"
        )

        dm_msgs = await notify_staff_dm(guild, dm_embed, ticket_name)
        ticket_dm_messages[ticket_channel.id] = dm_msgs

        await log_action(
            title="Ticket Created",
            description=f"**User:** {member.mention}\n**Channel:** {ticket_channel.mention}",
            color=Theme.SUCCESS,
            thumbnail=member.display_avatar.url
        )

        await interaction.followup.send(
            embed=create_embed(
                title="Ticket Created",
                description=f"Your ticket: {ticket_channel.mention}",
                color=Theme.SUCCESS
            ),
            ephemeral=True
        )

class ConfirmView(discord.ui.View):
    def __init__(self, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

# ==========================
# WELCOME BANNER
# ==========================

async def generate_welcome_banner(member: discord.Member) -> discord.File:
    bg = Image.open(WELCOME_BG_FILE).convert("RGBA")
    width, height = bg.size

    session = await get_aio_session()
    avatar_url = member.display_avatar.replace(size=512).url
    
    async with session.get(avatar_url) as resp:
        avatar_bytes = await resp.read()
    
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

    avatar_size = int(height * 0.48)
    avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)

    mask = Image.new("L", (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

    border_size = avatar_size + 20
    border_img = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
    border_mask = Image.new("L", (border_size, border_size), 0)

    bdraw = ImageDraw.Draw(border_mask)
    bdraw.ellipse((0, 0, border_size, border_size), fill=255)
    bdraw.ellipse((10, 10, border_size - 10, border_size - 10), fill=0)

    border_draw = ImageDraw.Draw(border_img)
    border_draw.ellipse((0, 0, border_size, border_size), fill=(255, 255, 255, 230))

    center_x = width // 2
    avatar_x = center_x - avatar_size // 2
    avatar_y = int(height * 0.10)

    bg.paste(border_img, (center_x - border_size // 2, avatar_y - 10), border_mask)
    bg.paste(avatar, (avatar_x, avatar_y), mask)

    buffer = io.BytesIO()
    bg.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="welcome.png")

# ==========================
# MEMBER COUNT
# ==========================

async def update_member_counts() -> None:
    guild = get_main_guild()
    if not guild:
        return

    total = guild.member_count
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)

    all_ch = guild.get_channel(ALL_MEMBERS_CHANNEL_ID)
    on_ch = guild.get_channel(ONLINE_MEMBERS_CHANNEL_ID)

    try:
        if isinstance(all_ch, discord.VoiceChannel):
            name = f"Members: {total}"
            if all_ch.name != name:
                await all_ch.edit(name=name)
        
        if isinstance(on_ch, discord.VoiceChannel):
            name = f"Online: {online}"
            if on_ch.name != name:
                await on_ch.edit(name=name)
    except:
        pass

@tasks.loop(minutes=5)
async def stats_loop():
    await update_member_counts()

@stats_loop.before_loop
async def before_stats_loop():
    await bot.wait_until_ready()

# ==========================
# EVENTS
# ==========================

@bot.event
async def on_ready():
    print(f"\n{'═'*40}")
    print(f"  {bot.user.name}")
    print(f"  ID: {bot.user.id}")
    print(f"  Servers: {len(bot.guilds)}")
    print(f"{'═'*40}\n")
    
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"  Synced {len(synced)} commands")
    except Exception as e:
        print(f"  Sync error: {e}")

    bot.add_view(WelcomeButtons())
    bot.add_view(TicketPanelView())
    bot.add_view(TicketCloseView())

    if not stats_loop.is_running():
        stats_loop.start()

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=SERVER_NAME
        )
    )

@bot.event
async def on_member_join(member: discord.Member):
    if member.bot:
        return

    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass

    try:
        banner = await generate_welcome_banner(member)
    except:
        banner = None

    embed = discord.Embed(
        title=f"✨ Welcome to {SERVER_NAME} ✨",
        description=(
            f"Hey {member.mention}!\n\n"
            f"We're glad you're here 🎉.\n\n"
            f"**Your story begins now!:**\n"
            f"<#{RULES_CHANNEL_ID}> — Server Rules\n"
            f"<#{WHITELIST_CHANNEL_ID}> — Whitelist Application"
        ),
        color=Theme.PRIMARY
    )
    
    embed.set_footer(text=f"Member #{member.guild.member_count}")
    embed.timestamp = discord.utils.utcnow()
    
    if banner:
        embed.set_image(url="attachment://welcome.png")

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        try:
            if banner:
                await channel.send(embed=embed, file=banner, view=WelcomeButtons())
            else:
                await channel.send(embed=embed, view=WelcomeButtons())
        except:
            pass

@bot.event
async def on_member_remove(member: discord.Member):
    if member.bot:
        return
    
    await log_action(
        title="Member Left",
        description=f"**User:** {member.mention}\n**ID:** `{member.id}`",
        color=Theme.WARNING,
        thumbnail=member.display_avatar.url
    )

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return
    
    if after.channel and after.channel.id == WAITING_SUPPORT_VC_ID:
        if before.channel and before.channel.id == WAITING_SUPPORT_VC_ID:
            return
        
        guild = member.guild
        waiting_count = len(after.channel.members)
        
        dm_embed = create_embed(
            title="Voice Support Request",
            description="A user is waiting for voice support.",
            color=Theme.WARNING,
            thumbnail=member.display_avatar.url,
            fields=[
                ("User", f"{member.mention}", True),
                ("Channel", f"{after.channel.mention}", True),
                ("Waiting", f"{waiting_count} user(s)", True)
            ],
            footer=f"{SERVER_NAME} • Voice Support"
        )
        
        await notify_staff_dm(guild, dm_embed)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild or message.guild.id != GUILD_ID:
        return

    now = time.time()
    uid = message.author.id

    if uid not in user_message_times:
        user_message_times[uid] = []

    user_message_times[uid].append(now)
    user_message_times[uid] = [t for t in user_message_times[uid] if now - t <= SPAM_WINDOW_SECONDS]

    if len(user_message_times[uid]) > SPAM_MAX_MESSAGES:
        if SPAM_PUNISH_DELETE:
            try:
                await message.delete()
            except:
                pass

        if SPAM_PUNISH_WARN:
            try:
                embed = create_embed(
                    title="Slow Down",
                    description=f"{message.author.mention}, you're sending messages too fast.",
                    color=Theme.WARNING
                )
                await message.channel.send(embed=embed, delete_after=5)
            except:
                pass

    await bot.process_commands(message)

# ==========================
# COMMANDS
# ==========================

@bot.tree.command(name="help", description="View all commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Command List",
        description="All available commands for this server.",
        color=Theme.PRIMARY
    )
    
    embed.add_field(
        name="Moderation",
        value="`warn` `kick` `ban` `unban` `purge` `slowmode` `lock` `unlock`",
        inline=False
    )
    
    embed.add_field(
        name="Utility",
        value="`help` `ping` `userinfo` `serverinfo` `avatar`",
        inline=False
    )
    
    embed.add_field(
        name="Staff",
        value="`say` `announce` `ticketpanel` `adduser` `removeuser`",
        inline=False
    )
    
    embed.set_footer(text=SERVER_NAME)
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    
    embed = create_embed(
        title="Latency",
        description=f"`{latency}ms`",
        color=Theme.SUCCESS if latency < 100 else Theme.WARNING if latency < 200 else Theme.ERROR
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="userinfo", description="View user information")
@app_commands.describe(user="Target user")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    
    roles = [r.mention for r in user.roles[1:]][:5]
    roles_str = " ".join(roles) if roles else "None"
    
    embed = discord.Embed(
        title="User Information",
        color=user.color if user.color != discord.Color.default() else Theme.PRIMARY
    )
    
    embed.set_thumbnail(url=user.display_avatar.url)
    
    embed.add_field(name="User", value=f"{user.mention}\n`{user.id}`", inline=True)
    embed.add_field(name="Nickname", value=user.nick or "None", inline=True)
    embed.add_field(name="Top Role", value=user.top_role.mention, inline=True)
    embed.add_field(name="Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="Joined", value=f"<t:{int(user.joined_at.timestamp())}:R>", inline=True)
    embed.add_field(name=f"Roles ({len(user.roles) - 1})", value=roles_str, inline=False)
    
    embed.set_footer(text=SERVER_NAME)
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="View server information")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    
    embed = discord.Embed(
        title="Server Information",
        color=Theme.PRIMARY
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="Name", value=guild.name, inline=True)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="Members", value=f"{guild.member_count}", inline=True)
    embed.add_field(name="Channels", value=f"{len(guild.channels)}", inline=True)
    embed.add_field(name="Roles", value=f"{len(guild.roles)}", inline=True)
    embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=True)
    embed.add_field(name="Boosts", value=f"{guild.premium_subscription_count}", inline=True)
    
    embed.set_footer(text=SERVER_NAME)
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="View user avatar")
@app_commands.describe(user="Target user")
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    
    embed = discord.Embed(
        title=f"{user.name}'s Avatar",
        color=Theme.PRIMARY
    )
    embed.set_image(url=user.display_avatar.url)
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Open", style=discord.ButtonStyle.link, url=user.display_avatar.url))
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="ticketpanel", description="Send ticket panel")
async def ticketpanel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Administrator only.", color=Theme.ERROR),
            ephemeral=True
        )

    guild = interaction.guild
    channel = guild.get_channel(TICKET_PANEL_CHANNEL_ID)
    
    if not isinstance(channel, discord.TextChannel):
        return await interaction.response.send_message(
            embed=create_embed(title="Error", description="Invalid channel configuration.", color=Theme.ERROR),
            ephemeral=True
        )

    panel_embed = discord.Embed(
        title="Support Center",
        description=(
            "Need help? Open a ticket below.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Before opening:**\n"
            f"• Read <#{RULES_CHANNEL_ID}>\n"
            "• Prepare issue details\n"
            "• Be patient for response"
        ),
        color=Theme.TICKET
    )
    
    panel_embed.set_author(
        name=guild.name,
        icon_url=guild.icon.url if guild.icon else None
    )
    
    if guild.icon:
        panel_embed.set_thumbnail(url=guild.icon.url)
    
    panel_embed.set_footer(text=f"{SERVER_NAME} • Support")
    panel_embed.timestamp = discord.utils.utcnow()

    await channel.send(embed=panel_embed, view=TicketPanelView())
    
    await interaction.response.send_message(
        embed=create_embed(title="Panel Sent", description=f"Sent to {channel.mention}", color=Theme.SUCCESS),
        ephemeral=True
    )

@bot.tree.command(name="adduser", description="Add user to ticket")
@app_commands.describe(user="User to add")
async def adduser(interaction: discord.Interaction, user: discord.Member):
    if not staff_only(interaction):
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Staff only.", color=Theme.ERROR),
            ephemeral=True
        )
    
    if not interaction.channel.name.startswith("ticket-"):
        return await interaction.response.send_message(
            embed=create_embed(title="Error", description="Use in ticket channels only.", color=Theme.ERROR),
            ephemeral=True
        )
    
    await interaction.channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
    
    await interaction.response.send_message(
        embed=create_embed(title="User Added", description=f"{user.mention} added to ticket.", color=Theme.SUCCESS)
    )

@bot.tree.command(name="removeuser", description="Remove user from ticket")
@app_commands.describe(user="User to remove")
async def removeuser(interaction: discord.Interaction, user: discord.Member):
    if not staff_only(interaction):
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Staff only.", color=Theme.ERROR),
            ephemeral=True
        )
    
    if not interaction.channel.name.startswith("ticket-"):
        return await interaction.response.send_message(
            embed=create_embed(title="Error", description="Use in ticket channels only.", color=Theme.ERROR),
            ephemeral=True
        )
    
    await interaction.channel.set_permissions(user, overwrite=None)
    
    await interaction.response.send_message(
        embed=create_embed(title="User Removed", description=f"{user.mention} removed from ticket.", color=Theme.SUCCESS)
    )

@bot.tree.command(name="purge", description="Delete messages")
@app_commands.describe(amount="Number of messages (1-100)")
async def purge(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Missing permissions.", color=Theme.ERROR),
            ephemeral=True
        )

    amount = max(1, min(100, amount))
    await interaction.response.defer(ephemeral=True)
    
    deleted = await interaction.channel.purge(limit=amount)
    
    await interaction.followup.send(
        embed=create_embed(title="Purge Complete", description=f"Deleted {len(deleted)} messages.", color=Theme.SUCCESS),
        ephemeral=True
    )
    
    await log_action(
        title="Messages Purged",
        description=f"**By:** {interaction.user.mention}\n**Channel:** {interaction.channel.mention}\n**Count:** {len(deleted)}",
        color=Theme.WARNING
    )

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="User to warn", reason="Warning reason")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not staff_only(interaction):
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Staff only.", color=Theme.ERROR),
            ephemeral=True
        )

    try:
        dm_embed = create_embed(
            title="Warning Received",
            description=f"You received a warning in **{interaction.guild.name}**",
            color=Theme.WARNING,
            fields=[("Reason", reason, False)]
        )
        await user.send(embed=dm_embed)
    except:
        pass

    embed = create_embed(
        title="User Warned",
        description=f"{user.mention} has been warned.",
        color=Theme.WARNING,
        fields=[
            ("Reason", reason, False),
            ("Moderator", interaction.user.mention, False)
        ]
    )
    
    await interaction.response.send_message(embed=embed)
    
    await log_action(
        title="User Warned",
        description=f"**User:** {user.mention}\n**By:** {interaction.user.mention}\n**Reason:** {reason}",
        color=Theme.WARNING,
        thumbnail=user.display_avatar.url
    )

@bot.tree.command(name="kick", description="Kick a user")
@app_commands.describe(user="User to kick", reason="Kick reason")
async def kick_cmd(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Missing permissions.", color=Theme.ERROR),
            ephemeral=True
        )

    try:
        dm_embed = create_embed(
            title="You Were Kicked",
            description=f"You were kicked from **{interaction.guild.name}**",
            color=Theme.ERROR,
            fields=[("Reason", reason, False)]
        )
        await user.send(embed=dm_embed)
    except:
        pass

    await interaction.response.defer()
    
    try:
        await user.kick(reason=f"{interaction.user} - {reason}")
        
        await interaction.followup.send(
            embed=create_embed(
                title="User Kicked",
                description=f"{user} has been kicked.",
                color=Theme.SUCCESS,
                fields=[("Reason", reason, False)]
            )
        )
        
        await log_action(
            title="User Kicked",
            description=f"**User:** {user}\n**By:** {interaction.user.mention}\n**Reason:** {reason}",
            color=Theme.ERROR,
            thumbnail=user.display_avatar.url
        )
    except Exception as e:
        await interaction.followup.send(
            embed=create_embed(title="Error", description=f"Failed: {e}", color=Theme.ERROR)
        )

@bot.tree.command(name="ban", description="Ban a user")
@app_commands.describe(user="User to ban", reason="Ban reason")
async def ban_cmd(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Missing permissions.", color=Theme.ERROR),
            ephemeral=True
        )

    view = ConfirmView()
    embed = create_embed(
        title="Confirm Ban",
        description=f"Ban **{user}**?\n\n**Reason:** {reason}",
        color=Theme.WARNING
    )
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await view.wait()
    
    if view.value is None:
        return await interaction.edit_original_response(
            embed=create_embed(title="Timed Out", description="Confirmation expired.", color=Theme.ERROR),
            view=None
        )
    
    if not view.value:
        return await interaction.edit_original_response(
            embed=create_embed(title="Cancelled", description="Ban cancelled.", color=Theme.INFO),
            view=None
        )

    try:
        dm_embed = create_embed(
            title="You Were Banned",
            description=f"You were banned from **{interaction.guild.name}**",
            color=Theme.ERROR,
            fields=[("Reason", reason, False)]
        )
        await user.send(embed=dm_embed)
    except:
        pass

    try:
        await user.ban(reason=f"{interaction.user} - {reason}", delete_message_days=1)
        
        await interaction.edit_original_response(
            embed=create_embed(title="User Banned", description=f"{user} has been banned.", color=Theme.SUCCESS),
            view=None
        )
        
        await log_action(
            title="User Banned",
            description=f"**User:** {user}\n**By:** {interaction.user.mention}\n**Reason:** {reason}",
            color=Theme.ERROR,
            thumbnail=user.display_avatar.url
        )
    except Exception as e:
        await interaction.edit_original_response(
            embed=create_embed(title="Error", description=f"Failed: {e}", color=Theme.ERROR),
            view=None
        )

@bot.tree.command(name="unban", description="Unban a user")
@app_commands.describe(user_id="User ID to unban")
async def unban_cmd(interaction: discord.Interaction, user_id: str):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Missing permissions.", color=Theme.ERROR),
            ephemeral=True
        )

    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        
        await interaction.response.send_message(
            embed=create_embed(title="User Unbanned", description=f"{user} has been unbanned.", color=Theme.SUCCESS)
        )
        
        await log_action(
            title="User Unbanned",
            description=f"**User:** {user}\n**By:** {interaction.user.mention}",
            color=Theme.SUCCESS
        )
    except Exception as e:
        await interaction.response.send_message(
            embed=create_embed(title="Error", description=f"Failed: {e}", color=Theme.ERROR),
            ephemeral=True
        )

@bot.tree.command(name="slowmode", description="Set slowmode")
@app_commands.describe(seconds="Delay in seconds (0 to disable)")
async def slowmode(interaction: discord.Interaction, seconds: int):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Missing permissions.", color=Theme.ERROR),
            ephemeral=True
        )

    seconds = max(0, min(21600, seconds))
    await interaction.channel.edit(slowmode_delay=seconds)
    
    if seconds == 0:
        title = "Slowmode Disabled"
        desc = "Slowmode has been disabled."
    else:
        title = "Slowmode Set"
        desc = f"Slowmode set to {seconds} seconds."
    
    await interaction.response.send_message(embed=create_embed(title=title, description=desc, color=Theme.SUCCESS))
    
    await log_action(
        title="Slowmode Updated",
        description=f"**Channel:** {interaction.channel.mention}\n**Delay:** {seconds}s\n**By:** {interaction.user.mention}",
        color=Theme.INFO
    )

@bot.tree.command(name="lock", description="Lock channel")
async def lock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Missing permissions.", color=Theme.ERROR),
            ephemeral=True
        )

    overwrites = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrites.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
    
    await interaction.response.send_message(
        embed=create_embed(title="Channel Locked", description="This channel has been locked.", color=Theme.ERROR)
    )
    
    await log_action(
        title="Channel Locked",
        description=f"**Channel:** {interaction.channel.mention}\n**By:** {interaction.user.mention}",
        color=Theme.ERROR
    )

@bot.tree.command(name="unlock", description="Unlock channel")
async def unlock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Missing permissions.", color=Theme.ERROR),
            ephemeral=True
        )

    overwrites = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrites.send_messages = True
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
    
    await interaction.response.send_message(
        embed=create_embed(title="Channel Unlocked", description="This channel has been unlocked.", color=Theme.SUCCESS)
    )
    
    await log_action(
        title="Channel Unlocked",
        description=f"**Channel:** {interaction.channel.mention}\n**By:** {interaction.user.mention}",
        color=Theme.SUCCESS
    )

@bot.tree.command(name="say", description="Send a message as bot")
@app_commands.describe(message="Message content")
async def say(interaction: discord.Interaction, message: str):
    if not staff_only(interaction):
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Staff only.", color=Theme.ERROR),
            ephemeral=True
        )
    
    await interaction.response.send_message(
        embed=create_embed(title="Sent", description="Message sent.", color=Theme.SUCCESS),
        ephemeral=True
    )
    
    await interaction.channel.send(message)

# PREMIUM ANNOUNCE COMMAND
@bot.tree.command(name="announce", description="Send a professional announcement")
@app_commands.describe(
    title="Announcement title",
    message="Announcement message",
    footer="Custom footer (optional)",
    ping_everyone="Ping @everyone",
    ping_here="Ping @here",
    role="Role to ping (optional)",
    channel="Target channel (optional)"
)
@app_commands.choices(ping_everyone=[
    app_commands.Choice(name="Yes", value="yes"),
    app_commands.Choice(name="No", value="no")
])
@app_commands.choices(ping_here=[
    app_commands.Choice(name="Yes", value="yes"),
    app_commands.Choice(name="No", value="no")
])
async def announce(
    interaction: discord.Interaction,
    title: str,
    message: str,
    footer: str = None,
    ping_everyone: str = "no",
    ping_here: str = "no",
    role: discord.Role = None,
    channel: discord.TextChannel = None
):
    if not staff_only(interaction):
        return await interaction.response.send_message(
            embed=create_embed(title="Access Denied", description="Staff only.", color=Theme.ERROR),
            ephemeral=True
        )

    target_channel = channel or interaction.channel

    mentions = []
    if ping_everyone == "yes":
        mentions.append("@everyone")
    if ping_here == "yes":
        mentions.append("@here")
    if role:
        mentions.append(role.mention)
    
    mention_text = " ".join(mentions) if mentions else None

    embed = discord.Embed(
        title=title,
        description=message,
        color=Theme.PREMIUM
    )
    
    embed.set_author(
        name=interaction.guild.name,
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    
    footer_text = footer if footer else SERVER_NAME
    embed.set_footer(
        text=footer_text,
        icon_url=interaction.user.display_avatar.url
    )
    
    embed.timestamp = discord.utils.utcnow()

    if mention_text:
        await target_channel.send(content=mention_text, embed=embed)
    else:
        await target_channel.send(embed=embed)
    
    confirm_embed = create_embed(
        title="Announcement Sent",
        description=f"Posted in {target_channel.mention}",
        color=Theme.SUCCESS
    )
    
    if mentions:
        confirm_embed.add_field(name="Pinged", value=" ".join(mentions), inline=False)
    
    await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
    
    await log_action(
        title="Announcement Posted",
        description=f"**By:** {interaction.user.mention}\n**Channel:** {target_channel.mention}\n**Title:** {title}",
        color=Theme.PREMIUM
    )

# ==========================
# RUN
# ==========================

if __name__ == "__main__":
    bot.run(TOKEN)