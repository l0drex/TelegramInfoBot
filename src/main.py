from telegram.ext import Updater, Filters
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
import opalcheck


# fetch updates from telegram and pass them to the dispatcher
updater = Updater(token='1287009635:AAEXmTiLS4Ff363FHB6kaHTSpE6CjTrJfwE')
dispatcher = updater.dispatcher
jobs = updater.job_queue


def setup():
    # create logs
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    # register handlers
    dispatcher.add_handler(
        CommandHandler('start', handler_start))
    dispatcher.add_handler(
        MessageHandler(Filters.text & (~Filters.command), handler_message))
    dispatcher.add_handler(
        CommandHandler('check_opal', handler_opal_check))
    dispatcher.add_handler(
        MessageHandler(Filters.command, handler_unknown))
    dispatcher.add_handler(
        CallbackQueryHandler(handler_button))


def main():
    # start the bot
    updater.start_polling()
    updater.idle()


def help(update, context):
    # TODO
    update.message.reply_text("Benutze /start um den Bot zu testen.")


def check_opal(context: CallbackContext):
    """Things to do periodically"""
    print('Checking opal status')
    if opalcheck.check_status():
        context.bot.send_message(chat_id='598112141', text='Opal ist wieder online :party:')
        # FIXME check if this works
        context.job.schedule_removal()


# define handlers for commands

def handler_start(update, context):
    """Handler for /start"""
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def handler_message(update, context):
    """Handler for regular messages"""
    # TODO check if this is something the bot can do
    pass


def handler_opal_check(update, context):
    """Handler to check the status of opal"""
    status = "online"
    online = True
    if not opalcheck.check_status():
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
            job_check_opal = jobs.run_repeating(check_opal, 1, interval=60, first=0)
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
