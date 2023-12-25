import discord
import re
from asyncio import sleep

EVENT_CATEGORY_NAME = "イベント🎪🚩"
YYYY_MM_DD_PATTERN  = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
MM_DD_PATTERN = r"(\d{1,2})月(\d{1,2})日(.*)"

# 【】を削除
def remove_brackets(text):
    return text.replace("【", "").replace("】", "")

# 正規パターンマッチング
def match_date_pattern(pattern, text):
    match = re.match(pattern, text)
    return match

# イベント通知を送信
async def send_event_notification(creator, match):
    if match:
        date = match.group(1) + "月" + match.group(2) + "日"
        event_title = match.group(3)
        message = f"ハロ～、ドクター。\n{date}に{event_title}を開催するのね。\n"
        message += "このテンプレートに沿ってイベント概要を書いてくれるかしら。\n"
        message += "フフ、あなたの計画が上手く行くことを願っているわ。"
    else:
        message = "ハロ～、ドクター。\nイベントの日程がまだ決まっていないようね。\n"
        message += "後でいいから追記しておいてくれるかしら。\n"
        message += "一応テンプレートも置いておくから、空欄を埋めておいてね。"
    await creator.send(message)

# テンプレートを送信
async def send_event_template(creator):
    await creator.send("--------------------------\n" +
                       "趣旨：\n" + 
                       "期限：\n" +
                       "日程：yyyy年MM月dd日\n" +
                       "場所：\n" +
                       "予算：\n" +
                       "人数：\n" +
                       "特記：\n" + 
                       "--------------------------")
    
# メンバーにイベント通知を送信する
async def notify_members(channel, url, event_title, month, day):
    if channel.guild:
        all_members = channel.guild.members
        for member in all_members:
            if not member.name == "ロドス宴会部長":
                try:
                    await member.send(f"ハロ～、ドクター。\n{month}月{day}日に{event_title}が開催されるらしいわ。\n"
                                      "忘れないうちにカレンダーにさっさと登録しちゃいましょう。")
                    await member.send(url)
                except discord.Forbidden:
                    print(f"Could not send DM to {member.display_name}")

# インテントの生成
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# クライアントの生成
client = discord.Client(intents=intents)

# discordと接続した時に呼ばれる
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

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

    if isinstance(message.channel, discord.TextChannel) and message.channel.category and message.channel.category.name == EVENT_CATEGORY_NAME:
        if "趣旨：" in message.content and "期限：" in message.content and "日程：" in message.content \
                and "場所：" in message.content and "予算：" in message.content and "人数：" in message.content and "特記：" in message.content:
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

                await notify_members(message.channel, url, event_title, month, day)

# クライアントの実行
# 同一ディレクトリにトークンが記載された"token.txt"を配置
file_path = "token.txt"
try:
    with open(file_path, "r") as file:
        token = file.read()
except FileNotFoundError:
    print(f"エラー: {file_path} が見つかりませんでした。")
except Exception as e:
    print(f"エラー: ファイルの読み込み中に問題が発生しました。")
    print(f"詳細: {e}")

client.run(token)