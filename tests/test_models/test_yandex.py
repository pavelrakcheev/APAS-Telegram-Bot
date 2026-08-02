"""Unit tests for YandexGPT AI model integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestYandexModels:
    """Test YandexGPT model configurations."""

    def test_yandex_models_dict_structure(self):
        """Test that YANDEX_MODELS has expected structure."""
        from Models.yandex import YANDEX_MODELS

        assert isinstance(YANDEX_MODELS, dict)
        assert len(YANDEX_MODELS) > 0

        for model_key, model_config in YANDEX_MODELS.items():
            assert "name" in model_config
            assert "description" in model_config
            assert "provider" in model_config
            assert "model_uri" in model_config
            assert "category" in model_config
            assert model_config["provider"] == "yandex"

    def test_yandex_models_have_unique_uris(self):
        """Test that all Yandex model URIs are unique."""
        from Models.yandex import YANDEX_MODELS

        model_uris = [m["model_uri"] for m in YANDEX_MODELS.values()]
        assert len(model_uris) == len(set(model_uris))


class TestYandexResponse:
    """Test YandexGPT response generation."""

    @pytest.mark.asyncio
    async def test_generate_yandex_response_success(self, mock_yandex_response):
        """Test successful YandexGPT response generation."""
        from Models.yandex import generate_yandex_response

        with patch("Models.yandex.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_yandex_response
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            model_config = {
                "name": "Test Yandex Model",
                "model_uri": "gpt://test/yandexgpt/latest",
                "provider": "yandex"
            }

            result = await generate_yandex_response(
                model_config=model_config,
                system_prompt="You are a test assistant",
                user_message="Hello"
            )

            assert result == "Test Yandex response"

    @pytest.mark.asyncio
    async def test_generate_yandex_response_error(self):
        """Test YandexGPT response generation with error."""
        from Models.yandex import generate_yandex_response

        with patch("Models.yandex.requests.post") as mock_post:
            mock_post.side_effect = Exception("API Error")

            model_config = {
                "name": "Test Yandex Model",
                "model_uri": "gpt://test/yandexgpt/latest",
                "provider": "yandex"
            }

            with pytest.raises(Exception) as exc_info:
                await generate_yandex_response(
                    model_config=model_config,
                    system_prompt="You are a test assistant",
                    user_message="Hello"
                )

            assert "Error with Test Yandex Model" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_yandex_response_http_error(self):
        """Test YandexGPT response generation with HTTP error."""
        from Models.yandex import generate_yandex_response

        with patch("Models.yandex.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 400")
            mock_post.return_value = mock_response

            model_config = {
                "name": "Test Yandex Model",
                "model_uri": "gpt://test/yandexgpt/latest",
                "provider": "yandex"
            }

            with pytest.raises(Exception) as exc_info:
                await generate_yandex_response(
                    model_config=model_config,
                    system_prompt="You are a test assistant",
                    user_message="Hello"
                )

            assert "Error with Test Yandex Model" in str(exc_info.value)
