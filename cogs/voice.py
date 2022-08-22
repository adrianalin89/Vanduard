from logging import exception
from discord.ext import commands
from numpy import empty
import discord
import asyncio
import traceback
import sqlite3
import validators
import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "sqlite.db")

#USER_ROLE_ID = "944682584930132001"
#STAFF_ROLE_ID = "944682584930132001"
OWNER_ID = "326019096825167872"

class voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
         
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        print('--->Update listen')
        
        if after.channel is not None: #if the joined channel is NOT none
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            guildID = member.guild.id #get server id
            c.execute("SELECT voiceChannelID FROM guild WHERE guildID = ?", (guildID,))
            voice=c.fetchone() #get the stage voice ch id
            if voice is None: #if this is none, no stage voice ch created
                print('no stage voice ch created')
                pass
            else:
                stageID = voice[0]
                try:
                    if after.channel.id == stageID: #if the user joins the stage voice ch
                        print('user joins the stage voice ch')
                        c.execute("SELECT * FROM voiceChannel WHERE userID = ?", (member.id,)) #check if user is spaming
                        cooldown=c.fetchone()
                        print(cooldown)
                        if cooldown is None:
                            pass
                        else:
                            print('[ERROR]' + member.name + ' (id: ' + str(member.id) + ") is creating channels too quickly (creating channel failed).")
                            await member.send("Creating channels too quickly you've been put on a 15 second cooldown! Wait it out in the hub voice cheat and you will get transfer to your own voice channel.")
                            await asyncio.sleep(15)

                        c.execute("SELECT voiceCategoryID FROM guild WHERE guildID = ?", (guildID,)) #get the stage category id to create aditional voice ch
                        voice=c.fetchone()
                        c.execute("SELECT channelName, channelLimit FROM userSettings WHERE userID = ?", (member.id,))
                        setting=c.fetchone()
                        c.execute("SELECT channelLimit FROM guildSettings WHERE guildID = ?", (guildID,))
                        guildSetting=c.fetchone()
                        if setting is None: #if there is no voice chanell tied to the user
                            name = f"{member.name}'s voice"
                            #get the limit of the voice chanel
                            if guildSetting is None: 
                                limit = 3
                            else:
                                limit = guildSetting[0]
                        else:
                            if guildSetting is None:
                                name = setting[0]
                                limit = setting[1]
                            elif guildSetting is not None and setting[1] == 0:
                                name = setting[0]
                                limit = guildSetting[0]
                            else:
                                name = setting[0]
                                limit = setting[1]
                        categoryID = voice[0]
                        id = member.id
                        category = self.bot.get_channel(categoryID)
                        
                        server_id = member.guild.id
                        
                        c.execute("SELECT * FROM serverSettings WHERE serverID = ?", (server_id,))
                        serverSettings=c.fetchone()
                        maxChannels = serverSettings[1]
                        
                        c.execute("select (select count() from roomCreated) as count, * from roomCreated")
                        rooms=c.fetchone() #get all romes and the count of them
                        
                        if rooms == None: #if no rooms
                            c.execute("INSERT INTO roomCreated VALUES (0)") #create one
                        total_rooms = rooms[0]
                        print('total rooms=% maxChannels=%',total_rooms,maxChannels)
                        if(total_rooms <= maxChannels):
                            #create new voice channel
                            channel2 = await member.guild.create_voice_channel(name,category=category,position=10)
                            channelID = channel2.id

                            #utenti = discord.utils.get(member.guild.roles, id=USER_ROLE_ID)
                            #staff = discord.utils.get(member.guild.roles, id=STAFF_ROLE_ID)
                            role = discord.utils.get(member.guild.roles, name='@everyone')
                           
                            #move user to the new channel
                            await member.move_to(channel2)
                            await channel2.set_permissions(self.bot.user, connect=True,read_messages=True)
                            await channel2.set_permissions(member, manage_channels=True, mute_members=True, connect=True, move_members=True)
                            #await channel2.set_permissions(utenti, connect=False,read_messages=True)
                            #await channel2.set_permissions(staff, connect=True,read_messages=True)

                            await channel2.set_permissions(role, read_messages=True)
                            await channel2.edit(name=name, user_limit=limit)
                            print('setup of frontend room complete')

                            c.execute("INSERT INTO roomCreated VALUES (?)", (channelID,))
                            conn.commit()
                            
                            c.execute("INSERT INTO voiceChannel VALUES (?, ?)", (id,channelID))
                            conn.commit()

                            
                            print('(' + member.guild.name + ') ' + member.name + ' (id: ' + str(member.id) + ") 's room has been created.")
                            print("Channels: "+str(total_rooms)+"/"+str(maxChannels))
                            
                            def check(a,b,c):
                                return len(channel2.members) == 0
                            await self.bot.wait_for('voice_state_update', check=check)
                            await channel2.delete()
                            
                            c.execute('DELETE FROM voiceChannel WHERE userID=?', (id,))
                            
                            c.execute('DELETE FROM roomCreated WHERE stageID=?', (channelID,))

                            c.execute("select (select count() from roomCreated) as count, * from roomCreated")

                            rooms=c.fetchone()
                            
                            total_rooms = rooms[0]
                            
                            print('(' + member.guild.name + ') ' + member.name + ' (id: ' + str(member.id) + ") 's room has been deleted.")
                            print("Channels: "+str(total_rooms-1)+"/"+str(maxChannels))
                        else:
                            await member.send("Impossibile creare il tuo canale! È stato raggiunto il limite massimo!")
                            print('[ERROR] (' + ctx.author.guild.name + ') Unable to create a voice channel. Max channels limit reached! (reset configs failed).')
                    else:
                        print('else after.channel.id == stageID')

                except Exception as e: 
                    print(e)
                    pass
            conn.commit()
            conn.close()
        else:
            print('else after.channel is none ?')
            print(after.channel)

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="Fireteam voice Helper", description="Guardian to customize the fireteam voice channel use the fallowing commands. You must be in a voice channel to take effect.",color=0x7289da)
        embed.set_author(name=f"{ctx.guild.me.display_name}", icon_url=f"{ctx.guild.me.avatar_url}")
        embed.add_field(name=f'**Commands:**', value=f'**Config the max guardians in your voice channel(Default is 3):**\n`.voice limit number`\n**Example:** `.voice limit 6`\n\n'
                        f'**Rename your channel command:**\n`.voice name <name>`\n**Example:** `.voice name GM farm`\n\n'
                        f'**Take over the channel**\n`.voice claim`\n**Example:** `.voice claim`\nOnly if the owner of the channel left.\n\n'
                        f'**Set incognito:**\n`.voice lock`\nThis will not allow everybody to join the channel\n\n'
                        f'**Exit incognito:**\n`.voice unlock`\nDefault channel are open for everybody\n\n'
                        f'**Wile in incognito, invite user to the channel:**\n`.voice permit @person`\n**Example:** `.voice permit @Alin#1234`\n\n'
                        f'**Wile in incognito, remove and kick user from channel:**\n`.voice reject @person`\n**Example:** `.voice reject @Alin#1234`\n\n', inline='false')
        embed.set_footer(text='Bot powered by Alin')
        await ctx.channel.send(embed=embed)

    @commands.group()
    async def voice(self, ctx):
        pass

    @voice.command()
    async def setup(self, ctx):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        guildID = ctx.guild.id
        id = ctx.author.id
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == OWNER_ID:
            def check(m):
                return m.author.id == ctx.author.id
            print('\n[SETUP] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has started the setup.")
            await ctx.channel.send("**You have 60 seconds to answer each question!**")
            await ctx.channel.send(f"Enter the __name of the category__ you wish to create the channels in: (e.g `voice Channels`)")
            try:
                category = await self.bot.wait_for('message', check=check, timeout = 60.0)
            except asyncio.TimeoutError:
                await ctx.channel.send('Took too long to answer!')
                print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") took too long to answer (setup failed).")
            else:
                new_cat = await ctx.guild.create_category_channel(category.content)
                print('[SETUP] (' + ctx.author.guild.name + ") Category's name: " + category.content)
                await ctx.channel.send('Enter the __name of the voice channel hub__: (e.g `Join To Create`)')
                try:
                    channel = await self.bot.wait_for('message', check=check, timeout = 60.0)
                except asyncio.TimeoutError:
                    await ctx.channel.send('Took too long to answer!')
                    print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") took too long to answer (setup failed).")
                else:
                    print('[SETUP] (' + ctx.author.guild.name + ") voice channel hub's name: " + channel.content)
                    await ctx.channel.send('Max channels __number__:')
                    try:
                        maxChannels = await self.bot.wait_for('message', check=check, timeout = 60.0)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('Took too long to answer!')
                        print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") took too long to answer (setup failed).")
                    else:
                        print('[SETUP] (' + ctx.author.guild.name + ") Max channels: " + maxChannels.content)
                        try:
                            c.execute("SELECT * FROM serverSettings WHERE serverID = ?", (guildID,))
                            voice=c.fetchone()
                            if voice is None:
                                c.execute ("INSERT INTO serverSettings VALUES (?, ?, ?)",(guildID,maxChannels.content,'0'))
                                print('[SETUP] (' + ctx.author.guild.name + ") Created server settings!")
                            else:
                                c.execute ("UPDATE serverSettings SET serverID = ?, maxChannels = ?, roleID = ?",(guildID,maxChannels.content,'0'))
                                print('[SETUP] (' + ctx.author.guild.name + ") Updated server settings!")
                            
                        except asyncio.TimeoutError:
                            await ctx.channel.send('Took too long to answer!')
                            print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") took too long to answer (setup failed).")
                        else:
                            try:
                                channel = await ctx.guild.create_voice_channel(channel.content, category=new_cat)
                                c.execute("SELECT * FROM guild WHERE guildID = ? AND ownerID=?", (guildID, id))
                                voice=c.fetchone()
                                if voice is None:
                                    c.execute ("INSERT INTO guild VALUES (?, ?, ?, ?)",(guildID,id,channel.id,new_cat.id))
                                else:
                                    c.execute ("UPDATE guild SET guildID = ?, ownerID = ?, voiceChannelID = ?, voiceCategoryID = ? WHERE guildID = ?",(guildID,id,channel.id,new_cat.id, guildID))
                                await ctx.channel.send("**You are all setup and ready to go!**")
                                print('\n[SETUP] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has completed the setup!\n")
                            except:
                                await ctx.channel.send("You didn't enter the information properly. Use `.voice setup` again!")
                                print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") didn't enter the information properly (setup failed).")
        else:
            await ctx.channel.send(f"{ctx.author.mention} only the owner of the server can setup the bot!")
            print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") is not the owner of the server (setup failed).")
        conn.commit()
        conn.close()

    @commands.command()
    async def setlimit(self, ctx, num):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == OWNER_ID:
            c.execute("SELECT * FROM guildSettings WHERE guildID = ?", (ctx.guild.id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO guildSettings VALUES (?, ?, ?)", (ctx.guild.id,f"{ctx.author.name}'s channel",num))
            else:
                c.execute("UPDATE guildSettings SET channelLimit = ? WHERE guildID = ?", (num, ctx.guild.id))
            await ctx.send("You have changed the default channel limit for your server!")
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has changed the server's limit.")
        else:
            await ctx.channel.send(f"{ctx.author.mention} only the owner of the server can setup the bot!")
            print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") is not the owner of the server (change default limit failed).")
        conn.commit()
        conn.close()

    @setup.error
    async def info_error(self, ctx, error):
        print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') has generated an error:\n' + error + '\n------\n')

    @voice.command()
    async def reset(self, ctx):
        id = ctx.author.id
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == OWNER_ID:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM roomCreated")
            print('\n[RESET] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') has started the reset:')
            channel_to_delete = c.fetchall()
            for channel in channel_to_delete:
                for id in channel:
                    if id != 0:
                        try:
                            channel = self.bot.get_channel(id)
                            print('[RESET] (' + ctx.author.guild.name + ') ' + 'Deleting channel: ' + channel.name)
                            await channel.delete()
                        except Exception as error:
                            print(error)

            c.execute("DELETE FROM roomCreated")
            c.execute("INSERT INTO roomCreated VALUES (0)")
            
            print('[RESET] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') has completed the reset.\n')
            await ctx.send("Reset completato!")
            
            conn.commit()
            conn.close()
        else:
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") is not the server owner (reset configs failed).")
            await ctx.channel.send(f"{ctx.author.mention} only the owner of the server can reset the bot!")

    @voice.command()
    async def lock(self, ctx):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (lock channel failed).")
        else:
            channelID = voice[0]
            #role = discord.utils.get(ctx.guild.roles, id=USER_ROLE_ID)
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=False,read_messages=True)
            await ctx.channel.send(f'🔒 {ctx.author.mention} voice chat locked!')
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has locked his channel.")
        conn.commit()
        conn.close()

    @voice.command()
    async def unlock(self, ctx):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (unlock channel failed).")
        else:
            channelID = voice[0]
            #role = discord.utils.get(ctx.guild.roles, id=USER_ROLE_ID)
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=True,read_messages=True)
            await ctx.channel.send(f'🔓 {ctx.author.mention} voice chat unlocked!')
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has unlocked his channel.")
        conn.commit()
        conn.close()

    @voice.command(aliases=["allow"])
    async def permit(self, ctx, member : discord.Member):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (permited user failed).")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(member, connect=True,read_messages=True)
            await ctx.channel.send(f'✅ {ctx.author.mention} you have permited {member.name} to have access to the channel.')
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') permited ' + member.name + '(id: ' + str(member.id) + ') to have access to the channel.')
        conn.commit()
        conn.close()

    @voice.command(aliases=["deny"])
    async def reject(self, ctx, member : discord.Member):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        guildID = ctx.guild.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (reject user failed).")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            for members in channel.members:
                if members.id == member.id:
                    c.execute("SELECT voiceChannelID FROM guild WHERE guildID = ?", (guildID,))
                    voice=c.fetchone()
                    channel2 = self.bot.get_channel(voice[0])
                    await member.move_to(channel2)
            await channel.set_permissions(member, connect=False,read_messages=False)
            await ctx.channel.send(f':no_entry_sign: {ctx.author.mention} you have rejected {member.name} from accessing the channel.')
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') reject ' + member.name + '(id: ' + str(member.id) + ') to have access to the channel.')
        conn.commit()
        conn.close()

    @voice.command()
    async def limit(self, ctx, limit):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (channel limit failed).")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(user_limit = limit)
            await ctx.channel.send(f'{ctx.author.mention} You have set the channel limit to be '+ '{}!'.format(limit))
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has changed the limit of his channel.")
            c.execute("SELECT channelName FROM userSettings WHERE userID = ?", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO userSettings VALUES (?, ?, ?)", (id,f'{ctx.author.name}',limit))
            else:
                c.execute("UPDATE userSettings SET channelLimit = ? WHERE userID = ?", (limit, id))
        conn.commit()
        conn.close()

    @voice.command(aliases=["rename"])
    async def name(self, ctx,*, name):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (rename channel failed).")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(name = name)
            await ctx.channel.send(f'{ctx.author.mention} you have changed the channel name to '+ '{}!'.format(name))
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has changed the name of his channel.")
            c.execute("SELECT channelName FROM userSettings WHERE userID = ?", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO userSettings VALUES (?, ?, ?)", (id,name,3))
            else:
                c.execute("UPDATE userSettings SET channelName = ? WHERE userID = ?", (name, id))
        conn.commit()

    @voice.command()
    async def claim(self, ctx):
        x = False
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        channel = ctx.author.voice.channel
        if channel == None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you're not in a voice channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") was not in a voice channel (claim channel failed).")
        else:
            id = ctx.author.id
            c.execute("SELECT userID FROM voiceChannel WHERE voiceID = ?", (channel.id,))
            voice=c.fetchone()
            if voice is None:
                await ctx.channel.send(f"❌ {ctx.author.mention} you can't own that channel!")
                print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") can not claim this channel (claim channel failed).")
            else:
                for data in channel.members:
                    if data.id == voice[0]:
                        owner = ctx.guild.get_member(voice [0])
                        await ctx.channel.send(f"{ctx.author.mention} this channel is already owned by {owner.mention}!")
                        print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") was already the owner of the channel (claim channel failed).")
                        x = True
                if x == False:
                    await ctx.channel.send(f"{ctx.author.mention} you are now the owner of the channel!")
                    print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") claims a channel.")
                    c.execute("UPDATE voiceChannel SET userID = ? WHERE voiceID = ?", (id, channel.id))
            conn.commit()
            conn.close()

def setup(bot):
    bot.add_cog(voice(bot))