from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import StudentAccount, Request, DocumentType, AdminAccount
from django.contrib.auth.decorators import login_required
from django.conf import settings
from accounts.forms import StudentProfileForm
import json
import uuid
import os
from django.views.decorators.cache import never_cache
from django.utils import timezone
from datetime import timedelta
from .decorators import student_required  # ✅ NEW IMPORT


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
            
            # Save locally
            media_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', str(student.student_number))
            os.makedirs(media_dir, exist_ok=True)
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            local_path = os.path.join(media_dir, unique_filename)

            with open(local_path, 'wb') as f:
                for chunk in profile_picture.chunks():
                    f.write(chunk)

            profile_picture_url = os.path.join(
                settings.MEDIA_URL, 'profile_pictures', str(student.student_number), unique_filename
            ).replace('\\', '/')

        # Update fields
        student.first_name = request.POST.get('first_name', student.first_name)
        student.last_name = request.POST.get('last_name', student.last_name)
        student.email = request.POST.get('email', student.email)
        student.course = request.POST.get('course', student.course)
        student.year_level = request.POST.get('year_level', student.year_level)
        student.contact_number = request.POST.get('contact_number', student.contact_number)
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
            status='Pending'
        )
        
        pending_count = Request.objects.filter(student=student, status='Pending').count()
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
            'approved_count': 0,
            'completed_count': 0,
            'recent_requests': [],
            'approved_requests': [],
            'overdue_requests': []
        }

    pending_count = Request.objects.filter(student=student, status='Pending').count()
    approved_count = Request.objects.filter(student=student, status='Approved').count()
    completed_count = Request.objects.filter(student=student, status='Completed').count()
    recent_requests = Request.objects.filter(student=student).order_by('-date_requested')[:3]
    approved_requests = Request.objects.filter(student=student, status='Approved').order_by('-date_requested')[:2]
    threshold_date = timezone.now() - timedelta(days=14)
    overdue_requests = Request.objects.filter(
        student=student, status='Approved', date_requested__lt=threshold_date
    ).order_by('-date_requested')[:2]

    return {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
        'recent_requests': recent_requests,
        'approved_requests': approved_requests,
        'overdue_requests': overdue_requests
    }


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
        'all_requests': Request.objects.filter(student=student).order_by('-date_requested'),
        'pending_requests': Request.objects.filter(student=student, status='Pending'),
        'approved_requests': Request.objects.filter(student=student, status='Approved'),
        'completed_requests': Request.objects.filter(student=student, status='Completed'),
    }
    return render(request, 'requested_documents.html', context)


@never_cache
@login_required
@student_required
def history(request):
    """History of document requests"""
    student_data = get_student_data(request.user)
    student = student_data['student']

    context = {
        **student_data,
        'completed_requests': Request.objects.filter(student=student, status='Completed'),
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

    context = {
        'admin': admin,
        'pending_count': Request.objects.filter(status='Pending').count(),
        'approved_count': Request.objects.filter(status='Approved').count(),
        'rejected_count': Request.objects.filter(status='Rejected').count(),
        'recent_requests': Request.objects.select_related('student', 'document').order_by('-date_requested')[:10],
    }
    return render(request, 'admin/admin_dashboard.html', context)


@never_cache
@login_required
def admin_document_requests(request):
    """Admin document requests management"""
    try:
        AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        messages.error(request, "Access denied: staff accounts only.")
        return redirect('dashboard')

    context = {
        'all_requests': Request.objects.select_related('student', 'document').order_by('-date_requested')
    }
    return render(request, 'admin/admin_document_requests.html', context)


@never_cache
@login_required
def admin_manage_students(request):
    """Admin manage students page"""
    try:
        AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        messages.error(request, "Access denied: staff accounts only.")
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
        messages.error(request, "Access denied: staff accounts only.")
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

    try:
        AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    req_id = request.POST.get('request_id') or request.POST.get('id')
    action = request.POST.get('action')
    note = request.POST.get('note', '')

    if not req_id or not action:
        return JsonResponse({'success': False, 'error': 'Missing parameters'}, status=400)

    try:
        req_obj = Request.objects.select_related('student', 'document').get(id=int(req_id))
    except Request.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Request not found'}, status=404)

    action = action.lower()
    valid_actions = ['approve', 'reject', 'complete', 'cancel']
    if action not in valid_actions:
        return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)

    admin = AdminAccount.objects.get(user=request.user)

    if action == 'approve':
        req_obj.status = 'Approved'
        req_obj.assigned_admin = admin
        if note:
            req_obj.notes = (req_obj.notes or '') + f"\n[Approved by {admin.user.username}]: {note}"
    elif action == 'reject':
        req_obj.status = 'Rejected'
        req_obj.assigned_admin = admin
        if note:
            req_obj.notes = (req_obj.notes or '') + f"\n[Rejected by {admin.user.username}]: {note}"
    elif action == 'complete':
        req_obj.status = 'Completed'
        req_obj.assigned_admin = admin
        if note:
            req_obj.notes = (req_obj.notes or '') + f"\n[Completed by {admin.user.username}]: {note}"
    elif action == 'cancel':
        req_obj.status = 'Cancelled'
        req_obj.assigned_admin = admin
        if note:
            req_obj.notes = (req_obj.notes or '') + f"\n[Cancelled by {admin.user.username}]: {note}"

    req_obj.save()

    # Optionally: create a Notification for the student (lightweight)
    try:
        from accounts.models import Notification
        Notification.objects.create(
            student=req_obj.student,
            request=req_obj,
            message=f"Your request #{req_obj.id} has been updated to '{req_obj.status}'."
        )
    except Exception:
        # don't block action if notification creation fails
        pass

    return JsonResponse({'success': True, 'status': req_obj.status, 'request_id': req_obj.id})


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
            'notes': req_obj.notes,
            'date_requested': req_obj.date_requested.strftime('%Y-%m-%d %H:%M:%S'),
        },
        'student': {
            'name': f"{req_obj.student.first_name} {req_obj.student.last_name}",
            'student_number': req_obj.student.student_number,
            'email': req_obj.student.email,
            'contact': req_obj.student.contact_number,
            'profile_picture': req_obj.student.profile_picture,
        },
        'attachments': attachments,
    }

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
