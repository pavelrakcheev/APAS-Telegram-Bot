"""Unit tests for Groq AI model integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestGroqModels:
    """Test Groq model configurations."""

    def test_groq_models_dict_structure(self):
        """Test that GROQ_MODELS has expected structure."""
        from Models.groq import GROQ_MODELS

        assert isinstance(GROQ_MODELS, dict)
        assert len(GROQ_MODELS) > 0

        for model_key, model_config in GROQ_MODELS.items():
            assert "name" in model_config
            assert "description" in model_config
            assert "provider" in model_config
            assert "model_id" in model_config
            assert "category" in model_config
            assert model_config["provider"] == "groq"

    def test_groq_models_have_unique_ids(self):
        """Test that all Groq model IDs are unique."""
        from Models.groq import GROQ_MODELS

        model_ids = [m["model_id"] for m in GROQ_MODELS.values()]
        assert len(model_ids) == len(set(model_ids))

    def test_get_available_groq_models(self):
        """Test get_available_groq_models returns all models."""
        from Models.groq import get_available_groq_models, GROQ_MODELS

        result = get_available_groq_models()
        assert result == GROQ_MODELS


class TestGroqResponse:
    """Test Groq response generation."""

    @pytest.mark.asyncio
    async def test_generate_groq_response_success(self, mock_groq_response):
        """Test successful Groq response generation."""
        from Models.groq import generate_groq_response

        with patch("Models.groq.get_groq_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_groq_response

            model_config = {
                "name": "Test Model",
                "model_id": "test-model",
                "provider": "groq"
            }

            result = await generate_groq_response(
                model_config=model_config,
                system_prompt="You are a test assistant",
                user_message="Hello",
                streaming_enabled=False
            )

            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_generate_groq_response_error(self):
        """Test Groq response generation with error."""
        from Models.groq import generate_groq_response

        with patch("Models.groq.get_groq_client") as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("API Error")

            model_config = {
                "name": "Test Model",
                "model_id": "test-model",
                "provider": "groq"
            }

            with pytest.raises(Exception) as exc_info:
                await generate_groq_response(
                    model_config=model_config,
                    system_prompt="You are a test assistant",
                    user_message="Hello",
                    streaming_enabled=False
                )

            assert "Error with Test Model" in str(exc_info.value)
