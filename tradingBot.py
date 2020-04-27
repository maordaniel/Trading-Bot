from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram import ParseMode
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.schedulers.blocking import BlockingScheduler
from requests_html import HTMLSession
from emoji import emojize
import json
import logging

updater = Updater(token='Your Telegram Bot Token')

j = updater.job_queue
scheduler = BlockingScheduler()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

group_id = "Group/Chat ID"


def get_daily_data(bot, job):
    arrow_down = emojize(":chart_with_upwards_trend:", use_aliases=True)
    arrow_up = emojize(":chart_with_downwards_trend:", use_aliases=True)
    session = HTMLSession()
    with open('symbols.json') as json_file:
        json_data = json.load(json_file)
        symbols = json_data["symbols"]
        for item in symbols:
            res = session.get(item['url'])
            title = res.html.find("[class='float_lang_base_1 relativeAttr']")[0].text
            data = res.html.find("[class='top bold inlineblock']")[0].find('span')
            trade_data = {"price": data[0].text, "daily_change": data[1].text, "percentage": data[3].text}
            change = data[3].text[0]
            if change == '-':
                arrow = arrow_down
            elif change == '+':
                arrow = arrow_up
            else:
                arrow = ""
            text_message = f"""
                *{title}*
            
{arrow} {trade_data['price']}  {trade_data['daily_change']}  ({trade_data['percentage']})"""
            if not item["msgId"]:
                message = bot.send_message(chat_id=group_id, text=text_message, timeout=60,
                                           parse_mode=ParseMode.MARKDOWN)
                item["msgId"] = message.message_id
                with open('symbols.json', 'w') as outfile:
                    json.dump(json_data, outfile)
            else:
                try:
                    bot.edit_message_text(text=text_message, chat_id=group_id, message_id=item["msgId"],
                                          timeout=60, parse_mode=ParseMode.MARKDOWN)
                except BadRequest:
                    pass


def get_weekly_data(bot, job):
    bar = emojize(":bar_chart:", use_aliases=True)
    # arrow_up = emojize(":chart_with_downwards_trend:", use_aliases=True)
    session = HTMLSession()
    with open('Oil.json') as json_file:
        json_data = json.load(json_file)
        symbols = json_data["symbols"]
        for item in symbols:
            res = session.get(item['url'])
            title = res.html.find("[class='ecTitle float_lang_base_1 relativeAttr']")[0].text
            data = res.html.find("[class='releaseInfo bold']")[0].find('span')
            text_message = f"""
                    {bar}*{title}*

"""
            for val in data:
                text = val.text.rsplit('\n')
                text_message += f"{text[0]}: {text[1]}\n"
            if not item["msgId"]:
                message = bot.send_message(chat_id=group_id, text=text_message, timeout=60,
                                           parse_mode=ParseMode.MARKDOWN)
                item["msgId"] = message.message_id
                with open('Oil.json', 'w') as outfile:
                    json.dump(json_data, outfile)
            else:
                try:
                    bot.edit_message_text(text=text_message, chat_id=group_id, message_id=item["msgId"],
                                          timeout=60, parse_mode=ParseMode.MARKDOWN)
                except BadRequest:
                    pass


trigger1 = OrTrigger([CronTrigger(minute=31, second=5)])
trigger2 = OrTrigger([CronTrigger(second=30)])
scheduler.add_job(get_weekly_data, trigger1, [updater.bot, j])
scheduler.add_job(get_daily_data, trigger2, [updater.bot, j])

scheduler.start()

dispatch = updater.dispatcher
print('Running ...')
updater.start_polling()
updater.idle()
