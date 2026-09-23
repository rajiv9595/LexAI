# STEP 24 — Assistant Conversation List

## Endpoint

`GET /api/v1/assistant/conversations` (authenticated, `get_current_user`).

Paginated lightweight discovery of the caller's conversations:

```json
{
  "items": [
    {
      "conversation_id": "conversation-abc123",
      "updated_at": "2026-09-23T15:33:05",
      "message_count": 4,
      "first_user_message_preview": "My landlord kept my…"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 42
}
```

Query params: `page` (≥ 1, default 1), `page_size` (1–100, default 20).
Out-of-range values return 422. Empty users get
`{"items": [], "page": 1, "page_size": 20, "total": 0}` (200, never 404).

## Contract

- **Ownership:** filtered by `assistant_conversations.user_id = current_user.id`
  only. No `user_id` query param. Legacy `NULL`-owned rows are excluded.
- **Sorting (server-side):** `updated_at DESC`, tie-break `id DESC`.
  `save_message()` bumps the parent `updated_at` (existing column, no
  migration) so new activity surfaces first.
- **Preview:** earliest user-authored message only (assistant/system text
  never used); `null` when none. Server-truncated to 160 chars with a
  trailing `…`; the frontend must not re-truncate or render as HTML.
- **Counts:** single `GROUP BY` query for the page — no N+1. Previews use
  one `IN` query; earliest picked by `(created_at, numeric message
  sequence)`.
- **No provenance in list items:** `references` are intentionally absent.
  Full messages + generation-time reference snapshots load via the detail
  endpoint `GET /api/v1/assistant/conversations/{id}`, which is unchanged.
- **No schema change:** this step adds no migration and no index. Sorting
  reuses the existing `updated_at` column at capstone scale.
