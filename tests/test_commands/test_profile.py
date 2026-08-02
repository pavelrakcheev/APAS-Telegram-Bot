"""Unit tests for profile command."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes


class TestProfileCommand:
    """Test /profile command."""

    @pytest.mark.asyncio
    async def test_profile_command_guest_mode(self):
        """Test profile command blocks guest users."""
        from Commands.profile import profile_command

        # Mock update and context
        update = AsyncMock()
        context = AsyncMock()

        update.effective_user.id = 123456
        context.user_data = {"is_guest": True}

        with patch("Commands.profile.is_guest_mode", return_value=True):
            await profile_command(update, context)

            # Should send restricted message
            update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_profile_command_not_setup(self):
        """Test profile command for user without completed setup."""
        from Commands.profile import profile_command

        update = AsyncMock()
        context = AsyncMock()

        update.effective_user.id = 123456
        context.user_data = {"setup_completed": False}

        with patch("Commands.profile.is_guest_mode", return_value=False):
            await profile_command(update, context)

            # Should ask to setup profile
            update.message.reply_text.assert_called_once_with(
                "Сначала настройте свой профиль с помощью команды /start"
            )

    @pytest.mark.asyncio
    async def test_profile_command_success(self):
        """Test successful profile display."""
        from Commands.profile import profile_command

        update = AsyncMock()
        context = AsyncMock()

        update.effective_user.id = 123456
        context.user_data = {
            "setup_completed": True,
            "name": "Test User",
            "age": 25,
            "city": "Moscow",
            "username": "testuser",
            "points": 100,
            "registration_date": "2024-01-01"
        }

        with patch("Commands.profile.is_guest_mode", return_value=False):
            with patch("Commands.profile.load_user_data"):
                await profile_command(update, context)

                # Should reply with profile text
                update.message.reply_text.assert_called_once()
                call_args = update.message.reply_text.call_args
                assert "Test User" in call_args[0][0]
                assert "100" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_profile_command_with_iss_play(self):
        """Test profile display with ISS Play linked."""
        from Commands.profile import profile_command

        update = AsyncMock()
        context = AsyncMock()

        update.effective_user.id = 123456
        context.user_data = {
            "setup_completed": True,
            "name": "Test User",
            "age": 25,
            "city": "Moscow",
            "username": "testuser",
            "points": 100,
            "iss_play_linked": True,
            "iss_play_nickname": "CoolGamer123"
        }

        with patch("Commands.profile.is_guest_mode", return_value=False):
            with patch("Commands.profile.load_user_data"):
                await profile_command(update, context)

                update.message.reply_text.assert_called_once()
                call_args = update.message.reply_text.call_args
                assert "CoolGamer123" in call_args[0][0]
