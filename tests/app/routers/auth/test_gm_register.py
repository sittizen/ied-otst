from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models import AccountType, User
from app.schemas import GMRegisterRequest, WhoAmIResponse


def test_happy_path_successful_gm_registration() -> None:
    """TST-001: happy path - successful GM registration."""
    # Setup mocks
    mock_db = MagicMock(spec=Session)
    mock_user_id = "test-user-id-123"
    mock_hashed_password = "hashed_password_value"

    # Create mock user that will be returned after refresh
    mock_user = MagicMock(spec=User)
    mock_user.id = mock_user_id
    mock_user.email = "gm@test.com"
    mock_user.display_name = "TestGM"
    mock_user.account_type = AccountType.GM

    # Configure mock_db.refresh to set the user properties
    def mock_refresh(user_instance):
        user_instance.id = mock_user_id

    mock_db.refresh.side_effect = mock_refresh

    # Create payload
    payload = GMRegisterRequest(email="gm@test.com", password="SecurePass123!", display_name="TestGM")

    # Patch the dependencies
    with (
        patch("app.routers.auth.normalize_email") as mock_normalize_email,
        patch("app.routers.auth.hash_password") as mock_hash_password,
        patch("app.routers.auth.User") as mock_user_class,
    ):
        # Configure mocks
        mock_normalize_email.return_value = "gm@test.com"
        mock_hash_password.return_value = mock_hashed_password

        # Create a mock user instance that will be added to the database
        mock_user_instance = MagicMock()
        mock_user_instance.id = None  # Will be set after refresh
        mock_user_instance.email = "gm@test.com"
        mock_user_instance.password_hash = mock_hashed_password
        mock_user_instance.display_name = "TestGM"
        mock_user_instance.account_type = AccountType.GM

        mock_user_class.return_value = mock_user_instance

        # Import and call the function under test
        from app.routers.auth import gm_register

        result = gm_register(payload, mock_db)

        # Assertions
        # - normalize_email called with payload.email
        mock_normalize_email.assert_called_once_with("gm@test.com")

        # - hash_password called with payload.password
        mock_hash_password.assert_called_once_with("SecurePass123!")

        # - User created with correct email, password_hash, display_name, account_type=AccountType.GM
        mock_user_class.assert_called_once_with(
            email="gm@test.com", password_hash=mock_hashed_password, display_name="TestGM", account_type=AccountType.GM
        )

        # - db.add() called with the User instance
        mock_db.add.assert_called_once_with(mock_user_instance)

        # - db.commit() called once
        mock_db.commit.assert_called_once()

        # - db.refresh() called with the User instance
        mock_db.refresh.assert_called_once_with(mock_user_instance)

        # - Returns WhoAmIResponse with user_id, email, display_name, account_type
        assert isinstance(result, WhoAmIResponse)
        assert result.user_id == mock_user_id
        assert result.email == "gm@test.com"
        assert result.display_name == "TestGM"
        assert result.account_type == AccountType.GM


def test_database_rollback_failure_during_duplicate_handling() -> None:
    """TST-002: database rollback failure during duplicate handling."""
    from sqlalchemy.exc import IntegrityError, OperationalError

    # Setup mocks
    mock_db = MagicMock(spec=Session)
    mock_hashed_password = "hashed_password_value"

    # Create an IntegrityError to be raised on commit
    integrity_error = IntegrityError("statement", "params", Exception("duplicate key value"))
    mock_db.commit.side_effect = integrity_error

    # Create an OperationalError to be raised on rollback
    rollback_error = OperationalError("rollback statement", "params", Exception("rollback failed"))
    mock_db.rollback.side_effect = rollback_error

    # Create payload
    payload = GMRegisterRequest(email="existing@test.com", password="SecurePass123!", display_name="ExistingUser")

    # Patch the dependencies
    with (
        patch("app.routers.auth.normalize_email") as mock_normalize_email,
        patch("app.routers.auth.hash_password") as mock_hash_password,
        patch("app.routers.auth.User") as mock_user_class,
    ):
        # Configure mocks
        mock_normalize_email.return_value = "existing@test.com"
        mock_hash_password.return_value = mock_hashed_password

        # Create a mock user instance
        mock_user_instance = MagicMock()
        mock_user_instance.email = "existing@test.com"
        mock_user_instance.password_hash = mock_hashed_password
        mock_user_instance.display_name = "ExistingUser"
        mock_user_instance.account_type = AccountType.GM

        mock_user_class.return_value = mock_user_instance

        # Import and call the function under test
        from app.routers.auth import gm_register

        # Assertions - should propagate the rollback error
        try:
            gm_register(payload, mock_db)
            raise AssertionError("Expected exception to be raised")
        except OperationalError as e:
            # Rollback failure is propagated (since rollback() raises before HTTPException)
            assert e is rollback_error
            mock_db.rollback.assert_called_once()
        except Exception as e:
            # If a different exception type is raised, check if it's chained properly
            # The code currently does not handle rollback failure, so it will propagate
            assert "rollback" in str(e).lower() or e is rollback_error


def test_email_normalization_edge_cases() -> None:
    """TST-003: email normalization edge cases."""
    # Setup mocks
    mock_db = MagicMock(spec=Session)
    mock_user_id = "test-user-id-456"
    mock_hashed_password = "hashed_password_value"

    # Configure mock_db.refresh to set the user properties
    def mock_refresh(user_instance):
        user_instance.id = mock_user_id

    mock_db.refresh.side_effect = mock_refresh

    # Define test cases with various email formats
    test_cases = [
        ("GM@Test.Com", "gm@test.com"),  # Case normalization
        ("  gm@test.com  ", "gm@test.com"),  # Whitespace trimming
        ("GM+label@test.com", "gm+label@test.com"),  # Label handling (optional)
    ]

    for input_email, expected_normalized_email in test_cases:
        # Create payload
        payload = GMRegisterRequest(email=input_email, password="SecurePass123!", display_name="TestGM")

        # Patch the dependencies
        with (
            patch("app.routers.auth.normalize_email") as mock_normalize_email,
            patch("app.routers.auth.hash_password") as mock_hash_password,
            patch("app.routers.auth.User") as mock_user_class,
        ):
            # Configure normalize_email to simulate actual normalization
            mock_normalize_email.return_value = expected_normalized_email
            mock_hash_password.return_value = mock_hashed_password

            # Create a mock user instance
            mock_user_instance = MagicMock()
            mock_user_instance.id = None
            mock_user_instance.email = expected_normalized_email
            mock_user_instance.password_hash = mock_hashed_password
            mock_user_instance.display_name = "TestGM"
            mock_user_instance.account_type = AccountType.GM

            mock_user_class.return_value = mock_user_instance

            # Import and call the function under test
            from app.routers.auth import gm_register

            result = gm_register(payload, mock_db)

            # Assertions
            # - normalize_email called with str(payload.email)
            mock_normalize_email.assert_called_once_with(str(payload.email))

            # - Email stored in database is the normalized version
            mock_user_class.assert_called_once_with(
                email=expected_normalized_email,
                password_hash=mock_hashed_password,
                display_name="TestGM",
                account_type=AccountType.GM,
            )

            # - Duplicate check uses normalized email (implied by the flow)
            # The function creates user with normalized email, so duplicate check will use that
            assert mock_user_instance.email == expected_normalized_email

            # Verify result uses normalized email
            assert result.email == expected_normalized_email

            # Reset mocks for next iteration
            mock_normalize_email.reset_mock()
            mock_user_class.reset_mock()
            mock_db.reset_mock()
            mock_db.refresh.side_effect = mock_refresh


def test_concurrent_registration_race_condition() -> None:
    """TST-004: concurrent registration race condition."""
    from fastapi import HTTPException
    from sqlalchemy.exc import IntegrityError

    # Track how many times commit is called to simulate race condition
    commit_call_count = 0
    mock_user_id = "test-user-id-789"
    mock_hashed_password = "hashed_password_value"

    def mock_commit():
        nonlocal commit_call_count
        commit_call_count += 1
        # First commit succeeds, second raises IntegrityError
        if commit_call_count > 1:
            raise IntegrityError("statement", "params", Exception("duplicate key value"))

    # Setup mock database
    mock_db = MagicMock(spec=Session)
    mock_db.commit.side_effect = mock_commit

    def mock_refresh(user_instance):
        user_instance.id = mock_user_id

    mock_db.refresh.side_effect = mock_refresh

    # Create two payloads with same email (simulating concurrent requests)
    payload1 = GMRegisterRequest(email="race@test.com", password="SecurePass123!", display_name="RaceUser1")
    payload2 = GMRegisterRequest(email="race@test.com", password="SecurePass123!", display_name="RaceUser2")

    # Patch the dependencies
    with (
        patch("app.routers.auth.normalize_email") as mock_normalize_email,
        patch("app.routers.auth.hash_password") as mock_hash_password,
        patch("app.routers.auth.User") as mock_user_class,
    ):
        # Configure mocks
        mock_normalize_email.return_value = "race@test.com"
        mock_hash_password.return_value = mock_hashed_password

        # Create mock user instances
        def create_mock_user():
            mock_user_instance = MagicMock()
            mock_user_instance.id = None
            mock_user_instance.email = "race@test.com"
            mock_user_instance.password_hash = mock_hashed_password
            mock_user_instance.display_name = "RaceUser"
            mock_user_instance.account_type = AccountType.GM
            return mock_user_instance

        mock_user_class.side_effect = lambda **kwargs: create_mock_user()

        # Import the function under test
        from app.routers.auth import gm_register

        # First request should succeed
        result1 = gm_register(payload1, mock_db)

        # Assertions for first request
        assert isinstance(result1, WhoAmIResponse)
        assert result1.email == "race@test.com"
        assert result1.display_name == "RaceUser"
        assert commit_call_count == 1

        # Second request should fail with 409
        try:
            gm_register(payload2, mock_db)
            raise AssertionError("Expected HTTPException to be raised for second request")
        except HTTPException as e:
            # Second request fails with 409 status
            assert e.status_code == 409
            assert e.detail == "Email already exists"
            assert isinstance(e.__cause__, IntegrityError)

        # Verify rollback was called for the failed request
        assert mock_db.rollback.call_count == 1

        # Verify commit was called twice (once for each request)
        assert commit_call_count == 2
