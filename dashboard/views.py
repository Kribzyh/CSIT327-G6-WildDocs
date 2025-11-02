from django.shortcuts import render, redirect
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


@login_required
def dashboard_redirect(request):
    """Redirect /dashboard/ depending on user type"""
    if hasattr(request.user, 'adminaccount'):
        return redirect('admin_dashboard')
    elif hasattr(request.user, 'studentaccount'):
        return dashboard(request)
    return redirect('login')
