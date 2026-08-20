# Authentication and role-based access control

Week 3 note (Rishikesh) on the auth implementation in `backend/app/core/security.py`,
`backend/app/dependencies.py`, and `backend/app/routers/auth.py`. Matches the approach
already documented in [architecture.md](architecture.md)'s "Open decisions" /
`research-evaluation.md` era notes: JWT via `bcrypt` + `PyJWT`, not `passlib` or
server-side sessions.

## Token flow

1. `POST /auth/register` — End User self-registration only (email, full name,
   password). Department Engineer and Admin accounts are not self-service — see
   "Demo accounts" below.
2. `POST /auth/login` — OAuth2 password grant (`username`/`password` form fields,
   `username` holds the email). Returns a JWT (`sub` = user id, `role` = the user's
   role, 60-minute expiry by default).
3. Protected endpoints take `Authorization: Bearer <token>`. `get_current_user`
   (`app/dependencies.py`) decodes the token, loads the user from the database, and
   rejects inactive/missing users with 401.

Passwords are hashed with `bcrypt` directly (not `passlib`, which has an unresolved
bcrypt-backend maintenance issue). Tokens are stateless JWTs — no session store, no
Redis, consistent with the project's [scope exclusions](../README.md#scope).

## Role-based access control

Three roles: `end_user`, `department_engineer`, `admin` (matching the `ck_users_role`
constraint on `users.role`). Enforcement happens two ways:

- **`require_role(*roles)`** (`app/dependencies.py`) — a hard gate for endpoints that
  only some roles should reach at all. Not yet used by any Week 3 endpoint (ticket
  create/list/detail are open to any authenticated role, scoped by visibility instead —
  see below), but available for Week 4+ endpoints that are role-exclusive (e.g. admin
  user management).
- **Row-level visibility scoping** (`app/routers/tickets.py`) — `GET /tickets` and
  `GET /tickets/{id}` don't hide the endpoint by role, they filter *which rows* a role
  can see: End User sees only tickets they submitted, Department Engineer sees only
  tickets in their own department, Admin sees everything. This matches
  `docs/wireframes.md`'s per-role screens more directly than an all-or-nothing route
  gate would.

## Demo accounts

Since Department Engineer and Admin can't self-register, `backend/app/scripts/
seed_demo_users.py` creates one account per role for local development and the Week 3
mentor demo (`uv run python -m app.scripts.seed_demo_users`, run against a live `db`):

| Role | Email | Password |
|---|---|---|
| End User | `customer@demo.local` | `Demo@123` |
| Department Engineer | `engineer@demo.local` (Networking) | `Demo@123` |
| Admin | `admin@demo.local` | `Demo@123` |

Never use these credentials outside local development.

## What's not done yet

- No password reset / email verification flow.
- No refresh tokens — a token simply expires after 60 minutes and the user logs in
  again; acceptable for a capstone demo, not production-grade.
- `require_role` isn't exercised by any endpoint yet, only unit-testable in isolation —
  the first real use will likely be Week 4+ admin endpoints.
