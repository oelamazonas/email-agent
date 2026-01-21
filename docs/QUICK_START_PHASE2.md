# Quick Start: Phase 2 Email Actions

**5-minute guide to using the new email actions system**

---

## 🎯 What's New in Phase 2?

Your Email Agent AI can now:

1. **Auto-classify** emails using rules (YAML) + AI (Ollama)
2. **Auto-move** emails to organized folders
3. **Auto-delete** spam
4. **Apply labels** (Gmail only)
5. **Log everything** for audit trail

---

## 🚀 Quick Start

### 1. Check Default Rules

View the default rules:
```bash
cat rules/global_rules.yaml
```

These rules handle common patterns like:
- Invoices → `Finance/Invoices`
- Receipts → `Finance/Receipts`
- Newsletters → `Newsletters`
- Spam → Auto-delete

### 2. Start the System

```bash
docker-compose up -d
```

The system now automatically:
- Syncs emails every 5 minutes
- Classifies pending emails every 10 minutes
- Applies actions (move/delete) based on classification

### 3. Watch It Work

Check logs:
```bash
docker-compose logs -f worker
```

You'll see:
```
[INFO] Syncing account 1
[INFO] Fetched 10 emails
[INFO] Triggering classification for 10 new emails
[INFO] Email matched rule: Invoice by subject
[INFO] Email 123 actions completed: ['moved_to:Finance/Invoices']
```

---

## 📋 Common Tasks

### Add Custom Rules

Edit `rules/global_rules.yaml`:

```yaml
rules:
  - name: "My boss emails"
    priority: 200
    conditions:
      sender_contains: "boss@company.com"
    category: PROFESSIONAL
    folder: "Important/Boss"

  - name: "Project X emails"
    priority: 150
    conditions:
      subject_contains: "Project X|ProjectX"
      sender_contains: "@company.com"
    category: PROFESSIONAL
    folder: "Projects/ProjectX"
```

**No restart needed** - rules reload automatically!

### Classify Specific Email

Using Python:
```python
from worker.tasks.email_classification import classify_single_email

# Classify email ID 123
result = classify_single_email.delay(123)
print(result.get())
```

Using API (if you build the endpoint):
```bash
curl -X POST http://localhost:8000/api/emails/123/classify
```

### Bulk Move Emails

```python
from worker.actions import bulk_move_emails
import asyncio

# Move emails 1-5 to Archive
result = asyncio.run(bulk_move_emails(
    email_ids=[1, 2, 3, 4, 5],
    folder="Archive/2025"
))

print(f"Moved: {len(result['succeeded'])} emails")
print(f"Failed: {len(result['failed'])} emails")
```

### Check Action Logs

```python
from api.database import get_db_context
from api.models import ProcessingLog
from sqlalchemy import select

async def check_logs(email_id):
    async with get_db_context() as db:
        logs = await db.execute(
            select(ProcessingLog)
            .where(ProcessingLog.email_id == email_id)
            .order_by(ProcessingLog.created_at.desc())
        )
        for log in logs.scalars().all():
            print(f"[{log.level}] {log.message}")
            if log.details:
                print(f"  Details: {log.details}")

# Check logs for email 123
import asyncio
asyncio.run(check_logs(123))
```

---

## 🔧 Configuration

### Processing Mode

Edit `.env`:
```bash
# Suggest mode: Preview actions, don't execute
PROCESSING_MODE=suggest

# Auto mode: Execute actions automatically (default)
PROCESSING_MODE=auto
```

### Sync Frequency

```bash
# Sync every 5 minutes (default)
EMAIL_POLL_INTERVAL=5

# Sync every 1 minute (more frequent)
EMAIL_POLL_INTERVAL=1

# Sync every 15 minutes (less frequent)
EMAIL_POLL_INTERVAL=15
```

### Classification Schedule

Edit `worker/celery_app.py`:
```python
'classify-pending-emails': {
    'task': 'worker.tasks.email_classification.classify_pending_emails',
    'schedule': crontab(minute='*/10'),  # Every 10 min
    'kwargs': {'limit': 100}
}
```

---

## 📊 Understanding Categories

| Category | Default Action | Folder |
|----------|---------------|--------|
| INVOICE | Move | Finance/Invoices |
| RECEIPT | Move | Finance/Receipts |
| DOCUMENT | Move | Documents |
| NEWSLETTER | Move | Newsletters |
| PROMOTION | Move | Promotions |
| SOCIAL | Move | Social |
| NOTIFICATION | Move | Notifications |
| PROFESSIONAL | Keep | INBOX |
| PERSONAL | Keep | INBOX |
| SPAM | Delete | - |
| UNKNOWN | Keep | INBOX |

---

## 🎓 Rule Writing Tips

### Priority

- **High priority** (100+): Specific, important patterns
- **Medium priority** (50-99): General patterns
- **Low priority** (0-49): Catch-all rules

### Conditions

**Sender matching**:
```yaml
# Single sender
sender_contains: "@company.com"

# Multiple senders (OR logic)
sender_contains: "@company.com|@vendor.com"

# Exact match
sender_equals: "boss@company.com"
```

**Subject matching**:
```yaml
# Case-insensitive
subject_contains: "invoice"

# Multiple patterns
subject_contains: "invoice|facture|factuur"

# Exact match
subject_equals: "Important: Review needed"
```

**Attachments**:
```yaml
# Has any attachment
has_attachments: true

# Attachment name contains
attachment_name_contains: "invoice"
```

**Combining conditions** (AND logic):
```yaml
conditions:
  sender_contains: "@bank.com"
  subject_contains: "statement"
  has_attachments: true
```

---

## 🐛 Troubleshooting

### Rules Not Working

1. **Check YAML syntax**:
   ```bash
   # Validate YAML
   python -c "import yaml; yaml.safe_load(open('rules/global_rules.yaml'))"
   ```

2. **Check categories are uppercase**:
   ```yaml
   category: INVOICE  # ✅ Correct
   category: invoice  # ❌ Wrong
   ```

3. **Reload rules manually**:
   ```python
   from worker.rules import rules_parser
   rules_parser.load_rules(force_reload=True)
   print(f"Loaded {len(rules_parser.rules)} rules")
   ```

### Actions Not Executing

1. **Check connector works**:
   ```bash
   python scripts/test_imap_connector.py
   ```

2. **Check folder exists**:
   - Gmail: Labels are auto-created
   - IMAP/Outlook: Folders must exist

3. **Check logs**:
   ```bash
   docker-compose logs worker | grep ERROR
   ```

### Slow Classification

1. **Add more rules** (rules are 100x faster than LLM)
2. **Reduce LLM timeout**:
   ```bash
   OLLAMA_TIMEOUT=60  # Default: 120
   ```
3. **Use lighter model**:
   ```bash
   OLLAMA_MODEL=phi  # Instead of mistral
   ```

---

## 📚 Next Steps

1. **Customize rules** for your email patterns
2. **Monitor logs** to see classification accuracy
3. **Adjust priorities** based on what matches most
4. **Build API endpoints** for manual control
5. **Explore Phase 3** features (OCR, fine-tuning)

---

## 🔗 Resources

- **Full Documentation**: `docs/PHASE_2_ACTIONS.md`
- **Main Guide**: `CLAUDE.md`
- **Test Examples**: `tests/test_email_actions.py`
- **Default Rules**: `rules/global_rules.yaml`

---

**Happy organizing! 📧✨**
