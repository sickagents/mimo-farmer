# mimo-farmer

Free public MiMo account creator.

Free version only exposes one flow:

```powershell
python -m mimo_farmer create --referral CODE --count N
```

Advanced balance runner, siklus, auto-farm, dashboard, CDP tuning, and paid workflow are not exposed in this free CLI. Use `mimo-farmer-reborn` for paid/internal workflow.

## Features

- Create accounts using a referral code.
- Create fixed number of accounts with `--count`.
- Automatic generator.email OTP polling.
- reCAPTCHA audio solving using existing local pipeline.
- Xiaomi signup, terms dialog, balance check, API key extraction.
- Batch TXT output under `accounts/`.

## Requirements

- Windows 10/11 recommended.
- Python 3.12 on Rafi's machine:

```powershell
C:\Users\rafi\AppData\Local\Programs\Python\Python312\python.exe
```

- Existing dependencies installed for this project.
- `PYTHONPATH` cleared before running on Rafi's machine.

## Usage

### Help

```powershell
cd C:\Users\rafi\mimo-farmer; $env:PYTHONPATH=""; C:\Users\rafi\AppData\Local\Programs\Python\Python312\python.exe -m mimo_farmer --help
```

### Create accounts

```powershell
cd C:\Users\rafi\mimo-farmer; $env:PYTHONPATH=""; C:\Users\rafi\AppData\Local\Programs\Python\Python312\python.exe -m mimo_farmer create --referral ABC123 --count 5
```

Short flags:

```powershell
cd C:\Users\rafi\mimo-farmer; $env:PYTHONPATH=""; C:\Users\rafi\AppData\Local\Programs\Python\Python312\python.exe -m mimo_farmer create -r ABC123 -n 5
```

If `--referral` or `--count` is omitted, CLI asks interactively.

## Public CLI

```text
usage: mimo [-h] [-V] {create} ...

positional arguments:
  {create}
    create       Create MiMo accounts

options:
  -h, --help     show help
  -V, --version  show version
```

Create command:

```text
usage: mimo create [-h] [--referral CODE] [--count N]

options:
  --referral CODE, -r CODE  Referral code to use
  --count N, -n N           Number of accounts to create
```

## Removed from free CLI

These modes are intentionally not exposed:

- `--target-balance`
- `--siklus`
- `--continuous` / `--auto`
- `--parallel`
- `--proxy`
- `--ip-rotate`
- `--cdp-url` / `--no-cdp`
- `--platform-signup`
- `--captcha`
- `accounts`, `export`, and `web` subcommands

## Output

Generated files are saved under:

```text
accounts\batch_YYYYMMDD_HHMMSS.txt
```

Example:

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

## Safety before publishing

Generated account files are ignored by Git:

```text
accounts/*.txt
accounts/*.json
accounts/*.csv
```

Do not commit `.env`, generated credentials, or local account output.
