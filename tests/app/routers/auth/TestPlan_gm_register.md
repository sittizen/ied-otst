# TestPlan for "def gm_register" @ "src/app/routers/auth.py"

Registers a new Game Master user account. Creates a User with normalized email, hashed password, display name, and GM account type. Handles duplicate email conflicts with 409 response. Tests focus on database integrity, error handling, and edge cases in user creation.

## used in:
- src/app/routers/auth.py (defined here, exposed as POST /api/gm/register endpoint)

## TST-001: happy path - successful GM registration
- [x] Status: DONE
Test the expected path when valid registration data is provided and database operations succeed.
**required fixtures**
- Mock database session (Session) with working add(), commit(), refresh() methods
- Valid GMRegisterRequest with email="gm@test.com", password="SecurePass123!", display_name="TestGM"
- Mock normalize_email returning "gm@test.com"
- Mock hash_password returning a hashed value
- Mock User model and WhoAmIResponse
**required asserts**
- normalize_email called with payload.email
- hash_password called with payload.password
- User created with correct email, password_hash, display_name, account_type=AccountType.GM
- db.add() called with the User instance
- db.commit() called once
- db.refresh() called with the User instance
- Returns WhoAmIResponse with user_id, email, display_name, account_type

## TST-002: database rollback failure during duplicate handling
- [x] Status: DONE
Test behavior when rollback() itself fails after IntegrityError, ensuring proper error propagation.
**required fixtures**
- Mock database session where commit() raises IntegrityError
- Mock database session where rollback() raises another exception (e.g., OperationalError)
- Valid GMRegisterRequest
**required asserts**
- Original IntegrityError from commit is not suppressed
- Rollback failure is handled (either chained or propagated)
- No partial database state left in inconsistent condition

## TST-003: email normalization edge cases
- [x] Status: DONE
Test that email normalization handles various formats correctly before database check.
**required fixtures**
- Mock normalize_email that converts to lowercase and trims whitespace
- Test cases: "GM@Test.Com", "  gm@test.com  ", "GM+label@test.com"
- Mock database session
**required asserts**
- normalize_email called with str(payload.email)
- Email stored in database is the normalized version
- Duplicate check uses normalized email (case insensitive uniqueness)

## TST-004: concurrent registration race condition
- [x] Status: DONE
Test behavior when two simultaneous requests attempt to register the same email.
**required fixtures**
- Mock database that simulates race condition (first commit succeeds, second raises IntegrityError)
- Two concurrent GMRegisterRequest with same email
- Mock normalize_email returning same value for both
**required asserts**
- First request succeeds with 201 status
- Second request fails with 409 status
- Only one User record created in database
- No partial or duplicate records exist
