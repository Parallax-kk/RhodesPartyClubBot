import discord
import re
from asyncio import sleep

eventCategoryName = "イベント🎪🚩"
yyyyMMddPattern = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
MMddPattern = r"(\d{1,2})月(\d{1,2})日(.*)"

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

    # チャンネルカテゴリ取得
    category = channel.category
    if category.name != eventCategoryName:
        return

    # チャンネルタイトル取得
    channelTitle = channel.name.replace("【", "").replace("】", "")

    # マッチングを試みる
    match = re.match(MMddPattern, channelTitle)

    # DMを送信
    # チャンネルを作成したユーザーのID
    async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create):
        # entry.userがチャンネルを作成したユーザー
        creator = entry.user
        if entry.target.id == channel.id:
            if match:
                # マッチした場合は日付とテキストを返す
                date = match.group(1) + "月" + match.group(2) + "日"
                eventTitle = match.group(3)
                await creator.send("ハロ～、ドクター。\n" + date +"に"+eventTitle+"を開催するのね。\n"+
                                   "このテンプレートに沿ってイベント概要を書いてくれるかしら。\n" +
                                   "フフ、あなたの計画が上手く行くことを願っているわ。")
                await creator.send("--------------------------\n" +
                                   "趣旨：\n" + 
                                   "期限：\n" +
                                   "日程：yyyy年MM月dd日\n" +
                                   "場所：\n" +
                                   "予算：\n" +
                                   "人数：\n" +
                                   "特記：\n" + 
                                   "--------------------------")
            else:
                # マッチしなかった場合はNoneを返す       
                await creator.send("ハロ～、ドクター。\nイベントの日程がまだ決まっていないようね。\n" + 
                                   "後でいいから追記しておいてくれるかしら。\n" + 
                                   "一応テンプレートも置いておくから、空欄を埋めておいてね。")
                await creator.send("--------------------------\n" +
                                   "趣旨：\n" + 
                                   "期限：\n" +
                                   "日程：yyyy年MM月dd日\n" +
                                   "場所：\n" +
                                   "予算：\n" +
                                   "人数：\n" +
                                   "特記：\n" + 
                                   "--------------------------")

# メッセージを受信した時に呼ばれる
@client.event
async def on_message(message):
    # 自分のメッセージを無効
    if message.author == client.user:
        return

    if isinstance(message.channel, discord.TextChannel) and message.channel.category and message.channel.category.name == eventCategoryName:
        # テンプレートのパターンに一致するか確認

        if "趣旨：" in message.content and "期限：" in message.content and "日程：" in message.content and "場所：" in message.content and "予算：" in message.content and "人数：" in message.content and "特記：" in message.content:
            # メッセージから各項目を抽出
            lines = message.content.split("\n")
            purpose, deadline, schedule, location, budget, attendees, notes = "", "", "", "", "", "", ""
            
            addGoogleCalendarFlag = True

            for line in lines:
                if line.startswith("趣旨："):
                    purpose = line[len("趣旨："):].strip()
                elif line.startswith("期限："):
                    deadline = line[len("期限："):].strip()
                elif line.startswith("日程："):
                    schedule = line[len("日程："):].strip()
                    match = re.match(yyyyMMddPattern, schedule)
                    if not match:
                        addGoogleCalendarFlag = False
                elif line.startswith("場所："):
                    location = line[len("場所："):].strip()
                elif line.startswith("予算："):
                    budget = line[len("予算："):].strip()
                elif line.startswith("人数："):
                    attendees = line[len("人数："):].strip()
                elif line.startswith("特記："):
                    notes = line[len("特記："):].strip()

            if addGoogleCalendarFlag:
                MMddMatch = re.match(MMddPattern, message.channel.name.replace("【", "").replace("】", ""))
                yyyyMMddMatch = re.match(yyyyMMddPattern, schedule)
                eventTitle = MMddMatch.group(3)
                year = yyyyMMddMatch.group(1)
                month = "{:02}".format(int(yyyyMMddMatch.group(2)))
                day = "{:02}".format(int(yyyyMMddMatch.group(3)))
                url = "https://www.google.com/calendar/event?action=TEMPLATE" + "&text=" + eventTitle + "&dates=" + year + month + day +  "/" + year + month + day + "&details=" + message.content.replace("\n", "%0D%0A") + "&location=" + location
                if message.guild:
                    all_members = message.guild.members
                    for member in all_members:
                        if not member.name == "ロドス宴会部長":
                            try:
                                await member.send("ハロ～、ドクター。\n" + month + "月" + day + "日" +"に" + eventTitle + "が開催されるらしいわ。\n"+
                                                  "忘れないうちにカレンダーにさっさと登録しちゃいましょう。")
                                await member.send(url)
                            except discord.Forbidden:
                                # 送信が失敗した場合、Forbidden例外が発生します（通常、DMを許可していない場合）
                                print(f"Could not send DM to {member.display_name}")

# クライアントの実行
# 同一ディレクトリにトークンが記載された"Token.txt"を配置
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