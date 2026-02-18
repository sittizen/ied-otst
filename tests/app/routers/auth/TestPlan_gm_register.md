# TestPlan for "def gm_register" @ "src/app/routers/auth.py"

Registers a new Game Master user account. Creates a User with normalized email, hashed password, display name, and GM account type. Handles duplicate email conflicts with 409 response. Tests focus on database integrity, error handling, and edge cases in user creation.

## used in:
- src/app/routers/auth.py (defined here, exposed as POST /api/gm/register endpoint)

## TST-001: happy path - successful GM registration
- [ ] Status: TODO
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

## TST-002: duplicate email - 409 conflict response
- [ ] Status: TODO
Test that attempting to register with an existing email raises HTTPException with status 409.
**required fixtures**
- Mock database session that raises IntegrityError on commit()
- Valid GMRegisterRequest with email="existing@test.com"
- Mock normalize_email and hash_password
**required asserts**
- db.commit() raises IntegrityError
- db.rollback() called once
- HTTPException raised with status_code=409 and detail="Email already exists"
- The IntegrityError is set as the __cause__ of the HTTPException

## TST-003: database rollback failure during duplicate handling
- [ ] Status: TODO
Test behavior when rollback() itself fails after IntegrityError, ensuring proper error propagation.
**required fixtures**
- Mock database session where commit() raises IntegrityError
- Mock database session where rollback() raises another exception (e.g., OperationalError)
- Valid GMRegisterRequest
**required asserts**
- Original IntegrityError from commit is not suppressed
- Rollback failure is handled (either chained or propagated)
- No partial database state left in inconsistent condition

## TST-004: email normalization edge cases
- [ ] Status: TODO
Test that email normalization handles various formats correctly before database check.
**required fixtures**
- Mock normalize_email that converts to lowercase and trims whitespace
- Test cases: "GM@Test.Com", "  gm@test.com  ", "GM+label@test.com"
- Mock database session
**required asserts**
- normalize_email called with str(payload.email)
- Email stored in database is the normalized version
- Duplicate check uses normalized email (case insensitive uniqueness)

## TST-005: database commit failure - non-integrity error
- [ ] Status: TODO
Test handling of database commit failures that are not IntegrityError (e.g., connection lost, timeout).
**required fixtures**
- Mock database session where commit() raises OperationalError or ConnectionError
- Valid GMRegisterRequest
**required asserts**
- Exception propagates without being caught (not an IntegrityError)
- No HTTPException with 409 status raised
- User can distinguish between "email exists" vs "system error"

## TST-006: concurrent registration race condition
- [ ] Status: TODO
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
