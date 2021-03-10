from flask import Flask, request, abort
from threading import Thread
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
	ImageMessage, ImageSendMessage
)

import discordbot_main

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
group_id = os.environ["GROUP_ID"]

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

def send_message(event, message):
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text=message))

def send_image(event, url):
	line_bot_api.reply_message(
		event.reply_token,
		ImageSendMessage(original_content_url=url, 
						preview_image_url=url))

def send_message_image(event, message, url):
	line_bot_api.reply_message(
		event.reply_token, [
		TextSendMessage(text=message),
		ImageSendMessage(original_content_url=url, 
						preview_image_url=url)])

def send_push_message(group_id, message, author_name, author_url):
	send_data = {
			"type": "text",
			"text": message,
			"sender": {
				"name": author_name,
				"iconUrl": str(author_url)
			}
		}
	line_bot_api.push_message(group_id,
							TextSendMessage.new_from_json_dict(send_data))

def send_push_image(group_id, image_url, author_name, author_url):
	send_data = {
			"type": "image",
			"previewImageUrl": str(image_url),
			"originalContentUrl": str(image_url),
			"sender": {
				"name": author_name,
				"iconUrl": str(author_url)
			}
		}
	try:
		line_bot_api.push_message(group_id,
							ImageSendMessage.new_from_json_dict(send_data))
	except:
		pass

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	print(event)
	message_content = event.message.text
	event_group_id = event.source.group_id

	if event_group_id != group_id:
		# オウム返し
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(text=message_content))
		return

	try:
		profile = line_bot_api.get_profile(event.source.user_id)
		discordbot_main.send_to_discord(message_content, profile.display_name, profile.picture_url)
	except:
		discordbot_main.send_to_discord(message_content, "LINE", None)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
	print(event)
	message_id = event.message.id
	message_content = line_bot_api.get_message_content(message_id)

	from pathlib import Path
	with open(Path(f"images/{message_id}.jpg").absolute(), "wb") as f:
		for chunk in message_content.iter_content():
			f.write(chunk)

	try:
		profile = line_bot_api.get_profile(event.source.user_id)
		discordbot_main.send_to_discord(None, profile.display_name, profile.picture_url, f"{message_id}.jpg")
	except:
		discordbot_main.send_to_discord(None, "LINE", None, f"{message_id}.jpg")

def run():
	app.run(host="0.0.0.0")

def start():
	t = Thread(target=run)
	t.start()