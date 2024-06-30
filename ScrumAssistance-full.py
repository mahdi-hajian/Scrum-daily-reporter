import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from telegram import Update
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

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
group_id = -4220216586  # Replace with your group chat ID
topic_id = 140  # Replace with your group chat ID

# SQLite Database Setup
engine = create_engine('sqlite:///daily_reports.db')
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

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hi")


async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Use /report to start your daily report.')

async def start_report(update: Update, context: CallbackContext) -> int:
    """Start the daily report conversation."""
    await update.message.reply_text('Today I worked on (list your tasks):')
    return TASKS_TODAY

async def tasks_today(update: Update, context: CallbackContext) -> int:
    """Handle the tasks worked on today."""
    context.user_data['tasks_today'] = update.message.text
    await update.message.reply_text('Questions/Blockers (list any questions or blockers):')
    return BLOCKERS

async def blockers(update: Update, context: CallbackContext) -> int:
    """Handle the questions/blockers."""
    context.user_data['blockers'] = update.message.text
    await update.message.reply_text('Tomorrow I will be working on (list your tasks):')
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
    session.add(new_report)
    session.commit()
    session.close()

    await update.message.reply_text('Thank you for your report!')
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the conversation."""
    await update.message.reply_text('Daily report canceled.')
    return ConversationHandler.END

async def send_daily_report(context: CallbackContext) -> None:
    logger.info("asdfasdf")
    
    """Send daily report to the group."""
    logger.info("send_daily_report works")
    session = Session()
    reports = session.query(Report).all()
    session.close()

    if reports:
        report_text = "Daily Reports:\n\n"
        for report in reports:
            report_text += (
                f"Report from user ID {report.user_id}:\n"
                f"Today I worked on:\n{report.tasks_today}\n\n"
                f"Questions/Blockers:\n{report.blockers}\n\n"
                f"Tomorrow I will be working on:\n{report.tasks_tomorrow}\n\n"
            )
        
        await context.bot.send_message(group_id, message_thread_id=topic_id, text=report_text, parse_mode=ParseMode.MARKDOWN)

        # Delete all reports after sending
        session = Session()
        session.query(Report).delete()
        session.commit()
        session.close()

async def ask_for_daily_tasks(context: CallbackContext) -> None:
    """Send notification to group to send daily tasks."""
    print
    await context.bot.send_message(group_id, message_thread_id=topic_id, text="Please submit your daily tasks using /report.")


async def remind_users_to_send_tasks(context: Application) -> None:
    """Send reminder to users who haven't sent their tasks."""
    session = Session()
    all_users = await context.bot.get_chat_members(context.job.context)
    incomplete_reports = session.query(Report.user_id).filter(Report.tasks_today == None).all()
    session.close()

    if all_users and incomplete_reports:
        # Extract user IDs from the query results
        users_with_reports = {report.user_id for report in incomplete_reports}
        # Loop through all users in the group
        for user in all_users:
            user_id = user.user.id
            # Check if user hasn't submitted a report
            if user_id not in users_with_reports:
                # Send reminder to user
                await context.bot.send_message(user_id, text="Please submit your daily tasks using /report.")

async def send_daily_reports(update: Update, context: CallbackContext) -> None:
    """Command handler to manually fetch and send daily reports."""
    # Notify the user that reports are being fetched
    await update.message.reply_text("Fetching daily reports...")

    session = Session()
    reports = session.query(Report).all()
    session.close()

    if reports:
        report_text = "Daily Reports:\n\n"
        for report in reports:
            user = await context.bot.get_chat(report.user_id)
            first_name = user.first_name if user.first_name else "Unknown"
            last_name = user.last_name if user.last_name else ""
            profile_link = f"[{first_name} {last_name}](https://t.me/{user.username})"

            report_text += (
                f"Report from {profile_link}:\n"
                f"Today I worked on:\n{report.tasks_today}\n\n"
                f"Questions/Blockers:\n{report.blockers}\n\n"
                f"Tomorrow I will be working on:\n{report.tasks_tomorrow}\n\n"
            )

        # Send the accumulated reports
        await update.message.reply_text(report_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("No daily reports found.")
    
    # Delete all reports after sending
    session = Session()
    session.query(Report).delete()
    session.commit()
    session.close()

def schedule_jobs(application: Application) -> None:
    """Schedule daily jobs."""
    job_queue: JobQueue = application.job_queue

    # Schedule daily tasks
    job_queue.run_daily(send_daily_report, time=time(hour=9, minute=0))
    job_queue.run_daily(ask_for_daily_tasks, time=time(hour=16, minute=0))
    job_queue.run_daily(remind_users_to_send_tasks, time=time(hour=20, minute=0))

async def daily_message(context: CallbackContext):
    # Replace 'GROUP_CHAT_ID' with the actual chat ID of the group
    await context.bot.send_message(chat_id= group_id, message_thread_id=topic_id, text='Daily Message!')
    
def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7230447684:AAETM_yIJmnCCJQMjI7bZvZ3WNKosQQPnt4").build()
    
    # Add conversation handler with the states TASKS_TODAY, BLOCKERS, TASKS_TOMORROW
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('report', start_report)],
        states={
            TASKS_TODAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks_today)],
            BLOCKERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, blockers)],
            TASKS_TOMORROW: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks_tomorrow)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler("getreports", send_daily_reports))

    application.add_handler(conv_handler)
    
    # on different commands - answer in Telegram
    # application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("help", help_command))

    # Schedule the daily tasks
    schedule_jobs(application)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
