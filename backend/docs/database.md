# Database relationships

`users` contains a UUID string primary key (`id`), required unique `email`,
an optional `password_hash`, and `created_at`, using the existing Python UTC
timestamp default convention. The password hash is optional only so existing
users remain valid after the migration. New signup records always have a hash.
Email format validation and normalization belong to the auth layer; the unique
constraint alone does not guarantee case-insensitive email uniqueness.

`conversations.user_id` is a nullable foreign key to `users.id`. Existing API
requests continue to create unowned conversations. SQLAlchemy exposes ownership
through `Conversation.user` and `User.conversations`.

## Message token counts

Revision `20261008_0005` adds nullable integer columns `messages.prompt_tokens`
and `messages.completion_tokens`. Existing rows keep their data and get `NULL`
counts. Assistant messages store counts from Gemini usage data. User messages
and unknown counts keep `NULL` values. Conversation usage totals treat `NULL`
as zero and exclude title requests.

Run `alembic upgrade head` from `backend/` to apply the change. Run
`alembic downgrade 20261008_0004` to remove the token columns. The downgrade
retains messages but removes their token counts.

## Relationship indexes

`ix_conversations_user_id` indexes conversation ownership. The message-index
revision (`20261005_0003`) adds `ix_messages_conversation_id` for fetching a
conversation's messages and locating dependent rows during deletion. Both are
non-unique indexes; a user can own multiple conversations and a conversation can
contain multiple messages. Downgrading to `20261003_0002` removes only the message
index, preserving rows, foreign keys, and the ownership index.

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
conversation-to-message ORM `all, delete-orphan` cascade is unchanged. Deleting
a conversation through the ORM deletes its messages but preserves its user and
other conversations. Removing a message from `Conversation.messages` deletes
that message when the session is flushed.

With database foreign-key enforcement enabled, direct SQL conversation deletion
also deletes its messages through `ON DELETE CASCADE`. Direct SQL user deletion
is rejected while owned conversations remain; clear their nullable `user_id`
first to preserve them. ORM deletion and direct SQL deletion intentionally have
different user handling.

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
