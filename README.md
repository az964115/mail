# Mail Quarantine Self-Service Portal

A Flask-based internal web portal for searching and releasing quarantined emails.

## Features
- Search quarantined emails by subject
- Release (resend) emails
- Admin credentials are stored server-side only

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
