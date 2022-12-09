# Imports
import discord, os, time, requests, json, dotenv, logging, paypalrestsdk, asyncio, httpx, pymysql
from discord.ext.commands import CommandNotFound
from discord.ext import commands, tasks
from discord.ui import Select, View, Button
from discord import app_commands, SelectOption
from itertools import cycle
from colorama import Fore, init, Style
from dotenv import load_dotenv
from threading import Timer
from datetime import datetime
from paypalrestsdk import Invoice
from math import log10 , floor

# Clear function
clear = lambda: os.system("cls" if os.name in ("nt", "dos") else "clear") # Don't touch this.
clear()

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

# Logo
logo = """

░█████╗░███╗░░██╗░██████╗░███████╗██████╗░
██╔══██╗████╗░██║██╔════╝░██╔════╝██╔══██╗
███████║██╔██╗██║██║░░██╗░█████╗░░██████╔╝
██╔══██║██║╚████║██║░░╚██╗██╔══╝░░██╔══██╗
██║░░██║██║░╚███║╚██████╔╝███████╗██║░░██║
╚═╝░░╚═╝╚═╝░░╚══╝░╚═════╝░╚══════╝╚═╝░░╚═╝"""
def printLogo():
    print(Fore.WHITE + logo + Style.RESET_ALL)
    print("✯ Payments bot 1.0 ✯\n♥ Made by kWAY#1701♥\n------------------------\n\n")

# Load .env file
load_dotenv()
bot_prefix = os.getenv("PREFIX")
currency = os.getenv("CURRENCY")
PAYPAL_MODE  = os.getenv("PAYPAL_MODE")
CHECK_DELAY = os.getenv("CHECK_DELAY")
BTC_ADDRESS = os.getenv("BTC_ADDRESS")
ETH_ADDRESS = os.getenv("ETH_ADDRESS")
LTC_ADDRESS = os.getenv("LTC_ADDRESS")
if PAYPAL_MODE == "sandbox":
    PAYPAL_ENDPOINT = "https://api-m.sandbox.paypal.com"
    PAYPAL_EMAIL = os.getenv("PAYPAL_SANDBOX_MAIL")
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID_SANDBOX")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET_SANDBOX")
    PAYPAL_PAY = f"https://www.sandbox.paypal.com/invoice/payerView/details/"
else:
    PAYPAL_ENDPOINT = "https://api-m.paypal.com"
    PAYPAL_EMAIL = os.getenv("PAYPAL_LIVE_MAIL")
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID_LIVE")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET_LIVE")
    PAYPAL_PAY = f"https://www.paypal.com/invoice/payerView/details/"
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_name = os.getenv("DB_NAME")

# Set up rest sdk
paypalrestsdk.configure({
  "mode": PAYPAL_MODE, # sandbox or live
  "client_id": PAYPAL_CLIENT_ID,
  "client_secret": PAYPAL_CLIENT_SECRET })

# Define the bot client
bot = commands.Bot(command_prefix=bot_prefix, help_command=None, case_insensitive=True, intents=discord.Intents.all())
connection = pymysql.connect(host=db_host, user=db_user, password=db_pass, db=db_name)

# Function to create table if it doesn't exist
async def create_table():
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    try:
        # Create cursor
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, price DECIMAL(10,2) NOT NULL, description VARCHAR(255), server_id BIGINT NOT NULL)")

        # Save changes
        connection.commit()

    except pymysql.err.ProgrammingError:
        # If table already exists, print it
        print(f"{Fore.RED}>{Fore.WHITE} Database already exists")

    except Exception as e:
        # If something goes wrong, print error message
        print(f"{Fore.RED}>{Fore.WHITE} Error creating database: {e}")
        connection.rollback()

    else:
        # If nothing goes wrong, print success message
        print(f"{Fore.GREEN}>{Fore.WHITE} Table created successfully")

# Function to add a product to the database
async def add_product(name, price, description, server_id):
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    print(f"{Fore.YELLOW}>{Fore.WHITE} Trying to add product {name} with price {price} and description {description}")
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO products (name, price, description, server_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, price, description, server_id))
            connection.commit()
            print(f"{Fore.GREEN}>{Fore.WHITE} Product {name} added successfully")

    except Exception as e:
        # If any error occurs, rollback the changes
        print(f"{Fore.RED}>{Fore.WHITE} Error adding product: {e}")
        connection.rollback()

# Function to delete a product from the database
async def delete_product(name):
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    print(f"{Fore.YELLOW}>{Fore.WHITE} Trying to delete product {name}")
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM products WHERE name = %s"
            cursor.execute(sql, (name))
            connection.commit()
            print(f"{Fore.GREEN}>{Fore.WHITE} Product {name} deleted successfully")

    except Exception as e:
        # If any error occurs, rollback the changes
        print(f"{Fore.RED}>{Fore.WHITE} Error deleting product: {e}")
        connection.rollback()

# Function to change product price
async def change_price(name, price):
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    print(f"{Fore.YELLOW}>{Fore.WHITE} Trying to edit product {name}")

    try:
        with connection.cursor() as cursor:
            sql = "UPDATE products SET price = %s WHERE name = %s"
            cursor.execute(sql, (price, name))
            connection.commit()
            print(f"{Fore.GREEN}>{Fore.WHITE} Product {name} price edited successfully")

    except Exception as e:
        # If any error occurs, rollback the changes
        print(f"{Fore.RED}>{Fore.WHITE} Error editing product: {e}")
        connection.rollback()

# Function to change product name
async def change_name(name, new_name):
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    print(f"{Fore.YELLOW}>{Fore.WHITE} Trying to edit product {name}")

    try:
        with connection.cursor() as cursor:
            sql = "UPDATE products SET name = %s WHERE name = %s"
            cursor.execute(sql, (new_name, name))
            connection.commit()
            print(f"{Fore.GREEN}>{Fore.WHITE} Product {name} name edited successfully")


    except Exception as e:
        # If any error occurs, rollback the changes
        print(f"{Fore.RED}>{Fore.WHITE} Error editing product: {e}")
        connection.rollback()

# Function to change product description
async def change_description(name, description):
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    print(f"{Fore.YELLOW}>{Fore.WHITE} Trying to edit product {name}")

    try:
        with connection.cursor() as cursor:
            sql = "UPDATE products SET description = %s WHERE name = %s"
            cursor.execute(sql, (description, name))
            connection.commit()
            print(f"{Fore.GREEN}>{Fore.WHITE} Product {name} description edited successfully")

    except Exception as e:
        # If any error occurs, rollback the changes
        print(f"{Fore.RED}>{Fore.WHITE} Error editing product: {e}")
        connection.rollback()

# Function to change product server_id
async def change_server_id(name, server_id):
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    print(f"{Fore.YELLOW}>{Fore.WHITE} Trying to edit product {name}")

    try:
        with connection.cursor() as cursor:
            sql = "UPDATE products SET server_id = %s WHERE name = %s"
            cursor.execute(sql, (server_id, name))
            connection.commit()
            print(f"{Fore.GREEN}>{Fore.WHITE} Product {name} server_id edited successfully")

    except Exception as e:
        # If any error occurs, rollback the changes
        print(f"{Fore.RED}>{Fore.WHITE} Error editing product: {e}")
        connection.rollback()

# Function to get all products from the database
async def get_all_products():
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM products"
            cursor.execute(sql)
            result = cursor.fetchall()
            print(f"{Fore.GREEN}>{Fore.WHITE} Products fetched successfully")
            return result
    
    except pymysql.err.ProgrammingError:
        print(f"{Fore.RED}>{Fore.WHITE} No products in the database")
        return f"No products in the database"

    except Exception as e:
        # If any error occurs, rollback the changes
        print(f"{Fore.RED}>{Fore.WHITE} Error fetching products: {e}")
        connection.rollback()

# Function to get a product from the database
async def get_product(name):
    print(f"{Fore.GREEN}>{Fore.WHITE} Database connected")
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM products WHERE name = %s"
            cursor.execute(sql, (name))
            result = cursor.fetchone()
            print(f"{Fore.GREEN}>{Fore.WHITE} Product {name} fetched successfully")
            return result

    except pymysql.err.ProgrammingError:
        print(f"{Fore.RED}>{Fore.WHITE} Product {name} not found")
        return f"Product {name} not found"

    except Exception as e:
        # If any error occurs, rollback the changes
        print(f"{Fore.RED}>{Fore.WHITE} Error fetching product: {e}")
        connection.rollback()

# Dynamic activity
status = cycle(["payments", "discord.gg/kws", "your wallet", "kwayservices.top", "paypal",  "crypto"])
@tasks.loop(seconds=30)
async def changeStatus():
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name=next(status)))

# Format a date for PayPal API
async def format_date(date):
    d = date.strftime('%Y-%m-%dT%H:%M:%SZ')
    return d

# Get OAuth Token from PayPal
async def get_token():
    url = PAYPAL_ENDPOINT + '/v1/oauth2/token'
    
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
        
    payload = {
        "grant_type": "client_credentials"
    }

    response = requests.post(url, auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET), data=payload)
    data = response.json()

    # keep the token alive
    token_expire = int(data['expires_in']) - 100
    t = Timer(token_expire, get_token)
    t.daemon = True
    t.start()

    logging.info(f"Got new access token.")
    return data['access_token']

# Create invoice function
async def create_invoice(price: int, service: str, quantity: int):
    invoice = Invoice({
    'merchant_info': {
        "email": PAYPAL_EMAIL,
    },
    "items": [{
        "name": service,
        "quantity": quantity,
        "unit_price": {
            "currency": currency,
            "value": price
        }
        }],
    })
    response = invoice.create()
    if response:
        print(f"{Fore.GREEN}[{Fore.RESET}OK{Fore.GREEN}] {Fore.RESET}Invoice with ID %s created successfully" % (invoice.id))
        return invoice.id
    else:
        print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}] {Fore.RESET}Error while creating invoice: ", response.error)
        return response.error

# Send invoice function
async def send_invoice(invoice_id: str):
    try:
        invoice = Invoice.find(invoice_id)
        invoice.send()
        print(f"{Fore.GREEN}[{Fore.RESET}OK{Fore.GREEN}] {Fore.RESET}Invoice with ID %s sent successfully" % (invoice.id))
        return True
    except:
        print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}] {Fore.RESET}Error sending invoice: ", response.error)
        return False

# Check invoice status function
async def check_invoice_status(invoice_id: str):
    try:
        invoice = Invoice.find(invoice_id)
        status = invoice.to_dict()['status']
        return status

    except ResourceNotFound as error:
        print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}] {Fore.RESET}Error while checking invoice status: ", error.message)

# Check crypto status function
async def check_crypto_status(txid: str, crypto: str):
    if crypto == "btc":
        url = "https://api.blockcypher.com/v1/btc/main/txs/" + txid
    elif crypto == "eth":
        url = "https://api.blockcypher.com/v1/eth/main/txs/" + txid
    elif crypto == "ltc":
        url = "https://api.blockcypher.com/v1/ltc/main/txs/" + txid

    response = requests.get(url)
    data = response.json()
    confirmations = data['confirmations']
    return confirmations

# On Ready Event
@bot.event
async def on_ready():
    clear()
    printLogo()
    print(f"{Fore.MAGENTA}[{Fore.RESET}!{Fore.MAGENTA}] {Fore.RESET}Logged in as {bot.user.name}#{bot.user.discriminator}.")
    await create_table()
    logging.basicConfig(handlers=[logging.FileHandler('anger.log', 'a+', 'utf-8')], level=logging.INFO, format='%(asctime)s: %(message)s')

    global PAYPAL_TOKEN
    PAYPAL_TOKEN = await get_token()
    try:
        print(f"{Fore.GREEN}[{Fore.RESET}OK{Fore.GREEN}] {Fore.RESET}Got new {Fore.MAGENTA}PayPal{Fore.RESET} token")
    except Exception as e:
        print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}] {Fore.RESET}Failed to get {Fore.CYAN}PayPal{Fore.RESET} token, error: {str(e)}")

    changeStatus.start()
    bot.add_view(SelectView())

# Log function
async def log(title: str, description: str, color: str):
    channel = bot.get_channel(int(os.getenv("LOGS_CHANNEL")))
    if color == "red":
        color = 0xFF0000
    elif color == "green":
        color = 0x00FF00
    elif color == "blue":
        color = 0x0000FF
    elif color == "yellow":
        color = 0xFFFF00
    elif color == "purple":
        color = 0x800080
    elif color == "orange":
        color = 0xFFA500
    elif color == "cyan":
        color = 0x00FFFF
    elif color == "pink":
        color = 0xFFC0CB
    elif color == "white":
        color = 0xFFFFFF
    elif color == "black":
        color = 0x000000
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Anger Payment Bot")
    embed.timestamp = datetime.utcnow()
    await channel.send(embed=embed)

# Sync slash commands
@bot.command()
async def sync(ctx):
    try:
        await ctx.message.delete()
        await bot.tree.sync()
        msg = await ctx.send("Done!")
        time.sleep(2)
        await msg.delete()
        await log("Sync Slash Commands", "Synced `slash` commands!", "green")
        print(f"{Fore.GREEN}[{Fore.RESET}+{Fore.GREEN}] {Fore.RESET}Synced slash commands!")
    except Exception as e:
        await log("Sync Slash Commands", f"Error: {str(e)}", "red")

# Ping Command
@bot.tree.command(name="ping", description="Test if the bot is working")
async def ping(interaction: discord.Interaction, member: discord.Member):
    latency = round(bot.latency *  1000)
    await log("Ping", f"{member.mention} pinged the bot.", "cyan")
    await interaction.response.send_message(f"Hey! {member.mention}! My latency is `{latency}` ms!")

class SelectView(View):
    def __init__(self):
        super().__init__(timeout=None)

# Panel Command
@bot.tree.command(name="panel", description="Send the panel")
async def panel(interaction: discord.Interaction):

    products = await get_all_products()
    print(interaction.guild.id)
    filtered_products = [product for product in products if product[4] == interaction.guild.id]

    select = Select(
        placeholder="Select a product", 
        custom_id="panel-select", 
        options= [
            SelectOption(label=product[1], value=product[1]) for product in filtered_products
            ] + [
                SelectOption(label="Cancel", value="cancel", emoji="❌")
                ])
    
    async def callback(interaction):
        select.disabled = True
        if select.values[0] == "cancel":
            await interaction.response.send_message("Cancelled!", ephemeral=True)
            return
        else:
            for product in products:
                if select.values[0] == product[1]:
                    result = await get_product(product[1])
                    iId = result[0]
                    iName = result[1]
                    iPrice = result[2]
                    iDesc = result[3]
                    iSv = result[4]
                    await interaction.response.send_message(f"✨ID: `{iId}`\n📇Name: `{iName}`\n💸Price: `{iPrice}`\n💬Description: `{iDesc}`\n🌐Server ID: `{iSv}`", ephemeral=True)

    select.callback = callback
    view = SelectView()
    view.add_item(select)
    await interaction.response.send_message(view=view)

# Create PayPal invoice command
@bot.tree.command(name="paypal", description="Create a PayPal invoice")
@app_commands.checks.has_permissions(administrator=True)
async def paypal(interaction: discord.Interaction, member: discord.Member, price: float, quantity: int, service: str):
    delay = int(CHECK_DELAY)
    await interaction.response.defer()
    try:
        invoice_id = await create_invoice(price, service, quantity)
        await log("PayPal - Invoice Created", f"{member.mention} created a PayPal invoice.", "green")
    except Exception as e:
        await log("PayPal - Create Invoice", f"Error: {str(e)}", "red")
        logging.error(f"Error creating Paypal invoice: {str(e)}")
        print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}] {Fore.RESET}Failed to create PayPal invoice, error: {str(e)}")
        await interaction.followup.send(f"Hey! {member.mention}! There was an error creating your invoice. Check the logs for more info.")
        return
    try:
        sent = await send_invoice(invoice_id)
        if sent:
            await log("PayPal - Invoice Sent", f"{member.mention} sent a PayPal invoice.", "green")
    except Exception as e:
        await log("PayPal - Send Invoice", f"Error: {str(e)}", "red")
        logging.error(f"Failed to send PayPal invoice, error: {str(e)}")
        print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}] {Fore.RESET}Failed to send PayPal invoice, error: {str(e)}")
        await interaction.followup.send(f"Hey! {member.mention}! There was an error sending your invoice. Check the logs for more info.")
        return
    view=Buttons()
    URL = f"{PAYPAL_PAY}{invoice_id}"
    view.add_item(discord.ui.Button(label="Pay here",style=discord.ButtonStyle.link,url=URL,emoji="💸"))
    embed = discord.Embed(title="PayPal Invoice", description=f"Hey! {member.mention}! \nInvoice ID: *{invoice_id}*", color=0xFFDBE9)
    embed.add_field(name="Customer", value=f"{member.mention}")
    embed.add_field(name="Price/Unit", value=f"`{price}`")
    embed.add_field(name="Quantity", value=f"`{quantity}`")
    embed.add_field(name="Total Price", value=f"`{price * quantity}`")
    embed.add_field(name="Service", value=f"`{service}`")
    embed.add_field(name="Paypal Email", value=f"`{PAYPAL_EMAIL}`")
    embed.add_field(name="Paypal Link", value=f"Click [here]({URL})")
    embed.add_field(name="Status", value="`UNPAID`")
    embed.set_thumbnail(url="https://i.imgur.com/RhvKGZx.png")
    embed.set_footer(text="Anger Payment Bot")
    embed.timestamp = datetime.utcnow()
    msg = await interaction.followup.send(embed=embed, view=view)
    @tasks.loop(seconds=delay)
    async def checkStatus():
        try:
            invoice = await check_invoice_status(invoice_id)
            while not invoice == "PAID":
                if invoice == "CANCELLED":
                    break
                    embed = discord.Embed(title="PayPal Invoice", description=f"Hey! {member.mention}! \nInvoice ID: *{invoice_id}*", color=0xFF2800)
                    embed.add_field(name="Customer", value=f"{member.mention}")
                    embed.add_field(name="Price/Unit", value=f"`{price}`")
                    embed.add_field(name="Quantity", value=f"`{quantity}`")
                    embed.add_field(name="Total Price", value=f"`{price * quantity}`")
                    embed.add_field(name="Service", value=f"`{service}`")
                    embed.add_field(name="Paypal Email", value=f"`{PAYPAL_EMAIL}`")
                    embed.add_field(name="Paypal Link", value=f"Click [here]({URL})")
                    embed.add_field(name="Status", value="`CANCELLED`")
                    embed.set_thumbnail(url="https://i.imgur.com/RhvKGZx.png")
                    embed.set_footer(text="Anger Payment Bot")
                    embed.timestamp = datetime.utcnow()
                    await msg.edit(embed=embed)
                invoice = await check_invoice_status(invoice_id)
                await asyncio.sleep(delay)
                embed = discord.Embed(title="PayPal Invoice", description=f"Hey! {member.mention}! \nInvoice ID: *{invoice_id}*", color=0xFFDBE9)
                embed.add_field(name="Customer", value=f"{member.mention}")
                embed.add_field(name="Price/Unit", value=f"`{price}`")
                embed.add_field(name="Quantity", value=f"`{quantity}`")
                embed.add_field(name="Total Price", value=f"`{price * quantity}`")
                embed.add_field(name="Service", value=f"`{service}`")
                embed.add_field(name="Paypal Email", value=f"`{PAYPAL_EMAIL}`")
                embed.add_field(name="Paypal Link", value=f"Click [here]({URL})")
                embed.add_field(name="Status", value=f"`{invoice}`")
                embed.set_thumbnail(url="https://i.imgur.com/RhvKGZx.png")
                embed.set_footer(text="Anger Payment Bot")
                embed.timestamp = datetime.utcnow()
                await msg.edit(embed=embed)
            await log("PayPal - Invoice Paid", f"{member.mention} paid the invoice.", "green")
            embed = discord.Embed(title="PayPal Invoice", description=f"Hey! {member.mention}! \nInvoice ID: *{invoice_id}*", color=0x00FF00)
            embed.add_field(name="Customer", value=f"{member.mention}")
            embed.add_field(name="Price/Unit", value=f"`{price}`")
            embed.add_field(name="Quantity", value=f"`{quantity}`")
            embed.add_field(name="Total Price", value=f"`{price * quantity}`")
            embed.add_field(name="Service", value=f"`{service}`")
            embed.add_field(name="Paypal Email", value=f"`{PAYPAL_EMAIL}`")
            embed.add_field(name="Paypal Link", value=f"Click [here]({URL})")
            embed.add_field(name="Status", value="`PAID`")
            embed.set_thumbnail(url="https://i.imgur.com/RhvKGZx.png")
            embed.set_footer(text="Anger Payment Bot")
            embed.timestamp = datetime.utcnow()
            checkStatus.stop()
            await msg.edit(embed=embed)
        except Exception as e:   
            await log("PayPal - Invoice Paid", f"Error: {str(e)}", "red")
            logging.error(f"Error checking invoice status: {str(e)}")
            print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}] {Fore.RESET}Failed to check invoice status, error: {str(e)}")
            await interaction.followup.send(f"Hey! {member.mention}! There was an error checking the invoice status. Check the logs for more info.")
            return
    checkStatus.start()

# Check PayPal invoice command 
@bot.tree.command(name="check", description="Check invoice status")
@app_commands.checks.has_permissions(administrator=True)
async def check(interaction: discord.Interaction, invoice_id: str):
    await interaction.response.defer()
    try:
        status = await check_invoice_status(invoice_id)
        await log("PayPal - Check Invoice", f"Checked invoice status: {status}", "cyan")
        await interaction.followup.send(f"Hey! {interaction.user.mention}! The status of your invoice is: {status}")
    except Exception as e:
        await log("PayPal - Check Invoice", f"Error: {str(e)}", "red")
        logging.error(f"Error checking invoice status: {str(e)}")
        print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}] {Fore.RESET}Failed to check invoice status, error: {str(e)}")
        await interaction.followup.send(f"Hey! {interaction.user.mention}! There was an error checking your invoice status. Check the logs for more info.")


# Crypto payment command    
@bot.tree.command(name="crypto", description="Create a crypto invoice")
@app_commands.checks.has_permissions(administrator=True)
async def crypto(interaction: discord.Interaction, service: str, price: float, quantity: int, crypto: str):

    def checkMsg(m):
        return m.author == interaction.user and m.channel == interaction.channel

    def round_it(x, sig):
        return round(x, sig-int(floor(log10(abs(x))))-1)

    await interaction.response.defer()
    totalPrice = price * quantity
    if crypto  == "ltc":
        sym = "LTC"
        chain = "litecoin"
        addy = LTC_ADDRESS
    elif crypto  == "btc":
        sym = "BTC"
        chain = "bitcoin"
        addy = BTC_ADDRESS
    elif crypto  == "eth":
        sym = "ETH"
        chain = "ethereum"
        addy = ETH_ADDRESS

    usd_price = httpx.get(f"https://min-api.cryptocompare.com/data/price?fsym={sym}&tsyms=EUR").json()["EUR"]
    global crypto_price
    crypto_price = totalPrice/usd_price
    crypto_price = round_it(crypto_price, 4)

    # send the invoice
    embed = discord.Embed(title="Crypto Invoice", description=f"Hey! {interaction.user.mention}!", color=0xFFDBE9)
    embed.add_field(name="Customer", value=f"{interaction.user.mention}")
    embed.add_field(name="Price/Unit", value=f"`{price}`")
    embed.add_field(name="Quantity", value=f"`{quantity}`")
    embed.add_field(name="Total Price", value=f"`{price * quantity}`")
    embed.add_field(name="Service", value=f"`{service}`")
    embed.add_field(name="Address", value=f"`{addy}`")
    embed.add_field(name="Crypto", value=f"`{sym}`")
    embed.add_field(name="Crypto Price", value=f"`{crypto_price}`")
    embed.add_field(name="Status", value="`UNPAID`")
    embed.set_thumbnail(url="https://i.imgur.com/8zcUqJB.png")
    embed.set_footer(text="Anger Payment Bot")
    embed.timestamp = datetime.utcnow()
    cryptomsg = await interaction.followup.send(embed=embed)

    # ask the user for the transaction id
    await interaction.followup.send(f"Hey! {interaction.user.mention}! Send the transaction ID of your payment to the bot and no other message until you sent the transaction ID. You have 60 seconds to send the transaction ID.")
    try:
        msg = await bot.wait_for("message", check=checkMsg, timeout=60)
        txid = msg.content
    except asyncio.TimeoutError:
        await interaction.followup.send(f"Hey! {interaction.user.mention}! You took too long to send the transaction ID.")
        return
    
    @tasks.loop(seconds=60)
    async def checkCrypto():
        try:
            status = await check_crypto_status(txid, crypto)
            url = f"https://api.blockcypher.com/v1/{crypto}/main/txs/{txid}"
            view=Buttons()
            view.add_item(discord.ui.Button(label="Check progress",style=discord.ButtonStyle.link,url=url,emoji="🕒"))
            if status < 3:
                embed = discord.Embed(title="Crypto Invoice", description=f"Hey! {interaction.user.mention}!", color=0xFFDBE9)
                embed.add_field(name="Customer", value=f"{interaction.user.mention}")
                embed.add_field(name="Price/Unit", value=f"`{price}`")
                embed.add_field(name="Quantity", value=f"`{quantity}`")
                embed.add_field(name="Total Price", value=f"`{price * quantity}`")
                embed.add_field(name="Service", value=f"`{service}`")
                embed.add_field(name="Address", value=f"`{addy}`")
                embed.add_field(name="Crypto", value=f"`{sym}`")
                embed.add_field(name="Crypto Price", value=f"`{crypto_price}`")
                embed.add_field(name="Status", value="`UNPAID`")
                embed.add_field(name="Confirmations", value=f"`{status}/3`")
                embed.set_thumbnail(url="https://i.imgur.com/8zcUqJB.png")
                embed.set_footer(text="Anger Payment Bot")
                embed.timestamp = datetime.utcnow()
                await cryptomsg.edit(embed=embed, view=view)
            elif status >= 3:
                embed = discord.Embed(title="Crypto Invoice", description=f"Hey! {interaction.user.mention}!", color=0x00FF00)
                embed.add_field(name="Customer", value=f"{interaction.user.mention}")
                embed.add_field(name="Price/Unit", value=f"`{price}`")
                embed.add_field(name="Quantity", value=f"`{quantity}`")
                embed.add_field(name="Total Price", value=f"`{price * quantity}`")
                embed.add_field(name="Service", value=f"`{service}`")
                embed.add_field(name="Address", value=f"`{addy}`")
                embed.add_field(name="Crypto", value=f"`{sym}`")
                embed.add_field(name="Crypto Price", value=f"`{crypto_price}`")
                embed.add_field(name="Status", value="`PAID`")
                embed.add_field(name="Confirmations", value=f"`{status}/3`")
                embed.set_thumbnail(url="https://i.imgur.com/8zcUqJB.png")
                embed.set_footer(text="Anger Payment Bot")
                embed.timestamp = datetime.utcnow()
                checkCrypto.stop()
                await cryptomsg.edit(embed=embed, view=view)
        except Exception as e:   
            await log("Crypto - Invoice Paid", f"Error: {str(e)}", "red")
            logging.error(f"Error checking invoice status: {str(e)}")
            print(f"{Fore.RED}[{Fore.RESET}ERROR{Fore.RED}]{Fore.RESET} Error checking invoice status: {str(e)}")
            checkCrypto.stop()
            return
        
    checkCrypto.start()

# Add shop product command 
@bot.tree.command(name="add_product", description="Add a product to the shop database")
@app_commands.checks.has_permissions(administrator=True)
async def add_product_command(interaction: discord.Interaction, name: str, price: float, description: str, server_id: str):
    await interaction.response.defer()
    server_id = int(server_id)
    await add_product(name, price, description, server_id)
    await interaction.followup.send(f"Added product `{name}` to the database with a price of `{price}` and description `{description}`")

# Remove shop product command
@bot.tree.command(name="delete_product", description="Delete a product from the shop database")
@app_commands.checks.has_permissions(administrator=True)
async def remove_product_command(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    await delete_product(name)
    await interaction.followup.send(f"Deleted product `{name}` from the database")

# Change product price command
@bot.tree.command(name="change_price", description="Change the price of a product in the shop database")
@app_commands.checks.has_permissions(administrator=True)
async def change_price_command(interaction: discord.Interaction, name: str, price: float):
    await interaction.response.defer()
    await change_price(name, price)
    await interaction.followup.send(f"Changed the price of product `{name}` to `{price}`")

# Change product description command
@bot.tree.command(name="change_description", description="Change the description of a product in the shop database")
@app_commands.checks.has_permissions(administrator=True)
async def change_description_command(interaction: discord.Interaction, name: str, description: str):
    await interaction.response.defer()
    await change_description(name, description)
    await interaction.followup.send(f"Changed the description of product `{name}` to `{description}`")

# Change product name command
@bot.tree.command(name="change_name", description="Change the name of a product in the shop database")
@app_commands.checks.has_permissions(administrator=True)
async def change_name_command(interaction: discord.Interaction, name: str, new_name: str):
    await interaction.response.defer()
    await change_name(name, new_name)
    await interaction.followup.send(f"Changed the name of product `{name}` to `{new_name}`")

# Change product server id command  
@bot.tree.command(name="change_server_id", description="Change the server id of a product in the shop database")
@app_commands.checks.has_permissions(administrator=True)
async def change_server_id_command(interaction: discord.Interaction, name: str, server_id: int):
    await interaction.response.defer()
    await change_server_id(name, server_id)
    await interaction.followup.send(f"Changed the server id of product `{name}` to `{server_id}`")

# Show all products command
@bot.tree.command(name="shop", description="Show all products in the shop database")
@app_commands.checks.has_permissions(administrator=True)
async def show_products_command(interaction: discord.Interaction):
    await interaction.response.defer()
    result = await get_all_products()
    if result == f"No products in the database":
        await interaction.followup.send(result)
        return
    embed = discord.Embed(title="Products", description=f"🌐 All products in the database", color=0x000000)
    for product in result:
        embed.add_field(name=f"✨ID: `{product[0]}`", value=f"📇Name: `{product[1]}`\n💸Price: `{product[2]}`\n💬Description: `{product[3]}`\n🌐Server ID: `{product[4]}`", inline=True)
    await interaction.followup.send(embed=embed)

# Get info about a product command
@bot.tree.command(name="info", description="Get info about a product in the shop database")
@app_commands.checks.has_permissions(administrator=True)
async def info_command(interaction: discord.Interaction, product: str):
    await interaction.response.defer()
    result = await get_product(product)
    if result == f"Product {product} not found":
        await interaction.followup.send(result)
        return
    embed = discord.Embed(title="Product Info", description=f"Info about product `{product}`", color=0x000000)
    embed.add_field(name="Name", value=f"`{result[1]}`")
    embed.add_field(name="Price", value=f"`{result[2]}`")
    embed.add_field(name="Description", value=f"`{result[3]}`")
    embed.add_field(name="Server ID", value=f"`{result[4]}`")
    await interaction.followup.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
    # Close the database connection
    connection.close()
    print(f"{Fore.MAGENTA}>{Fore.WHITE} Closed connection.")