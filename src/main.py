#!/usr/bin/env/python

from telegram.ext import Updater, Filters
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
import url, secret


urls = {"opal": "https://bildungsportal.sachsen.de/opal/"}

# fetch updates from telegram and pass them to the dispatcher
updater = Updater(token=secret.token)
dispatcher = updater.dispatcher
jobs = updater.job_queue


def setup():
    # create logs
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    # register handlers
    dispatcher.add_handler(
        CommandHandler('start', handler_help))
    dispatcher.add_handler(
        CommandHandler('check_opal', handler_opal_check))
    dispatcher.add_handler(
        CallbackQueryHandler(handler_button))
    dispatcher.add_handler(
        MessageHandler(Filters.text & (~Filters.command), handler_message))
    dispatcher.add_handler(
        MessageHandler(Filters.command, handler_unknown))


def main():
    # start the bot
    updater.start_polling()
    updater.idle()


def handler_help(update, context):
    # TODO
    update.message.reply_text("/check_opal: Prüfe, ob Opal zur Zeit online ist.")


def handler_check_opal(context: CallbackContext):
    """Things to do periodically"""
    print('Checking opal status')
    if url.check_status(urls["opal"]):
        context.bot.send_message(chat_id='598112141', text='Opal ist wieder online :tada:')
        # FIXME check if this works
        context.job.schedule_removal()


# define handlers for commands

def handler_message(update, context):
    """Handler for regular messages"""
    # TODO check if this is something the bot can do
    pass


def handler_opal_check(update, context):
    """Handler to check the status of opal"""
    status = "online"
    online = True
    if not url.check_status(urls["opal"]):
        status = "mal wieder offline"
        online = False

    # FIXME just for testing
    online = False

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Opal ist zur Zeit {status}.")

    if not online:
        # if opal is down, ask to check periodical
        keyboard = [
                [
                    InlineKeyboardButton("Nein", callback_data='0'),
                    InlineKeyboardButton("Ja", callback_data='1')
                ]
            ]
        update.message.reply_text(
            'Soll eine Nachricht geschickt werden, ' +
            'sobald Opal wieder online ist?',
            reply_markup=InlineKeyboardMarkup(keyboard))


def handler_button(update, context):
    """Handler for button presses"""
    query = update.callback_query
    query.answer()
    message = 'Unknown button'

    # NOTE add button handlers here
    if query.message.text == 'Soll eine Nachricht geschickt werden, sobald Opal wieder online ist?':
        if query.data == '1':
            message = 'Ich werde eine Nachricht schicken, sobald Opal wieder online ist.'
            job_check_opal = jobs.run_repeating(handler_check_opal, 1, interval=60, first=0)
        else:
            message = 'Ich schicke keine Nachricht, wenn Opal wieder online ist.'

    query.edit_message_text(text=message)


def handler_unknown(update, context):
    """Handler for unknown commands"""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, das hab ich nicht verstanden."
        )


if __name__ == "__main__":
    setup()
    main()
