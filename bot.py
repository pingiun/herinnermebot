import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('root')

import locale
locale.setlocale(locale.LC_TIME, '')

import datetime
import asyncio

from tlask import Tlask
app = Tlask(__name__)

from parsetime import parsetime
from models import Herinnering
from database import db_session, init_db


@app.route('/', chattype='private')
async def start(res, update):
    await res.send(
        "Welkom bij deze bot, hij kan je helpen dingen te herinneren. Voor informatie over de commands, type /help."
    )


@app.route('/help')
async def help(res, update):
    commands = '\n'.join(app.commands)
    await trysendprivate(
        res, update['message']['message_id'],
        "Deze commands kan je gebruiken: \n{}".format(commands))


async def trysendprivate(res, reply_to, text, **options):
    try:
        await res.senduser(text, **options)
    except RuntimeError as e:
        if str(e).startswith('Got a 403 return status.') or str(e).startswith(
                'Got a 400 return status.'):
            await res.send(text, reply_to_message_id=reply_to, **options)
            await res.send(
                "Ik kan nu wel herinneringen voor je opslaan, maar je moet even een gesprek privé met me beginnen om ze ook te kunnen ontvangen."
            )
        else:
            raise


def addherinnering(user, dt, message, from_message):
    herinnering = Herinnering(user, dt, message, from_message[0],
                              from_message[1])
    db_session.add(herinnering)
    db_session.commit()


@app.route(
    '/herinnermij', help='/herinnermij <tijd> "<bericht>"', getextra=True)
async def herinnering(res, update, extra):
    if not extra:
        return await trysendprivate(
            res, update['message']['message_id'],
            "Gebruik dit commando in deze vorm:\n/herinnermij over 3 dagen \"Ik moest dit onthouden\""
        )

    split = extra.split('"')
    try:
        message = split[1]
    except IndexError:
        message = ''
    args = split[0].split()
    if args[0] == 'over':
        args = args[1:]

    if len(args) != 2:
        return await trysendprivate(
            res, update['message']['message_id'],
            "Je kan maar twee woorden gebruiken om een tijd aan te duiden, ik ben nog niet slim genoeg om jouw commando te parsen."
        )
    try:
        tijd = int(args[0])
    except:
        return await trysendprivate(
            res, update['message']['message_id'],
            "Je hoeveelheid moet met een getal uitgedrukt zijn, dus '5' in plaats van 'vijf'."
        )
    dt = parsetime(tijd, args[1])
    if 'reply_to_message' in update['message']:
        from_message = (update['message']['reply_to_message']['chat']['id'],
                        update['message']['reply_to_message']['message_id'])
    else:
        from_message = (None, None)
    try:
        addherinnering(update['message']['from']['id'], dt, message,
                       from_message)
        extratext = " vanwege \"{}\"".format(message) if message else ''
        await trysendprivate(
            res, update['message']['message_id'],
            "Ik zal je herinneren op {}{}.".format(
                dt.strftime("%A %d %B %Y om %H:%M"), extratext))
    except:
        logger.exception()
        await trysendprivate(res, update['message']['message_id'],
                             "Er ging iets mis!")


def bouwlijst(update):
    reminders = Herinnering.query.filter(
        Herinnering.user_id == update['message']['from']['id']).all()
    if len(reminders) == 0:
        return ("Je hebt momenteel geen herinneringen bij me opgeslagen.",
                None)
    lijst = "Dit zijn de herinneringen die je nu hebt staan:\n"
    for reminder in reminders:
        if reminder.message:
            message = reminder.message
        else:
            message = reminder.timestamp.strftime("%A %d %B %Y om %H:%M")
        lijst += "{}\n".format(message)

    keyboard = []
    for reminder in reminders:
        if reminder.message:
            message = reminder.message
        else:
            message = reminder.timestamp.strftime("%A %d %B %Y om %H:%M")
        keyboard.append([{'text': '❌{}'.format(message),
                          'callback_data': '/del/' + str(reminder.id)}])
    return (lijst, keyboard)


@app.route('/mijnherinneringen')
async def herinneringen(res, update):
    lijst, keyboard = bouwlijst(update)
    reply_markup = {'inline_keyboard': keyboard} if keyboard else None
    await trysendprivate(
        res, update['message']['message_id'], lijst, reply_markup=reply_markup)


@app.route('/del/<int:reminder_id>', flavor='callback_query')
async def del_herinnering(res, update, reminder_id):
    reminder = Herinnering.query.filter(Herinnering.id == reminder_id)
    if not reminder:
        await trysendprivate(res, update['message']['message_id'],
                             "Die herinnering bestond niet!")
    else:
        reminder.delete()
        db_session.commit()
        lijst, keyboard = bouwlijst(update['callback_query'])
        reply_markup = {'inline_keyboard': keyboard} if keyboard else None
        await app.editMessageText(
            lijst,
            chat_id=update['callback_query']['from']['id'],
            message_id=update['callback_query']['message']['message_id'],
            reply_markup=reply_markup)


async def handle_herinneringen():
    while True:
        logger.debug("Handling reminders")
        reminders = Herinnering.query.filter(
            Herinnering.timestamp <= datetime.datetime.now())
        if reminders:
            for reminder in reminders:
                logger.debug("Sending reminder to %s", reminder.user_id)
                if reminder.message:
                    message = "Ik moest je herinneren aan:\n" + reminder.message
                else:
                    message = "Ik moest je nu herinneren!"
                try:
                    if reminder.from_message_id and reminder.from_chat_id:
                        await app.forwardMessage(
                            chat_id=reminder.user_id,
                            from_chat_id=reminder.from_chat_id,
                            message_id=reminder.from_message_id)
                    await app.sendMessage(reminder.user_id, message)
                except RuntimeError:
                    pass
        reminders.delete()
        db_session.commit()
        await asyncio.sleep(60)


if __name__ == "__main__":
    init_db()
    app.eventloop.create_task(handle_herinneringen())
    with open('tokenfile') as f:
        app.run(f.read())
