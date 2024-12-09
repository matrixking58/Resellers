import telebot
import os
import random
import string
from datetime import datetime, timedelta
import pytz
import psycopg2
import logging
import time

from psycopg2 import pool

# Create connection pool
connection_pool = pool.SimpleConnectionPool(
    1, 20,
    host="aws-0-ap-south-1.pooler.supabase.com",
    database="postgres",
    user="postgres.ldmyijysjjaimrbpqmek",
    password="Uthaya$4123",
    port=6543
)

def get_connection():
    return connection_pool.getconn()

def release_connection(conn):
    connection_pool.putconn(conn)

# Bot Configuration
RESELLER_BOT_TOKEN = '7490965174:AAHmssJ7JPflECb1YCJlkjFwkC-aCbLnLW8'
ADMIN_IDS = ["7418099890"]  # Add admin Telegram IDs

# Price configuration (in INR)
PRICES = {
    "2h": 25,    # 2 hours
    "1d": 200,   # 1 day
    "7d": 800,   # 1 week
    "30d": 1200, # 1 month
    "60d": 2000  # 2 months
}

# Database configuration - use the same as main bot
DB_CONFIG = {
    "host": "aws-0-ap-south-1.pooler.supabase.com",
    "database": "postgres",
    "user": "postgres.ldmyijysjjaimrbpqmek",
    "password": "Uthaya$4123",
    "port": 6543
}

def get_db_connection():
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            connection = psycopg2.connect(
                host="aws-0-ap-south-1.pooler.supabase.com",
                database="postgres",
                user="postgres.ldmyijysjjaimrbpqmek", 
                password="Uthaya$4123",
                port=6543
            )
            connection.autocommit = False
            return connection
        except psycopg2.Error as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(retry_delay)

# Initialize bot and timezone
bot = telebot.TeleBot(RESELLER_BOT_TOKEN)
IST = pytz.timezone('Asia/Kolkata')

# Initialize database connection
connection = psycopg2.connect(**DB_CONFIG)
cursor = connection.cursor()

def setup_database():
    try:
        # Create resellers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resellers (
                telegram_id TEXT PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                added_by TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reseller_transactions (
                id SERIAL PRIMARY KEY,
                reseller_id TEXT,
                type TEXT,
                amount INTEGER,
                key_generated TEXT,
                duration TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES resellers(telegram_id)
            )
        """)
        connection.commit()
    except Exception as e:
        logging.error(f"Database setup error: {e}")
        connection.rollback()

@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    response = f"""
🌟𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗠𝗔𝗧𝗥𝗜𝗫 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗣𝗮𝗻𝗲𝗹🌟

👋 𝗛𝗲𝗹𝗹𝗼 {user_name}!

📝 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:
• Use /help for all commands
• Use /prices for pricing details
• Use /balance to check balance

🔥Bot: @MatrixCheats_ddos_bot

🔗 𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹 𝗖𝗵𝗮𝗻𝗻𝗲𝗹𝘀:
• Channel: @MATRIX_CHEATS

💫 𝗦𝘁𝗮𝗿𝘁 𝗥𝗲𝘀𝗲𝗹𝗹𝗶𝗻𝗴:
Contact @its_MATRIX_King to become a Offical Reseller
"""
    bot.reply_to(message, response)

@bot.message_handler(commands=['help'])
def show_help(message):
    user_id = str(message.from_user.id)
    help_text = """
🎮 𝗠𝗔𝗧𝗥𝗜𝗫 𝗥𝗘𝗦𝗘𝗟𝗟𝗘𝗥 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦

💎 𝗥𝗘𝗦𝗘𝗟𝗟𝗘𝗥 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦:
• /balance - Check your wallet balance
• /generatekey - Generate new license key
• /prices - View current key prices
• /mykeys - View your unused keys
• /myusers - View your active users
• /remove - Delete key/user

📊 𝗨𝗦𝗘𝗥 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧:
• /myusers - Monitor active users
• /mykeys - Track available keys
• /remove <key> - Remove specific key"""

    # Add admin commands if user is admin
    if user_id in ADMIN_IDS:
        help_text += """

👑 𝗔𝗗𝗠𝗜𝗡 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦:
• /addreseller - Register new reseller
• /addbalance - Add balance to reseller
• /allresellers - View all resellers
• /removecredits - Remove credits from reseller
• /removereseller - Delete reseller account
• /broadcast - Send mass message
"""

    help_text += """

📱 𝗦𝗨𝗣𝗣𝗢𝗥𝗧:
• Channel: @MATRIX_CHEATS
• Owner: @its_MATRiX_King

⚠️ 𝗡𝗢𝗧𝗘:
• Keep your reseller credentials safe
• Contact admin for any issues
• Prices are non-negotiable"""

    bot.reply_to(message, help_text)

@bot.message_handler(commands=['mykeys'])
def show_reseller_keys(message):
    user_id = str(message.chat.id)
    try:
        # Check if user is a reseller
        cursor.execute("""
            SELECT telegram_id FROM resellers 
            WHERE telegram_id = %s
        """, (user_id,))
        
        if not cursor.fetchone():
            bot.reply_to(message, "⛔️ Only resellers can use this command")
            return
            
        # Get all unused keys generated by this reseller
        cursor.execute("""
            SELECT k.key, k.duration, k.created_at
            FROM unused_keys k
            JOIN reseller_transactions rt ON k.key = rt.key_generated
            WHERE rt.reseller_id = %s AND k.is_used = FALSE
            ORDER BY k.created_at DESC
        """, (user_id,))
        
        keys = cursor.fetchall()
        if not keys:
            bot.reply_to(message, "📝 You have no unused keys available")
            return
            
        response = "🔑 𝗬𝗼𝘂𝗿 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗞𝗲𝘆𝘀:\n\n"
        for key in keys:
            duration_seconds = float(key[1])
            created_at = key[2].astimezone(IST)
            days = int(duration_seconds // (24 * 3600))
            remaining = duration_seconds % (24 * 3600)
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            
            response += f"🔑 Key: `{key[0]}`\n"
            if days > 0:
                response += f"⏱ Duration: {days}d {hours}h {minutes}m\n"
            elif hours > 0:
                response += f"⏱ Duration: {hours}h {minutes}m\n"
            else:
                response += f"⏱ Duration: {minutes}m\n"
            response += f"📅 Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')} IST\n\n"
            
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error fetching keys: {str(e)}")

@bot.message_handler(commands=['myusers'])
def show_reseller_users(message):
    user_id = str(message.chat.id)
    try:
        # Check if user is a reseller
        cursor.execute("""
            SELECT telegram_id FROM resellers 
            WHERE telegram_id = %s
        """, (user_id,))
        
        if not cursor.fetchone():
            bot.reply_to(message, "⛔️ Only resellers can use this command")
            return
            
        # Get all active users who used this reseller's keys
        cursor.execute("""
            SELECT u.user_id, u.username, u.key, u.expiration
            FROM users u
            JOIN reseller_transactions rt ON u.key = rt.key_generated
            WHERE rt.reseller_id = %s AND u.expiration > NOW()
            ORDER BY u.expiration DESC
        """, (user_id,))
        
        users = cursor.fetchall()
        if not users:
            bot.reply_to(message, "📝 You have no active users")
            return
            
        response = "👥 𝗬𝗼𝘂𝗿 𝗔𝗰𝘁𝗶𝘃𝗲 𝗨𝘀𝗲𝗿𝘀:\n\n"
        current_time = datetime.now(IST)
        
        for user in users:
            remaining = user[3].astimezone(IST) - current_time
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            
            response += (f"👤 User: @{user[1]}\n"
                       f"🆔 ID: {user[0]}\n"
                       f"🔑 Key: {user[2]}\n"
                       f"⏳ Remaining: {days}d {hours}h {minutes}m\n"
                       f"📅 Expires: {user[3].astimezone(IST).strftime('%Y-%m-%d %H:%M:%S')} IST\n\n")
            
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error fetching users: {str(e)}")

@bot.message_handler(commands=['remove'])
def remove_reseller_key(message):
    user_id = str(message.chat.id)
    try:
        # Check if user is a reseller
        cursor.execute("""
            SELECT telegram_id FROM resellers 
            WHERE telegram_id = %s
        """, (user_id,))
        
        if not cursor.fetchone():
            bot.reply_to(message, "⛔️ Only resellers can use this command")
            return
            
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "📝 Usage: /remove <key>")
            return
            
        key = args[1]
        
        # Verify the key belongs to this reseller
        cursor.execute("""
            SELECT key_generated FROM reseller_transactions
            WHERE reseller_id = %s AND key_generated = %s
        """, (user_id, key))
        
        if not cursor.fetchone():
            bot.reply_to(message, "❌ This key was not generated by you")
            return
            
        # Remove key and associated user
        cursor.execute("DELETE FROM unused_keys WHERE key = %s", (key,))
        cursor.execute("DELETE FROM users WHERE key = %s", (key,))
        connection.commit()
        
        bot.reply_to(message, f"""
✅ Key Removed Successfully
🔑 Key: {key}
""")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error removing key: {str(e)}")
        connection.rollback()

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "⛔️ Only administrators can add resellers.")
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "📝 Usage: /addreseller <telegram_id> <initial_balance>")
            return
            
        telegram_id = args[1]
        balance = int(args[2])
        
        cursor.execute("""
            INSERT INTO resellers (telegram_id, balance, added_by)
            VALUES (%s, %s, %s)
        """, (telegram_id, balance, str(message.from_user.id)))
        connection.commit()
        
        bot.reply_to(message, f"""
✅ Reseller Added Successfully
👤 Telegram ID: {telegram_id}
💰 Initial Balance: {balance}
""")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        connection.rollback()

@bot.message_handler(commands=['generatekey'])
def generate_key(message):
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, """
📝 𝗨𝘀𝗮𝗴𝗲: /generatekey <duration>
⏱️ 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻𝘀:
• 2h ➜ 25 Credits
• 1d ➜ 200 Credits
• 7d ➜ 800 Credits
• 30d ➜ 1,200 Credits
• 60d ➜ 2,000 Credits
📌 Example: /generatekey 2h""")
            return

        duration = args[1].lower()
        if duration not in PRICES:
            bot.reply_to(message, "❌ Invalid duration! Use 2h, 1d, 7d, 30d, or 60d")
            return

        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Check reseller balance
            cursor.execute("""
                SELECT balance, username FROM resellers 
                WHERE telegram_id = %s
            """, (str(message.from_user.id),))
            
            result = cursor.fetchone()
            if not result:
                bot.reply_to(message, "⛔️ You are not registered as a reseller. Contact @its_MATRIX_King")
                return

            balance, username = result
            price = PRICES[duration]
            
            if balance < price:
                bot.reply_to(message, f"""
❌ 𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗕𝗮𝗹𝗮𝗻𝗰𝗲!
Required: {price:,} Credits
Available: {balance:,} Credits""")
                return

            # Generate key
            key = f"MATRIX-{duration.upper()}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            duration_seconds = {
                "2h": 7200,
                "1d": 86400,
                "7d": 604800,
                "30d": 2592000,
                "60d": 5184000
            }[duration]

            # Database operations in transaction
            cursor.execute("""
                UPDATE resellers 
                SET balance = balance - %s 
                WHERE telegram_id = %s 
                RETURNING balance
            """, (price, str(message.from_user.id)))
            
            new_balance = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO reseller_transactions 
                (reseller_id, type, amount, key_generated, duration)
                VALUES (%s, 'KEY_GENERATION', %s, %s, %s)
            """, (str(message.from_user.id), price, key, duration))

            cursor.execute("""
                INSERT INTO unused_keys 
                (key, duration, created_at, is_used)
                VALUES (%s, %s, NOW(), FALSE)
            """, (key, duration_seconds))

            # Notify admin about key generation
            admin_message = f"""
🔑 𝗡𝗲𝘄 𝗞𝗲𝘆 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱
👤 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿: @{username}
🆔 𝗜𝗗: {message.from_user.id}
🔑 𝗞𝗲𝘆: {key}
⏱️ 𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {duration.upper()}
💰 𝗖𝗿𝗲𝗱𝗶𝘁𝘀 𝗨𝘀𝗲𝗱: {price:,}"""

            for admin in admin_id:
                bot.send_message(admin, admin_message)

            connection.commit()
            
            bot.reply_to(message, f"""
✅ 𝗞𝗲𝘆 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!
🔑 𝗞𝗲𝘆: `{key}`
⏱️ 𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {duration.upper()}
💰 𝗖𝗿𝗲𝗱𝗶𝘁𝘀 𝗨𝘀𝗲𝗱: {price:,}
💳 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴: {new_balance:,}""")

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        bot.reply_to(message, f"❌ 𝗘𝗿𝗿𝗼𝗿: {str(e)}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()

@bot.message_handler(commands=['balance'])
def check_balance(message):
    try:
        cursor.execute("""
            SELECT balance 
            FROM resellers 
            WHERE telegram_id = %s
        """, (str(message.from_user.id),))
        result = cursor.fetchone()
        
        if not result:
            bot.reply_to(message, "⛔️ You are not registered as a reseller.")
            return
            
        bot.reply_to(message, f"""
💰 Your Balance
Available: Credits{result[0]}

📝 Use /generatekey to create keys
""")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "⛔️ Only administrators can add balance.")
        return
        
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "📝 Usage: /addbalance <telegram_id> <amount>")
            return
            
        telegram_id = args[1]
        amount = int(args[2])
        
        cursor.execute("""
            UPDATE resellers 
            SET balance = balance + %s 
            WHERE telegram_id = %s
            RETURNING balance
        """, (amount, telegram_id))
        result = cursor.fetchone()
        
        if not result:
            bot.reply_to(message, "❌ Reseller not found!")
            return
            
        connection.commit()
        bot.reply_to(message, f"""
✅ Balance Added Successfully
👤 Telegram ID: {telegram_id}
💰 Added Amount: Credits{amount}
💳 New Balance: Credits{result[0]}
""")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        connection.rollback()

@bot.message_handler(commands=['allresellers'])
def show_all_resellers(message):
    if str(message.chat.id) not in ADMIN_IDS:
        bot.reply_to(message, "⛔️ Access Denied: Admin only command")
        return

    try:
        cursor.execute("""
            SELECT r.telegram_id, r.username, r.balance, r.created_at 
            FROM resellers r
            ORDER BY r.created_at DESC
        """)
        resellers = cursor.fetchall()

        if not resellers:
            bot.reply_to(message, "📝 No resellers found")
            return

        response = "👥 𝗔𝗰𝘁𝗶𝘃𝗲 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀:\n\n"
        
        for reseller in resellers:
            telegram_id, username, balance, created_at = reseller
            created_at_ist = created_at.astimezone(IST)
            
            # Get username from Telegram API if not in database
            try:
                user_info = bot.get_chat(telegram_id)
                display_username = user_info.username or user_info.first_name
            except:
                display_username = username if username else "Unknown"

            response += (
                f"🆔 𝗜𝗗: {telegram_id}\n"
                f"👤 𝗨𝘀𝗲𝗿: @{display_username}\n"
                f"💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: Credits{balance}\n"
                f"📅 𝗝𝗼𝗶𝗻𝗲𝗱: {created_at_ist.strftime('%Y-%m-%d %H:%M:%S')} IST\n"
                "━━━━━━━━━━━━━━━\n"
            )

        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error fetching resellers: {str(e)}")

@bot.message_handler(commands=['removecredits'])
def remove_credits(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "⛔️ Only administrators can remove credits.")
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "📝 Usage: /removecredits <telegram_id> <amount>")
            return
            
        telegram_id = args[1]
        amount = int(args[2])
        
        cursor.execute("""
            UPDATE resellers 
            SET balance = GREATEST(0, balance - %s)
            WHERE telegram_id = %s 
            RETURNING balance
        """, (amount, telegram_id))
        
        result = cursor.fetchone()
        if not result:
            bot.reply_to(message, "❌ Reseller not found!")
            return
            
        connection.commit()
        
        bot.reply_to(message, f"""
✅ Credits Removed Successfully
👤 Telegram ID: {telegram_id}
💰 Removed Amount: Credits{amount}
💳 New Balance: Credits{result[0]}
""")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        connection.rollback()

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "⛔️ Only administrators can remove resellers.")
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "📝 Usage: /removereseller <telegram_id>")
            return

        telegram_id = args[1]

        # Get reseller info and try to fetch current username from Telegram
        cursor.execute("""
            SELECT username, balance 
            FROM resellers 
            WHERE telegram_id = %s
        """, (telegram_id,))
        
        result = cursor.fetchone()
        if not result:
            bot.reply_to(message, "❌ Reseller not found!")
            return

        stored_username, balance = result

        # Try to get current username from Telegram API
        try:
            user_info = bot.get_chat(telegram_id)
            current_username = user_info.username or user_info.first_name
        except:
            current_username = stored_username

        # Use the most up-to-date username
        display_username = current_username if current_username else stored_username

        # Delete reseller and associated transactions
        cursor.execute("""
            DELETE FROM reseller_transactions 
            WHERE reseller_id = %s
        """, (telegram_id,))
        
        cursor.execute("""
            DELETE FROM resellers 
            WHERE telegram_id = %s
        """, (telegram_id,))
        
        connection.commit()

        admin_message = f"""
✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆
👤 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{display_username}
🆔 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺 𝗜𝗗: {telegram_id}
💰 𝗙𝗶𝗻𝗮𝗹 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: Credits{balance}
📅 𝗥𝗲𝗺𝗼𝘃𝗲𝗱: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST"""

        bot.reply_to(message, admin_message)

        # Notify other admins
        for admin in ADMIN_IDS:
            if admin != str(message.from_user.id):
                bot.send_message(admin, f"""
🚫 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 𝗔𝗹𝗲𝗿𝘁
👤 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 𝗯𝘆: @{message.from_user.username}
🆔 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 𝗜𝗗: {telegram_id}
👤 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{display_username}
📅 𝗧𝗶𝗺𝗲: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST""")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        connection.rollback()


@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "⛔️ Only administrators can broadcast messages.")
        return

    try:
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            bot.reply_to(message, "📝 Usage: /broadcast <message>")
            return

        broadcast_text = args[1]

        # Get all active resellers
        cursor.execute("""
            SELECT telegram_id, username 
            FROM resellers 
            ORDER BY username
        """)
        resellers = cursor.fetchall()

        if not resellers:
            bot.reply_to(message, "📝 No resellers found to broadcast to.")
            return

        success_count = 0
        failed_resellers = []

        for reseller_id, username in resellers:
            try:
                formatted_message = f"""
📢 𝗥𝗘𝗦𝗘𝗟𝗟𝗘𝗥 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧

{broadcast_text}

━━━━━━━━━━━━━━━
𝗦𝗲𝗻𝘁 𝗯𝘆: @{message.from_user.username}
𝗧𝗶𝗺𝗲: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST
"""
                bot.send_message(reseller_id, formatted_message)
                success_count += 1
                time.sleep(0.1)  # Prevent flooding
            except Exception as e:
                failed_resellers.append(f"@{username}")

        # Send summary to admin
        summary = f"""
✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗦𝘂𝗺𝗺𝗮𝗿𝘆:
📨 𝗧𝗼𝘁𝗮𝗹 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀: {len(resellers)}
✅ 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹: {success_count}
❌ 𝗙𝗮𝗶𝗹𝗲𝗱: {len(failed_resellers)}
"""
        if failed_resellers:
            summary += f"\n❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀:\n" + "\n".join(failed_resellers)

        bot.reply_to(message, summary)

    except Exception as e:
        bot.reply_to(message, f"❌ Error during broadcast: {str(e)}")

@bot.message_handler(commands=['prices'])
def show_prices(message):
    price_text = """
💎 𝗣𝗔𝗡𝗘𝗟 𝗣𝗥𝗜𝗖𝗘𝗦:
• ₹1,000 ➜ 4,000 Credits
• ₹1,500 ➜ 6,200 Credits
• ₹2,000 ➜ 9,000 Credits
• ₹3,000 ➜ 14,000 Credits

💰 𝗞𝗘𝗬 𝗣𝗥𝗜𝗖𝗘𝗦:
• 2 Hours: 25 Credits
• 1 Day: 200 Credits
• 7 Days: 800 Credits
• 30 Days: 1,200 Credits
• 60 Days: 2,000 Credits

📌 𝗠𝗜𝗡𝗜𝗠𝗨𝗠 𝗕𝗨𝗬: 1,000₹ (4,000 Credits)"""
    bot.reply_to(message, price_text)

def run_bot():
    setup_database()
    while True:
        try:
            print("Reseller bot is running...")
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Bot error: {e}")
            time.sleep(15)

if __name__ == "__main__":
    run_bot()
