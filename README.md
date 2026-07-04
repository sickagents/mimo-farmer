# mimo-farmer

MiMo account creator CLI.

Simple flow:

```powershell
python -m mimo_farmer create --referral CODE --count N
```

## Features

- Create MiMo accounts with referral code.
- Set account quantity with `--count`.
- Automatic OTP polling from generator.email.
- reCAPTCHA handling through existing pipeline.
- Xiaomi signup, terms handling, balance check, and API key extraction.
- Batch TXT output in `accounts/`.
- **Parallel mode** for high-CPU VPS (up to 50 workers).

## Requirements

- Python 3.12 recommended.
- Google Chrome / supported browser environment.
- Project dependencies installed.

Example Python command:

```powershell
python
```

## Installation

```powershell
git clone https://github.com/rapoii/mimo-farmer.git
cd mimo-farmer
pip install -e .
```

If running on Rafi's local machine, clear `PYTHONPATH` first:

```powershell
$env:PYTHONPATH=""
```

## Usage

### Show help

```powershell
python -m mimo_farmer --help
```

### Create accounts (sequential)

```powershell
python -m mimo_farmer create --referral ABC123 --count 5
```

Short version:

```powershell
python -m mimo_farmer create -r ABC123 -n 5
```

If `--referral` or `--count` is not provided, CLI asks interactively.

### Create accounts (parallel mode)

```powershell
python -m mimo_farmer create -r ABC123 -n 30 --workers 20
```

Short version:

```powershell
python -m mimo_farmer create -r ABC123 -n 30 -w 20
```

## Commands

```text
mimo create --referral CODE --count N [--workers W]
```

| Option | Description |
|---|---|
| `--referral`, `-r` | Referral code to use |
| `--count`, `-n` | Number of accounts to create |
| `--workers`, `-w` | Number of parallel workers (default: 1, max: 50) |

## Parallel Mode

For high-CPU VPS, use `--workers` to run multiple account creations simultaneously.
Each worker gets its own browser instance and proxy IP (Xiaomi detects same-IP bulk
registration).

### Recommended worker counts

| VPS vCPUs | Workers | Notes |
|---|---|---|
| 4-8 | 1-3 | Sequential fine |
| 16-32 | 5-10 | Moderate parallelism |
| 64-128 | 15-25 | Good throughput |
| 160+ | 20-30 | Optimal for 160 vCPU |

**Important constraints:**
- Each worker uses a separate proxy IP (round-robin from free proxy pool)
- Semaphore limits concurrent browsers to prevent OOM
- One worker failure does not stop other workers
- Default `--workers 1` is identical to sequential mode (backward compatible)

### Examples

```powershell
# 5 accounts, 1 at a time (default)
python -m mimo_farmer create -r ABC123 -n 5

# 30 accounts, 20 parallel workers (160 vCPU VPS)
python -m mimo_farmer create -r ABC123 -n 30 -w 20

# 100 accounts, 30 parallel workers
python -m mimo_farmer create -r ABC123 -n 100 -w 30
```

## Output

Output file:

```text
accounts\batch_YYYYMMDD_HHMMSS.txt
```

Example format:

```text
[1] | 26/06/2026
Mail: user@example.com
Link: https://generator.email/user@example.com
Pw: password
Api-Key: sk-...
Balance: $2.72

Total Balance: $2.72

Apikey:
sk-...
```

Only successful accounts with API key are written.

## Notes

- Generated account files are ignored by Git.
- Do not commit `.env`, credentials, or account output files.
- Use `Ctrl+C` to stop a running batch.
