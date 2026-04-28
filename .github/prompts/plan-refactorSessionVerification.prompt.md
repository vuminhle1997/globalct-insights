# Plan: Refactor Duplicated Redis Session Verification

**TL;DR**: Create an async dependency in `dependencies.py` that extracts and returns both `user_id` and `claims` from Redis/JWT, then replace all 6 duplicated instances across the API routes with a simple dependency injection. This will also require converting affected route handlers to `async`.

## Steps

1. **Create new async dependency** in `backend/dependencies.py` — add an `async` function `get_session_claims()` that:
   - Extracts `session_id` from request cookies
   - Fetches token from Redis using the session key
   - Decodes JWT with `decode_jwt()`
   - Returns a tuple of `(user_id, claims)` with proper type hints
   - Uses `HTTPException(status_code=401)` for all auth failures
   - Logs all errors consistently

2. **Update `backend/routers/api/avatar.py`** — replace lines 32-38 in `get_avatar_of_chat()`:
   - Convert function to `async`
   - Replace session verification block with: `user_id, claims = Depends(get_session_claims)`
   - Simplify the verification logic

3. **Update `backend/routers/api/favourites.py`** — replace 3 functions (lines 102-108, 145-160, and the POST handler):
   - Convert functions to `async`
   - Replace session verification blocks with dependency injection
   - Remove redundant user_id extraction

4. **Update `backend/routers/api/messages.py`** — lines 72-78 in `get_messages_by_chat_id()`:
   - Convert function to `async`
   - Replace session verification block with dependency injection

5. **Update `backend/routers/api/chats.py`** — 3 instances (lines 321-327, 356-362, 872-879):
   - Convert affected functions to `async`: `get_all_chats()`, `get_chats_by_title()`, `create_chat()`
   - Replace each session verification block with dependency injection

6. **Update `backend/routers/api/models.py`** — align to standard pattern:
   - Convert `get_models()` to `async`
   - Replace inline Redis call (lines 38-40) with dependency injection
   - Ensure proper JWT decoding is used

7. **Verification**:
   - Run all existing tests to ensure no regressions: `pytest backend/tests/`
   - Manually verify session flows work for each endpoint (login → create chat → get messages → get favourites)
   - Check error responses return `401` status instead of `404`
   - Validate JWT claims are properly decoded and `user_id` is correctly extracted

## Relevant Files
- `backend/dependencies.py` — add new `get_session_claims()` dependency
- `backend/routers/api/avatar.py` — refactor session verification, make async
- `backend/routers/api/favourites.py` — refactor session verification (3 functions), make async
- `backend/routers/api/messages.py` — refactor session verification, make async
- `backend/routers/api/chats.py` — refactor session verification (3 functions), make async
- `backend/routers/api/models.py` — align to standard pattern, make async

## Decisions
- Return `(user_id, claims)` tuple instead of just `user_id` to provide flexibility for routes that need additional claim data
- Use `async` dependency to properly support async route handlers (prerequisite for modern FastAPI patterns)
- Standardize on `401 Unauthorized` for all authentication failures (more semantically correct than `404`)
- Keep consistent logging with `logger.error()` and `logger.warning()` for all failures

## Current State of Duplication
- **6 instances** of session verification code across API routes
- **1 variation** in models.py that skips JWT decoding
- **Existing dependency** in dependencies.py but it only returns session_id, not claims/user_id

## Pattern Details
All instances follow this structure:
```python
session_id = request.cookies.get("session_id")
if not session_id:
    logger.error(f"No session_id cookie found")
    raise HTTPException(status_code=404, detail="Session not found")

token = redis_client.get(f"session:{session_id}")
claims = decode_jwt(token)
user_id = claims["oid"]
```

Location breakdown:
- `backend/routers/api/avatar.py` (line 32-38) - `get_avatar_of_chat()`
- `backend/routers/api/favourites.py` (line 102-108) - `get_favourites_of_user()`
- `backend/routers/api/messages.py` (line 72-78) - `get_messages_by_chat_id()`
- `backend/routers/api/chats.py` (line 321-327) - `get_all_chats()`
- `backend/routers/api/chats.py` (line 356-362) - `get_chats_by_title()`
- `backend/routers/api/chats.py` (line 872-879) - `create_chat()`
- `backend/routers/api/models.py` (line 38-40) - `get_models()` (variation)

## Further Considerations
1. The existing `verify_session()` in dependencies.py can be deprecated or enhanced — should it be removed or kept for backward compatibility? (Recommendation: keep it but add a note it's legacy)
2. Consider adding request/response validation tests to ensure the new dependency works correctly across different scenarios
