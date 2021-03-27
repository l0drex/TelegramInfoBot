#!/usr/bin/env python

from datetime import date, timedelta
import logging
from typing import List

from telegram.ext import Updater, Filters
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secret
from modules import openmensa, url

logger = logging.getLogger(__name__)
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
        CommandHandler('check_opal', command_opal))
    dispatcher.add_handler(
        CommandHandler('mensa', command_canteen))
    dispatcher.add_handler(
        CallbackQueryHandler(button))
    dispatcher.add_handler(
        MessageHandler(Filters.command, command_unknown))
    dispatcher.add_error_handler(error)


def main():
    # start the bot
    updater.start_polling()
    updater.idle()


def check_opal(context: CallbackContext):
    """Checking opal periodically"""
    logger.debug('Checking status of opal.')
    if url.check_status(urls["opal"]):
        logger.info('Opal is online')
        context.bot.send_message(chat_id='598112141', text='Opal ist wieder online :tada:')
        # FIXME check if this works
        context.job.schedule_removal()


# define handlers for commands

def command_help(update, _):
    """Command to show what the bot can do."""
    logger.info('Executing command help.')
    message = '/check_opal: Prüfe, ob Opal zur Zeit online ist. :books:'
    message += '\n/mensa <name> <tag>: Schicke die aktuellen Speisen in der Mensa. :fork_and_knife:'
    update.message.reply_text(message)


def command_opal(update, _):
    """Handler to check the status of opal"""
    logger.info('Executing command opal.')

    status = "online"
    online = True
    if not url.check_status(urls["opal"]):
        logger.info('Opal is offline.')
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
    logger.info('Executing command mensa.')

    # /mensa alte-mensa morgen

    # get canteen
    canteen = None
    canteen_str = ''
    if len(context.args) >= 1:
        canteen_str = context.args[0].casefold()
        canteens: List[openmensa.Canteen] = openmensa.get_canteens()

        # search for a canteen that matches the user request
        for c in canteens:
            c_name = c.name.casefold().replace(' ', '-')
            if canteen_str != '' and canteen_str in c_name:
                canteen = openmensa.Canteen(c.id, c.name)
                break
    else:
        logger.warning('No canteen provided')

    # if no canteen could be found, provide buttons
    if canteen is None:
        logger.warning(f'No canteen matching {canteen_str} found.')
        # TODO let the user select a canteen
        update.message.reply_text(
            'Mensa konnte nicht gefunden werden.\n' +
            'Folgende Mensen sind verfügbar:\n\n' +
            '\n'.join(map(str, [c.name.casefold().replace(' ', '-') for c in openmensa.get_canteens()]))
        )
        return

    logger.info(f'Using canteen {canteen.name}')

    # get day
    if len(context.args) >= 2:
        day_str = context.args[1].casefold()
        if day_str in ['heute', 'today']:
            day = date.today()
        elif day_str in ['morgen', 'tomorrow']:
            day = date.today() + timedelta(days=1)
        else:
            logger.info('Trying to parse provided string as iso format.')
            try:
                day = date.fromisoformat(day_str)
            except ValueError as e:
                logger.error(e)
                update.message.reply_text('Das Datum hat ein ungültiges Format.')
                return

            if day < date.today():
                logger.warning('Given date is in the past')
                update.message.reply_text('Das Datum ist in der Vergangenheit.')
    else:
        logger.warning('No date provided. Using today.')
        day = date.today()

    logger.info(f'Using day {day.isoformat()}')

    # get meals
    meals = canteen.get_meals(day)

    if canteen.get_day(day)['closed']:
        logger.warning('Canteen is closed.')
        day: date = canteen.get_next_day_opened()
        update.message.reply_text(f'Die {canteen.name} ist leider geschlossen. '
                                  f'Sie öffnet wieder am {day.strftime("%d.%m.%Y")}')
        return

    update.message.reply_text(f'Am {day.strftime("%d.%m.%Y")} hat die {canteen.name}:')
    for meal in meals:
        meal_name = meal['name']
        meal_price = f"{meal['prices']['Studierende']}€ / {meal['prices']['Bedienstete']}€"
        meal_url = meal['url']
        # only provide non-standard photos
        meal_photo = f"meal['image']" \
            if meal['image'] != 'https://static.studentenwerk-dresden.de/bilder/mensen/studentenwerk-dresden-lieber-mensen-gehen.jpg' \
            else ''
        # TODO markdown parsing  for url
        # seems to be broken currently
        message: str = f'{meal_name} ({meal_price})\n{meal_url}'
        update.message.reply_text(message)


def command_unknown(update, _):
    """Handler for unknown commands"""
    logger.info('Executing command unknown.')

    update.message.reply_text("Sorry, das hab ich nicht verstanden.")


def button(update, _):
    """Handler for button presses"""
    query = update.callback_query
    query.answer()
    message = 'Unknown button'

    # NOTE add button handlers here
    # opal
    if query.message.text == 'Soll eine Nachricht geschickt werden, sobald Opal wieder online ist?':
        logger.debug('Got a response from opal buttons')
        if query.data == '1':
            message = 'Ich werde eine Nachricht schicken, sobald Opal wieder online ist.'
            jobs.run_repeating(check_opal, interval=120, first=0)
        else:
            message = 'Ich schicke keine Nachricht, wenn Opal wieder online ist.'
    query.edit_message_text(text=message)


def error(_, context):
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
    except ChatMigrated:
        pass
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        pass
        # handle all other telegram related errors


if __name__ == "__main__":
    setup()
    main()
