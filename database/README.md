# Database schema

MySQL 8.4, utf8mb4. Django migrations create and maintain all tables; no SQL bootstrap files. SQLite is supported **only for local automated tests**.

```mermaid
erDiagram
    User ||--o{ Card : owns
    User ||--o{ Transaction : initiates
    User ||--o{ AdminLog : acts
    Card |o--o{ Transaction : used_for
    User { bigint id PK
           string username UK
           string email UK
           string password_hash
           boolean is_staff
           boolean is_active }
    Card { bigint id PK
           bigint user_id FK
           string card_type
           string cardholder_name
           string card_brand
           string last_four
           smallint expiry_month
           smallint expiry_year }
    Transaction { bigint id PK
                  uuid reference UK
                  bigint user_id FK
                  bigint card_id FK_nullable
                  bigint original_card_id
                  string card_last_four
                  decimal amount
                  string currency
                  string status
                  string idempotency_key
                  datetime created_at
                  datetime updated_at }
    AdminLog { bigint id PK
               bigint admin_user_id FK
               string action
               string target_type
               string target_id
               json metadata
               datetime timestamp }
```

The custom `User` extends Django's built-in `AbstractUser` (not a parallel credentials table). `is_staff` defines the admin role, while only a superuser may grant staff access. Passwords are hashed by Django; refresh token blacklist, admin sessions and permissions use Django-managed auxiliary tables.

No PAN, CVV, PIN, or authentication data exists in any table. `masked_number` is computed on serialization from `last_four`; it is never a persisted field. A deleted card leaves `Transaction.card_id` null; `original_card_id` and `card_last_four` preserve a non-sensitive historical snapshot for idempotency and reports.

Indexes: unique `User.username`/`email`, `Transaction.reference`, `(user_id, idempotency_key)`; `Transaction.status`, `created_at`, `(user_id, created_at DESC)`, `(status, created_at)`; `AdminLog.timestamp`. Foreign-key indexes are created by Django. Amount is `DECIMAL(12,2)` and currency is presently USD only.

Migration: `docker compose exec django python manage.py migrate`. Back up: `docker compose exec -T mysql sh -c 'exec mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > backup.sql` (PowerShell redirection may alter encoding; for portable binary-safe output run from Bash or use your database backup tooling). Restore only in an isolated environment; dumps contain user PII and password hashes. Never commit dumps. Provision encrypted storage, retention and access controls for production backups.