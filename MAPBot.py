import os

import asyncio
import json
import requests
import discord
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import Bot
from discord.ext import tasks, commands
import mysql.connector
from ast import For

# Environnement variables

token = os.environ['TOKEN']
Prefix = os.environ['Prefix']
APIUrl = os.environ['DOUrl']
SecretToken = os.environ['SecretToken']
DBName = os.environ['DBName']
DBPassword = os.environ['DBPassword']
DBUser = os.environ['DBUser']
DBHost = os.environ['DBHost']

#loading class
class StatusInfo:
    # init
    def __init__(self, dbcon, tablename):
        self.url = os.environ['DOUrl']
        self.do_token = os.environ['SecretToken']
        self.dbcon = dbcon
        self.tablename = tablename
        self.DBHost = DBHost = os.environ['DBHost']
        self.DBUser = os.environ['DBUser']
        self.DBPassword = os.environ['DBPassword']
        self.DBName = os.environ['DBName']
    # Loading functions
    def AMPStatus(self):
        header = {
            "accept": "application/json",
            "X-Require-Whisk-Auth": self.do_token
            }
        response = requests.get(self.url, headers=header)
        result = json.loads(response.text)
        return result

    def checkTableExists(self):
        dbcur = self.dbcon.cursor()
        dbcur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{0}'
            """.format(self.tablename.replace('\'', '\'\'')))
        if dbcur.fetchone()[0] == 1:
            dbcur.close()
            return True

        dbcur.close()
        return False

    # Connecting to the database

    mydb = mysql.connector.connect(
    host=DBHost,
    port="25060",
    user=DBUser,
    password=DBPassword,
    database=DBName
    )

    # Writing to Database

    mycursor = mydb.cursor()

    if checkTableExists(mydb, "InstanceStatus") == False:
        mycursor.execute("SET @ORIG_SQL_REQUIRE_PRIMARY_KEY = @@SQL_REQUIRE_PRIMARY_KEY")
        mycursor.execute("SET SQL_REQUIRE_PRIMARY_KEY = 0")
        mycursor.execute("CREATE TABLE InstanceStatus (FriendlyName VARCHAR(255), ActiveUsers VARCHAR(255), MaxUsers VARCHAR(255), Game VARCHAR(255), Running VARCHAR(255), CPUUsage VARCHAR(255), MemoryUsage VARCHAR(255))")
        mydb.commit()

    AddData= "INSERT INTO InstanceStatus (FriendlyName, ActiveUsers, MaxUsers, Game, Running, CPUUsage, MemoryUsage) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    for instance in AMPStatus(APIUrl,SecretToken):
        FriendlyName = instance['FriendlyName']
        ActiveUsers = instance['Active Users']
        MaxUsers = instance['Max Users']
        Game = instance['Game']
        Running = instance['Running']
        CPUUsage = instance['CPU Usage']
        MemoryUsage = instance['Memory Usage']
        mycursor.execute(AddData, (FriendlyName,
                                ActiveUsers,
                                MaxUsers,
                                Game,
                                Running,
                                CPUUsage,
                                MemoryUsage
                                )
                        )
        mydb.commit()

# Starting the bot

Description = '''
    Bot made to manage and report on game servers that are hosted on Markaplay™.
'''

intents = discord.Intents.default()

OWNERS = [232011534367326230]
BLACKLIST = []
client = commands.Bot(command_prefix=Prefix,
                      description=Description,
                      intents=intents,
                      help_command=None
                      )


@client.event  # Change the status of the bot
async def on_ready():
    instances_status = StatusInfo()
    while instances_status:
        for instance_status in instances_status:
            await client.change_presence(status=discord.Status.online, activity=discord.Game(
                fr"{instance_status['Game']} | {instance_status['FriendlyName']} | Active Users: {instance_status['Active Users']}\{instance_status['Max Users']}"))
            await asyncio.sleep(10)


@client.command()
async def help(ctx):
    embed = discord.Embed(
        colour=discord.Colour.orange()
    )

    embed.set_author(name='Help')
    embed.add_field(name='GetAllServersStatus', value='Get all Game Servers Status', inline=True)
    embed.add_field(name='GetServerStatus', value='Get a specific Game Server Status', inline=True)

    await ctx.send(embed=embed)


@client.command()  # command to get the result of all the metrics of all the AMP Instances
async def GetAllServersStatus(ctx):
    all_status = StatusInfo()
    for instance_status in all_status:
        embed = discord.Embed(
            colour=discord.Colour.blurple()
        )
        embed.set_author(name=instance_status['FriendlyName'])
        embed.add_field(name='Game', value=instance_status['Game'], inline=True)
        embed.add_field(name='Running', value=instance_status['Running'], inline=True)
        embed.add_field(name='Active Users', value=f"{instance_status['Active Users']}/{instance_status['Max Users']}", inline=True)
        embed.add_field(name='CPU Usage', value=f"{instance_status['CPU Usage']}%", inline=True)
        embed.add_field(name='Memory Usage', value=f"{instance_status['Memory Usage']}%", inline=True)
        
        await ctx.send(embed=embed)


@client.command()  # command to get the result of all the metrics of specific AMP Instances
async def GetServerStatus(ctx, name):
    all_status = StatusInfo()
    is_found = []
    for instance_status in all_status:
        if name in instance_status['FriendlyName']:  # match for the user reponse in the list of all the AMP Instances | powershell equivilent would be if($name -like $instance.FriendlyName)
            is_found.append(True)
            embed = discord.Embed(
                colour=discord.Colour.blurple()
            )
            embed.set_author(name=instance_status['FriendlyName'])
            embed.add_field(name='Game', value=instance_status['Game'], inline=True)
            embed.add_field(name='Running', value=instance_status['Running'], inline=True)
            embed.add_field(name='Active Users', value=f"{instance_status['Active Users']}/{instance_status['Max Users']}", inline=True)
            embed.add_field(name='CPU Usage', value=f"{instance_status['CPU Usage']}%", inline=True)
            embed.add_field(name='Memory Usage', value=f"{instance_status['Memory Usage']}%", inline=True)
            await ctx.send(embed=embed)
        else:
            is_found.append(False)
    if is_found[True] < 0:
        await ctx.send("Oh no! The server you are looking for is not found! :pensive:")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"I don't understand :thinking: \n Please do {Prefix}help to see what commands i can respond to!")


client.run(token)
