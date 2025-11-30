import subprocess
import sys
from pathlib import Path

repo = Path(__file__).resolve().parent

def git(cmd):
    return subprocess.check_output(['git'] + cmd, cwd=repo, text=True)

status = git(['status', '--porcelain'])
lines = [l for l in status.splitlines() if l.strip()]
if not lines:
    print('No changes to commit')
    sys.exit(0)

for line in lines:
    # porcelain: XY <path> or '?? <path>'
    parts = line.split(maxsplit=1)
    if len(parts) == 1:
        continue
    code, path = parts
    path = path.strip().strip('"')
    full = repo / path
    # determine message heuristically
    msg = None
    if 'admin_document_requests.html' in path:
        msg = 'Admin modal: prioritize Payment Details, add receipt preview and centering.'
    elif 'requested_documents.html' in path:
        msg = 'Student UI: Submit Requirements modal and payment upload improvements.'
    elif path.endswith('dashboard/views.py'):
        msg = 'Backend: upload payment receipts to Supabase and record PaymentUpload; return payment_receipt URL.'
    elif path.endswith('accounts/models.py'):
        msg = 'Model: change Request.payment_receipt to URLField for Supabase compatibility.'
    elif path.endswith('request/models.py'):
        msg = 'Models: adjust upload metadata fields and PaymentUpload schema.'
    elif path.endswith('dashboard/templates/admin/admin_dashboard.html'):
        msg = 'Admin dashboard: UI tweaks.'
    elif path.endswith('.css'):
        msg = f'Frontend styles updated: {path}'
    elif path.endswith('.js'):
        msg = f'Frontend behavior updated: {path}'
    elif path.endswith('.py'):
        msg = f'Backend change: {path}'
    else:
        msg = f'Update {path}'

    try:
        # if deleted (starts with D or ' D' or 'D ')
        if code.startswith('D') or code[0]=='D' or code.startswith('R') and not full.exists():
            print('Removing', path)
            subprocess.check_call(['git','rm', path], cwd=repo)
            subprocess.check_call(['git','commit','-m', msg, '--', path], cwd=repo)
            print('Committed removal:', path)
            continue
    except subprocess.CalledProcessError as e:
        print('Error removing', path, e)

    try:
        subprocess.check_call(['git','add', path], cwd=repo)
        subprocess.check_call(['git','commit','-m', msg, '--', path], cwd=repo)
        print('Committed:', path, '->', msg)
    except subprocess.CalledProcessError as e:
        print('Commit failed for', path, e)

print('Done')
