# Swiftnodebot
Telegram bot for monitoring the status of SwiftNodes.

## Table of contents:
1. [About](#About)
2. [Contacts](#Contacts)
3. [Installing Swiftcash core](#InstallingSwiftcashcore)
4. [Installing MariaDB](#InstallingMariaDB)
5. [Creating a user and database](#Creatingauseranddatabase)
6. [Installing Python3](#InstallingPython3)
7. [Setting  permissions for script Files](#SettingpermissionsforscriptFiles)
8. [Getting API key and specifying it in our scripts](#GettingAPIkeyandspecifyingitinourscripts)
9. [Configuring main.cfg  and script.py](#Configuringmain.cfgandscript.py)
10. [Adding to crontab](#Addingtocrontab)
11. [Installing supervisor](#Installingsupervisor)
12. [Final step](#Finalstep)

## <a name="About"></a> About 
Bot written in Python.  
The bot consists of two scripts.  
The first script is to handle information from swiftcash node.   
The second script is telegram bot. This script processes the commands that are sent to the bot and send answers.  
The bot also requires a SQL database.  
It has the following tables:
- nodes
- nodes_users
- users

We need:
- VPS or dedicated server at least 512GB RAM, 1GB HDD or SSD free space. 1 CPU. 
- Ubuntu 18.04

This is MVP version.   

This bot is only for monitoring the SwiftCash network.  
We are not responsible for this bot. We are not responsible for your coins - we do not have access to them. The program code is delivered "as is".  

---
## <a name="Contacts"></a> Contacts
If you have any questions please find me in discord - discord.swiftcash.cc username is SW911#9533. Or telegram - @cooperationblockchain.  
**For donations (further product development) - SwiftAddress SkZ4yZ3Cz3NH3gf3NAUmVicVXCCNVSqRoR**

---

## <a name="InstallingSwiftcashcore"></a> Installing Swiftcash core
1. Log in to your VPS (server). Install the latest Swiftcash core wallet. All info ou can find here:
https://github.com/swiftcashproject/swiftcash  
2. Open .swiftcash directory and write in swiftcash.conf file parametrs rpcuser and rpcpassword.  
For example:  
```
rpcuser=swiftuser
rpcpassword=passswiftuser123
```
3. After that run swiftcashd

---

## <a name="InstallingMariaDB"></a> Installing MariaDB  
```
sudo apt-get install software-properties-common
sudo apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xF1656F24C74CD1D8
sudo add-apt-repository 'deb [arch=amd64] http://mirrors.supportex.net/mariadb/repo/10.2/ubuntu bionic main'
sudo apt update
sudo apt install mariadb-server  mariadb-client
sudo systemctl stop mariadb.service
sudo systemctl start mariadb.service
sudo systemctl enable mariadb.service
sudo mysql_secure_installation
```
During the installation, go through the following steps.
```
Enter current password for root (enter for none): Click Enter, there is no password by default
Set root password? [Y / n]: Y
New password: Specify Password
Re-enter new password: Specify the password again
(Be sure to write down this password. We need him later)
Remove anonymous users? [Y / n]: Y
Disallow root login remotely? [Y / n]: Y
Remove test database and access to it? [Y / n]: Y
Reload privilege tables now? [Y / n]: Y
```
After that you should increase parameter "max_connections" to 1000.
```
sudo  nano /etc/mysql/mariadb.conf.d/50-server.cnf
```
Find line **"max_connections"** and set here this:
```
max_connections  = 1000
```
After that press Ctrl+X and save (press Y). Do this command:
```
sudo systemctl start mariadb.service
```


## <a name="Creatingauseranddatabase"></a> Creating a user and database
Open mysql:
```
mysql -u root –p
```
After that input your password for root user.

Create a new user in mysql command line:
```
CREATE USER 'non-root' @ 'localhost' IDENTIFIED BY '123';
```
In this command, ‘non-root’ is the name that we assign to our new user. And ‘123’ is his password. You can replace with your own values inside quotes.
```
GRANT ALL PRIVILEGES ON *. * TO 'non-root' @ 'localhost';
```
In order for the changes to take effect, run the update command:
```
FLUSH PRIVILEGES;
```
It's all! Your new user has the same permissions in the database as the root user.

After that create a database
```
CREATE DATABASE swiftnodebot;
```
Now you should select your new base:
```
USE swiftnodebot;
```
Now you need to import into it the existing dump database swiftnodebot.sql
```
source_file_path + swiftnodebot.sql;
```

## <a name="InstallingPython3"></a> Installing Python3
```
sudo apt install python3-pip
sudo apt install python3-mysqldb
sudo pip3 install requests python-telegram-bot
```

## <a name="Setting permissionsforscriptFiles"></a> Setting  permissions for script Files
```
chmod +x swiftbot.py
chmod +x script.py
```

## <a name="GettingAPIkeyandspecifyingitinourscripts"></a> Getting API key and specifying it in our scripts
Find in telegram @BotFather
then enter the command /newbot and follow the instructions.

After you get your unique key:
"Use this token to access the HTTP API:
770423201:AAFbdFDNWnsjDNWnDSnnsjWDnf8wAhQMRKQU"  
Copy this key and write it down. We need it in the next step.

Open swiftbot.py file
```
sudo nano swiftbot.py
```
Here you need to do the following steps:
1. Specify the full path to the main.cfg file
config_file = '/home/sergey/9/main.cfg'
replace it with your value.
2. Specify token  
TOKEN = '770423201:AAFbdFDNWnsjDNWnDSnnsjWDnf8wAhQMRKQU'  
replace this value with what BotFatner issued to you


## <a name="Configuringmain.cfgandscript.py"></a> Configuring main.cfg  and script.py

Open main.cfg file and enter here the following values:
```
sudo nano main.cfg
```
Specify your options here:  
```
dbserver - MYSQL server
dbuser - MySQL user
dbpasswd - MySQL user password
database - database name
rpcPort - 8543 (default)
rpcUser - rpcuser of your node (from 1st step)
rpcPassword - rpcuser password of your node (from 1st step)
rpcserver - (localhost) server of your node 
```

Open script.py file
```
sudo nano script.py
```
Here you need to do the following steps:
Specify the full path to the main.cfg, log file, lastblock.cfg:
logfile='/home/sergey/9/script.log'
config_file='/home/sergey/9/main.cfg'
last_block_cfg='/home/sergey/9/lastblock.cfg'
Specify token:
Find line
```
link='https://api.telegram.org/bot770423201:AAFbdFDNWnsjDNWnDSnnsjWDnf8wAhQMRKQU/sendMessage?chat_id=%s&text=%s' % (node['user_id'], message)
```
```
link='https://api.telegram.org/bot770423201:AAFbdFDNWnsjDNWnDSnnsjWDnf8wAhQMRKQU/sendMessage?chat_id=%s&text=%s' % (node['user_id'], message)
```
and put here your token.

## <a name="Addingtocrontab"></a> Adding to crontab
Put the script to autorun by cron:
```
sudo crontab -e
```
And put this:
```
* * * * /script.py 
```
## <a name="Installingsupervisor"></a> Installing supervisor

You should install supervisor for bot  
```
sudo apt install supervisor  
```
then in the /etc/supervisor/conf.d folder, create a file with the .conf extension and paste it inside
```
[program: swiftnodebot]
process_name = swiftnodebot
command = /home/hrzuser/swiftnodebot/swiftbot.py
autostart = true
# autorestart = true
redirect_stderr = true
stdout_logfile = /home/hrzuser/swiftnodebot/swiftbot.log
```
But you must write your own values (specify the full path to the swiftbot.log and swiftbot.py files)

After that do:
```
supervisorctl update
```

After that by the command 
```
ps -A | grep py
```
you should show that swiftbot.py is running

## <a name="Finalstep"></a> Final step  

After that start script.py and check log file.
```
sudo python3 script.py
```

Done:)
