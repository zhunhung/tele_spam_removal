import asyncio
import logging
import os
import random
import re
from datetime import timedelta, date
from telethon import TelegramClient, events, types, custom, utils, errors, Button

logging.basicConfig(level=logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.DEBUG)

API_ID = '' #Add your API ID
API_HASH = '' #Add your API Hash
TOKEN = '' #Add your API Token
NAME = TOKEN.split(':')[0]
bot = TelegramClient(NAME, API_ID, API_HASH)
channel = [] #Add channels/groups you want the bot to work in
user_vote_threshold = 5
ban_threshold = 10 # Limits the number of bans a day

# Cheeky messages to choose from
BAN = (
    "Aiyo, another one. Should I ban this user?",
    "Today Uncle on a roll. Ban this user ah?",
    "Wah, busy day for Uncle. Should I ban this user?",
    "Coming coming! Uncle ask this user to siam?",
    "Haiyo, Uncle working from home leh. Who want to ban this user?",
    "No scared, uncle here! Ban?",
    "Should I ban this user? Btw Uncle still haven't receive pay"
)

# Messages to send when people advertise in the group
ADVERT = (
    "Please ah, no advertising here hor. Uncle be fair to all",
    "Sorry ah, if want to share contacts, please pm those asking directly ok? Thank u ah",
    "Tolong tolong, don't advertise here. Uncle give chance liao."
)

ban_user = {k:{} for k in channel}
advert_user = {k:{} for k in channel}
ban_count = {k:{} for k in channel}

# For report
@bot.on(events.NewMessage(pattern='!report', forwards=False))
async def handler(event):
    msg_id = event.message.reply_to_msg_id
    print(event.chat_id)
    if event.chat_id in channel:
        msg_obj = await bot.get_messages(event.chat_id, ids=msg_id)
        if msg_obj:
            user_id = msg_obj.from_id
            admins = []
            async for user in bot.iter_participants(event.chat_id, filter=types.ChannelParticipantsAdmins):
                admins.append(user.id)

            if user_id not in admins:
                today = date.today()
                today_date = today.strftime("%d-%m-%y")
                if today_date in ban_count[event.chat_id]:
                    if ban_count[event.chat_id][today_date] >= ban_threshold:
                        await asyncio.wait([
                            event.respond('Sorry, Uncle today too tired. Oi, @thisiszh your turn', reply_to=event.reply_to_msg_id)
                        ])
                    else:
                        ban_user[event.chat_id][user_id] = {'msg_id':msg_id, 'ban':[], 'noban':[]}
                        await asyncio.wait([
                            event.respond(random.choice(BAN), reply_to=event.reply_to_msg_id, 
                            buttons=[Button.inline('Ban user 0/{}'.format(user_vote_threshold), 'ban {}'.format(user_id)), 
                            Button.inline("Don't ban 0/{}".format(user_vote_threshold), 'noban {}'.format(user_id))])
                        ])
                else:
                    ban_user[event.chat_id][user_id] = {'msg_id':msg_id, 'ban':[], 'noban':[]}
                    await asyncio.wait([
                        event.respond(random.choice(BAN), reply_to=event.reply_to_msg_id, 
                        buttons=[Button.inline('Ban user 0/{}'.format(user_vote_threshold), 'ban {}'.format(user_id)), 
                        Button.inline("Don't ban 0/{}".format(user_vote_threshold), 'noban {}'.format(user_id))])
                    ])

@bot.on(events.CallbackQuery())
async def callback(event):
    button_arr = []
    count = str(event.data, 'utf-8')
    is_ban = count.split(' ')[0]
    user_id = int(count.split(' ')[1])
    voting_user = int(event._sender.id)
    orig_msg = await event.get_message()
    button_row = orig_msg.reply_markup.rows

    for row in button_row:
        button_arr += row.buttons
    
    msg_id = ban_user[event.chat_id][user_id]['msg_id']
    vote_ban_users = ban_user[event.chat_id][user_id]['ban']
    vote_noban_users = ban_user[event.chat_id][user_id]['noban']

    if is_ban == 'ban':
        if voting_user in vote_ban_users:
            vote_ban_users.remove(voting_user)
        
        elif voting_user in vote_noban_users:
            vote_ban_users.append(voting_user)
            vote_noban_users.remove(voting_user)

        else:
            vote_ban_users.append(voting_user)

        if len(vote_ban_users) >= user_vote_threshold:
            # ban user
            await bot.edit_permissions(event.chat_id, int(user_id), view_messages=False)
            try:
                await bot.delete_messages(event.chat_id, msg_id)
            except:
                logging.error('Unable to delete message {}'.format(msg_id), exc_info=True)
            await event.edit("Ok, Uncle make spammer disappear liao.".format(event.data))

            # Counter for number of bans
            today = date.today()
            today_date = today.strftime("%d-%m-%y")
            if len(ban_count[event.chat_id]) == 0:
                ban_count[event.chat_id] = {today_date: 1}
            else:
                existing_key = list(ban_count[event.chat_id].keys())[0]
                if existing_key == today_date:
                    ban_count[event.chat_id][existing_key] += 1
                else:
                    ban_count[event.chat_id] = {today_date:1}

            if user_id in ban_user[event.chat_id]:
                del ban_user[event.chat_id][user_id]
        else:
            new_msg = 'Come faster vote. Should I ban? {} users have participated in the vote'.format(len(vote_ban_users)+len(vote_noban_users))
            buttons=[Button.inline('Ban user {}/{}'.format(str(len(vote_ban_users)), user_vote_threshold), button_arr[0].data), 
            Button.inline("Don't ban user {}/{}".format(str(len(vote_noban_users)), user_vote_threshold), button_arr[1].data)]
            await event.edit(new_msg, buttons=buttons)
            ban_user[event.chat_id][user_id] = {'msg_id':msg_id, 'ban':vote_ban_users,'noban':vote_noban_users}

    else:
        if voting_user in vote_ban_users:
            vote_ban_users.remove(voting_user)
            vote_noban_users.append(voting_user)
        
        elif voting_user in vote_noban_users:
            vote_noban_users.remove(voting_user)

        else:
            vote_noban_users.append(voting_user)

        if len(vote_noban_users) >= user_vote_threshold:
            await event.edit("Ok, Uncle shall not ban")
            if user_id in ban_user[event.chat_id]:
                del ban_user[event.chat_id][user_id]

        else:
            new_msg = 'Come faster vote. Should I ban? {} users have participated in the vote'.format(len(vote_ban_users)+len(vote_noban_users))
            buttons=[Button.inline('Ban user {}/{}'.format(str(len(vote_ban_users)), user_vote_threshold), button_arr[0].data), 
            Button.inline("Don't ban user {}/{}".format(str(len(vote_noban_users)), user_vote_threshold), button_arr[1].data)]
            await event.edit(new_msg, buttons=buttons)
            ban_user[event.chat_id][user_id] = {'msg_id':msg_id, 'ban':vote_ban_users,'noban':vote_noban_users}

    await event.answer()

@bot.on(events.NewMessage)
async def handler(event):
    msg_obj = event.message
    msg_txt = event.message.text
    # print(event.chat_id)
    result = re.match(r"[6|8|9]\d{7}|\+65[6|8|9]\d{7}|\+65\s[6|8|9]\d{7}", msg_txt)
    if (event.chat_id in channel) and (event.chat_id != -1001167169561):
        # Remove contacts
        if msg_obj.contact or result:
            user_id = msg_obj.from_id
            admins = []
            async for user in bot.iter_participants(event.chat_id, filter=types.ChannelParticipantsAdmins):
                admins.append(user.id)

            if user_id not in admins:
                if user_id not in advert_user:
                    advert_user[event.chat_id][user_id] = 1
                else:
                    warning_count = advert_user[event.chat_id][user_id]
                    print('User {} warned {} times'.format(user_id, warning_count))
                    if warning_count >= 3:
                        # silence for awhile
                        await bot.edit_permissions(event.chat_id, user=int(user_id), until_date=timedelta(minutes=60),
                        send_messages=False,
                        send_media=False, send_stickers=False, send_gifs=False,
                        send_games=False, send_inline=False, send_polls=False)
                        del advert_user[event.chat_id][user_id]

                    else:
                        advert_user[event.chat_id][user_id] = warning_count + 1
                user_obj = await bot.get_entity(user_id)
                user_name = user_obj.username
                user_display_name = user_obj.first_name
                if user_name:
                    user_display_name = '@{}'.format(user_name)

                response_msg = random.choice(ADVERT)
                response_msg = response_msg.split(', ')
                response_msg[1] = response_msg[0] + ' ' + user_display_name + ' ' + response_msg[1]
                response_msg = response_msg[1:]
                response_msg = ', '.join(response_msg)
                await asyncio.wait([
                    event.respond(response_msg, reply_to=event.reply_to_msg_id),
                    event.delete()
                ])

    

bot.start(bot_token=TOKEN)
bot.run_until_disconnected()