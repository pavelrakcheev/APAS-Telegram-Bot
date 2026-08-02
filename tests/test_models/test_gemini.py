"""Unit tests for Gemini AI model integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestGeminiModels:
    """Test Gemini model configurations."""

    def test_gemini_models_dict_structure(self):
        """Test that GEMINI_MODELS has expected structure."""
        from Models.gemini import GEMINI_MODELS

        assert isinstance(GEMINI_MODELS, dict)
        assert len(GEMINI_MODELS) > 0

        for model_key, model_config in GEMINI_MODELS.items():
            assert "name" in model_config
            assert "description" in model_config
            assert "provider" in model_config
            assert "model_id" in model_config
            assert "category" in model_config
            assert model_config["provider"] == "gemini"

    def test_gemini_models_have_unique_ids(self):
        """Test that all Gemini model IDs are unique."""
        from Models.gemini import GEMINI_MODELS

        model_ids = [m["model_id"] for m in GEMINI_MODELS.values()]
        assert len(model_ids) == len(set(model_ids))

    def test_get_available_gemini_models(self):
        """Test get_available_gemini_models returns all models."""
        from Models.gemini import get_available_gemini_models, GEMINI_MODELS

        result = get_available_gemini_models()
        assert result == GEMINI_MODELS


class TestGeminiResponse:
    """Test Gemini response generation."""

    @pytest.mark.asyncio
    async def test_generate_gemini_response_success(self, mock_gemini_response):
        """Test successful Gemini response generation."""
        from Models.gemini import generate_gemini_response

        with patch("Models.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_chat = MagicMock()
            mock_chat.send_message.return_value = mock_gemini_response
            mock_model.start_chat.return_value = mock_chat
            mock_genai.GenerativeModel.return_value = mock_model

            model_config = {
                "name": "Test Gemini Model",
                "model_id": "test-model",
                "provider": "gemini"
            }

            result = await generate_gemini_response(
                model_config=model_config,
                system_prompt="You are a test assistant",
                user_message="Hello"
            )

            assert result == "Test Gemini response"

    @pytest.mark.asyncio
    async def test_generate_gemini_response_error(self):
        """Test Gemini response generation with error."""
        from Models.gemini import generate_gemini_response

        with patch("Models.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_chat = MagicMock()
            mock_chat.send_message.side_effect = Exception("API Error")
            mock_model.start_chat.return_value = mock_chat
            mock_genai.GenerativeModel.return_value = mock_model

            model_config = {
                "name": "Test Gemini Model",
                "model_id": "test-model",
                "provider": "gemini"
            }

            with pytest.raises(Exception) as exc_info:
                await generate_gemini_response(
                    model_config=model_config,
                    system_prompt="You are a test assistant",
                    user_message="Hello"
                )

            assert "Error with Test Gemini Model" in str(exc_info.value)
