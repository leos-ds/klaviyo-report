# ClickUp API cheatsheet (v2)

Base URL: `https://api.clickup.com/api/v2`
Auth header: `Authorization: <personal_token>` (no `Bearer ` prefix for personal tokens)
Rate limit: ~100 req/min for personal tokens; back off 1s on 429.

## Hierarchy

```
Workspace (= "team" in API)
└── Space
    └── Folder (optional — lists can also live directly under a Space)
        └── List
            └── Task
                └── Subtask / Comment / Custom field value
```

For Digismoothie Email Marketing setup:
- Workspace: Digismoothie agency
- Space: "Email marketing"
- Folder: per-client (e.g. "Krekry")
- Lists: per-client subfolders (typically "flows" and "campaigns")
- Tasks: individual audit items, briefs, fixes

## Endpoints (used by this skill)

### Discovery (read-only)
```
GET  /team
GET  /team/{team_id}/space?archived=false
GET  /space/{space_id}/folder?archived=false
GET  /folder/{folder_id}/list?archived=false
GET  /list/{list_id}/task              # for idempotency check
```

### Task creation
```
POST /list/{list_id}/task
Content-Type: application/json
Body:
{
  "name": "string (required)",
  "description": "markdown string",
  "tags": ["array", "of", "strings"],
  "status": "open" | "in progress" | "review" | "complete" | <custom>,
  "priority": 1 | 2 | 3 | 4,    # 1=urgent, 4=low
  "due_date": null | unix_ms,
  "due_date_time": false | true,
  "assignees": [user_id, ...],
  "notify_all": false
}
```

### Task update (idempotency)
```
PUT /task/{task_id}
Body: same as POST except `name` is optional
```

### Search by name (for idempotency)
ClickUp does not have a direct search-by-name in personal API. Use:
```
GET /list/{list_id}/task?include_closed=true&page=0
```
Then filter client-side by `task.name === target_name`.

## Priority mapping

| Severity | priority | UI label |
|---|---|---|
| P1 | 1 | Urgent |
| P2 | 2 | High |
| P3 | 3 | Normal |
| Low | 4 | Low |

## Custom fields

If the client's lists have custom fields (open rate, channel, etc.), discover them:
```
GET /list/{list_id}/field
```

Then set values when creating tasks:
```
"custom_fields": [
  { "id": "field_uuid", "value": "..." }
]
```

## Common errors

- `401 Unauthorized` → token expired or revoked. Rotate.
- `404 Not Found` → folder/list ID wrong or archived. Re-run discovery.
- `429 Too Many Requests` → back off 1-5s, retry.
- `OAUTH_027` (when listed in error) → client OAuth scope missing; not applicable for personal tokens but check token type.

## Example: create one task

```bash
curl -s -X POST \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.clickup.com/api/v2/list/901512345678/task" \
  -d '{
    "name": "[P1] Fix Cart Abandonment open rate",
    "description": "Open rate 15.9% vs 40% benchmark...",
    "tags": ["digismoothie-audit","p1","cart-abandon"],
    "priority": 1,
    "notify_all": false
  }' | jq '{id, name, url}'
```

## Example: list tasks for idempotency

```bash
curl -s -H "Authorization: $CLICKUP_API_TOKEN" \
  "https://api.clickup.com/api/v2/list/901512345678/task?include_closed=true&subtasks=false" \
  | jq '.tasks[] | {id, name}'
```
