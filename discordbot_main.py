import discord
import os

import linebot_main

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
webhook_url = os.getenv("WEBHOOK_URL")
group_id = os.getenv("GROUP_ID")

def send_to_discord(content, user_name, avatar_url, file_name=None):
	webhook = discord.Webhook.from_url(webhook_url, adapter=discord.RequestsWebhookAdapter())
	if file_name:
		with open(f"images/{file_name}", "rb") as f:
			send_file = discord.File(f, "image.jpg")
		webhook.send(content=content, username=user_name, avatar_url=avatar_url, file=send_file)
		os.remove(f"images/{file_name}")
	else:
		webhook.send(content=content, username=user_name, avatar_url=avatar_url)

@client.event
async def on_ready():
	await client.change_presence(activity=discord.Game(name="Discord", type=1))

@client.event
async def on_message(message):

	if message.author.bot:
		return
	
	# サーバーの確認
	if message.guild.id != 000000000000000000:
		return

	content = message.content
	author_name = message.author.display_name
	author_url = message.author.avatar_url

	if content:
		linebot_main.send_push_message(group_id, content, author_name, author_url)

	for attachment in message.attachments:
		url = attachment.proxy_url
		linebot_main.send_push_image(group_id, url, author_name, author_url)

def run():
	client.run(TOKEN)

def start():
	run()