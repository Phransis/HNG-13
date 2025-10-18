# Backend Wizards — Stage 0 (Django implementation)

## Requirements
- Python 3.10+ recommended
- pip

## Setup (local)
1. Clone repo:
   git clone https://github.com/Phransis/HNG-13.git && cd core

2. Create virtualenv and install:
   python -m venv venv
   source venv/bin/activate   
   pip install -r requirements.txt

3. Create .env file from .env.example and set your values:
   cp .env.example .env

4. Run migrations:
   python manage.py migrate

5. Run server locally:
   python manage.py runserver 0.0.0.0:8000

6. Access at http://hng-13-production.up.railway.app/me

7. Test the endpoint:
   curl -i http://127.0.0.1:8000/me

   Expected JSON shape:
   {
     "status": "success",
     "user": { "email": "...", "name": "...", "stack": "..." },
     "timestamp": "2025-10-15T12:34:56.789Z",
     "fact": "A random cat fact..."
   }

## Run tests
   python manage.py test

## Notes / behavior
- The app fetches a new cat fact on every request from https://catfact.ninja/fact with a timeout of ~2.5s.
- If the external API call fails, the response still returns HTTP 200 with a fallback `fact` message (keeps schema consistent).
- Timestamp is generated at request time in UTC and formatted as ISO 8601 with millisecond precision and trailing `Z`.
- Content-Type header is application/json.



## Submission checklist (for the cohort)

