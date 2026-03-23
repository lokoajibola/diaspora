# Deploy to PythonAnywhere (`diasporaway.pythoneverywhere.com`)

## 1) Create PythonAnywhere web app
1. Log in to PythonAnywhere.
2. Go to **Web** → **Add a new web app**.
3. Choose **Manual configuration**.
4. Pick **Python 3.11** (or your preferred supported version).

## 2) Clone project and create venv (Bash console)
```bash
cd ~
git clone <your-repo-url> diaspora
cd diaspora
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Set environment variables
In PythonAnywhere, set environment variables in your WSGI file (see step 5).
Use values from `.env.example`:
- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY=<strong-random-secret>`
- `DJANGO_ALLOWED_HOSTS=diasporaway.pythoneverywhere.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://diasporaway.pythoneverywhere.com`
- `PAYSTACK_PUBLIC_KEY=<your-paystack-public-key>`
- `PAYSTACK_SECRET_KEY=<your-paystack-secret-key>`

## 4) Run migrations and collect static
```bash
cd ~/diaspora
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 5) Configure WSGI file
Open Web tab → your app → **WSGI configuration file** and replace with:

```python
import os
import sys

path = '/home/diasporaway/diaspora'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_SECRET_KEY'] = '<strong-random-secret>'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'diasporaway.pythoneverywhere.com'
os.environ['DJANGO_CSRF_TRUSTED_ORIGINS'] = 'https://diasporaway.pythoneverywhere.com'
os.environ['PAYSTACK_PUBLIC_KEY'] = '<your-paystack-public-key>'
os.environ['PAYSTACK_SECRET_KEY'] = '<your-paystack-secret-key>'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 6) Static and media mappings (Web tab)
Set these under **Static files**:
- URL: `/static/` → Directory: `/home/diasporaway/diaspora/staticfiles`
- URL: `/media/` → Directory: `/home/diasporaway/diaspora/media`

## 7) Reload app
In Web tab, click **Reload**.
Then open:
- `https://diasporaway.pythoneverywhere.com`

## 8) Troubleshooting
- Check PythonAnywhere **Error log** first.
- If you see host errors, verify `DJANGO_ALLOWED_HOSTS`.
- If CSS is missing, rerun `collectstatic` and confirm static mapping.
- If payment init fails, verify Paystack keys are set in WSGI env vars.
