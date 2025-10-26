from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import StudentAccount, Request, DocumentType
from django.contrib.auth.decorators import login_required
from django.conf import settings
from accounts.forms import StudentProfileForm
import json
import uuid
import os
from django.views.decorators.cache import never_cache


@never_cache
@login_required
def dashboard(request):
    # Extra guard: if the user is not authenticated ensure we redirect to login.
    # This prevents rendering the dashboard for anonymous users even if the decorator
    # were accidentally removed in the future.
    if hasattr(request.user, 'adminaccount'):
        return redirect('admin_dashboard')

    if not request.user.is_authenticated:
        # Preserve next parameter so user returns to dashboard after login
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")
    try:
        student = StudentAccount.objects.get(user=request.user)
        student_name = str(student)
        student_id_number = student.student_number
    except StudentAccount.DoesNotExist:
        student = None
        student_name = "Unknown"
        student_id_number = "N/A"
    
    # Handle document request submission and profile updates
    if request.method == 'POST':
        # Check if this is a profile update request
        if request.POST.get('action') == 'update_profile':
            try:
                if not student:
                    return JsonResponse({'success': False, 'error': 'Student account not found'})
                
                form = StudentProfileForm(request.POST, request.FILES, instance=student)
                if form.is_valid():
                    updated_student = form.save()
                    
                    # Prepare response data
                    response_data = {
                        'success': True,
                        'message': 'Profile updated successfully!',
                        'student': {
                            'first_name': updated_student.first_name,
                            'last_name': updated_student.last_name,
                            'course': updated_student.course,
                            'program': updated_student.program,
                            'year_level': updated_student.year_level,
                            'email': updated_student.email,
                            'contact_number': updated_student.contact_number,
                                'profile_picture_url': updated_student.profile_picture if updated_student.profile_picture else None
                        }
                    }
                    
                    # Update student_name for context
                    student_name = str(updated_student)
                    
                    return JsonResponse(response_data)
                else:
                    # Return form errors
                    errors = []
                    for field, error_list in form.errors.items():
                        for error in error_list:
                            errors.append(f"{field}: {error}")
                    return JsonResponse({'success': False, 'error': '; '.join(errors)})
                    
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # Handle document request submission (existing code)
        try:
            document_type = request.POST.get('document_type')
            purpose = request.POST.get('purpose')
            copies = request.POST.get('copies', 1)
            
            # Map document type values to document names (matching the database exactly)
            document_mapping = {
                'transcript': 'Transcript of Records',
                'enrollment': 'Certificate of Enrollment',
                'diploma': 'Diploma Copy',
                'moral': 'Certificate of Good Moral',
                'graduation': 'Certificate of Graduation',
                'dismissal': 'Honorable Dismissal'  # This will be created if it doesn't exist
            }
            
            document_name = document_mapping.get(document_type)
            if not document_name:
                return JsonResponse({'success': False, 'error': f'Invalid document type: {document_type}'})
            
            # Try to get existing document type first
            try:
                document = DocumentType.objects.get(name=document_name)
            except DocumentType.DoesNotExist:
                # If not found, create with default values
                document = DocumentType.objects.create(
                    name=document_name,
                    description=f'Request for {document_name}',
                    fee=100.00
                )
            
            # Create the request
                if student:
                    new_request = Request.objects.create(
                        student=student,
                        document=document,
                        purpose=purpose,
                        copies=int(copies),
                        status='Pending'
                    )
                    # Return serialized info so the frontend can update without a full reload
                    pending_count = Request.objects.filter(student=student, status='Pending').count()
                    request_data = {
                        'id': new_request.id,
                        'document_name': new_request.document.name,
                        'status': new_request.status,
                        'date_requested': new_request.date_requested.strftime('%B %d, %Y'),
                        'copies': new_request.copies,
                        'purpose': new_request.purpose,
                    }
                    return JsonResponse({'success': True, 'message': 'Request submitted successfully!', 'request': request_data, 'pending_count': pending_count})
            else:
                return JsonResponse({'success': False, 'error': 'Student account not found'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Get request counts for dashboard stats  
    pending_count = Request.objects.filter(student=student, status='Pending').count() if student else 0
    approved_count = Request.objects.filter(student=student, status='Approved').count() if student else 0
    completed_count = Request.objects.filter(student=student, status='Completed').count() if student else 0
    
    # Get recent requests for display
    recent_requests = Request.objects.filter(student=student).order_by('-date_requested')[:3] if student else []
    
    # Get approved requests for reminders
    approved_requests = Request.objects.filter(student=student, status='Approved').order_by('-date_requested')[:2] if student else []
    
    # Get overdue approved requests (older than 14 days)
    from django.utils import timezone
    from datetime import timedelta
    threshold_date = timezone.now() - timedelta(days=14)
    overdue_requests = Request.objects.filter(
        student=student, 
        status='Approved',
        date_requested__lt=threshold_date
    ).order_by('-date_requested')[:2] if student else []
    
    context = {
        'student': student,
        'student_name': student_name,
        'student_id_number': student_id_number,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
        'recent_requests': recent_requests,
        'approved_requests': approved_requests,
        'overdue_requests': overdue_requests,
    }
    
    return render(request, 'dashboard.html', context)


@never_cache
@login_required
def student_profile(request):
    try:
        student = StudentAccount.objects.get(user=request.user)
        student_name = str(student)
        student_id_number = student.student_number
    except StudentAccount.DoesNotExist:
        student = None
        student_name = "Unknown"
        student_id_number = "N/A"
    
    # Handle profile update requests
    if request.method == 'POST' and request.POST.get('action') == 'update_profile':
        try:
            if not student:
                return JsonResponse({'success': False, 'error': 'Student account not found'})
            
            # Handle profile picture upload to Supabase
            profile_picture_url = student.profile_picture  # Keep existing URL
            
            if 'profile_picture' in request.FILES:
                profile_picture = request.FILES['profile_picture']

                # Validate file size (max 10MB)
                if profile_picture.size > 10 * 1024 * 1024:
                    return JsonResponse({'success': False, 'error': 'Image file too large. Maximum size is 10MB.'})

                # Validate extension
                file_extension = os.path.splitext(profile_picture.name)[1].lower()
                if file_extension not in ['.jpg', '.jpeg', '.png', '.gif']:
                    return JsonResponse({'success': False, 'error': 'Invalid file format. Please use JPG, PNG, or GIF.'})

                # Save file locally to MEDIA_ROOT/profile_pictures/<student_number>/
                from django.conf import settings
                media_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', str(student.student_number))
                os.makedirs(media_dir, exist_ok=True)

                unique_filename = f"{uuid.uuid4()}{file_extension}"
                local_path = os.path.join(media_dir, unique_filename)

                try:
                    with open(local_path, 'wb') as f:
                        for chunk in profile_picture.chunks():
                            f.write(chunk)

                    # Build a URL path for serving via MEDIA_URL
                    profile_picture_url = os.path.join(settings.MEDIA_URL, 'profile_pictures', str(student.student_number), unique_filename).replace('\\', '/')

                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Failed to save uploaded image locally: {e}'})
            
            # Update other fields
            student.first_name = request.POST.get('first_name', student.first_name)
            student.last_name = request.POST.get('last_name', student.last_name)
            student.email = request.POST.get('email', student.email)
            student.course = request.POST.get('course', student.course)
            student.year_level = request.POST.get('year_level', student.year_level)
            student.contact_number = request.POST.get('contact_number', student.contact_number)
            student.profile_picture = profile_picture_url
            
            # Auto-determine program based on course
            if student.course:
                if any(keyword in student.course for keyword in ['Engineering', 'Architecture']):
                    student.program = 'College of Engineering & Architecture'
                elif any(keyword in student.course for keyword in ['Business', 'Accountancy', 'Hospitality', 'Tourism', 'Office Administration', 'Public Administration']):
                    student.program = 'College of Business & Accountancy'
                elif any(keyword in student.course for keyword in ['Information Technology', 'Computer Science', 'Information Systems']):
                    student.program = 'College of Computer Studies'
                elif any(keyword in student.course for keyword in ['Communication', 'English', 'Education', 'Multimedia', 'Biology', 'Math', 'Psychology']):
                    student.program = 'College of Arts, Sciences & Education'
                elif any(keyword in student.course for keyword in ['Nursing', 'Pharmacy', 'Medical Technology']):
                    student.program = 'College of Nursing & Allied Health Sciences'
                elif 'Criminology' in student.course:
                    student.program = 'College of Criminal Justice'
            
            student.save()
            
            response_data = {
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
            }
            
            return JsonResponse(response_data)
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    context = {
        'student': student,
        'student_name': student_name,
        'student_id_number': student_id_number,
    }
    
    return render(request, 'student_profile.html', context)


@never_cache
@login_required
def requested_documents(request):
    try:
        student = StudentAccount.objects.get(user=request.user)
        student_name = str(student)
        student_id_number = student.student_number
    except StudentAccount.DoesNotExist:
        student = None
        student_name = "Unknown"
        student_id_number = "N/A"
    
    # Get all requests for display
    all_requests = Request.objects.filter(student=student).order_by('-date_requested') if student else []
    pending_requests = Request.objects.filter(student=student, status='Pending').order_by('-date_requested') if student else []
    approved_requests = Request.objects.filter(student=student, status='Approved').order_by('-date_requested') if student else []
    completed_requests = Request.objects.filter(student=student, status='Completed').order_by('-date_requested') if student else []
    
    context = {
        'student': student,
        'student_name': student_name,
        'student_id_number': student_id_number,
        'all_requests': all_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'completed_requests': completed_requests,
    }
    
    return render(request, 'requested_documents.html', context)


@never_cache
@login_required
def history(request):
    try:
        student = StudentAccount.objects.get(user=request.user)
        student_name = str(student)
        student_id_number = student.student_number
    except StudentAccount.DoesNotExist:
        student = None
        student_name = "Unknown"
        student_id_number = "N/A"
    
    # Get completed requests for history
    completed_requests = Request.objects.filter(student=student, status='Completed').order_by('-date_requested') if student else []
    all_requests = Request.objects.filter(student=student).order_by('-date_requested') if student else []
    
    context = {
        'student': student,
        'student_name': student_name,
        'student_id_number': student_id_number,
        'completed_requests': completed_requests,
        'all_requests': all_requests,
    }
    
    return render(request, 'history.html', context)


@never_cache
@login_required
def about_us(request):
    try:
        student = StudentAccount.objects.get(user=request.user)
        student_name = str(student)
        student_id_number = student.student_number
    except StudentAccount.DoesNotExist:
        student = None
        student_name = "Unknown"
        student_id_number = "N/A"
    
    context = {
        'student': student,
        'student_name': student_name,
        'student_id_number': student_id_number,
    }
    
    return render(request, 'about_us.html', context)


@never_cache
@login_required
def faqs(request):
    try:
        student = StudentAccount.objects.get(user=request.user)
        student_name = str(student)
        student_id_number = student.student_number
    except StudentAccount.DoesNotExist:
        student = None
        student_name = "Unknown"
        student_id_number = "N/A"
    
    context = {
        'student': student,
        'student_name': student_name,
        'student_id_number': student_id_number,
    }
    
    return render(request, 'faqs.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from accounts.models import AdminAccount, Request

@never_cache
@login_required
def admin_dashboard(request):
    # Ensure only staff/admin users can access
    try:
        admin = AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        messages.error(request, "Access denied: Staff account required.")
        return redirect('dashboard')  # Redirect non-staff users safely

    # --- Dashboard metrics ---
    pending_count = Request.objects.filter(status='Pending').count()
    approved_count = Request.objects.filter(status='Approved').count()
    rejected_count = Request.objects.filter(status='Rejected').count()

    # --- Recent requests table ---
    recent_requests = Request.objects.select_related('student', 'document').order_by('-date_requested')[:10]

    context = {
        'admin': admin,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'recent_requests': recent_requests,
    }

    # ✅ This was missing
    return render(request, 'admin/admin_dashboard.html', context)


@never_cache
@login_required
def admin_document_requests(request):
    try:
        AdminAccount.objects.get(user=request.user)
    except AdminAccount.DoesNotExist:
        messages.error(request, "Access denied: staff accounts only.")
        return redirect('dashboard')

    all_requests = Request.objects.select_related('student', 'document').order_by('-date_requested')

    context = {
        'all_requests': all_requests
    }
    return render(request, 'admin/admin_document_requests.html', context)

@login_required
def dashboard_redirect(request):
    """
    Redirect /dashboard/ if a staff is logged in.
    Students can stay on /dashboard/.
    """
    if hasattr(request.user, 'adminaccount'):
        return redirect('admin_dashboard')
    elif hasattr(request.user, 'studentaccount'):
        # Student stays in dashboard
        from .views import dashboard
        return dashboard(request)
    else:
        return redirect('login')
    
    
