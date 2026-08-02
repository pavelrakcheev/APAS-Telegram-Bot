"""Unit tests for shared utilities."""

import pytest
import json
import os
from unittest.mock import patch, mock_open


class TestUsernameUtils:
    """Test username utility functions."""

    def test_is_username_available_new_username(self):
        """Test that new username is available."""
        from shared import is_username_available, users_data

        # Mock empty users_data
        with patch("shared.users_data", {}):
            result = is_username_available("newuser")
            assert result is True

    def test_is_username_available_existing_username(self):
        """Test that existing username is not available."""
        from shared import is_username_available

        mock_users = {
            "123456": {"username": "existinguser"}
        }
        with patch("shared.users_data", mock_users):
            result = is_username_available("existinguser")
            assert result is False

    def test_is_username_available_own_username(self):
        """Test that user can keep their own username."""
        from shared import is_username_available

        mock_users = {
            "123456": {"username": "myusername"}
        }
        with patch("shared.users_data", mock_users):
            result = is_username_available("myusername", current_user_id=123456)
            assert result is True

    def test_find_user_id_by_username_found(self):
        """Test finding user by username."""
        from shared import find_user_id_by_username

        mock_users = {
            "123456": {"username": "testuser"},
            "789012": {"username": "otheruser"}
        }
        with patch("shared.users_data", mock_users):
            result = find_user_id_by_username("testuser")
            assert result == "123456"

    def test_find_user_id_by_username_not_found(self):
        """Test finding non-existent user."""
        from shared import find_user_id_by_username

        mock_users = {
            "123456": {"username": "testuser"}
        }
        with patch("shared.users_data", mock_users):
            result = find_user_id_by_username("nonexistent")
            assert result is None


class TestAdminAccess:
    """Test admin access functions."""

    def test_check_admin_access_valid(self):
        """Test valid admin access."""
        from shared import check_admin_access

        with patch("shared.TELEGRAM_ID", "123456789"):
            result = check_admin_access(123456789, "correct_password")
            assert result is True

    def test_check_admin_access_wrong_user(self):
        """Test admin access with wrong user."""
        from shared import check_admin_access

        with patch("shared.TELEGRAM_ID", "123456789"):
            result = check_admin_access(999999999, "correct_password")
            assert result is False

    def test_check_admin_access_wrong_password(self):
        """Test admin access with wrong password."""
        from shared import check_admin_access

        with patch("shared.TELEGRAM_ID", "123456789"):
            with patch("shared.ADMIN_PASSWORD", "correct_password"):
                result = check_admin_access(123456789, "wrong_password")
                assert result is False


class TestUserData:
    """Test user data loading/saving."""

    def test_load_users_data_file_exists(self, tmp_path):
        """Test loading users data from existing file."""
        from shared import load_users_data

        test_data = {"123": {"name": "Test User"}}
        test_file = tmp_path / "users_data.json"
        test_file.write_text(json.dumps(test_data))

        with patch("shared.USERS_DATA_FILE", str(test_file)):
            result = load_users_data()
            assert result == test_data

    def test_load_users_data_file_not_exists(self, tmp_path):
        """Test loading users data when file doesn't exist."""
        from shared import load_users_data

        with patch("shared.USERS_DATA_FILE", str(tmp_path / "nonexistent.json")):
            result = load_users_data()
            assert result == {}

    def test_save_users_data(self, tmp_path):
        """Test saving users data."""
        from shared import save_users_data

        test_data = {"123": {"name": "Test User"}}
        test_file = tmp_path / "users_data.json"

        with patch("shared.USERS_DATA_FILE", str(test_file)):
            save_users_data(test_data)

            # Verify file was written
            assert test_file.exists()
            loaded = json.loads(test_file.read_text())
            assert loaded == test_data
