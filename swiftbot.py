#!/usr/bin/python3
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os, time, re
import MySQLdb
import copy
from datetime import datetime, date
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove,KeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler, CallbackQueryHandler)
import string
from random import *
import logging
import requests, json

config_file='/home/hrzuser/swiftnodebot/main.cfg'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN='770423201:AAFbdFDNWnsjDNWnDSnnsjWDnf8wAhQMRKQU'

config={}
if os.path.isfile(config_file):
    with open(config_file, 'r') as myfile:
        data=myfile.readlines()
        for line in data:
            if "=" in line:
                (key, val) = line.rstrip("\n").split("=")
                config[key] = val


dbserver=config['dbserver']
dbuser=config['dbuser']
dbpasswd=config['dbpasswd']
database=config['database']
rpcPort=config['rpcPort']
rpcUser=config['rpcUser']
rpcPassword=config['rpcPassword']
rpcserver=config['rpcserver']

serverURL = 'http://' + rpcUser + ':' + rpcPassword + '@' + rpcserver + ':' + str(rpcPort)
headers = {'content-type': 'application/json'}

helptxt="""
Commands description
/addnode - Add your node. Example:
For one: /addnode 185.220.222.10:8544 node1
For multiple adding: /addnode 185.220.222.10:8544 node1; 185.220.222.11:8544 node2
/removenode – Remove your node. Example:
For one: /removenode 185.220.222.10:8544
For multiple adding: /removenode 185.220.222.10:8544; 185.220.222.11:8544
/removeallnodes - Remove all your nodes from bot's database.
/mynodes - Show all of my nodes added to this bot. These metrics include:
Nodename
IP
Status
Rank
ActiveTime
LastPaid
/nodecount – Get the number of working nodes in the network.
/mynodesbalance – Get the final balance of your nodes.
/enablewinnernotification – Enable notification when your nodes get rewards.
/disablewinnernotification - Disable notification when your nodes get rewards.
/enablestatusnotification - Enable notification when your nodes сhanged status or went offline.
/disablestatusnotification - Disable notification when your nodes сhanged status or went offline.
/help – Get commands description.
/faq – Get FAQ section. Frequently asked questions and user errors.
"""

faqtxt="""FAQ section:
Please see https://telegra.ph/SwiftNodeBot-FAQ-11-29"""


greeting="""
Hello, I'm SwiftNodeBot! Nice to meet you!
I was created to help you with monitoring your swiftnode(s).
Please, add me your swiftnode(s) using the syntax explained in /help.
If you have any question, try the /faq command.
In any case, my developer can answer your questions in discord.swiftcash.cc; his username is SW911#9533.
"""


def query_one(sql):
    try:
        db = MySQLdb.connect(host=dbserver, user=dbuser, passwd=dbpasswd, db=database, charset="utf8")
        db.autocommit(True)
        cursor=db.cursor()
    except MySQLdb.Error:
        raise MySQLdb.Error
    except MySQLdb.Warning:
        pass
    cursor.execute(sql)
    data = cursor.fetchone()
    cursor.close()
    db.close()
    return data


def query_all(sql):
    try:
        db = MySQLdb.connect(host=dbserver, user=dbuser, passwd=dbpasswd, db=database, charset="utf8")
        db.autocommit(True)
        cursor=db.cursor()
    except MySQLdb.Error:
        raise MySQLdb.Error
    except MySQLdb.Warning:
        pass
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return data


def old_user(id):
        sql="""SELECT id FROM users WHERE id=%s""" % (id)
        data=query_one(sql)
        if data:
                return True
        else:
                return False


def start(bot, update):
        if not old_user(update.message.from_user.id):
                sql="INSERT INTO users (id) VALUES (%s)" % (update.message.from_user.id)
                query_one(sql)
        update.message.reply_text(greeting, reply_markup=ReplyKeyboardRemove())


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

def help(bot, update):
        update.message.reply_text(helptxt)


def faq(bot, update):
        update.message.reply_text(faqtxt[0])
        update.message.reply_text(faqtxt[1])


def enablewinnernotification(bot, update):
        sql="UPDATE users SET win_notif=1 WHERE id=%s" %(update.message.from_user.id)
        query_one(sql)
        update.message.reply_text("Winner notification enabled")

def disablewinnernotification(bot, update):
        sql="UPDATE users SET win_notif=0 WHERE id=%s" %(update.message.from_user.id)
        query_one(sql)
        update.message.reply_text("Winner notification disabled")

def enablestatusnotification(bot, update):
        sql="UPDATE users SET stat_notif=1 WHERE id=%s" %(update.message.from_user.id)
        query_one(sql)
        update.message.reply_text("Status change notification enabled")

def disablestatusnotification(bot, update):
        sql="UPDATE users SET stat_notif=0 WHERE id=%s" %(update.message.from_user.id)
        query_one(sql)
        update.message.reply_text("Status change notification disabled")


def addnode(bot, update, args):
        user_id=update.message.from_user.id
        all_nodes=[i[0] for i in query_all("SELECT netaddr FROM nodes")]
        new_nodes=" ".join(args).split(";")
        for node in new_nodes:
                if len(node)>0:
                        try:
                                netaddr, name = node.strip().split()
                        except:
                                message="%s is incorrect netaddress and name pair" % (node)
                                bot.send_message(chat_id=update.message.chat_id, text=message)
                        else:
                                data=query_one("SELECT id FROM nodes WHERE netaddr='%s'" % (netaddr))
                                if data:
                                        node_id=data[0]
                                        data=query_one("SELECT * FROM nodes_users WHERE user_id=%s AND node_id=%s" % (user_id, node_id))
                                        if data:
                                                message="Node %s already in your list" % (netaddr)
                                                bot.send_message(chat_id=update.message.chat_id, text=message)
                                        else:
                                                sql="INSERT INTO nodes_users (user_id, node_id, name) VALUES (%s,%s, '%s')" % (user_id, node_id, name)
                                                query_one(sql)
                                                message="Added node with name %s at IP %s " % (name, netaddr)
                                                bot.send_message(chat_id=update.message.chat_id, text=message)
                                else:
                                        message="Node %s doesn't exist" % (netaddr)
                                        bot.send_message(chat_id=update.message.chat_id, text=message)


def removenode(bot, update, args):
        user_id=update.message.from_user.id
        pattern = re.compile('[0-9]+(?:\.[0-9]+){3}:{0,1}[0-9]*')
        for arg in args:
                if pattern.match(arg):
                        sql="SELECT id FROM nodes WHERE netaddr='%s'" % (arg)
                        data = query_one(sql)
                        if data:
                                node_id = data[0]
                                data=query_one("SELECT * FROM nodes_users WHERE user_id=%s AND node_id=%s" % (user_id, node_id))
                                if data:
                                        sql="DELETE FROM nodes_users WHERE user_id=%s AND node_id=%s" % (user_id, node_id)
                                        query_one(sql)
                                        message="Node %s was deleted" % (arg)
                                        bot.send_message(chat_id=update.message.chat_id, text=message)
                                else:
                                        message="You don't have node %s in your list" % (arg)
                                        bot.send_message(chat_id=update.message.chat_id, text=message)
                        else:
                                message="There's no node %s in our database" % (arg)
                                bot.send_message(chat_id=update.message.chat_id, text=message)


def removeallnodes(bot, update):
        user_id=update.message.from_user.id
        sql="DELETE FROM nodes_users WHERE user_id=%s" % (user_id)
        query_one(sql)
        message="Your nodes were deleted"
        bot.send_message(chat_id=update.message.chat_id, text=message)


def mynodes(bot, update):
        user_id=update.message.from_user.id
        message=""
        sql="""SELECT nu.name, n.netaddr, n.status, n.rank, n.activetime, n.lastpaid
                        FROM nodes n
                        INNER JOIN nodes_users nu
                        ON n.id = nu.node_id
                        INNER JOIN users u
                        ON u.id = nu.user_id WHERE u.id=%s""" % (user_id)
        if len(query_all(sql))==0:
                message="You don't have nodes"
                bot.send_message(chat_id=update.message.chat_id, text=message)
        else:
                mynodes=query_all(sql)
                for idx, node in enumerate(mynodes):
                        lastpaid=datetime.fromtimestamp(node[5]).strftime('%Y-%m-%d %H:%M:%S')
                        txt="Name - %s\nIP - %s\nStatus - %s\nRank - %s\nActiveTime - %s\nLastPaid - %s\n\n" %(node[0],node[1], node[2], node[3], node[4],lastpaid)
                        message+=txt
                        if len(mynodes)>25 and idx % 25==0:
                                message=""
                                bot.send_message(chat_id=update.message.chat_id, text=message)
                if len(message)>0:
                        bot.send_message(chat_id=update.message.chat_id, text=message)

def mynodesbalance(bot, update):
        user_id=update.message.from_user.id
        message=""
        sql="""SELECT n.addr, n.netaddr
        FROM nodes n
        INNER JOIN nodes_users nu
        ON n.id = nu.node_id
        INNER JOIN users u
        ON u.id = nu.user_id WHERE u.id=%s""" %(user_id)

        if len(query_all(sql))==0:
                message="You don't have nodes"
                bot.send_message(chat_id=update.message.chat_id, text=message)
        else:
                for node in query_all(sql):
                        link='https://explorer.swiftcash.cc/api/balance/%s' % (node[0])
                        r=requests.get(link)
                        balance=r.json()['balance']
                        txt = "%s - %s\n" % (node[1], balance)
                        message+=txt
                bot.send_message(chat_id=update.message.chat_id, text=message)


def nodecount(bot, update):
        payload = json.dumps({"method": 'swiftnode', "params": ["list"], "jsonrpc": "2.0"})
        response = requests.get(serverURL, headers=headers, data=payload)
        message="Total nodes count: %s" % (len(response.json()['result']))
        bot.send_message(chat_id=update.message.chat_id, text=message)


def wrong(bot, update):
        message="I'm not sure what you mean? Try /help"
        bot.send_message(chat_id=update.message.chat_id, text=message)

updater = Updater(token=TOKEN, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
dispatcher = updater.dispatcher
addnode_handler=CommandHandler("addnode", addnode, pass_args=True)
removenode_handler=CommandHandler("removenode", removenode, pass_args=True)
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('cancel', cancel))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('faq', faq))
dispatcher.add_handler(CommandHandler('mynodes', mynodes))
dispatcher.add_handler(CommandHandler('removeallnodes', removeallnodes))
dispatcher.add_handler(CommandHandler('nodecount', nodecount))
dispatcher.add_handler(CommandHandler('mynodesbalance', mynodesbalance))
dispatcher.add_handler(CommandHandler('enablewinnernotification', enablewinnernotification))
dispatcher.add_handler(CommandHandler('disablewinnernotification', disablewinnernotification))
dispatcher.add_handler(CommandHandler('enablestatusnotification', enablestatusnotification))
dispatcher.add_handler(CommandHandler('disablestatusnotification', disablestatusnotification))
#dispatcher.add_handler(MessageHandler(Filters.command, wrong))

dispatcher.add_handler(addnode_handler)
dispatcher.add_handler(removenode_handler)
dispatcher.add_error_handler(error)
updater.start_polling()
updater.idle()