import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, CallbackQuery, Message, User
from telegram.ext import ContextTypes
import psycopg
from agents.telegram_agent import (
    start_command,
    help_command,
    research_command,
    trends_command,
    status_command,
    domains_command,
    about_command,
    button_callback,
    WELCOME_MESSAGE
)


class TestTelegramAgent(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.update = MagicMock(spec=Update)
        self.context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        self.message = AsyncMock(spec=Message)
        self.update.message = self.message
        self.update.effective_message = self.message
        
        # Mock authorized user
        user = MagicMock(spec=User)
        user.id = 5555278895
        self.update.effective_user = user

    async def test_start_command(self):
        await start_command(self.update, self.context)
        self.message.reply_text.assert_awaited_once()
        args, kwargs = self.message.reply_text.call_args
        self.assertEqual(args[0], WELCOME_MESSAGE)
        self.assertIn("reply_markup", kwargs)

    async def test_help_command(self):
        await help_command(self.update, self.context)
        self.message.reply_text.assert_awaited_once()
        args, kwargs = self.message.reply_text.call_args
        self.assertIn("SAKHR AVA_R PROFESSIONAL COMMAND SYSTEM", args[0])

    async def test_status_command(self):
        with patch("agents.telegram_agent.get_statistics", return_value={"papers": 10, "analyses": 5, "sources": 6}):
            await status_command(self.update, self.context)
            self.message.reply_text.assert_awaited()
            args, _ = self.message.reply_text.call_args
            self.assertIn("System Status", args[0])

    async def test_status_command_db_error(self):
        with patch("agents.telegram_agent.get_statistics", side_effect=psycopg.OperationalError("Connection refused")):
            await status_command(self.update, self.context)
            # Should handle exception and reply/edit with error message without raising NameError or AttributeError
            self.assertTrue(self.message.reply_text.await_count > 0 or self.message.edit_text.await_count > 0)

    async def test_domains_command(self):
        await domains_command(self.update, self.context)
        self.message.reply_text.assert_awaited_once()
        args, _ = self.message.reply_text.call_args
        self.assertIn("Supported Scientific Disciplines", args[0])

    async def test_about_command(self):
        await about_command(self.update, self.context)
        self.message.reply_text.assert_awaited_once()
        args, _ = self.message.reply_text.call_args
        self.assertIn("About SAKHR AVA_R", args[0])

    async def test_button_callback(self):
        query = AsyncMock(spec=CallbackQuery)
        query.message = AsyncMock(spec=Message)
        query.data = "btn_research"
        self.update.callback_query = query
        self.update.effective_message = query.message
        
        await button_callback(self.update, self.context)
        query.answer.assert_awaited_once()
        query.message.reply_text.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
