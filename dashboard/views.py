from django.views.decorators.csrf import csrf_exempt
# ===== ADMIN AJAX: Save staff instructions for a request =====
@csrf_exempt
@login_required
def save_request_instructions(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        req_id = data.get('request_id')
        instructions = data.get('request_instructions')
        if not req_id or instructions is None:
            return JsonResponse({'success': False, 'error': 'Missing request_id or instructions'}, status=400)
        req_obj = get_object_or_404(Request, id=req_id)
        req_obj.request_instructions = instructions
        req_obj.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
# pyright: reportAttributeAccessIssue=false
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import (
    StudentAccount,
    Request,
    DocumentType,
    AdminAccount,
    Notification,
    RequestWorkflow,
)
from django.contrib.auth.decorators import login_required
from django.conf import settings
from accounts.forms import StudentProfileForm
import json
import uuid
import os
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from .decorators import student_required  # ✅ NEW IMPORT
from request.models import RequestStatusHistory, RequirementUpload, PaymentUpload
from django.urls import reverse
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

# Lazy-load Supabase client to avoid import-time errors when credentials are missing
_supabase_client = None

def get_supabase_client() -> Client:
    """Return a Supabase client, or None if not configured."""
    global _supabase_client
    if _supabase_client is None:
        url = getattr(settings, 'SUPABASE_URL', None)
        key = getattr(settings, 'SUPABASE_SERVICE_KEY', None)
        if url and key:
            try:
                _supabase_client = create_client(url, key)
            except Exception as e:
                logger.error(f"Failed to create Supabase client: {e}")
                return None
        else:
            logger.warning("Supabase credentials not configured")
            return None
    return _supabase_client

STAFF_ONLY_MESSAGE = "Access denied: staff accounts only."
PENDING_STATUSES = RequestWorkflow.pending_statuses()
APPROVAL_STATUSES = RequestWorkflow.approval_statuses()
COMPLETED_STATUSES = RequestWorkflow.completed_statuses()
REQUIREMENT_ACTION_STATUSES = RequestWorkflow.requirements_upload_statuses()
PAYMENT_ACTION_STATUSES = RequestWorkflow.payment_upload_statuses()


# ===== HELPER FUNCTIONS =====

def get_student_data(user):
    """Get student data or return None if not found"""
    try:
        student = StudentAccount.objects.get(user=user)
        return {
            'student': student,
            'student_name': str(student),
            'student_id_number': student.student_number
        }
    except StudentAccount.DoesNotExist:
        return {
            'student': None,
            'student_name': "Unknown",
            'student_id_number': "N/A"
        }


def handle_profile_update(request, student):
    """Handle profile update requests"""
    try:
        if not student:
            return JsonResponse({'success': False, 'error': 'Student account not found'})
        
        profile_picture_url = student.profile_picture  # Keep existing

        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']

            # Validate file size
            if profile_picture.size > 10 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'Image file too large (max 10MB).'})
            
            # Validate format
            file_extension = os.path.splitext(profile_picture.name)[1].lower()
            if file_extension not in ['.jpg', '.jpeg', '.png', '.gif']:
                return JsonResponse({'success': False, 'error': 'Invalid format. Use JPG, PNG, or GIF.'})
            
            # Upload to Supabase Storage
            unique_filename = f"{student.student_number}_{uuid.uuid4()}{file_extension}"
            file_data = profile_picture.read()

            supabase_client = get_supabase_client()
            if not supabase_client:
                return JsonResponse({'success': False, 'error': 'Storage service unavailable'})
            
            supabase_client.storage.from_("profile-pictures").upload(
                unique_filename,
                file_data,
                {"content-type": profile_picture.content_type}
            )

            # Get public URL
            public_url = supabase_client.storage.from_("profile-pictures").get_public_url(unique_filename)
            profile_picture_url = public_url

        # Validate contact number (Philippine format: 09XXXXXXXXX or +639XXXXXXXXX)
        contact_number = request.POST.get('contact_number', '').strip()
        if contact_number:
            import re
            # Remove spaces and dashes
            cleaned = re.sub(r'[\s\-]', '', contact_number)
            # Check Philippine mobile format
            if not re.match(r'^(09\d{9}|\+639\d{9})$', cleaned):
                return JsonResponse({'success': False, 'error': 'Invalid contact number. Please use format: 09XXXXXXXXX'})
            contact_number = cleaned

        # Update fields
        student.first_name = request.POST.get('first_name', student.first_name)
        student.last_name = request.POST.get('last_name', student.last_name)
        student.email = request.POST.get('email', student.email)
        student.course = request.POST.get('course', student.course)
        student.year_level = request.POST.get('year_level', student.year_level)
        student.contact_number = contact_number if contact_number else student.contact_number
        student.profile_picture = profile_picture_url

        # Auto-determine program
        if student.course:
            if any(k in student.course for k in ['Engineering', 'Architecture']):
                student.program = 'College of Engineering & Architecture'
            elif any(k in student.course for k in ['Business', 'Accountancy', 'Hospitality', 'Tourism', 'Office Administration', 'Public Administration']):
                student.program = 'College of Business & Accountancy'
            elif any(k in student.course for k in ['Information Technology', 'Computer Science', 'Information Systems']):
                student.program = 'College of Computer Studies'
            elif any(k in student.course for k in ['Communication', 'English', 'Education', 'Multimedia', 'Biology', 'Math', 'Psychology']):
                student.program = 'College of Arts, Sciences & Education'
            elif any(k in student.course for k in ['Nursing', 'Pharmacy', 'Medical Technology']):
                student.program = 'College of Nursing & Allied Health Sciences'
            elif 'Criminology' in student.course:
                student.program = 'College of Criminal Justice'
        
        student.save()

        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully!',
            'student': {
                'first_name': student.first_name,
                'last_name': student.last_name,
                'course': student.course,
                'program': student.program,
                'year_level': student.year_level,
                'email': student.email,
                'contact_number': student.contact_number,
                'profile_picture_url': student.profile_picture
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def handle_document_request(request, student):
    """Handle document request submission"""
    try:
        if not student:
            return JsonResponse({'success': False, 'error': 'Student account not found.'})
        
        document_type = request.POST.get('document_type')
        purpose = request.POST.get('purpose')
        copies = request.POST.get('copies', 1)

        document_mapping = {
            'transcript': 'Transcript of Records',
            'enrollment': 'Certificate of Enrollment',
            'diploma': 'Diploma Copy',
            'moral': 'Certificate of Good Moral',
            'graduation': 'Certificate of Graduation',
            'dismissal': 'Honorable Dismissal'
        }

        document_name = document_mapping.get(document_type)
        if not document_name:
            return JsonResponse({'success': False, 'error': f'Invalid document type: {document_type}'})
        
        try:
            document = DocumentType.objects.get(name=document_name)
        except DocumentType.DoesNotExist:
            document = DocumentType.objects.create(
                name=document_name,
                description=f'Request for {document_name}',
                fee=100.00
            )
        
        new_request = Request.objects.create(
            student=student,
            document=document,
            purpose=purpose,
            copies=int(copies),
            status=RequestWorkflow.PENDING_REVIEW
        )
        RequestStatusHistory.objects.create(
            request=new_request,
            old_status=None,
            new_status=new_request.status,
            changed_by=student.user.get_full_name() or student.user.username,
            notes='Request submitted by student.'
        )
        
        pending_count = Request.objects.filter(student=student, status__in=PENDING_STATUSES).count()
        return JsonResponse({
            'success': True,
            'message': 'Request submitted successfully!',
            'request': {
                'id': new_request.id,
                'document_name': new_request.document.name,
                'status': new_request.status,
                'date_requested': new_request.date_requested.strftime('%B %d, %Y'),
                'copies': new_request.copies,
                'purpose': new_request.purpose,
            },
            'pending_count': pending_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_dashboard_stats(student):
    """Get dashboard statistics for a student"""
    if not student:
        return {
            'pending_count': 0,
            'ready_pickup_count': 0,
            'completed_count': 0,
            'recent_requests': [],
            'approved_requests': [],
            'overdue_requests': [],
            'notifications': []
        }

    pending_count = Request.objects.filter(student=student, status__in=PENDING_STATUSES).count()
    ready_pickup_count = Request.objects.filter(student=student, status=RequestWorkflow.READY_FOR_PICKUP).count()
    completed_count = Request.objects.filter(student=student, status__in=COMPLETED_STATUSES).count()
    recent_requests = Request.objects.filter(student=student).order_by('-date_requested')[:3]
    approved_requests = Request.objects.filter(
        student=student,
        status__in=APPROVAL_STATUSES
    ).order_by('-date_requested')[:2]
    threshold_date = timezone.now() - timedelta(days=14)
    overdue_requests = Request.objects.filter(
        student=student,
        status__in={
            RequestWorkflow.READY_FOR_PICKUP,
            RequestWorkflow.APPROVED_FOR_PAYMENT,
            RequestWorkflow.LEGACY_APPROVED
        },
        date_requested__lt=threshold_date
    ).order_by('-date_requested')[:2]
    notifications = (
        Notification.objects.filter(student=student)
        .select_related('request', 'student')
        .order_by('-date_sent')[:20]
    )

    return {
        'pending_count': pending_count,
        'ready_pickup_count': ready_pickup_count,
        'completed_count': completed_count,
        'recent_requests': recent_requests,
        'approved_requests': approved_requests,
        'overdue_requests': overdue_requests,
        'notifications': notifications
    }


ACTION_STATUS_MAP = {
    'approve': RequestWorkflow.APPROVED_FOR_PAYMENT,
    'approve_payment': RequestWorkflow.APPROVED_FOR_PAYMENT,
    'need_requirements': RequestWorkflow.REQUIREMENTS_NEEDED,
    'requirements_issue': RequestWorkflow.REQUIREMENTS_ISSUE,
    'requirements_accept': RequestWorkflow.APPROVED_FOR_PAYMENT,
    'payment_issue': RequestWorkflow.PAYMENT_ISSUE,
    'payment_accept': RequestWorkflow.PROCESSING,
    'processing': RequestWorkflow.PROCESSING,
    'ready_for_pickup': RequestWorkflow.READY_FOR_PICKUP,
    'complete': RequestWorkflow.COMPLETED,
    'reject': RequestWorkflow.REJECTED,
    'cancel': RequestWorkflow.CANCELLED,
}

STATUS_BADGE_MAP = {
    RequestWorkflow.PENDING_REVIEW: 'badge-pending-review',
    RequestWorkflow.LEGACY_PENDING: 'badge-pending-review',
    RequestWorkflow.REQUIREMENTS_NEEDED: 'badge-requirements-needed',
    RequestWorkflow.REQUIREMENTS_SUBMITTED: 'badge-requirements-submitted',
    RequestWorkflow.REQUIREMENTS_ISSUE: 'badge-requirements-issue',
    RequestWorkflow.APPROVED_FOR_PAYMENT: 'badge-approved-payment',
    RequestWorkflow.LEGACY_APPROVED: 'badge-approved-payment',
    'Approved – For Payment': 'badge-approved-payment',  # Legacy status
    RequestWorkflow.PAYMENT_SUBMITTED: 'badge-payment-submitted',
    RequestWorkflow.PAYMENT_ISSUE: 'badge-payment-issue',
    RequestWorkflow.PROCESSING: 'badge-processing',
    RequestWorkflow.READY_FOR_PICKUP: 'badge-ready-pickup',
    RequestWorkflow.COMPLETED: 'badge-completed',
    RequestWorkflow.LEGACY_COMPLETED: 'badge-completed',
    RequestWorkflow.CANCELLED: 'badge-cancelled',
    RequestWorkflow.REJECTED: 'badge-rejected',
}

STATUS_STAGE_MAP = {
    RequestWorkflow.PENDING_REVIEW: 'Review Queue',
    RequestWorkflow.LEGACY_PENDING: 'Review Queue',
    RequestWorkflow.REQUIREMENTS_NEEDED: 'Requirements (Student)',
    RequestWorkflow.REQUIREMENTS_SUBMITTED: 'Requirements (Verify)',
    RequestWorkflow.REQUIREMENTS_ISSUE: 'Requirements (Follow-up)',
    RequestWorkflow.APPROVED_FOR_PAYMENT: 'Payment (Student)',
    RequestWorkflow.LEGACY_APPROVED: 'Payment (Student)',
    'Approved – For Payment': 'Payment (Student)',  # Legacy status
    RequestWorkflow.PAYMENT_SUBMITTED: 'Payment (Verify)',
    RequestWorkflow.PAYMENT_ISSUE: 'Payment (Follow-up)',
    RequestWorkflow.PROCESSING: 'Processing',
    RequestWorkflow.READY_FOR_PICKUP: 'Ready for Pickup',
    RequestWorkflow.COMPLETED: 'Completed',
    RequestWorkflow.LEGACY_COMPLETED: 'Completed',
    RequestWorkflow.CANCELLED: 'Cancelled',
    RequestWorkflow.REJECTED: 'Rejected',
}

STATUS_STAGE_CATEGORY_MAP = {
    # Pending review statuses should be their own 'pending' category so the
    # dashboard can filter them separately from requirement-handling statuses.
    RequestWorkflow.PENDING_REVIEW: 'pending',
    RequestWorkflow.LEGACY_PENDING: 'pending',
    RequestWorkflow.REQUIREMENTS_NEEDED: 'requirements',
    RequestWorkflow.REQUIREMENTS_SUBMITTED: 'requirements',
    RequestWorkflow.REQUIREMENTS_ISSUE: 'requirements',
    RequestWorkflow.APPROVED_FOR_PAYMENT: 'payment',
    RequestWorkflow.LEGACY_APPROVED: 'payment',
    'Approved – For Payment': 'payment',  # Legacy status
    RequestWorkflow.PAYMENT_SUBMITTED: 'payment',
    RequestWorkflow.PAYMENT_ISSUE: 'payment',
    RequestWorkflow.PROCESSING: 'processing',
    RequestWorkflow.READY_FOR_PICKUP: 'pickup',
    RequestWorkflow.COMPLETED: 'completed',
    RequestWorkflow.LEGACY_COMPLETED: 'completed',
    RequestWorkflow.CANCELLED: 'exceptions',
    RequestWorkflow.REJECTED: 'exceptions',
}

ATTENTION_STATUSES = [
    RequestWorkflow.PENDING_REVIEW,
    RequestWorkflow.REQUIREMENTS_SUBMITTED,
    RequestWorkflow.REQUIREMENTS_ISSUE,
    RequestWorkflow.PAYMENT_SUBMITTED,
    RequestWorkflow.PAYMENT_ISSUE,
]


def decorate_requests_with_display_meta(queryset):
    """Attach badge/stage helpers used by admin templates."""
    items = list(queryset)
    for req in items:
        req.badge_class = STATUS_BADGE_MAP.get(req.status, 'bg-light text-dark')
        req.stage_label = STATUS_STAGE_MAP.get(req.status, '—')
        req.stage_category = STATUS_STAGE_CATEGORY_MAP.get(req.status, 'other')
        # Provide a more specific stage key to allow narrow client-side filters
        # (e.g. requirements queue should sometimes only show 'requirements needed').
        # Use the RequestWorkflow constants imported above to set a narrow key
        # for 'requirements needed' so the front-end can filter it precisely.
        if req.status == RequestWorkflow.REQUIREMENTS_NEEDED:
            req.stage_key = 'requirements_needed'
        else:
            req.stage_key = req.stage_category
    return items


def _append_admin_note(current_note, admin, status_label, note):
    safe_note = note.strip()
    if not safe_note:
        return current_note
    prefix = f"\n[{status_label} by {admin.user.username}]: "
    return (current_note or '') + prefix + safe_note


def _apply_request_action(req_obj, admin, action, note):
    new_status = ACTION_STATUS_MAP[action]
    old_status = req_obj.status
    timestamp = timezone.now()

    if action == 'need_requirements':
        req_obj.requirements_instructions = note or req_obj.requirements_instructions
        req_obj.requirements_feedback = ''
        req_obj.requirements_submission_file = None if note else req_obj.requirements_submission_file
        req_obj.requirements_submitted_at = None
    elif action == 'requirements_accept':
        req_obj.requirements_verified_at = timestamp
        if note:
            req_obj.requirements_feedback = note
    elif action == 'requirements_issue':
        req_obj.requirements_feedback = note or 'Please review the listed items.'
    elif action in {'approve', 'approve_payment'}:
        if not req_obj.requirements_verified_at:
            req_obj.requirements_verified_at = timestamp
    elif action == 'payment_accept':
        req_obj.payment_verified_at = timestamp
        if note:
            req_obj.payment_feedback = note
    elif action == 'payment_issue':
        req_obj.payment_feedback = note or 'Receipt requires clarification.'
    elif action == 'processing':
        if not req_obj.payment_verified_at:
            req_obj.payment_verified_at = timestamp
    elif action == 'ready_for_pickup':
        req_obj.ready_for_pickup_at = timestamp
    elif action == 'complete':
        req_obj.completed_at = timestamp

    req_obj.status = new_status
    req_obj.assigned_admin = admin
    if note:
        req_obj.notes = _append_admin_note(req_obj.notes, admin, new_status, note)
    return old_status, new_status


def _notify_request_update(req_obj):
    """Create a notification for the student about request status update.
    Uses get_or_create to prevent duplicate notifications."""
    try:
        from accounts.models import Notification
        
        status_label = RequestWorkflow.status_label(req_obj.status)
        message = f"Request #{req_obj.id}: Status updated"
        
        # Use get_or_create to atomically prevent duplicates
        Notification.objects.get_or_create(
            student=req_obj.student,
            request=req_obj,
            message=message
        )
    except Exception:
        pass


# ===== STUDENT VIEWS =====

@never_cache
@login_required
@student_required
def dashboard(request):
    """Main dashboard view for students"""
    student_data = get_student_data(request.user)
    student = student_data['student']

    if request.method == 'POST':
        if request.POST.get('action') == 'update_profile':
            return handle_profile_update(request, student)
        return handle_document_request(request, student)

    stats = get_dashboard_stats(student)
    context = {**student_data, **stats}
    return render(request, 'dashboard.html', context)


@never_cache
@login_required
@student_required
def student_profile(request):
    """Student profile page"""
    student_data = get_student_data(request.user)
    student = student_data['student']

    if request.method == 'POST' and request.POST.get('action') == 'update_profile':
        return handle_profile_update(request, student)

    return render(request, 'student_profile.html', student_data)


@never_cache
@login_required
@student_required
def requested_documents(request):
    """Requested documents page"""
    student_data = get_student_data(request.user)
    student = student_data['student']

    context = {
        **student_data,
        # Decorate request objects with display metadata (badge, stage_category, stage_key)
        'all_requests': decorate_requests_with_display_meta(
            Request.objects.filter(student=student).select_related('document').order_by('-date_requested')
        ),
        'pending_requests': decorate_requests_with_display_meta(
            Request.objects.filter(student=student, status__in=PENDING_STATUSES).select_related('document')
        ),
        'approved_requests': decorate_requests_with_display_meta(
            Request.objects.filter(student=student, status__in=APPROVAL_STATUSES).select_related('document')
        ),
        'completed_requests': decorate_requests_with_display_meta(
            Request.objects.filter(student=student, status__in=COMPLETED_STATUSES).select_related('document')
        ),
        'requirements_requests': decorate_requests_with_display_meta(
            Request.objects.filter(student=student, status__in=REQUIREMENT_ACTION_STATUSES).select_related('document')
        ),
        'payment_requests': decorate_requests_with_display_meta(
            Request.objects.filter(student=student, status__in=PAYMENT_ACTION_STATUSES).select_related('document')
        ),
        'workflow': RequestWorkflow,
        'workflow_sets': {
            'pending': list(PENDING_STATUSES),
            'completed': list(COMPLETED_STATUSES),
            'requirements': list(REQUIREMENT_ACTION_STATUSES),
            'payment': list(PAYMENT_ACTION_STATUSES),
        },
    }
    return render(request, 'requested_documents.html', context)


@login_required
@student_required
def get_requirement_uploads(request, request_id):
    """Return JSON list of RequirementUpload entries for a given request (student-owned)."""
    try:
        student = StudentAccount.objects.get(user=request.user)
    except StudentAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student account not found.'}, status=404)

    req_obj = get_object_or_404(Request, id=request_id, student=student)

    uploads = RequirementUpload.objects.filter(request=req_obj).order_by('-created_at')
    files = []
    for u in uploads:
        files.append({
            'id': u.id,
            'name': u.file_name,
            'url': u.file_url,
            'delete_url': reverse('delete_requirement_upload', args=[u.id]),
            'content_type': u.content_type,
            'file_size': u.file_size,
            'created_at': u.created_at.isoformat(),
        })

    return JsonResponse({'request_id': request_id, 'files': files})


@never_cache
@login_required
@student_required
def submit_requirements(request, request_id):
    # Debug: log incoming request basics to aid diagnosing AJAX vs form submissions
    try:
        print(f"submit_requirements called: method={request.method}, user={getattr(request.user, 'username', None)}, authenticated={request.user.is_authenticated}")
        # show a concise list of relevant headers
        hdrs = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}
        print('submit_requirements headers snippet:', {k: hdrs.get(k) for k in ['HTTP_X_REQUESTED_WITH', 'HTTP_ACCEPT', 'HTTP_COOKIE'] if hdrs.get(k)})
        # files info
        print('submit_requirements FILES keys:', list(request.FILES.keys()), 'total_files:', sum(1 for _ in request.FILES))
    except Exception as _e:
        print('submit_requirements debug logging failed', _e)

    if request.method != 'POST':
        messages.error(request, 'Invalid submission method.')
        return redirect('requested_documents')

    student_data = get_student_data(request.user)
    student = student_data['student']
    req_obj = get_object_or_404(Request, id=request_id, student=student)

    if req_obj.status not in REQUIREMENT_ACTION_STATUSES:
        messages.error(request, 'This request is not waiting for requirements.')
        return redirect('requested_documents')

    # Accept multiple files under either 'requirements_file[]' (from JS) or 'requirements_file'
    files = request.FILES.getlist('requirements_file[]') or request.FILES.getlist('requirements_file')
    # fallback single-key
    if not files:
        single = request.FILES.get('requirements_file') or request.FILES.get('requirements')
        files = [single] if single else []

    if not files:
        messages.error(request, 'Please attach the required document(s).')
        return redirect('requested_documents')

    # Upload each file to Supabase and create RequirementUpload rows
    uploaded_meta = []
    upload_errors = []
    bucket = getattr(settings, 'SUPABASE_REQUIREMENTS_BUCKET', 'requirements')
    supabase_client = get_supabase_client()
    for f in files:
        if not f:
            continue
        try:
            ext = os.path.splitext(f.name)[1].lower()
            unique_name = f"{req_obj.id}/{uuid.uuid4().hex}{ext}"
            file_data = f.read()

            # upload to Supabase storage
            if not supabase_client:
                raise RuntimeError("Storage service unavailable")
            supabase_client.storage.from_(bucket).upload(unique_name, file_data, {"content-type": f.content_type or 'application/octet-stream'})

            public_url = supabase_client.storage.from_(bucket).get_public_url(unique_name)

            # create DB record
            # create DB record. Some deployments have a NOT NULL constraint on
            # `delete_url` at the DB level (older migration); ensure we provide
            # a non-null placeholder so the insert doesn't fail. We'll update
            # the field with the real absolute URL right after creation.
            ru = RequirementUpload.objects.create(
                request=req_obj,
                uploaded_by=student,
                file_name=f.name,
                file_url=public_url,
                supabase_id=unique_name,
                delete_url='',
                content_type=f.content_type,
                file_size=f.size,
                provider='supabase'
            )

            # build delete endpoint (Django view) for clients to call and persist it
            try:
                delete_path = reverse('delete_requirement_upload', args=[ru.id])
                ru.delete_url = request.build_absolute_uri(delete_path)
                ru.save()
            except Exception:
                # don't let a failure to set the delete_url prevent the upload
                # record from being available; log full traceback for diagnosis
                import traceback
                print('Failed to set delete_url for RequirementUpload id=', getattr(ru, 'id', None))
                traceback.print_exc()

            uploaded_meta.append({
                'id': ru.id,
                'name': ru.file_name,
                'url': ru.file_url,
                'delete_url': ru.delete_url,
            })
        except Exception as e:
            # log and continue; we will return error if nothing succeeded
            err_msg = f"Requirement upload error for file '{getattr(f, 'name', '')}': {e}"
            print(err_msg)
            upload_errors.append(err_msg)
    # If no files were successfully uploaded, return errors (AJAX) or redirect with message
    if not uploaded_meta:
        is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', '')
        if is_xhr:
            return JsonResponse({'success': False, 'error': 'Upload failed', 'errors': upload_errors}, status=500)
        messages.error(request, 'Upload failed. Please try again.')
        return redirect('requested_documents')

    # At least one file uploaded successfully — update request status and history now
    previous_status = req_obj.status
    req_obj.requirements_submission_note = request.POST.get('student_note', '').strip()
    req_obj.requirements_submitted_at = timezone.now()
    req_obj.status = RequestWorkflow.REQUIREMENTS_SUBMITTED
    req_obj.save()

    RequestStatusHistory.objects.create(
        request=req_obj,
        old_status=previous_status,
        new_status=req_obj.status,
        changed_by=student.user.get_full_name() or student.user.username,
        notes='Requirements uploaded by student.'
    )

    Notification.objects.create(
        student=req_obj.student,
        request=req_obj,
        message=f"Request #{req_obj.id}: Requirements submitted"
    )

    # Return uploaded metadata for the client to update the UI
    return JsonResponse({'request_id': req_obj.id, 'files': uploaded_meta})


@never_cache
@login_required
@student_required
def submit_payment_receipt(request, request_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid submission method.')
        return redirect('requested_documents')

    student_data = get_student_data(request.user)
    student = student_data['student']
    req_obj = get_object_or_404(Request, id=request_id, student=student)

    if req_obj.status not in PAYMENT_ACTION_STATUSES:
        messages.error(request, 'This request is not waiting for payment proof.')
        return redirect('requested_documents')

    upload = request.FILES.get('payment_receipt')
    if not upload:
        messages.error(request, 'Please upload your payment receipt.')
        return redirect('requested_documents')

    # Upload the payment receipt to Supabase storage and create a PaymentUpload record
    bucket = getattr(settings, 'SUPABASE_PAYMENTS_BUCKET', 'payments')
    try:
        ext = os.path.splitext(upload.name)[1].lower()
        unique_name = f"{req_obj.id}/{uuid.uuid4().hex}{ext}"
        file_data = upload.read()

        supabase_client = get_supabase_client()
        if not supabase_client:
            messages.error(request, 'Storage service unavailable. Please try again later.')
            return redirect('requested_documents')
        
        supabase_client.storage.from_(bucket).upload(unique_name, file_data, {"content-type": upload.content_type or 'application/octet-stream'})
        public_url = supabase_client.storage.from_(bucket).get_public_url(unique_name)

        # create DB record for the uploaded receipt
        pu = PaymentUpload.objects.create(
            request=req_obj,
            uploaded_by=student,
            file_name=upload.name,
            file_url=public_url,
            supabase_id=unique_name,
            delete_url='',
            content_type=upload.content_type,
            file_size=upload.size,
            provider='supabase'
        )
        # attempt to set a delete URL if a view exists for it (best-effort)
        try:
            # If a delete view is defined later, this will populate the delete_url; ignore failures
            delete_path = reverse('delete_payment_upload', args=[pu.id])
            pu.delete_url = request.build_absolute_uri(delete_path)
            pu.save()
        except Exception:
            pass

    except Exception as e:
        print('Payment upload error:', e)
        messages.error(request, 'Failed to upload payment receipt. Please try again.')
        return redirect('requested_documents')

    previous_status = req_obj.status
    # store primary receipt URL on the Request for backward compatibility
    req_obj.payment_receipt = public_url
    req_obj.payment_reference_code = request.POST.get('payment_reference_code', '').strip()
    req_obj.payment_submitted_at = timezone.now()
    req_obj.payment_feedback = ''
    req_obj.status = RequestWorkflow.PAYMENT_SUBMITTED
    req_obj.save()

    RequestStatusHistory.objects.create(
        request=req_obj,
        old_status=previous_status,
        new_status=req_obj.status,
        changed_by=student.user.get_full_name() or student.user.username,
        notes='Payment receipt uploaded by student.'
    )

    Notification.objects.create(
        student=req_obj.student,
        request=req_obj,
        message=f"Request #{req_obj.id}: Payment submitted"
    )

    messages.success(request, 'Payment receipt submitted and saved.')
    return redirect('requested_documents')


@never_cache
@login_required
@student_required
def delete_requirement_upload(request, upload_id):
    """Delete a previously uploaded requirement file (called by the client via DELETE)."""
    if request.method not in ('DELETE', 'POST'):
        return JsonResponse({'error': 'Invalid method'}, status=405)

    student_data = get_student_data(request.user)
    student = student_data['student']

    try:
        ru = RequirementUpload.objects.get(id=upload_id, request__student=student)
    except RequirementUpload.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    # remove from Supabase if possible
    bucket = getattr(settings, 'SUPABASE_REQUIREMENTS_BUCKET', 'requirements')
    try:
        supabase_client = get_supabase_client()
        if ru.supabase_id and supabase_client:
            supabase_client.storage.from_(bucket).remove([ru.supabase_id])
    except Exception as e:
        # log but continue to delete DB row
        print('Supabase delete error:', e)

    ru.delete()
    return JsonResponse({'success': True})


@never_cache
@login_required
@student_required
def history(request):
    """History of document requests"""
    student_data = get_student_data(request.user)
    student = student_data['student']

    context = {
        **student_data,
        'completed_requests': Request.objects.filter(student=student, status__in=COMPLETED_STATUSES),
        'all_requests': Request.objects.filter(student=student),
    }
    return render(request, 'history.html', context)


@never_cache
@login_required
@student_required
def about_us(request):
    """About Us page"""
    context = get_student_data(request.user)
    return render(request, 'about_us.html', context)


@never_cache
@login_required
@student_required
def faqs(request):
    """FAQs page"""
    context = get_student_data(request.user)
    return render(request, 'faqs.html', context)


# ===== ADMIN VIEWS =====

@never_cache
@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    try:
        admin = AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        messages.error(request, "Access denied: Staff account required.")
        return redirect('dashboard')

    status_counts = {
        row['status']: row['total']
        for row in Request.objects.values('status').annotate(total=Count('id'))
    }

    workflow_stage_cards = [
        {
            'key': 'pending',
            'label': 'Pending',
            'icon': 'fa-hourglass-half',
            'color': 'info',
            'description': 'Requests awaiting initial review.',
            'statuses': [
                RequestWorkflow.PENDING_REVIEW,
                RequestWorkflow.LEGACY_PENDING,
            ],
        },
        {
            'key': 'requirements',
            'label': 'Requirements Queue',
            'icon': 'fa-list-check',
            'color': 'info',
            'description': 'Collecting or verifying requirements.',
            'statuses': [
                RequestWorkflow.REQUIREMENTS_NEEDED,
                RequestWorkflow.REQUIREMENTS_SUBMITTED,
                RequestWorkflow.REQUIREMENTS_ISSUE,
            ],
        },
        {
            'key': 'payment',
            'label': 'Payment Queue',
            'icon': 'fa-credit-card',
            'color': 'warning',
            'description': 'Waiting for payment proof or validation.',
            'statuses': [
                RequestWorkflow.APPROVED_FOR_PAYMENT,
                RequestWorkflow.PAYMENT_SUBMITTED,
                RequestWorkflow.PAYMENT_ISSUE,
            ],
        },
        {
            'key': 'processing',
            'label': 'Processing / Printing',
            'icon': 'fa-gear',
            'color': 'secondary',
            'description': 'Registrar is preparing the document.',
            'statuses': [RequestWorkflow.PROCESSING],
        },
        {
            'key': 'pickup',
            'label': 'Ready for Pickup',
            'icon': 'fa-box',
            'color': 'success',
            'description': 'Waiting for students to claim.',
            'statuses': [RequestWorkflow.READY_FOR_PICKUP],
        },
        {
            'key': 'completed',
            'label': 'Completed / Released',
            'icon': 'fa-circle-check',
            'color': 'success',
            'description': 'Documents already claimed.',
            'statuses': list(RequestWorkflow.completed_statuses()),
        },
        {
            'key': 'exceptions',
            'label': 'Cancelled / Rejected',
            'icon': 'fa-triangle-exclamation',
            'color': 'danger',
            'description': 'Requests that need follow-up outside the workflow.',
            'statuses': [RequestWorkflow.REJECTED, RequestWorkflow.CANCELLED],
        },
    ]

    def stage_count(status_list):
        return sum(status_counts.get(status, 0) for status in status_list)

    for stage in workflow_stage_cards:
        stage['count'] = stage_count(stage['statuses'])
        labels = []
        for value in stage['statuses']:
            label = RequestWorkflow.status_label(value)
            if label not in labels:
                labels.append(label)
        stage['status_labels'] = labels

    # Define open as the combination of pending (review) and processing (printing)
    totals = {
        'open': sum(
            stage['count'] for stage in workflow_stage_cards if stage['key'] in {'pending', 'processing'}
        ),
        'completed': next((stage['count'] for stage in workflow_stage_cards if stage['key'] == 'completed'), 0),
        'exceptions': next((stage['count'] for stage in workflow_stage_cards if stage['key'] == 'exceptions'), 0),
        'overall': sum(status_counts.values()) or 0,
    }

    # Provide all recent requests to the dashboard search panel so administrators
    # can search across all documents. Keep the ordering by newest first.
    recent_requests = decorate_requests_with_display_meta(
        Request.objects.select_related('student', 'document').order_by('-date_requested')
    )
    attention_requests = decorate_requests_with_display_meta(
        Request.objects.select_related('student', 'document')
        .filter(status__in=ATTENTION_STATUSES)
        .order_by('-date_requested')[:5]
    )

    context = {
        'admin': admin,
        'workflow_stage_cards': workflow_stage_cards,
        'totals': totals,
        'recent_requests': recent_requests,
        'attention_requests': attention_requests,
    }
    return render(request, 'admin/admin_dashboard.html', context)


@never_cache
@login_required
def admin_document_requests(request):
    """Admin document requests management"""
    try:
        AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        messages.error(request, STAFF_ONLY_MESSAGE)
        return redirect('dashboard')

    context = {
        'all_requests': decorate_requests_with_display_meta(
            Request.objects.select_related('student', 'document').order_by('-date_requested')
        ),
        'workflow': RequestWorkflow,
    }
    return render(request, 'admin/admin_document_requests.html', context)


@never_cache
@login_required
def admin_manage_students(request):
    """Admin manage students page"""
    try:
        AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        messages.error(request, STAFF_ONLY_MESSAGE)
        return redirect('dashboard')

    students = StudentAccount.objects.select_related('user').order_by('last_name', 'first_name')

    context = {
        'students': students,
    }
    return render(request, 'admin/admin_manage_students.html', context)


@never_cache
@login_required
def admin_settings(request):
    """Admin settings placeholder page"""
    try:
        admin = AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        messages.error(request, STAFF_ONLY_MESSAGE)
        return redirect('dashboard')

    # For now this is a simple settings placeholder. Expand as needed.
    context = {
        'admin': admin,
    }
    return render(request, 'admin/admin_settings.html', context)


@never_cache
@login_required
def admin_request_action(request):
    """Handle admin actions on requests via AJAX: approve, reject, complete, cancel."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=400)

    # Debug: log incoming request context to help diagnose AJAX/action failures
    try:
        print('admin_request_action called:', 'user=', getattr(request.user, 'username', None), 'is_authenticated=', request.user.is_authenticated)
        print('Headers: X-Requested-With=', request.META.get('HTTP_X_REQUESTED_WITH'), 'X-CSRFToken=', request.META.get('HTTP_X_CSRFTOKEN'))
        print('POST keys:', list(request.POST.keys()))
    except Exception:
        pass

    admin = AdminAccount.objects.filter(user=request.user).first()
    if not admin:
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    req_id = request.POST.get('request_id') or request.POST.get('id')
    action = (request.POST.get('action') or '').lower()
    note = request.POST.get('note', '')

    if not req_id or not action:
        return JsonResponse({'success': False, 'error': 'Missing parameters'}, status=400)

    try:
        req_obj = Request.objects.select_related('student', 'document').get(id=int(req_id))
    except (Request.DoesNotExist, ValueError):
        return JsonResponse({'success': False, 'error': 'Request not found'}, status=404)

    if action not in ACTION_STATUS_MAP:
        return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)

    old_status, new_status = _apply_request_action(req_obj, admin, action, note)
    # Set staff name for each action
    if new_status == RequestWorkflow.REQUIREMENTS_SUBMITTED or new_status == RequestWorkflow.REQUIREMENTS_ISSUE or new_status == RequestWorkflow.REQUIREMENTS_NEEDED:
        req_obj.requirements_verified_by = admin
    if new_status == RequestWorkflow.APPROVED_FOR_PAYMENT or new_status == RequestWorkflow.PAYMENT_ISSUE or new_status == RequestWorkflow.PAYMENT_SUBMITTED:
        req_obj.payment_verified_by = admin
    if new_status == RequestWorkflow.READY_FOR_PICKUP:
        req_obj.ready_for_pickup_by = admin
    if new_status == RequestWorkflow.COMPLETED:
        req_obj.completed_by = admin
    req_obj.save()
    RequestStatusHistory.objects.create(
        request=req_obj,
        old_status=old_status,
        new_status=new_status,
        changed_by=admin.full_name if hasattr(admin, 'full_name') else admin.user.username,
        notes=note
    )
    _notify_request_update(req_obj)

    return JsonResponse({
        'success': True,
        'status': req_obj.status,
        'status_label': RequestWorkflow.status_label(req_obj.status),
        'stage_label': STATUS_STAGE_MAP.get(req_obj.status, '—'),
        'badge_class': STATUS_BADGE_MAP.get(req_obj.status, 'bg-light text-dark'),
        'request_id': req_obj.id,
        'requires_requirements_upload': req_obj.requires_requirements_upload(),
        'requires_payment_upload': req_obj.requires_payment_upload(),
    })


@never_cache
@login_required
@student_required
def get_notifications(request):
    """API endpoint to fetch notifications for the current student (for real-time updates)."""
    try:
        student = StudentAccount.objects.get(user=request.user)
    except StudentAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
    
    notifications = (
        Notification.objects.filter(student=student)
        .select_related('request', 'request__document')
        .order_by('-date_sent')[:20]
    )
    
    notifications_data = []
    for notif in notifications:
        notif_data = {
            'id': notif.id,
            'message': notif.message,
            'date_sent': notif.date_sent.strftime('%B %d, %Y') if notif.date_sent else '',
            'date_sent_iso': notif.date_sent.isoformat() if notif.date_sent else '',
        }
        if notif.request:
            notif_data['request'] = {
                'id': notif.request.id,
                'status': notif.request.status,
                'document_name': notif.request.document.name if notif.request.document else 'Unknown'
            }
        else:
            notif_data['request'] = None
        notifications_data.append(notif_data)
    
    # Also return dashboard stats for real-time stat updates
    stats = get_dashboard_stats(student)
    
    return JsonResponse({
        'success': True,
        'notifications': notifications_data,
        'stats': {
            'pending_count': stats['pending_count'],
            'ready_pickup_count': stats['ready_pickup_count'],
            'completed_count': stats['completed_count'],
        },
        'recent_requests': [
            {
                'id': req.id,
                'document_name': req.document.name if req.document else 'Unknown',
                'status': req.status,
                'status_label': RequestWorkflow.status_label(req.status),
                'date_requested': req.date_requested.strftime('%b %d, %Y') if req.date_requested else '',
            }
            for req in stats['recent_requests']
        ]
    })


@never_cache
@login_required
@student_required
def get_student_requests(request):
    """API endpoint to fetch all student requests for real-time table updates."""
    try:
        student = StudentAccount.objects.get(user=request.user)
    except StudentAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
    
    all_requests = Request.objects.filter(student=student).select_related('document').order_by('-date_requested')
    
    requests_data = []
    for req in all_requests:
        req_data = {
            'id': req.id,
            'document_name': req.document.name if req.document else 'Unknown',
            'purpose': req.purpose or '',
            'copies': req.copies or 1,
            'status': req.status,
            'status_label': RequestWorkflow.status_label(req.status),
            'badge_class': STATUS_BADGE_MAP.get(req.status, 'bg-light text-dark'),
            'stage_category': STATUS_STAGE_CATEGORY_MAP.get(req.status, 'other'),
            'date_requested': req.date_requested.strftime('%B %d, %Y') if req.date_requested else '',
            'requirements_feedback': req.requirements_feedback or '',
            'payment_feedback': req.payment_feedback or '',
            'requirements_instructions': req.requirements_instructions or '',
        }
        # Determine if action is needed
        if req.status == RequestWorkflow.REQUIREMENTS_SUBMITTED or req.status == RequestWorkflow.PAYMENT_SUBMITTED:
            req_data['action_type'] = 'submitted'
        elif STATUS_STAGE_CATEGORY_MAP.get(req.status) == 'pending':
            req_data['action_type'] = 'cancel'
        elif req.status in REQUIREMENT_ACTION_STATUSES or STATUS_STAGE_CATEGORY_MAP.get(req.status) == 'requirements':
            req_data['action_type'] = 'submit_requirements'
        elif req.status in PAYMENT_ACTION_STATUSES or STATUS_STAGE_CATEGORY_MAP.get(req.status) == 'payment':
            req_data['action_type'] = 'upload_receipt'
        else:
            req_data['action_type'] = 'none'
        
        requests_data.append(req_data)
    
    # Calculate counts for stat cards
    pending_count = sum(1 for r in requests_data if r['stage_category'] == 'pending')
    requirements_count = sum(1 for r in requests_data if r['stage_category'] == 'requirements')
    payment_count = sum(1 for r in requests_data if r['stage_category'] in ('payment', 'processing', 'pickup'))
    completed_count = sum(1 for r in requests_data if r['stage_category'] == 'completed')
    cancelled_count = sum(1 for r in requests_data if r['stage_category'] == 'exceptions')
    
    return JsonResponse({
        'success': True,
        'requests': requests_data,
        'counts': {
            'total': len(requests_data),
            'pending': pending_count,
            'requirements': requirements_count,
            'payment': payment_count,
            'completed': completed_count,
            'cancelled': cancelled_count,
        }
    })


@login_required
def admin_debug_echo(request):
    """Simple authenticated debug endpoint that echoes key headers and POST payload.

    Use this from the browser to confirm that `fetch` is sending cookies/CSRF and
    that expected AJAX headers are present.
    """
    # Collect a subset of headers (safe for debug output)
    headers = {
        'X-Requested-With': request.META.get('HTTP_X_REQUESTED_WITH'),
        'X-CSRFToken': request.META.get('HTTP_X_CSRFTOKEN'),
        'Cookie': request.META.get('HTTP_COOKIE'),
        'User-Agent': request.META.get('HTTP_USER_AGENT'),
        'Host': request.META.get('HTTP_HOST'),
    }

    # Convert POST to a plain dict for JSON serialization
    post_data = {k: v for k, v in request.POST.items()} if request.method == 'POST' else {}

    # Try to decode body (for non-form payloads)
    body_text = None
    try:
        body_text = request.body.decode('utf-8') if request.body else ''
    except Exception:
        body_text = '<binary or undecodable body>'

    resp = {
        'success': True,
        'user': getattr(request.user, 'username', None),
        'is_authenticated': request.user.is_authenticated,
        'method': request.method,
        'headers': headers,
        'post': post_data,
        'body': body_text,
    }
    return JsonResponse(resp)


@never_cache
@login_required
def admin_request_detail(request):
    """Return JSON details for a request (used by admin view modal)."""
    req_id = request.GET.get('request_id') or request.GET.get('id')
    if not req_id:
        return JsonResponse({'success': False, 'error': 'request_id required'}, status=400)

    try:
        AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    try:
        req_obj = Request.objects.select_related('student__user', 'document').get(id=int(req_id))
    except Request.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Request not found'}, status=404)

    # Collect attachments if model exists
    attachments = []
    try:
        for a in req_obj.attachment_set.all():
            attachments.append({
                'id': a.id,
                'url': a.file.url if hasattr(a.file, 'url') else str(a.file),
                'size': a.file_size,
            })
    except Exception:
        # ignore if attachment relation missing
        pass

    data = {
        'success': True,
        'request': {
            'id': req_obj.id,
            'document': req_obj.document.name,
            'purpose': req_obj.purpose,
            'copies': req_obj.copies,
            'status': req_obj.status,
             'status_label': RequestWorkflow.status_label(req_obj.status),
            'notes': req_obj.notes,
            'date_requested': req_obj.date_requested.strftime('%Y-%m-%d %H:%M:%S'),
            'requirements_instructions': req_obj.requirements_instructions,
            'requirements_submission_note': req_obj.requirements_submission_note,
            'requirements_feedback': req_obj.requirements_feedback,
            'requirements_file': req_obj.requirements_submission_file.url if req_obj.requirements_submission_file else None,
            'payment_reference_code': req_obj.payment_reference_code,
            'payment_feedback': req_obj.payment_feedback,
            'payment_receipt': req_obj.payment_receipt if req_obj.payment_receipt else None,
            'payment_submitted_at': req_obj.payment_submitted_at.isoformat() if req_obj.payment_submitted_at else None,
        },
        'student': {
            'name': f"{req_obj.student.first_name} {req_obj.student.last_name}",
            'student_number': req_obj.student.student_number,
            'email': req_obj.student.email,
            'contact': req_obj.student.contact_number,
            'profile_picture': req_obj.student.profile_picture,
        },
        'attachments': attachments,
        'requirement_uploads': [],
    }

    # Include persisted requirement uploads for staff to review
    try:
        req_uploads = []
        for u in req_obj.requirement_uploads.all().order_by('-created_at'):
            uploaded_by_name = ''
            try:
                if u.uploaded_by and hasattr(u.uploaded_by, 'user'):
                    uploaded_by_name = u.uploaded_by.user.get_full_name() or str(u.uploaded_by.user.username)
                elif u.uploaded_by:
                    uploaded_by_name = str(u.uploaded_by)
            except Exception:
                uploaded_by_name = ''

            req_uploads.append({
                'id': u.id,
                'name': u.file_name,
                'url': u.file_url,
                'uploaded_by': uploaded_by_name,
                'content_type': u.content_type,
                'file_size': u.file_size,
                'created_at': u.created_at.isoformat() if hasattr(u, 'created_at') else None,
                'delete_url': u.delete_url or reverse('delete_requirement_upload', args=[u.id])
            })
        data['requirement_uploads'] = req_uploads
    except Exception:
        # ignore errors collecting uploads; admins can still view other details
        pass

    # Include persisted payment uploads for staff review (if any)
    try:
        pay_uploads = []
        for p in req_obj.payment_uploads.all().order_by('-created_at'):
            uploaded_by_name = ''
            try:
                if p.uploaded_by and hasattr(p.uploaded_by, 'user'):
                    uploaded_by_name = p.uploaded_by.user.get_full_name() or str(p.uploaded_by.user.username)
                elif p.uploaded_by:
                    uploaded_by_name = str(p.uploaded_by)
            except Exception:
                uploaded_by_name = ''

            pay_uploads.append({
                'id': p.id,
                'name': p.file_name,
                'url': p.file_url,
                'uploaded_by': uploaded_by_name,
                'content_type': p.content_type,
                'file_size': p.file_size,
                'created_at': p.created_at.isoformat() if hasattr(p, 'created_at') else None,
                'delete_url': p.delete_url or None,
                'supabase_id': p.supabase_id,
            })
        data['payment_uploads'] = pay_uploads
    except Exception:
        pass

    # If there are no DB-backed requirement uploads, try to list objects
    # directly from the Supabase storage bucket under the request's prefix
    try:
        if not data.get('requirement_uploads'):
            bucket = getattr(settings, 'SUPABASE_REQUIREMENTS_BUCKET', 'requirements')
            supabase_client = get_supabase_client()
            listed = None
            if supabase_client:
                try:
                    # supabase client list may expect the prefix as the first positional
                    # argument depending on client version
                    try:
                        listed = supabase_client.storage.from_(bucket).list(f"{req_obj.id}/")
                    except TypeError:
                        listed = supabase_client.storage.from_(bucket).list(prefix=f"{req_obj.id}/")
                except Exception as e:
                    listed = None
                    print('Supabase list error for request', req_obj.id, e)

            # Normalize the returned listing into a Python list named `items`.
            items = []
            try:
                if isinstance(listed, dict) and 'data' in listed:
                    items = listed.get('data') or []
                elif hasattr(listed, 'data'):
                    items = getattr(listed, 'data') or []
                elif isinstance(listed, (list, tuple)):
                    items = list(listed)
                elif listed is None:
                    items = []
                else:
                    # Last resort: try to iterate
                    try:
                        items = list(listed)
                    except Exception:
                        items = []
            except Exception:
                items = []

            print(f'admin_request_detail: supabase list returned {len(items)} items for request {req_obj.id}')

            # If nothing found under the exact prefix, attempt a broader scan
            # of the bucket and filter for object names that include the
            # request id (helps recover files uploaded without the expected
            # prefix). This is a best-effort fallback for existing uploads.
            if not items and supabase_client:
                try:
                    full_list = supabase_client.storage.from_(bucket).list()
                except Exception as e:
                    full_list = None
                    print('Supabase full-list error for request', req_obj.id, e)

                fallback_items = []
                try:
                    if isinstance(full_list, dict) and 'data' in full_list:
                        all_items = full_list.get('data') or []
                    elif hasattr(full_list, 'data'):
                        all_items = getattr(full_list, 'data') or []
                    elif isinstance(full_list, (list, tuple)):
                        all_items = list(full_list)
                    else:
                        try:
                            all_items = list(full_list)
                        except Exception:
                            all_items = []
                except Exception:
                    all_items = []

                for it in all_items:
                    try:
                        name = (it.get('name') if isinstance(it, dict) else getattr(it, 'name', None)) or (it.get('key') if isinstance(it, dict) else getattr(it, 'key', None))
                    except Exception:
                        name = None
                    if not name:
                        continue
                    if f"{req_obj.id}/" in name or name.startswith(f"{req_obj.id}/") or f"/{req_obj.id}/" in name or str(req_obj.id) in name:
                        fallback_items.append(it)

                if fallback_items:
                    print(f'admin_request_detail: fallback found {len(fallback_items)} items for request {req_obj.id}; sample: {[ (i.get("name") if isinstance(i, dict) else getattr(i, "name", None)) for i in fallback_items[:5] ]}')
                    items = fallback_items

            supa_files = []
            for it in items:
                # support dict or object shapes
                name = None
                size = None
                try:
                    if isinstance(it, dict):
                        name = it.get('name') or it.get('key')
                        size = it.get('metadata', {}).get('size') or it.get('size')
                    else:
                        name = getattr(it, 'name', None) or getattr(it, 'key', None)
                        size = getattr(it, 'size', None)
                except Exception:
                    name = None
                    size = None
                if not name:
                    continue
                try:
                    _public = supabase_client.storage.from_(bucket).get_public_url(name) if supabase_client else None
                    # supabase client may return a string or a dict; extract common keys
                    public = None
                    if isinstance(_public, str):
                        public = _public
                    elif isinstance(_public, dict):
                        public = _public.get('publicUrl') or _public.get('publicURL') or _public.get('public_url') or None
                    else:
                        # fallback to string conversion
                        public = str(_public)
                except Exception:
                    public = None
                supa_files.append({
                    'id': None,
                    'name': name.split('/')[-1],
                    'url': public,
                    'uploaded_by': '',
                    'content_type': None,
                    'file_size': size,
                    'created_at': None,
                    'delete_url': None,
                    'supabase_id': name,
                })

            if supa_files:
                data['requirement_uploads'] = supa_files
    except Exception:
        # best-effort only; if Supabase listing fails, do not block admin view
        import traceback
        print('Error while attempting to include supabase files for admin view', req_obj.id)
        traceback.print_exc()

    return JsonResponse(data)

@login_required
def cancel_request(request, request_id):
    # Get the logged-in student's StudentAccount instance
    try:
        student_acc = StudentAccount.objects.get(user=request.user)
    except StudentAccount.DoesNotExist:
        messages.error(request, "Student account not found.")
        return redirect("dashboard")

    # Get the request object only if it belongs to this student
    req = get_object_or_404(Request, id=request_id, student=student_acc)

    # Delete the request
    req.delete()
    messages.success(request, "Request cancelled")
    return redirect("requested_documents")

@login_required
def dashboard_redirect(request):
    """Redirect /dashboard/ depending on user type"""
    if hasattr(request.user, 'adminaccount'):
        return redirect('admin_dashboard')
    elif hasattr(request.user, 'studentaccount'):
        return dashboard(request)
    return redirect('login')


from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def submit_feedback(request):
    """Handle feedback/suggestion submissions from FAQs page"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        page = data.get('page', '')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Send email notification to admin
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'WildDocs Feedback/Suggestion'
        body = f"""
New feedback received:

From: {name or 'Anonymous'}
Email: {email or 'Not provided'}
Page: {page}

Message:
{message}
"""
        
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],  # Send to admin email
                fail_silently=False
            )
        except Exception as e:
            print(f"Failed to send feedback email: {e}")
            # Still return success - feedback was received
        
        return JsonResponse({'success': True, 'message': 'Feedback submitted successfully'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
