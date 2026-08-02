"""Unit tests for models command."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from telegram import Update, User, Message, Chat


class TestModelsCommand:
    """Test /models command."""

    @pytest.mark.asyncio
    async def test_models_command_guest_mode(self):
        """Test models command blocks guest users."""
        from Commands.models import models_command

        update = AsyncMock()
        context = AsyncMock()

        update.effective_user.id = 123456
        context.user_data = {"is_guest": True}

        with patch("Commands.models.load_user_data", return_value=context.user_data):
            with patch("Commands.models.is_guest_mode", return_value=True):
                await models_command(update, context)

                update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_models_command_success(self):
        """Test successful models display."""
        from Commands.models import models_command, MODELS, DEFAULT_MODEL

        update = AsyncMock()
        context = AsyncMock()

        update.effective_user.id = 123456
        context.user_data = {
            "setup_completed": True,
            "selected_model": DEFAULT_MODEL
        }

        with patch("Commands.models.load_user_data", return_value=context.user_data):
            with patch("Commands.models.is_guest_mode", return_value=False):
                await models_command(update, context)

                update.message.reply_text.assert_called_once()
                call_args = update.message.reply_text.call_args
                # Should mention current model
                assert "Groq" in call_args[0][0] or "GPT" in call_args[0][0]


class TestModelsCallback:
    """Test models callback handling."""

    @pytest.mark.asyncio
    async def test_handle_models_callback_groq(self):
        """Test Groq provider callback."""
        from Commands.models import handle_models_callback

        update = AsyncMock()
        context = AsyncMock()

        update.callback_query.from_user.id = 123456
        update.callback_query.data = "models_provider_groq"
        context.user_data = {"selected_model": "groq_gpt_oss_120b"}

        with patch("Commands.models.load_user_data", return_value=context.user_data):
            with patch("Commands.models.MODELS", {"groq_gpt_oss_120b": {"name": "GPT OSS 120B"}}):
                await handle_models_callback(update, context)

                update.callback_query.answer.assert_called_once()
                update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_models_callback_google(self):
        """Test Google provider callback."""
        from Commands.models import handle_models_callback

        update = AsyncMock()
        context = AsyncMock()

        update.callback_query.from_user.id = 123456
        update.callback_query.data = "models_provider_google"
        context.user_data = {"selected_model": "groq_gpt_oss_120b"}

        with patch("Commands.models.load_user_data", return_value=context.user_data):
            with patch("Commands.models.MODELS", {"groq_gpt_oss_120b": {"name": "GPT OSS 120B"}}):
                await handle_models_callback(update, context)

                update.callback_query.answer.assert_called_once()
                update.callback_query.edit_message_text.assert_called_once()


class TestModelsStructure:
    """Test MODELS dictionary structure."""

    def test_models_dict_not_empty(self):
        """Test that MODELS dict is populated."""
        from Commands.models import MODELS

        assert len(MODELS) > 0

    def test_models_have_required_fields(self):
        """Test that all models have required fields."""
        from Commands.models import MODELS

        for key, model in MODELS.items():
            assert "name" in model
            assert "provider" in model
            assert "model_id" in model or "model_uri" in model

    def test_default_model_exists(self):
        """Test that default model exists in MODELS."""
        from Commands.models import MODELS, DEFAULT_MODEL

        assert DEFAULT_MODEL in MODELS
