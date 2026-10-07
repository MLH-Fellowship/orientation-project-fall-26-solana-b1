# User model

`users` contains a UUID string primary key (`id`), required unique `email`,
and `created_at`, using the existing Python UTC timestamp default convention.
Email format validation and normalization belong to the auth layer; the unique
constraint alone does not guarantee case-insensitive email uniqueness.

`conversations.user_id` is a nullable foreign key to `users.id`. Existing API
requests continue to create unowned conversations. SQLAlchemy exposes ownership
through `Conversation.user` and `User.conversations`. No password or auth
endpoints are included.

## Schema migrations

Fresh and existing databases use Alembic; application startup does not create
tables. Stop the backend and back up the database before upgrading.
From `backend/`, with backend dependencies
installed and the usual `DATABASE_URL` or `.env` configuration, run:

```bash
alembic upgrade head
```

The user-model revision follows `20260929_0001`, creates `users`, and adds
nullable `conversations.user_id` with its foreign key and index. Existing
conversation and message rows are preserved. Alembic tracks applied revisions,
so rerunning the command does not apply them again.

For a database created by the original scaffold without Alembic history, first
verify that it matches the initial conversations/messages schema, then run
`alembic stamp 20260929_0001` before upgrading. Do not stamp a fresh database or
one already modified by the retired manual upgrade script.

To revert the user-model revision, run `alembic downgrade 20260929_0001`.
This removes users and ownership data while retaining conversations and messages.
SQLite table changes use Alembic batch operations.

## Deletion and enforcement

No destructive cascade from users to conversations is configured. With normal
ORM `Session.delete(user)`, SQLAlchemy clears associated conversations' `user_id`.
The user foreign key has no database `ON DELETE` action. The existing
conversation-to-message ORM `all, delete-orphan` cascade is unchanged.

SQLite foreign-key enforcement is enabled on every application connection.
Direct SQL deletion of a user with owned conversations is rejected; ORM deletion
clears ownership first. Deleting a conversation directly cascades to its messages.

Alembic disables enforcement only on its separate SQLite migration connection
because batch table rebuilds would otherwise trigger cascading message deletion.
It checks foreign-key integrity before and after migrations, using a transaction
that rolls back schema and data changes on failure.

Before deploying to an existing database, stop the backend, back up the database,
and run `alembic upgrade head`, even if no schema revisions are pending. If invalid
references exist, the command fails without changing the database. Inspect them
with `PRAGMA foreign_key_check`. Repair each reference deliberately (for example,
clear invalid optional ownership or restore the missing parent), then rerun the
command. No rows are automatically deleted or repaired. Scripts outside the
application must enable enforcement on their own SQLite connections.
