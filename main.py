        import telegram
        from telegram import Update, ReplyKeyboardMarkup
        from telegram.ext import (
            ApplicationBuilder,
            CommandHandler,
            MessageHandler,
            filters,
            ConversationHandler
        )
        from flask import Flask
        from threading import Thread
        import os
        import time
        import requests
        import json
        from datetime import datetime

        # Configuration - USE ENVIRONMENT VARIABLES IN PRODUCTION
        TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        MENU_PDF_URL = "https://docs.google.com/document/d/1sHbRmAsCfWgXU7DsbWR_7oAeX7P-3e8-2eJN3zpcqMQ/export?format=pdf"
        CAFETERIA_PHONE = "(306) 523-3200"
        SCHOOL_EMAIL = "balfourcollegiate@rbe.sk.ca"

        # School data channel ID - Make.com will listen to messages in this channel
        # Create a private channel, add your bot as admin, get the channel ID
        ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # Add this to your Replit secrets

        # Conversation states
        ROLE, MAIN_MENU, ORDER, COMPLAINT = range(4)

        # Keyboards
        role_keyboard = [["Student", "Teacher"]]
        main_keyboard = [["/menu", "/order"], ["/complaint", "/help"]]
        complaint_keyboard = [["Write Complaint", "Call Instead", "Message via Mail"]]

        # Flask server for keep-alive
        app = Flask('')

        @app.route('/')
        def home():
            return "Bot is alive and running!"

        def run_flask():
            app.run(host='0.0.0.0', port=8080)

        def keep_alive():
            t = Thread(target=run_flask)
            t.start()

        async def send_to_make(context, message_type, data):
            """Send structured data message that Make.com can parse"""
            if ADMIN_CHAT_ID:
                try:
                    # Create a formatted message that Make.com can easily filter and parse
                    formatted_message = f"MAKE_DATA_{message_type}: {json.dumps(data)}"
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=formatted_message)
                except Exception as e:
                    print(f"Failed to send to Make.com: {e}")

        async def start(update: Update, context) -> int:
            """Initial welcome with role selection"""
            await update.message.reply_text(
                "🍎 Welcome to Bearden Cafeteria!\n"
                "Are you a student or teacher?",
                reply_markup=ReplyKeyboardMarkup(role_keyboard, one_time_keyboard=True)
            )
            return ROLE

        async def handle_role(update: Update, context) -> int:
            """Store role and show main menu"""
            user_role = update.message.text
            context.user_data['role'] = user_role

            # Pricing note for students
            note = "\n🚨 Pre-order costs more!" if user_role == "Student" else ""

            await update.message.reply_text(
                f"👋 Hi {user_role}!{note}\n"
                "How can we help you today?",
                reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
            )
            return MAIN_MENU

        async def menu(update: Update, context) -> None:
            """Send PDF menu"""
            await update.message.reply_document(
                document=MENU_PDF_URL,
                caption="📋 Today's Menu\n"
                        "Pre-orders available 30 mins before lunch!"
            )

        async def order(update: Update, context) -> int:
            """Start order process"""
            await update.message.reply_text(
                "✍️ Please type your order:\n"
                "Example: '2 Chicken Sandwiches, 1 Salad'"
            )
            return ORDER

        async def process_order(update: Update, context) -> int:
            """Handle order submission"""
            order_text = update.message.text
            user_role = context.user_data.get('role', 'Unknown')
            user = update.effective_user

            # Original console logging (keep this)
            print(f"NEW ORDER ({user_role}): {order_text}")

            # Send structured data to Make.com via school channel
            order_data = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user.id,
                "username": user.username or "No username",
                "first_name": user.first_name or "Unknown",
                "last_name": user.last_name or "",
                "role": user_role,
                "order_text": order_text,
                "status": "Pending"
            }

            await send_to_make(context, "ORDER", order_data)

            await update.message.reply_text(
                "✅ Order received!\n"
                "Your food will be ready at lunch time.",
                reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
            )
            return MAIN_MENU

        async def complaint(update: Update, context) -> int:
            """Complaint options"""
            await update.message.reply_text(
                "How would you like to submit your concern?",
                reply_markup=ReplyKeyboardMarkup(complaint_keyboard, one_time_keyboard=True)
            )
            return COMPLAINT

        async def process_complaint(update: Update, context) -> int:
            """Handle complaint choice"""
            choice = update.message.text
            user = update.effective_user
            user_role = context.user_data.get('role', 'Unknown')

            if choice == "Call Instead":
                # Send data to Make.com for phone complaints
                complaint_data = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user.id,
                    "username": user.username or "No username",
                    "first_name": user.first_name or "Unknown",
                    "last_name": user.last_name or "",
                    "role": user_role,
                    "complaint_method": "Phone Call",
                    "complaint_text": f"User chose to call {CAFETERIA_PHONE}",
                    "status": "User will call"
                }
                await send_to_make(context, "COMPLAINT", complaint_data)

                await update.message.reply_text(f"☎️ Call Cafeteria: {CAFETERIA_PHONE}")
                await update.message.reply_text(
                    "📝 We've received your concern and will respond within 24 hours",
                    reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
                )
                return MAIN_MENU

            elif choice == "Message via Mail":
                # Send data to Make.com for email complaints
                complaint_data = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user.id,
                    "username": user.username or "No username",
                    "first_name": user.first_name or "Unknown",
                    "last_name": user.last_name or "",
                    "role": user_role,
                    "complaint_method": "Email",
                    "complaint_text": f"User chose to email {SCHOOL_EMAIL}",
                    "status": "User will email"
                }
                await send_to_make(context, "COMPLAINT", complaint_data)

                await update.message.reply_text(f"✉️ Email us at: {SCHOOL_EMAIL}")
                await update.message.reply_text(
                    "📝 We've received your concern and will respond within 24 hours",
                    reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
                )
                return MAIN_MENU

            elif choice == "Write Complaint":
                await update.message.reply_text("Please describe your issue:")
                context.user_data['complaint_stage'] = 'writing'
                return COMPLAINT
            else:
                # This handles the actual complaint text
                if context.user_data.get('complaint_stage') == 'writing':
                    complaint_text = update.message.text

                    # Original console logging (keep this)
                    print(f"COMPLAINT TEXT: {complaint_text}")

                    # Send structured data to Make.com via school channel
                    complaint_data = {
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user.id,
                        "username": user.username or "No username",
                        "first_name": user.first_name or "Unknown",
                        "last_name": user.last_name or "",
                        "role": user_role,
                        "complaint_method": "Telegram Bot",
                        "complaint_text": complaint_text,
                        "status": "New - Needs Response"
                    }

                    await send_to_make(context, "COMPLAINT", complaint_data)

                    await update.message.reply_text(
                        "📝 We've received your concern and will respond within 24 hours",
                        reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
                    )
                    context.user_data.pop('complaint_stage', None)
                    return MAIN_MENU
                else:
                    # Unknown choice, show complaint options again
                    await update.message.reply_text(
                        "Please choose one of the options:",
                        reply_markup=ReplyKeyboardMarkup(complaint_keyboard, one_time_keyboard=True)
                    )
                    return COMPLAINT

        async def help_command(update: Update, context) -> None:
            """Contact information"""
            await update.message.reply_text(
                "🆘 Bearden Cafeteria Support:\n\n"
                f"• Phone: {CAFETERIA_PHONE}\n"
                f"• Email: {SCHOOL_EMAIL}\n"
                "• Hours: 8 AM - 3 PM Mon-Fri"
            )

        async def handle_unknown_message(update: Update, context) -> int:
            """Handle unexpected messages"""
            await update.message.reply_text(
                "I'm not sure what you mean. Please use the menu buttons or type /start to begin.",
                reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
            )
            return MAIN_MENU

        def ping_server():
            """Ping the Flask server to keep it awake"""
            while True:
                try:
                    # This will ping your own server
                    requests.get("http://localhost:8080", timeout=5)
                    time.sleep(300)  # Ping every 5 minutes
                except Exception as e:
                    print(f"Ping failed: {e}")
                    time.sleep(60)

        def main() -> None:
            keep_alive()  # Start the Flask server

            # Start the ping thread
            ping_thread = Thread(target=ping_server)
            ping_thread.daemon = True
            ping_thread.start()

            try:
                # Build bot
                application = ApplicationBuilder().token(TOKEN).build()

                # Conversation flow
                conv_handler = ConversationHandler(
                    entry_points=[CommandHandler('start', start)],
                    states={
                        ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role)],
                        MAIN_MENU: [
                            CommandHandler('menu', menu),
                            CommandHandler('order', order),
                            CommandHandler('complaint', complaint),
                            CommandHandler('help', help_command)
                        ],
                        ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_order)],
                        COMPLAINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_complaint)]
                    },
                    fallbacks=[
                        CommandHandler('start', start),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message)
                    ]
                )

                application.add_handler(conv_handler)
                print("Bot is running...")
                application.run_polling()
            except Exception as e:
                print(f"Error starting bot: {e}")

        if __name__ == '__main__':
            main()