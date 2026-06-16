# ERD — Entity Relationship Diagram

## Entities

```
┌─────────────────────┐       ┌─────────────────────┐
│      Batch          │       │     Account         │
├─────────────────────┤       ├─────────────────────┤
│ PK batch_id (auto)  │───┐   │ PK account_id (auto)│
│    filename          │   │   │ FK batch_id         │
│    created_at        │   │   │    email            │
│    referral_code     │   │   │    password         │
│    mode              │   ├──►│    api_key          │
│    total_accounts    │   │   │    referral         │
│    success_count     │   │   │    own_referral     │
│    fail_count        │   │   │    balance          │
│    is_siklus         │   │   │    risk_control     │
└─────────────────────┘   │   │    status           │
                          │   │    created_at       │
                          │   │    position (MAIN/1-5)│
                          │   └─────────────────────┘
                          │
                          │   ┌─────────────────────┐
                          │   │     Siklus          │
                          │   ├─────────────────────┤
                          └──►│ PK siklus_id (auto) │
                              │ FK batch_id         │
                              │    siklus_number    │
                              │    main_account_id  │
                              │    referral_code    │
                              │    status           │
                              │    started_at       │
                              │    completed_at     │
                              └─────────────────────┘

┌─────────────────────┐       ┌─────────────────────┐
│    CreateJob        │       │    JobStep          │
├─────────────────────┤       ├─────────────────────┤
│ PK job_id (uuid)    │───┐   │ PK step_id (auto)   │
│    mode             │   │   │ FK job_id           │
│    referral_code    │   ├──►│    step_number (1-14)│
│    count            │   │   │    step_name        │
│    fast             │   │   │    status           │
│    status           │   │   │    started_at       │
│    started_at       │   │   │    completed_at     │
│    completed_at     │   │   │    error_message    │
│    error_message    │   │   └─────────────────────┘
└─────────────────────┘   │
                          │   ┌─────────────────────┐
                          │   │    LogEntry         │
                          │   ├─────────────────────┤
                          └──►│ PK log_id (auto)    │
                              │ FK job_id           │
                              │    timestamp        │
                              │    level (INFO/ERR) │
                              │    message          │
                              └─────────────────────┘

┌─────────────────────┐
│    Settings         │
├─────────────────────┤
│ PK key              │
│    value            │
│    updated_at       │
└─────────────────────┘
```

## Relationships

| Relasi | Tipe | Keterangan |
|--------|------|------------|
| Batch 1 → N Account | One-to-Many | Satu batch berisi banyak akun |
| Batch 1 → N Siklus | One-to-Many | Satu batch bisa punya banyak siklus (mode siklus) |
| Siklus 1 → 1 Account (main) | One-to-One | Satu siklus punya satu akun utama |
| CreateJob 1 → N JobStep | One-to-Many | Satu job punya 14 langkah pipeline |
| CreateJob 1 → N LogEntry | One-to-Many | Satu job menghasilkan banyak log |

## Catatan Implementasi

**Tidak ada database.** Semua data di-parse dari file:

| Entity | Sumber Data |
|--------|-------------|
| Batch | `accounts/batch_*.txt` (filename → metadata) |
| Account | Parse per-section dari batch file (`[MAIN]`, `[1]`, `[2]`, ...) |
| CreateJob | In-memory saat proses berjalan |
| JobStep | In-memory, broadcast via WebSocket |
| LogEntry | In-memory, stream via WebSocket |
| Settings | `config.py` + optional `settings.json` |

### Batch File Format (Data Source)

```
[MAIN]
Mail: user@domain.com
Pw: MmPass123!9
Api-Key: sk-abc...xyz
Referral: -
Own-Referral: XJ6YSS
Balance: $0.72

[1]
Mail: child1@domain.com
Pw: MmPass456!9
Api-Key: sk-def...uvw
Referral: XJ6YSS
Balance: $2.72
```

### Account Status States

```
created → active → risk_controlled
                  → expired
```

### Job Status States

```
pending → running → completed
                  → failed
                  → cancelled
```

### Step Status States

```
pending → running → completed
                  → skipped
                  → failed
```
