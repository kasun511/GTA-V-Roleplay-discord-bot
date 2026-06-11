# GTA V Roleplay Discord Bot

A Python Discord bot for GTA V/FiveM roleplay communities. It helps staff manage tickets, moderation, welcome messages, announcements, member stats, anti-spam protection, and server support workflows directly from Discord.

## Features

- Custom welcome banner for new members.
- Auto role assignment when members join.
- Welcome embed with rules, whitelist, and server connect button.
- Ticket panel with private ticket channels.
- Staff role access for tickets.
- Staff DM notifications for new tickets.
- Ticket close button.
- Add/remove users from tickets.
- Member count and online count voice channels.
- Anti-spam message protection.
- Join, leave, ticket, and moderation logs.
- Staff announcements with role, `@here`, and `@everyone` ping options.
- Moderation commands for warn, kick, ban, unban, purge, slowmode, lock, and unlock.
- Server info, avatar, ping, help, and utility commands.

## Requirements

- Python 3.10 or newer
- A Discord bot token
- A Discord server where you have administrator access
- Discord Developer Portal access

Install dependencies:

```bash
pip install discord.py pillow aiohttp
```

## Project Files

```text
GTA-V-Roleplay-discord-bot/
├── codexia_staff_bot.py
├── codexia_welcome_bg.png
├── ticket_counter.txt
├── LICENSE
└── README.md
```

## Fields You Must Change

Open `codexia_staff_bot.py` and replace every `change_me` value before running the bot.

### Bot Token

```python
TOKEN = "change_me"
```

Replace with your Discord bot token.

### Discord Server ID

```python
GUILD_ID = change_me
```

Replace with your Discord server/guild ID.

### Welcome Setup

```python
WELCOME_CHANNEL_ID   = change_me
RULES_CHANNEL_ID     = change_me
WHITELIST_CHANNEL_ID = change_me
AUTO_ROLE_ID         = change_me
```

Change these to:

- `WELCOME_CHANNEL_ID`: channel where welcome messages are sent.
- `RULES_CHANNEL_ID`: rules channel shown in the welcome embed.
- `WHITELIST_CHANNEL_ID`: whitelist/application channel shown in the welcome embed.
- `AUTO_ROLE_ID`: role given to new members.

### Server Branding

```python
JOIN_SERVER_URL = "change_me"
SERVER_NAME = "Codexia Roleplay"
WELCOME_BG_FILE = "codexia_welcome_bg.png"
```

Change:

- `JOIN_SERVER_URL`: your FiveM connect link, website, or server join URL.
- `SERVER_NAME`: your RP server name.
- `WELCOME_BG_FILE`: welcome background image filename if you rename it.

### Ticket System

```python
TICKET_PANEL_CHANNEL_ID = change_me
TICKET_CATEGORY_ID      = change_me
STAFF_ROLE_IDS = [
    change_me,
    change_me,
    change_me,
    change_me,
    change_me,
    change_me,
]
```

Change:

- `TICKET_PANEL_CHANNEL_ID`: channel where the ticket panel should be posted.
- `TICKET_CATEGORY_ID`: category where ticket channels are created.
- `STAFF_ROLE_IDS`: role IDs that can view/manage tickets.

### Staff DM Notifications

```python
DM_NOTIFY_ROLE_IDS = [
    change_me,
    change_me,
    change_me,
]
```

These roles receive DM notifications when a new ticket is created.

### Support Voice Channel

```python
WAITING_SUPPORT_VC_ID = change_me
```

Set this to your waiting/support voice channel ID if you use the voice support feature.

### Logging And Member Counters

```python
MOD_LOG_CHANNEL_ID        = change_me
ALL_MEMBERS_CHANNEL_ID    = change_me
ONLINE_MEMBERS_CHANNEL_ID = change_me
```

Change:

- `MOD_LOG_CHANNEL_ID`: channel for logs.
- `ALL_MEMBERS_CHANNEL_ID`: voice channel renamed to show total members.
- `ONLINE_MEMBERS_CHANNEL_ID`: voice channel renamed to show online members.

### Anti-Spam Settings

```python
SPAM_WINDOW_SECONDS = 5
SPAM_MAX_MESSAGES   = 5
SPAM_PUNISH_DELETE  = True
SPAM_PUNISH_WARN    = True
```

Default behavior: if a user sends more than 5 messages in 5 seconds, the bot can delete messages and warn them.

## Discord Developer Portal Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create an application.
3. Open the **Bot** page and create a bot.
4. Copy the bot token into `TOKEN`.
5. Enable these privileged gateway intents:
   - Server Members Intent
   - Message Content Intent
   - Presence Intent
6. Invite the bot to your server with `bot` and `applications.commands` scopes.

Recommended permissions:

- Administrator, easiest for first setup
- Manage Channels
- Manage Roles
- Manage Messages
- Kick Members
- Ban Members
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Use Slash Commands

## Run The Bot

```bash
python codexia_staff_bot.py
```

On startup, the bot syncs slash commands to the configured guild and loads persistent views for welcome buttons, ticket panel buttons, and ticket close buttons.

## Slash Commands

### General

```text
/help
/ping
/serverinfo
/avatar
```

### Tickets

```text
/ticketpanel
/adduser
/removeuser
```

### Moderation

```text
/purge
/warn
/kick
/ban
/unban
/slowmode
/lock
/unlock
```

### Staff

```text
/say
/announce
```

## Ticket Setup

1. Create a ticket category in Discord.
2. Create a channel for the ticket panel.
3. Add the category ID to `TICKET_CATEGORY_ID`.
4. Add the panel channel ID to `TICKET_PANEL_CHANNEL_ID`.
5. Add your staff role IDs to `STAFF_ROLE_IDS`.
6. Start the bot.
7. Run `/ticketpanel`.

Users can then click **Open Ticket** to create private support tickets.

## Welcome Setup

1. Keep `codexia_welcome_bg.png` in the same folder as the bot.
2. Set `WELCOME_CHANNEL_ID`.
3. Set `RULES_CHANNEL_ID`.
4. Set `WHITELIST_CHANNEL_ID`.
5. Set `AUTO_ROLE_ID`.
6. Set `JOIN_SERVER_URL`.

When a member joins, the bot sends a welcome embed and banner, adds the auto role, and shows useful RP server links.

## VPS Deployment

Install packages:

```bash
pip install discord.py pillow aiohttp
```

Run with `screen`:

```bash
screen -S gta-rp-bot
python codexia_staff_bot.py
```

Or use PM2:

```bash
pm2 start codexia_staff_bot.py --name gta-rp-bot --interpreter python3
pm2 save
```

## Security Notes

- Never commit your real bot token to GitHub.
- If your token is exposed, reset it immediately in the Discord Developer Portal.
- Keep staff commands restricted to trusted roles.
- Be careful with `@everyone` and `@here` options in `/announce`.
- Place the bot role high enough to manage users/channels, but below owner/admin roles you do not want it to control.

## License

This project is licensed under the MIT License.
