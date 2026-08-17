# DhanLaxmi Lottery

A runnable full-stack foundation for a transparent lottery platform: FastAPI + SQLite,
an authenticated web admin and a premium Flutter client. Draws are random and auditable;
there is no winner override or client-confirmed payment path.

> Before real-money use, obtain jurisdiction-specific legal review and use a payment provider
> that explicitly permits the business model. The included UPI adapter creates a deep link but
> accepts success only from an HMAC-signed provider webhook. It does not simulate success.

## Project map

- `backend/app`: API, models, auth, payment and draw services, admin UI
- `backend/tests`: core security and business-invariant tests
- `flutter_app`: Android/iOS/Web Flutter client
- `admin`: admin deployment notes
- `docs/ARCHITECTURE.md`: ER diagram, flows, API/security design and phases

## Run locally

Python 3.11–3.13 is recommended (some binary dependencies may lag Python 3.14).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export PYTHONPATH="$PWD/backend"
python backend/seed.py
uvicorn app.main:app --reload
```

Open [API docs](http://localhost:8000/docs) and [admin](http://localhost:8000/admin).
Seed login: `admin@example.com` / `ChangeMe123!`; change it immediately.

```bash
cd flutter_app
flutter pub get
flutter run
```

Android emulator uses `http://10.0.2.2:8000`; for iOS simulator/device, update `ApiClient.base`
in `flutter_app/lib/main.dart`. Production builds must use HTTPS and platform deep-link setup.

## Test

```bash
source .venv/bin/activate
export PYTHONPATH="$PWD/backend"
pytest backend/tests -q
cd flutter_app && flutter analyze && flutter test
```

## Provider integration

Implement a production provider adapter around the payment service. The provider callback signs
`payment_id|provider_reference|status` with `WEBHOOK_SECRET`; in production also verify the
provider certificate/IP, fetch transaction status server-to-server, enforce amount/currency and
store raw callback IDs. Webhook replay is safe because payment-to-ticket is unique.

## Database migration and deployment

Add Alembic before schema evolution, generate a baseline revision, test against PostgreSQL, then
change only `DATABASE_URL`. Deploy the container behind TLS, keep secrets in a secret manager,
disable public docs (`ENABLE_DOCS=false`), use strict CORS, persistent media/object storage,
database backups, centralized logs, monitoring, rate limiting at the edge and multiple workers.
Keep draw and ledger tables append-only with database permissions and retention controls.

## Remaining production integrations

Real payment credentials, push notifications, KYC, legal texts, object storage, device-abuse
signals and jurisdiction policies are deliberately configuration/integration tasks; inventing
fake provider verification would violate the product's security requirements.
# lottery
