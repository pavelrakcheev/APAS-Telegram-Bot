"""Unit tests for points command."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from telegram import Update, User, Message, Chat


class TestPointsTransactions:
    """Test points transactions loading/saving."""

    def test_load_points_transactions_file_exists(self, tmp_path):
        """Test loading points transactions from existing file."""
        from Commands.points import load_points_transactions

        test_data = {"123": [{"timestamp": 1234567890, "amount": 10}]}
        test_file = tmp_path / "points_transactions.json"
        test_file.write_text(json.dumps(test_data))

        with patch("Commands.points.POINTS_TRANSACTIONS_FILE", str(test_file)):
            result = load_points_transactions()
            assert result == test_data

    def test_load_points_transactions_file_not_exists(self, tmp_path):
        """Test loading points transactions when file doesn't exist."""
        from Commands.points import load_points_transactions

        with patch("Commands.points.POINTS_TRANSACTIONS_FILE", str(tmp_path / "nonexistent.json")):
            result = load_points_transactions()
            assert result == {}

    def test_save_points_transactions(self, tmp_path):
        """Test saving points transactions."""
        from Commands.points import save_points_transactions

        test_data = {"123": [{"timestamp": 1234567890, "amount": 10}]}
        test_file = tmp_path / "points_transactions.json"

        with patch("Commands.points.POINTS_TRANSACTIONS_FILE", str(test_file)):
            save_points_transactions(test_data)

            assert test_file.exists()
            loaded = json.loads(test_file.read_text())
            assert loaded == test_data


class TestPointsCommand:
    """Test /points command."""

    @pytest.mark.asyncio
    async def test_points_command_guest_mode(self):
        """Test points command blocks guest users."""
        from Commands.points import points_command

        update = AsyncMock()
        context = AsyncMock()

        update.effective_user.id = 123456
        context.user_data = {"is_guest": True}

        with patch("Commands.points.load_user_data"):
            with patch("Commands.points.is_guest_mode", return_value=True):
                await points_command(update, context)

                # Should send restricted message
                update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_points_command_success(self):
        """Test successful points display."""
        from Commands.points import points_command

        update = AsyncMock()
        context = AsyncMock()

        update.effective_user.id = 123456
        context.user_data = {
            "setup_completed": True,
            "points": 150
        }

        with patch("Commands.points.load_user_data"):
            with patch("Commands.points.is_guest_mode", return_value=False):
                await points_command(update, context)

                update.message.reply_text.assert_called_once()
                call_args = update.message.reply_text.call_args
                assert "150" in call_args[0][0]
