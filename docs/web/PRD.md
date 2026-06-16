# PRD — mimo-farmer Web UI

## Overview

mimo-farmer Web UI adalah interface berbasis web untuk mengelola automated Xiaomi MiMo account creation. Web UI berjalan di localhost dan membungkus CLI pipeline yang sudah ada dengan visual dashboard, real-time progress tracking, dan account management.

## Problem Statement

User mimo-farmer saat ini hanya bisa berinteraksi melalui CLI. Beberapa limitasi:
- Tidak ada visual feedback saat proses berjalan (hanya text output)
- Sulit manage ratusan akun yang sudah dibuat
- Tidak ada cara mudah export/filter/cari akun
- Tidak ada overview status (total akun, total balance, success rate)
- Manual CAPTCHA solving butuh switch antara terminal dan browser

## Goals

1. **Dashboard** — Overview stats (total akun, balance, success rate, recent activity)
2. **Account Creation** — Trigger pipeline dari web UI dengan real-time progress
3. **Account Management** — Table view semua akun dengan search, filter, sort
4. **Export** — Download credentials dalam berbagai format
5. **Settings** — Konfigurasi referral code, password, email domains
6. **Self-hosted** — Berjalan di localhost, user install sendiri

## Non-Goals

- Tidak ada multi-user auth (single user, localhost only)
- Tidak ada cloud deployment
- Tidak ada mobile app
- Tidak ada payment/billing

## User Personas

### Primary: Rafi (Developer/Power User)
- Teknik Industri student, heavy CLI user
- Ingin visual overview dan easier account management
- Sering create 30+ akun per session (5 siklus)
- Butuh export bulk untuk sharing/selling

## Features

### F1: Dashboard
- Total accounts created (all time + today)
- Total combined balance
- Success/failure rate
- Recent activity feed (last 10 accounts)
- Quick actions (Create, Export)

### F2: Create Account
- Form: referral code, count, mode (single/siklus/continuous/parallel)
- Fast mode toggle
- Real-time progress via WebSocket:
  - Current step (1/14 pipeline steps)
  - Status per step (pending/running/done/error)
  - CAPTCHA status (waiting for manual solve / auto-solving)
  - ETA
- Live log output (terminal-style)
- Cancel button

### F3: Account List
- Table: email, password, API key, referral, balance, created date, status
- Search by email/referral
- Filter by balance, date range, status
- Sort by any column
- Bulk select + export
- Copy single credential (email/pw/api key)
- Pagination (50 per page)

### F4: Export
- Format: JSON, TXT (batch format), CSV
- Filter before export (date range, balance, referral)
- Download file

### F5: Settings
- Default referral code
- Default password
- Fast mode default
- IP rotation reminder interval
- Browser settings (headless toggle)

## Technical Architecture

### Stack
- **Backend**: FastAPI + uvicorn (Python)
- **Frontend**: HTML/CSS/JS (served as static files by FastAPI)
- **Real-time**: WebSocket (FastAPI native)
- **Styling**: Neobrutalism theme (custom CSS)
- **Data**: JSON files (batch_*.txt parsing) — no database needed

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve frontend |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/accounts` | List all accounts (paginated) |
| POST | `/api/create` | Start account creation |
| WS | `/ws/progress` | Real-time progress updates |
| GET | `/api/export` | Export accounts (format param) |
| GET | `/api/settings` | Get current settings |
| PUT | `/api/settings` | Update settings |
| GET | `/api/batches` | List batch files |

## Success Metrics

- Web UI loads in < 1s
- Real-time progress updates with < 500ms latency
- Account creation works identically to CLI
- Can manage 500+ accounts without performance issues

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Planning | Day 1 | PRD, DCD, DFD, ERD, Design docs |
| Backend | Day 2 | FastAPI server + WebSocket + API |
| Frontend | Day 3 | Dashboard + Create + Account List |
| Polish | Day 4 | Settings, Export, Error handling |
| Testing | Day 5 | Integration test, bug fixes |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Playwright blocks event loop | High | Run in separate thread/process |
| WebSocket disconnects | Medium | Auto-reconnect + state recovery |
| Large batch files (500+ accounts) | Medium | Pagination + lazy loading |
| Browser compatibility | Low | Test Chrome/Firefox/Edge |
