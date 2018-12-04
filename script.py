#!/usr/bin/python3
from __future__ import print_function
import sys
import os
import time
import re
import MySQLdb
import string
import logging
import requests
import json
import concurrent.futures
import urllib.request

logfile='/home/hrzuser/swiftnodebot/script.log'
config_file='/home/hrzuser/swiftnodebot/main.cfg'
last_block_cfg='/home/hrzuser/swiftnodebot/lastblock.cfg'


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename=logfile,level=logging.INFO)
logger = logging.getLogger(__name__)

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

def send_stat(node, timeout):
    time.sleep(1)
    message="Node %s (%s) changed to %s" % (node['name'], node['address'], node['status'])
    link='https://api.telegram.org/bot770423201:AAFbdFDNWnsjDNWnDSnnsjWDnf8wAhQMRKQU/sendMessage?chat_id=%s&text=%s' % (node['user_id'], message)
    with urllib.request.urlopen(link, timeout=timeout) as conn:
        return conn.read()

def send_win(node, timeout):
    time.sleep(1)
    message="Node %s (%s) is a winner" % (node['name'], node['address'])
    link='https://api.telegram.org/bot770423201:AAFbdFDNWnsjDNWnDSnnsjWDnf8wAhQMRKQU/sendMessage?chat_id=%s&text=%s' % (node['user_id'], message)
    with urllib.request.urlopen(link, timeout=timeout) as conn:
        return conn.read()


def update_nodes(node, timeout):
    global stat_nodes
    if not node['status']==old_nodes[node['netaddr']]['status']:
        stat_nodes.append(node['addr'])
    sql="UPDATE nodes SET rank=%s, status='%s', lastseen=%s, lastpaid=%s, activetime=%s WHERE addr='%s'" % (node['rank'], node['status'], node['lastseen'], node['lastpaid'], node['activetime'], node['addr'])
    query_one(sql)


logger.info("Starting block check")
payload = json.dumps({"method": 'getblockcount', "jsonrpc": "2.0"})
response = requests.get(serverURL, headers=headers, data=payload)
latest=int(response.json()['result'])
if os.path.isfile(last_block_cfg):
    config=open(last_block_cfg, 'r')
    last_block=int(config.readline())
    config.close()
else:
    last_block=int(response.json()['result'])

logger.info("From block %s to %s", last_block, latest)

win_nodes=[]
payload = json.dumps({"method": 'swiftnode', "params": ["winners"], "jsonrpc": "2.0"})
response = requests.get(serverURL, headers=headers, data=payload)
for block in response.json()['result']:
    if block['nHeight']>last_block and block['nHeight']<=latest:
        try:
            win_nodes.append(block['winner']['address'])
        except:
            continue

stat_nodes=[]

old_nodes=dict()
for node in query_all("SELECT id, netaddr, status FROM nodes"):
        old_nodes[node[1]]={'id': node[0], 'status': node[2]}
payload = json.dumps({"method": 'swiftnode', "params": ["list"], "jsonrpc": "2.0"})
response = requests.get(serverURL, headers=headers, data=payload)
new_nodes= response.json()['result']
for key, value in old_nodes.items():
    if not any(d['netaddr'] == key for d in new_nodes):
        query_one("UPDATE nodes SET status='REMOVED' WHERE netaddr='%s'" % (key))

nodes_to_update=[]

for node in new_nodes:
    if not node['netaddr'] in old_nodes:
        new_id=query_one("SELECT MAX(id) FROM nodes")[0]
        if new_id==None:
            new_id=0
        else:
            new_id+=1
        sql="INSERT INTO nodes (id, addr, netaddr, rank, status, lastseen, lastpaid, activetime) VALUES (%s, '%s','%s',%s,'%s',%s,%s,%s)" % (new_id, node['addr'], node['netaddr'], node['rank'], node['status'], node['lastseen'], node['lastpaid'], node['activetime'])
        query_one(sql)
    else:
        nodes_to_update.append(node)


with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    future_to_url = {executor.submit(update_nodes, url, 2): url for url in nodes_to_update}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]

win_send=[]
foostring = "','".join(map(str, win_nodes))
foostring = "'"+foostring+"'"
sql="""
SELECT u.id, nu.name, n.netaddr
FROM users u
INNER JOIN nodes_users nu
ON u.id = nu.user_id
INNER JOIN nodes n
ON n.id = nu.node_id WHERE u.win_notif=1 AND n.addr IN (%s)""" % (foostring)
for i in query_all(sql):
    win_send.append({'user_id': i[0], 'name': i[1], 'address': i[2] })

logger.info("Sending %s winner notifications", len(win_send))

with concurrent.futures.ThreadPoolExecutor(max_workers=28) as executor:
    future_to_url = {executor.submit(send_win, url, 2): url for url in win_send}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]

stat_send=[]
foostring = "','".join(map(str, stat_nodes))
foostring = "'"+foostring+"'"
sql="""
SELECT u.id, nu.name, n.netaddr, n.status
FROM users u
INNER JOIN nodes_users nu
ON u.id = nu.user_id
INNER JOIN nodes n
ON n.id = nu.node_id WHERE u.stat_notif=1 AND n.addr IN (%s)""" % (foostring)
for i in query_all(sql):
    stat_send.append({'user_id': i[0], 'name': i[1], 'address': i[2], 'status': i[3] })

logger.info("Sending %s status change notifications", len(stat_nodes))

with concurrent.futures.ThreadPoolExecutor(max_workers=28) as executor:
    future_to_url = {executor.submit(send_stat, url, 2): url for url in stat_send}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]

config=open(last_block_cfg, 'w')
config.write(str(latest))
config.close()