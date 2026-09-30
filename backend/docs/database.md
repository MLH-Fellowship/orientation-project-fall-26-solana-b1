# User model (#6)

`users` contains a UUID string primary key (`id`), required unique `email`,
and `created_at`, using the existing Python UTC timestamp default convention.
Email format validation and normalization belong to the auth layer; the unique
constraint alone does not guarantee case-insensitive email uniqueness.

`conversations.user_id` is a nullable foreign key to `users.id`. Existing API
requests continue to create unowned conversations. SQLAlchemy exposes ownership
through `Conversation.user` and `User.conversations`. No password or auth
endpoints are included.

## Existing SQLite databases

Fresh databases receive the schema through normal application startup.
`create_all()` does not alter existing tables. Stop the backend and back up the
SQLite database before upgrading. From `backend/`, with backend dependencies
installed and the usual `DATABASE_URL` or `.env` configuration, run:

```bash
python -m scripts.upgrade_user_model
```

The upgrade creates `users` and adds nullable `conversations.user_id`, preserving
conversation and message rows. It can be rerun. It targets the original scaffold
schema; it does not repair a pre-existing, incompatible `users` table. For rollback,
restore the pre-upgrade backup before restarting the old application. Other
database engines require a corresponding migration.

## Deletion and enforcement

No destructive cascade from users to conversations is configured. With normal
ORM `Session.delete(user)`, SQLAlchemy clears associated conversations' `user_id`.
The user foreign key has no database `ON DELETE` action. The existing
conversation-to-message ORM `all, delete-orphan` cascade is unchanged.

SQLite foreign-key enforcement is not enabled by the current application engine;
declaring a foreign key alone does not enable it. Tests explicitly enable it when
checking referential integrity. Database-wide enforcement and the detailed
ORM/direct-SQL deletion review, along with both ownership indexes, remain for #10.
