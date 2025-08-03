import telegram
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

# Configuration (YOUR INFO)
import os
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7861460900:AAHt_IK7VOmXzX7tfJ3BmIatJozBEaju3uQ")
MENU_PDF_URL = "https://docs.google.com/document/d/1sHbRmAsCfWgXU7DsbWR_7oAeX7P-3e8-2eJN3zpcqMQ/export?format=pdf"
CAFETERIA_PHONE = "(306) 523-3200"
SCHOOL_EMAIL = "balfourcollegiate@rbe.sk.ca"

# Conversation states
ROLE, MAIN_MENU, ORDER, COMPLAINT = range(4)

# Keyboards
role_keyboard = [["Student", "Teacher"]]
main_keyboard = [["/menu", "/order"], ["/complaint", "/help"]]
complaint_keyboard = [["Write Complaint", "Call Instead", "Message via Mail"]]

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

    # In future: Add to Google Sheets here
    print(f"NEW ORDER ({user_role}): {order_text}")

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

    if choice == "Call Instead":
        await update.message.reply_text(f"☎️ Call Cafeteria: {CAFETERIA_PHONE}")
        await update.message.reply_text(
            "📝 We've received your concern and will respond within 24 hours",
            reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        )
        return MAIN_MENU
    elif choice == "Message via Mail":
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
            print(f"COMPLAINT TEXT: {complaint_text}")
            
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

def main() -> None:
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