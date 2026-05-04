"""
Telegram Bot - Interface for DeepResearch Agent via Telegram.
"""

import asyncio
import logging
import os
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from deepresearch.core.engine import ResearchEngine

logger = logging.getLogger(__name__)


class DeepResearchBot:
    """
    Telegram bot for DeepResearch Agent.
    
    Features:
    - /start - Welcome message
    - /research <topic> - Start research
    - /history - View recent research
    - /help - Show available commands
    - Any message - Treated as research topic
    """
    
    def __init__(self, token: str, config: dict[str, Any] | None = None):
        self.token = token
        self.config = config or {}
        self.engine = ResearchEngine(self.config)
        self.app: Application | None = None
    
    async def initialize(self):
        """Initialize the bot and engine."""
        await self.engine.initialize()
        
        self.app = Application.builder().token(self.token).build()
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("research", self.research_command))
        self.app.add_handler(CommandHandler("history", self.history_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Bot initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome = """
🔬 **Welcome to DeepResearch Agent!**

I'm an autonomous research agent powered by MiMo. I can research any topic and generate comprehensive reports.

**Commands:**
/research <topic> - Start researching a topic
/history - View recent research
/help - Show this message

**Or simply send me a topic and I'll research it!**

Examples:
• "Riset tentang AI di Indonesia"
• "Latest trends in quantum computing"
• "Compare React vs Vue vs Angular"
        """
        
        await update.message.reply_text(welcome, parse_mode="Markdown")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📚 **DeepResearch Agent Help**

**How it works:**
1. Send me a topic or question
2. I'll plan the research strategy
3. Search multiple sources (web, academic, news)
4. Analyze and cross-reference findings
5. Generate a comprehensive report

**Commands:**
/start - Welcome message
/research <topic> - Start research
/history - View recent research
/help - Show this message

**Tips:**
• Be specific for better results
• I can research in any language
• Reports include citations and confidence scores
        """
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def research_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /research command."""
        if not context.args:
            await update.message.reply_text(
                "Please provide a topic. Example: /research AI in Indonesia"
            )
            return
        
        topic = " ".join(context.args)
        await self._do_research(update, topic)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages as research topics."""
        topic = update.message.text
        await self._do_research(update, topic)
    
    async def _do_research(self, update: Update, topic: str):
        """Execute research and send results."""
        # Send "researching" message
        status_msg = await update.message.reply_text(
            f"🔬 Researching: *{topic}*\n\n"
            "⏳ Planning research strategy...",
            parse_mode="Markdown"
        )
        
        try:
            # Update status
            await status_msg.edit_text(
                f"🔬 Researching: *{topic}*\n\n"
                "🔍 Searching multiple sources...",
                parse_mode="Markdown"
            )
            
            # Run research
            result = await self.engine.research(topic)
            
            # Update status
            await status_msg.edit_text(
                f"🔬 Researching: *{topic}*\n\n"
                "✍️ Generating report...",
                parse_mode="Markdown"
            )
            
            # Prepare report
            report = result.report or "No report generated"
            confidence = result.confidence_score
            sources_count = len(result.citations)
            
            # Send report
            header = (
                f"📄 *Research Report*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Confidence: {confidence:.0%}\n"
                f"📚 Sources: {sources_count}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            
            # Telegram has message length limit
            max_length = 4000
            if len(header + report) > max_length:
                # Split into multiple messages
                await status_msg.edit_text(header, parse_mode="Markdown")
                
                # Send report in chunks
                chunks = [report[i:i+max_length] for i in range(0, len(report), max_length)]
                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode="Markdown")
            else:
                await status_msg.edit_text(
                    header + report,
                    parse_mode="Markdown"
                )
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            await status_msg.edit_text(
                f"❌ Research failed: {str(e)}\n\n"
                "Please try again or contact support.",
                parse_mode="Markdown"
            )
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command."""
        history = await self.engine.get_history(limit=5)
        
        if not history:
            await update.message.reply_text("No research history found.")
            return
        
        text = "📚 *Recent Research*\n\n"
        
        for item in history:
            status = "✅" if item["status"] == "completed" else "⏳"
            text += f"{status} {item['topic'][:40]}...\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    def run(self):
        """Run the bot."""
        asyncio.run(self._run())
    
    async def _run(self):
        """Run the bot asynchronously."""
        await self.initialize()
        
        logger.info("Bot starting...")
        await self.app.run_polling()


def main():
    """Main entry point for the Telegram bot."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        print("Get a token from @BotFather on Telegram")
        return
    
    config = {
        "db_path": "data/research.db",
        "llm_endpoint": os.environ.get("LLM_ENDPOINT", "https://api.mimo.xiaomi.com/v1/chat/completions"),
        "llm_key": os.environ.get("LLM_API_KEY", ""),
        "model": os.environ.get("LLM_MODEL", "mimo-7b")
    }
    
    bot = DeepResearchBot(token, config)
    bot.run()


if __name__ == "__main__":
    main()
