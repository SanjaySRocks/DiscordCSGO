import discord
from discord.ext import tasks
import json
from tabulate import tabulate
import valve.source.a2s
import time, datetime

client = discord.Client()


with open('config.json', 'r') as f:
    config = json.load(f)

MSG_TIMEOUT = int(config['MSG_TIMEOUT'])

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    server.start()

@tasks.loop(seconds = MSG_TIMEOUT)
async def server():
    try:
        with open('servers.json', 'r') as f:
            servers = json.load(f)

        channel = client.get_channel(int(config['QUERY_CHANNEL']))

        for server in servers['servers']:
            SERVER_IP = server['ip']
            SERVER_PORT = server['port']
            
            if server['enabled'] == True:
                try:
                    SERVER_ADDRESS = (SERVER_IP, int(SERVER_PORT))
                    with valve.source.a2s.ServerQuerier(SERVER_ADDRESS) as xserver:
                        info = xserver.info()
                        players = xserver.players()

                    embed = discord.Embed(title=f"{info['server_name']}",
                            description=f"```[{info['map']}] / ({info['player_count']}/{info['max_players']}) / {SERVER_IP}:{SERVER_PORT}```", 
                            color=discord.Color.green())
                    embed.set_thumbnail(url=f"https://image.gametracker.com/images/maps/160x120/csgo/{info['map']}.jpg")

                    if info['player_count'] > 0:
                        table_data = []
                        
                        for i, player in enumerate(players['players'], start=1):
                            if len(player['name']) > 0:
                                player['duration'] = time.strftime("%H:%M:%S", time.gmtime(player['duration']))
                                index = str(i)
                                table_data.append([index.zfill(2), player['name'][:8], player['score'], player['duration']])

                        tdata = tabulate(table_data, headers=['#','Player', 'Score', 'Time'])

                        embed.add_field(name="__Active Players__", value=f'```{tdata}```', inline=True)
                    else:
                        embed.add_field(name="__Active Players__", value="Be the first to join the server", inline=True)
                        
                    
                    embed.timestamp = datetime.datetime.utcnow()
                    embed.set_footer(text='⏱️ AnonymouS Gaming')

                    sent_message = await channel.send(embed=embed, delete_after=MSG_TIMEOUT)
                except valve.source.NoResponseError:
                    embed = discord.Embed(title=f"{SERVER_IP}:{SERVER_PORT} Not Responding...", 
                    description=f"```Error Occured in quering server...```", 
                    color=discord.Color.red())
                    sent_message = await channel.send(embed=embed, delete_after=MSG_TIMEOUT)
                except valve.source.messages.BrokenMessageError:
                    pass

                time.sleep(2)
    except discord.errors.DiscordServerError:
        pass


client.run(config['TOKEN'])