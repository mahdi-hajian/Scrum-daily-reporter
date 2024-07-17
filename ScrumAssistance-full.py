import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from telegram import Update, User, Bot
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    JobQueue,
    CallbackContext,
    ConversationHandler,
)
from datetime import time, datetime, timedelta
import os
import pytz

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)
group_id = os.getenv('GTOUP_ID')
report_topic_id = os.getenv('REPORT_TOPIC_ID')
alert_topic_id = os.getenv('ALERT_TOPIC_ID')
token = os.getenv('TOKEN')

# Ensure the /data directory exists
os.makedirs('data', exist_ok=True)

# SQLite Database Setup
directory_name = 'data'
database_name = 'database.db'
db_path = os.path.join(directory_name, database_name)
engine = create_engine(f'sqlite:///{db_path}')
Base = declarative_base()

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    tasks_today = Column(String)
    blockers = Column(String)
    tasks_tomorrow = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Stages for conversation handler
TASKS_TODAY, BLOCKERS, TASKS_TOMORROW = range(3)

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('لطفا گزارش روزانه خود را با ارسال /report تکمیل کنید')

async def start_report(update: Update, context: CallbackContext) -> int:
    """Start the daily report conversation."""
    await update.message.reply_text('امروز کار کردم روی:')
    return TASKS_TODAY

async def tasks_today(update: Update, context: CallbackContext) -> int:
    """Handle the tasks worked on today."""
    context.user_data['tasks_today'] = update.message.text
    await update.message.reply_text('سوال یا بلاکر:')
    return BLOCKERS

async def blockers(update: Update, context: CallbackContext) -> int:
    """Handle the questions/blockers."""
    context.user_data['blockers'] = update.message.text
    await update.message.reply_text('فردا قراره کار کنم روی:')
    return TASKS_TOMORROW

async def tasks_tomorrow(update: Update, context: CallbackContext) -> int:
    """Handle the tasks planned for tomorrow."""
    user_id = update.message.from_user.id
    context.user_data['tasks_tomorrow'] = update.message.text

    # Save report to SQLite
    session = Session()
    new_report = Report(
        user_id=user_id,
        tasks_today=context.user_data['tasks_today'],
        blockers=context.user_data['blockers'],
        tasks_tomorrow=context.user_data['tasks_tomorrow']
    )
    session.query(Report).filter(Report.user_id == user_id).delete()
    session.add(new_report)
    session.commit()
    session.close()

    await update.message.reply_text('گزارش روزانه شما ثبت شد.')
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the conversation."""
    await update.message.reply_text('درخواست گزارش شما لغو شد.')
    return ConversationHandler.END

async def get_daily_report_message(context, reports) -> String:
    report_text = "گزارشات روزانه:\n\n"
    for report in reports:
        user_link = await get_user_mention_by_user_id(context, report.user_id)
        report_text += (
            f"گزارش {user_link}:\n"
            f"دیروز کار کرده روی:\n{report.tasks_today}\n"
            f"سوال/ بلاکر:\n{report.blockers}\n"
            f"امروز قراره کار کنه روی:\n{report.tasks_tomorrow}\n"
            f"- - - - - - - -\n"
        )
    return report_text


async def send_daily_report(context: CallbackContext) -> None:
    """Send daily report to the group."""
    session = Session()
    reports = session.query(Report).all()
    session.close()

    if reports:
        logger.info("report exist")
        report_text = await get_daily_report_message(context, reports)
        logger.info(report_text)
        await context.bot.send_message(chat_id=group_id, message_thread_id=report_topic_id, text=report_text, parse_mode=ParseMode.MARKDOWN)
        logger.info("sent")

        # Delete all reports after sending
        session = Session()
        session.query(Report).delete()
        session.commit()
        session.close()
        logger.info("remove all")
        
    logger.info("report not exist")
    

async def ask_for_daily_tasks(context: CallbackContext) -> None:
    """Send notification to group to send daily tasks."""

    await context.bot.send_message(chat_id=group_id, message_thread_id=alert_topic_id, text="لطفا گزارش روزانه خود را با ارسال /report تکمیل کنید")

async def get_group_members(bot: Bot, chat_id: int) -> []:
    members = []
    try:
        # Get the list of administrators (including the bot itself)
        administrators = await bot.get_chat_administrators(chat_id)
        
        for admin in administrators:
            logger.info(admin.user.username)
            members.append(admin.user)
        
    except TelegramError as e:
        print(f'An error occurred: {e}')
    return members

async def remind_users_to_send_tasks(context: Application) -> None:
    """Send reminder to users who haven't sent their tasks."""
    
    session = Session()
    incomplete_reports = session.query(Report.user_id).all()
    session.close()

    all_users: [] = await get_group_members(context.bot, group_id)
    if all_users:
        # Extract user IDs from the query results
        users_with_reports = {report.user_id for report in incomplete_reports}
        users_to_remind = []

        # Loop through all users in the group
        for user in all_users:
            user_id = user.id
            # Check if user hasn't submitted a report
            if user_id not in users_with_reports:
                users_to_remind.append(user)
        
        if users_to_remind:
            # Create a message mentioning all users who need to submit their report
            mentions = [get_user_mention_by_user(user)+'\n' for user in users_to_remind]
            reminder_text = "لطفا گزارش روزانه خود را با ارسال /report تکمیل کنید\n" + "".join(mentions)
            # Send the message to the specified group and topic
            await context.bot.send_message(
                chat_id=group_id,
                message_thread_id=alert_topic_id,
                text=reminder_text,
                parse_mode=ParseMode.MARKDOWN
            )

async def get_user_info(context, user_id) -> User:
    return await context.bot.get_chat(user_id)

async def get_user_mention_by_user_id(context, user_id) -> User:
    user = await get_user_info(context, user_id)
    return get_user_mention_by_user(user)

def get_user_mention_by_user(user: User) -> User:
    mention = (f"[@{user.username}]" if False else f"[{user.first_name}]") + f'(tg://user?id={user.id})'
    return mention

async def send_daily_reports_manually(update: Update, context: CallbackContext) -> None:
    """Command handler to manually fetch and send daily reports."""
    # Notify the user that reports are being fetched
    await update.message.reply_text("در حال دریافت گزارشات ...")

    logger.info("Sending daily reports")

    session = Session()
    reports = session.query(Report).all()
    session.close()

    if reports:
        report_text = await get_daily_report_message(context, reports)
        await update.message.reply_text(report_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("هیچ گزارشی یافت نشد.")
    
def schedule_jobs(application: Application) -> None:
    """Schedule daily jobs."""
    job_queue: JobQueue = application.job_queue

    # Specify the timezone
    tz = pytz.timezone('Asia/Tehran')

    # Schedule daily tasks
    job_queue.run_daily(ask_for_daily_tasks, time=time(hour=16, minute=0, tzinfo=tz))
    job_queue.run_daily(remind_users_to_send_tasks, time=time(hour=18, minute=0, tzinfo=tz))
    job_queue.run_daily(send_daily_report, time=time(hour=11, minute=25, tzinfo=tz))
    
def main() -> None:
    """Start the bot."""
    
    proxy_url = os.getenv('HTTP_PROXY')

    # Create the application with or without the proxy based on its availability
    # Create the Application and pass it your bot's token.
    if proxy_url:
        logger.info("proxy")
        application = Application.builder().token(token).proxy(proxy_url).get_updates_proxy(proxy_url).build()
    else:
        logger.info("no proxy")
        application = Application.builder().token(token).build()

    group_filter = filters.ChatType.GROUPS
    
    # Add conversation handler with the states TASKS_TODAY, BLOCKERS, TASKS_TOMORROW
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('report',start_report , filters=group_filter)],
        states={
            TASKS_TODAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks_today)],
            BLOCKERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, blockers)],
            TASKS_TOMORROW: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks_tomorrow)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(CommandHandler("getreports", send_daily_reports_manually, filters=group_filter))

    application.add_handler(conv_handler)
    
    # Schedule the daily tasks
    schedule_jobs(application)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
