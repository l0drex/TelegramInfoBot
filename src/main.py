#!/usr/bin/env/python

from datetime import date
import logging
from typing import List

from telegram.ext import Updater, Filters
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secret
from modules import openmensa, url

urls = {'opal': 'https://bildungsportal.sachsen.de/opal/',
        'mensa': 'https://api.studentenwerk-dresden.de/openmensa/v2'}

# fetch updates from telegram and pass them to the dispatcher
updater = Updater(token=secret.token)
dispatcher = updater.dispatcher
jobs = updater.job_queue


def setup():
    openmensa.url_canteen = urls['mensa']

    # create logs
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    # register handlers
    dispatcher.add_handler(
        CommandHandler(['start', 'help'], command_help))
    dispatcher.add_handler(
        CommandHandler('check_opal', command_check))
    dispatcher.add_handler(
        CommandHandler('mensa', command_canteen))
    dispatcher.add_handler(
        CallbackQueryHandler(button))
    dispatcher.add_handler(
        MessageHandler(Filters.text & (~Filters.command), handler_message))
    dispatcher.add_handler(
        MessageHandler(Filters.command, command_unknown))
    dispatcher.add_error_handler(error)


def main():
    # start the bot
    updater.start_polling()
    updater.idle()


def check_opal(context: CallbackContext):
    """Checking opal periodically"""
    print('Checking opal status')
    if url.check_status(urls["opal"]):
        context.bot.send_message(chat_id='598112141', text='Opal ist wieder online :tada:')
        # FIXME check if this works
        context.job.schedule_removal()


# define handlers for commands

def command_help(update, context):
    """Command to show what the bot can do."""
    message = '/check_opal: Prüfe, ob Opal zur Zeit online ist. :books:'
    message += '\n/mensa <name> <tag>: Schicke die aktuellen Speisen in der Mensa. :fork_and_knife:'
    update.message.reply_text(message)


def command_check(update, context):
    """Handler to check the status of opal"""
    status = "online"
    online = True
    if not url.check_status(urls["opal"]):
        status = "mal wieder offline"
        online = False

    update.message.reply_text(f"Opal ist zur Zeit {status}.")

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


def command_canteen(update, context):
    """Handler to get current meals from the canteen"""
    # /mensa WUeins heute
    # /mensa Alte morgen
    # fixme

    # set argument variables
    day = date.today()
    canteen_selected = ''
    if len(context.args) >= 1:
        canteen_selected = context.args[0].casefold()
    elif len(context.args) >= 2:
        day = context.args[1]

    canteens: List[openmensa.Canteen] = openmensa.get_canteens()
    keyboard = []
    i = 0

    # search for a canteen that matches the user request
    for c in canteens:
        c_name = c.name.casefold().replace(' ', '')

        if i % 2 == 0:
            keyboard[i].append([])
        keyboard[(i * 0.5)][i % 2].append(InlineKeyboardButton(c.name, callback_data=c.id))
        if canteen_selected != '' and canteen_selected in c_name:
            canteen_selected = c
            break
        i += 1

    # if no canteen could be found, provide buttons
    if not isinstance(canteen_selected, openmensa.Canteen):
        # TODO let the user select a canteen
        update.message.reply_text(
            'Mensa konnte nicht gefunden werden.\n' +
            'Bitte wähle eine aus der Liste aus:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # get day
    if day == 'heute':
        day = date.today().isoformat()

    # get meals
    meals = canteen_selected.get_meals(day)

    message = 'Heute gibt es:'
    for meal in meals:
        meal_name = meal['name']
        meal_price = meal['prices']['Studierende']
        message += f'\n\n * {meal_name} ({meal_price}€)'

    update.message.reply_text(message)


def handler_message(update, context):
    """Handler for regular messages"""
    # TODO check if this is something the bot can do
    pass


def button(update, context):
    """Handler for button presses"""
    query = update.callback_query
    query.answer()
    message = 'Unknown button'

    # NOTE add button handlers here
    # opal
    if query.message.text == 'Soll eine Nachricht geschickt werden, sobald Opal wieder online ist?':
        if query.data == '1':
            message = 'Ich werde eine Nachricht schicken, sobald Opal wieder online ist.'
            job_check_opal = jobs.run_repeating(check_opal, interval=120, first=0)
        else:
            message = 'Ich schicke keine Nachricht, wenn Opal wieder online ist.'
    # mensa
    elif query.message.text == 'Mensa konnte nicht gefunden werden.\nBitte wähle eine aus der Liste aus:':
        context.args[0] = query.data
        command_canteen(update, context)
    query.edit_message_text(text=message)


def command_unknown(update, context):
    """Handler for unknown commands"""
    update.message.reply_text("Sorry, das hab ich nicht verstanden.")


def error(update, context):
    """Log errors caused by updates"""
    # TODO handle exceptions
    try:
        raise context.error
    except Unauthorized:
        # remove update.message.chat_id from conversation list
        pass
    except BadRequest:
        # handle malformed requests
        pass
    except TimedOut:
        # handle slow connection problems
        pass
    except NetworkError:
        # handle other connection problems
        pass
    except ChatMigrated as e:
        pass
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        pass
        # handle all other telegram related errors


if __name__ == "__main__":
    setup()
    main()
