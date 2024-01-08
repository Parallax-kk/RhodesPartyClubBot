import discord
import discord.app_commands
from discord.ext import commands
import re
from asyncio import sleep

EVENT_CATEGORY_NAME = "イベント🎪🚩"
YYYY_MM_DD_PATTERN  = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
MM_DD_PATTERN = r"(\d{1,2})月(\d{1,2})日(.*)"

ROLE = "宴会通知"
GUILD_ID = 1187676726109683722

EVNT_TEMPLATE = ("--------------------------\n" +
                 "趣旨：\n" +
                 "期限：\n" +
                 "日程：yyyy年MM月dd日\n" +
                 "場所：\n" +
                 "予算：\n" +
                 "人数：\n" +
                 "特記：\n" + 
                 "--------------------------")

MSG_ADD_EVENT_WITH_DATE = ("ハロ～、ドクター。\n{date}に{event_title}を開催するのね。\n" +
                           "このテンプレートに沿ってイベント概要を書いてくれるかしら。\n" +
                           "フフ、あなたの計画が上手く行くことを願っているわ。")

MSG_ADD_EVENT_WITHOUT_DATE = ("ハロ～、ドクター。\nイベントの日程がまだ決まっていないようね。\n" +
                              "後でいいから追記しておいてくれるかしら。\n" +
                              "一応テンプレートも置いておくから、空欄を埋めておいてね。")

MSG_SUBSCRIBE = ("あら、イベントの通知を任せてくれるのね？\nつまり、あなたはあたしがDMに書いた通りに行動するのよ、ドクター。\nほ～ら、いまさら後悔しても遅いんだからね、フフッ。\n" +
                  "> 通知ロールが付与されました")

MSG_UNSUBSCRIBE = ("お仕事終了ね、先にちょこっと休むわね。\n" +
                   "> 通知ロールが削除されました")

MSG_UPDATE_EVENT = ("ハロ～、ドクター。\n{month}月{day}日の{event_title}に変更があったわ。\n" +
                    "忘れないうちに予定を更新しちゃいましょう。")

MSG_ADD_EVENT_GENERAL = ("ハロ～、ドクター。\n{month}月{day}日に{event_title}が開催されるらしいわ。\n" +
                         "忘れないうちにカレンダーにさっさと登録しちゃいましょう。")

ERROR_MSG_CAN_NOT_SEND_DM = "DMを送信できませんでした : "
ERROR_MSG_PERMISSION_DENIED = "権限がありません。"
ERROR_MSG_ROLE_NOT_FOUND = "ロールが見つかりませんでした。"
ERROR_MSG_GUILD_ID_MISMATCH = "指定されたチャンネルIDと一致しません。"

# インテントの生成
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# クライアントの生成
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# 【】を削除
def remove_brackets(text):
    return text.replace("【", "").replace("】", "")

# 正規パターンマッチング
def match_date_pattern(pattern, text):
    return re.match(pattern, text)

# イベント概要検出処理
async def handle_event_detection(message, change):
    if all(keyword in message.content for keyword in ["趣旨：", "期限：", "日程：", "場所：", "予算：", "人数：", "特記："]):
        lines = message.content.split("\n")
        purpose, deadline, schedule, location, budget, attendees, notes = "", "", "", "", "", "", ""

        add_google_calendar_flag = True

        for line in lines:
            if line.startswith("趣旨："):
                purpose = line[len("趣旨："):].strip()
            elif line.startswith("期限："):
                deadline = line[len("期限："):].strip()
            elif line.startswith("日程："):
                schedule = line[len("日程："):].strip()
                match = match_date_pattern(YYYY_MM_DD_PATTERN, schedule)
                if not match:
                    add_google_calendar_flag = False
            elif line.startswith("場所："):
                location = line[len("場所："):].strip()
            elif line.startswith("予算："):
                budget = line[len("予算："):].strip()
            elif line.startswith("人数："):
                attendees = line[len("人数："):].strip()
            elif line.startswith("特記："):
                notes = line[len("特記："):].strip()

        if add_google_calendar_flag:
            mm_dd_match = match_date_pattern(MM_DD_PATTERN, remove_brackets(message.channel.name))
            yyyy_mm_dd_match = match_date_pattern(YYYY_MM_DD_PATTERN, schedule)
            event_title = mm_dd_match.group(3)
            year = yyyy_mm_dd_match.group(1)
            month = "{:02}".format(int(yyyy_mm_dd_match.group(2)))
            day = "{:02}".format(int(yyyy_mm_dd_match.group(3)))
            url = f"https://www.google.com/calendar/event?action=TEMPLATE" \
                  f"&text={event_title}&dates={year}{month}{day}/{year}{month}{day}" \
                  f"&details={message.content.replace('\n', '%0D%0A')}&location={location}"

            await notify_members(message.channel, url, event_title, month, day, change)

# イベント通知を送信
async def send_event_notification(creator, match):
    if match:
        date = match.group(1) + "月" + match.group(2) + "日"
        event_title = match.group(3)
        await creator.send(MSG_ADD_EVENT_WITH_DATE.format(date=date, event_title=event_title))
    else:
        await creator.send(MSG_ADD_EVENT_WITHOUT_DATE)

# テンプレートを送信
async def send_event_template(creator):
    await creator.send(EVNT_TEMPLATE)
    
# メンバーにイベント通知を送信する
async def notify_members(channel, url, event_title, month, day, change):
    role = discord.utils.get(channel.guild.roles, name=ROLE)

    if channel.guild:
        all_members = channel.guild.members
        for member in all_members:
            if not member.name == "ロドス宴会部長" and role in member.roles:
                try:
                    if change:
                        await member.send(MSG_UPDATE_EVENT.format(month=month, day=day, event_title=event_title))
                    else:
                        await member.send(MSG_ADD_EVENT_GENERAL.format(month=month, day=day, event_title=event_title))
                    await member.send(url)
                except discord.Forbidden:
                    print(ERROR_MSG_CAN_NOT_SEND_DM + "!{member.display_name}")

####################################################################

# discordと接続した時に呼ばれる
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=GUILD_ID))

# チャンネルを作成したときに呼ばれる
@client.event
async def on_guild_channel_create(channel):
    await sleep(1)
    category = channel.category
    if category.name != EVENT_CATEGORY_NAME:
        return

    channel_title = remove_brackets(channel.name)
    mm_dd_match = match_date_pattern(MM_DD_PATTERN, channel_title)

    async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create):
        creator = entry.user
        if entry.target.id == channel.id:
            await send_event_notification(creator, mm_dd_match)
            await send_event_template(creator)

# メッセージを受信したときに呼ばれる
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # イベント概要検出
    elif isinstance(message.channel, discord.TextChannel) and message.channel.category and message.channel.category.name == EVENT_CATEGORY_NAME:
        await handle_event_detection(message, False)

# メッセージの変更検出
@client.event
async def on_message_edit(before, after):
    # イベント概要検出
    if isinstance(after.channel, discord.TextChannel) and after.channel.category and after.channel.category.name == EVENT_CATEGORY_NAME:
        await handle_event_detection(after, True)

# Subscribeコマンド
@tree.command(name="subscribe",description="イベントの通知を受け取る")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.guilds(GUILD_ID)
async def subscribe(ctx:discord.Interaction):
    if ctx.guild.id == int(GUILD_ID):
        role = discord.utils.get(ctx.guild.roles, name=ROLE)

        if role:
            try:
                await ctx.user.add_roles(role)
                await ctx.response.send_message(MSG_SUBSCRIBE, ephemeral=True)
            except discord.Forbidden:
                await ctx.send(ERROR_MSG_PERMISSION_DENIED)
        else:
            await ctx.send(ERROR_MSG_ROLE_NOT_FOUND)
    else:
        await ctx.send(ERROR_MSG_GUILD_ID_MISMATCH)

# Unsubscribeコマンド
@tree.command(name="unsubscribe",description="イベントの通知を解除する")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.guilds(GUILD_ID)
async def unsubscribe(ctx:discord.Interaction):
    if ctx.guild.id == int(GUILD_ID):
        role = discord.utils.get(ctx.guild.roles, name=ROLE)

        if role:
            try:
                await ctx.user.remove_roles(role)
                await ctx.response.send_message(MSG_UNSUBSCRIBE, ephemeral=True)
            except discord.Forbidden:
                await ctx.send(ERROR_MSG_PERMISSION_DENIED)
        else:
            await ctx.send(ERROR_MSG_ROLE_NOT_FOUND)
    else:
        await ctx.send(ERROR_MSG_GUILD_ID_MISMATCH)

# クライアントの実行
client.run(TOKEN)