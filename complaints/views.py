import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Case, Count, IntegerField, Q, When
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    ComplaintForm,
    CustomUserCreationForm,
    ProfileForm,
    UserUpdateForm,
)
from .models import Complaint, Notification

DEBUG_LOG_PATH = Path(__file__).resolve().parent.parent / 'debug-264829.log'


def _debug_log(hypothesis_id, location, message, data=None, run_id='initial'):
    # #region agent log
    payload = {
        'sessionId': '264829',
        'runId': run_id,
        'hypothesisId': hypothesis_id,
        'location': location,
        'message': message,
        'data': data or {},
        'timestamp': int(__import__('time').time() * 1000),
    }
    with open(DEBUG_LOG_PATH, 'a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(payload) + '\n')
    # #endregion


def _parse_date(date_value):
    if not date_value:
        return None
    try:
        return datetime.strptime(date_value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _priority_rank_expression():
    return Case(
        When(priority='Emergency', then=0),
        When(priority='High', then=1),
        When(priority='Medium', then=2),
        default=3,
        output_field=IntegerField(),
    )


def _build_filtered_queryset(request, queryset):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    location = request.GET.get('location', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
            | Q(user__username__icontains=query)
        )

    if category:
        queryset = queryset.filter(category=category)
    if status:
        queryset = queryset.filter(status=status)
    if priority:
        queryset = queryset.filter(priority=priority)
    if location:
        queryset = queryset.filter(location__icontains=location)

    parsed_from = _parse_date(date_from)
    parsed_to = _parse_date(date_to)
    if parsed_from:
        queryset = queryset.filter(created_at__date__gte=parsed_from)
    if parsed_to:
        queryset = queryset.filter(created_at__date__lte=parsed_to)

    return queryset, {
        'query': query,
        'category': category,
        'status': status,
        'priority': priority,
        'location': location,
        'date_from': date_from,
        'date_to': date_to,
    }


def _serialize_chart(values, label_key, value_key='count'):
    return {
        'labels': json.dumps([item[label_key] for item in values]),
        'values': json.dumps([item[value_key] for item in values]),
    }


def _send_sms_message(phone_number, message):
    if not settings.SMS_WEBHOOK_URL or not phone_number:
        return False

    payload = json.dumps({
        'to': phone_number,
        'message': message,
        'sender': settings.SMS_SENDER_ID,
    }).encode('utf-8')
    request = Request(
        settings.SMS_WEBHOOK_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.SMS_AUTH_TOKEN}',
        } if settings.SMS_AUTH_TOKEN else {
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urlopen(request, timeout=5):
            return True
    except Exception:
        return False


def _send_user_sms(user, message):
    try:
        phone_number = user.profile.phone
    except Exception:
        phone_number = ''
    return _send_sms_message(phone_number, message)


def _notify_user_and_email(user, subject, email_message, notification_message, sms_message=None):
    Notification.objects.create(user=user, message=notification_message)
    if user.email:
        send_mail(
            subject,
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    if sms_message:
        _send_user_sms(user, sms_message)


def _notify_emergency_admins(complaint):
    if complaint.priority != 'Emergency':
        return

    staff_users = User.objects.filter(is_staff=True).exclude(email='')
    if staff_users.exists():
        send_mail(
            'Emergency Complaint Alert',
            (
                f'An emergency complaint "{complaint.title}" was submitted by '
                f'{complaint.display_user} for {complaint.location or "an unspecified location"}.'
            ),
            settings.DEFAULT_FROM_EMAIL,
            list(staff_users.values_list('email', flat=True)),
            fail_silently=True,
        )

    for staff_user in User.objects.filter(is_staff=True):
        Notification.objects.create(
            user=staff_user,
            message=f'Emergency complaint "{complaint.title}" needs urgent attention.',
        )
        _send_user_sms(
            staff_user,
            f'Emergency alert: {complaint.title} at {complaint.location or "unknown location"}.',
        )


def _build_login_redirect(next_url=None):
    login_url = reverse('login')
    if next_url:
        return f'{login_url}?{urlencode({"next": next_url})}'
    return login_url


def home(request):
    _debug_log('H4', 'complaints/views.py:204', 'home view entry', {
        'authenticated': bool(request.user.is_authenticated),
        'path': request.path,
        'method': request.method,
    })
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def register(request):
    _debug_log('H3', 'complaints/views.py:214', 'register view entry', {
        'method': request.method,
        'has_next': bool(request.GET.get('next') or request.POST.get('next')),
    })
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next') or request.POST.get('next')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! You can now login.')
            return redirect(_build_login_redirect(next_url))
    else:
        form = CustomUserCreationForm()

    return render(request, 'complaints/register.html', {'form': form, 'next': next_url})


@login_required
def profile(request):
    try:
        profile = request.user.profile
    except Exception:
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'complaints/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })


@login_required
def dashboard(request):
    _debug_log('H5', 'complaints/views.py:259', 'dashboard view entry', {
        'user': request.user.username,
        'is_staff': bool(request.user.is_staff),
        'query_params': list(request.GET.keys()),
    })
    base_query = Complaint.objects.all() if request.user.is_staff else Complaint.objects.filter(user=request.user)
    filtered_complaints, active_filters = _build_filtered_queryset(request, base_query)
    filtered_complaints = filtered_complaints.annotate(
        priority_rank=_priority_rank_expression()
    ).order_by('priority_rank', '-created_at')

    chart_data = filtered_complaints.values('category').annotate(count=Count('id'))
    monthly_data = (
        filtered_complaints.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    month_labels = [item['month'].strftime('%b %Y') for item in monthly_data if item['month']]
    month_counts = [item['count'] for item in monthly_data]
    hotspot_data = list(
        filtered_complaints.exclude(location='')
        .values('location')
        .annotate(count=Count('id'))
        .order_by('-count', 'location')[:5]
    )
    recent_activity = (
        request.user.notifications.order_by('-created_at')[:5]
        if not request.user.is_staff
        else Notification.objects.select_related('user').order_by('-created_at')[:5]
    )

    context = {
        'complaints': filtered_complaints,
        'total': filtered_complaints.count(),
        'pending': filtered_complaints.filter(status='Pending').count(),
        'assigned': filtered_complaints.filter(status='Assigned').count(),
        'in_progress': filtered_complaints.filter(status='In Progress').count(),
        'resolved': filtered_complaints.filter(status='Resolved').count(),
        'emergency': filtered_complaints.filter(priority='Emergency').count(),
        'high_priority': filtered_complaints.filter(priority='High').count(),
        'labels': json.dumps([item['category'] for item in chart_data]),
        'data': json.dumps([item['count'] for item in chart_data]),
        'month_labels': json.dumps(month_labels),
        'month_counts': json.dumps(month_counts),
        'hotspots': hotspot_data,
        'top_hotspot_count': hotspot_data[0]['count'] if hotspot_data else 1,
        'recent_activity': recent_activity,
        'category_choices': Complaint.CATEGORY_CHOICES,
        'status_choices': Complaint.STATUS_CHOICES,
        'priority_choices': Complaint.PRIORITY_CHOICES,
        **active_filters,
    }

    return render(request, 'complaints/dashboard.html', context)


@login_required
def create_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            _notify_user_and_email(
                request.user,
                'Complaint Raised Successfully',
                f'Your complaint "{complaint.title}" is now registered with status {complaint.status}.',
                f'Your complaint "{complaint.title}" has been raised successfully.',
                f'Complaint submitted: {complaint.title}. Status {complaint.status}.',
            )
            _notify_emergency_admins(complaint)

            messages.success(request, 'Complaint registered successfully.')
            return redirect('dashboard')
    else:
        form = ComplaintForm(user=request.user)

    return render(request, 'complaints/create.html', {'form': form})


@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if not request.user.is_staff and complaint.user != request.user:
        messages.error(request, 'You do not have permission to view that complaint.')
        return redirect('dashboard')

    comment_form = CommentForm(request.POST or None)
    if request.method == 'POST' and request.user.is_staff:
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.complaint = complaint
            comment.admin = request.user
            comment.save()
            _notify_user_and_email(
                complaint.user,
                f'Complaint Update for "{complaint.title}"',
                f'New admin remark: {comment.message}',
                f'Admin updated your complaint "{complaint.title}".',
                f'Admin update on {complaint.title}: {comment.message[:100]}',
            )
            messages.success(request, 'Update posted successfully.')
            return redirect('complaint_detail', pk=pk)

    return render(request, 'complaints/complaint_detail.html', {
        'complaint': complaint,
        'comment_form': comment_form,
        'status_choices': Complaint.STATUS_CHOICES,
        'staff_users': User.objects.filter(is_staff=True).order_by('username'),
    })


@login_required
@require_POST
def update_status(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Access Denied.')
        return redirect('dashboard')

    complaint = get_object_or_404(Complaint, pk=pk)
    valid_statuses = {choice[0] for choice in Complaint.STATUS_CHOICES}
    requested_status = request.POST.get('status', complaint.status)
    assigned_id = request.POST.get('assigned_to', '').strip()

    if requested_status not in valid_statuses:
        messages.error(request, 'Invalid complaint status selected.')
        return redirect('complaint_detail', pk=pk)

    complaint.status = requested_status
    complaint.assigned_to = None
    if assigned_id:
        complaint.assigned_to = get_object_or_404(User, pk=assigned_id, is_staff=True)
    complaint.save()
    _notify_user_and_email(
        complaint.user,
        f'Complaint Status Updated: "{complaint.title}"',
        (
            f'Your complaint "{complaint.title}" is now marked as {complaint.status}. '
            f'Assigned to: {complaint.assigned_to.username if complaint.assigned_to else "Unassigned"}.'
        ),
        f'Complaint "{complaint.title}" status updated to {complaint.status}.',
        (
            f'Status update: {complaint.title} is {complaint.status}. '
            f'Assigned to {complaint.assigned_to.username if complaint.assigned_to else "none"}.'
        ),
    )
    messages.success(request, f'Complaint #{pk} updated to {complaint.status}.')
    return redirect('complaint_detail', pk=pk)


@login_required
def export_complaints_csv(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    complaints, _ = _build_filtered_queryset(request, Complaint.objects.all())
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Title', 'Category', 'Location', 'Priority', 'Status', 'Assigned To', 'Created At'])

    for c in complaints.order_by('-created_at'):
        writer.writerow([
            c.id,
            c.display_user,
            c.title,
            c.category,
            c.location,
            c.priority,
            c.status,
            c.assigned_to.username if c.assigned_to else 'Unassigned',
            c.created_at,
        ])

    return response


@login_required
def notifications(request):
    notifications = request.user.notifications.order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'complaints/notifications.html', {'notifications': notifications})


@login_required
@require_POST
def reopen_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, user=request.user)
    if complaint.status != 'Resolved':
        messages.warning(request, 'Only resolved complaints can be reopened.')
        return redirect('complaint_detail', pk=pk)

    complaint.status = 'In Progress'
    complaint.save()
    _notify_user_and_email(
        request.user,
        f'Complaint Reopened: "{complaint.title}"',
        f'Your complaint "{complaint.title}" has been reopened and is now In Progress.',
        f'Complaint "{complaint.title}" has been reopened.',
        f'Complaint reopened: {complaint.title} is now In Progress.',
    )
    messages.success(request, 'Complaint reopened successfully.')
    return redirect('complaint_detail', pk=pk)


@login_required
def reports(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    complaints, active_filters = _build_filtered_queryset(request, Complaint.objects.all())
    total = complaints.count()
    resolved = complaints.filter(status='Resolved').count()
    pending = complaints.filter(status='Pending').count()
    emergency = complaints.filter(priority='Emergency').count()
    users = User.objects.count()
    assigned = complaints.filter(status='Assigned').count()
    in_progress = complaints.filter(status='In Progress').count()
    resolution_rate = round((resolved / total) * 100, 1) if total else 0

    category_data = list(complaints.values('category').annotate(count=Count('id')).order_by('-count', 'category'))
    status_data = list(complaints.values('status').annotate(count=Count('id')).order_by('status'))
    priority_data = list(complaints.values('priority').annotate(count=Count('id')).order_by('priority'))
    hotspot_data = list(
        complaints.exclude(location='')
        .values('location')
        .annotate(count=Count('id'))
        .order_by('-count', 'location')[:10]
    )
    monthly_data = list(
        complaints.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_chart = {
        'labels': json.dumps([item['month'].strftime('%b %Y') for item in monthly_data if item['month']]),
        'values': json.dumps([item['count'] for item in monthly_data]),
    }
    category_chart = _serialize_chart(category_data, 'category')
    status_chart = _serialize_chart(status_data, 'status')
    priority_chart = _serialize_chart(priority_data, 'priority')
    hotspot_chart = _serialize_chart(hotspot_data, 'location')
    user_data = (
        User.objects.annotate(complaint_count=Count('complaints'))
        .filter(complaint_count__gt=0)
        .order_by('-complaint_count', 'username')[:10]
    )

    return render(request, 'complaints/reports.html', {
        'total': total,
        'resolved': resolved,
        'pending': pending,
        'assigned': assigned,
        'in_progress': in_progress,
        'emergency': emergency,
        'users': users,
        'resolution_rate': resolution_rate,
        'category_data': category_data,
        'status_data': status_data,
        'priority_data': priority_data,
        'hotspot_data': hotspot_data,
        'monthly_chart': monthly_chart,
        'category_chart': category_chart,
        'status_chart': status_chart,
        'priority_chart': priority_chart,
        'hotspot_chart': hotspot_chart,
        'top_users': user_data,
        **active_filters,
    })


@login_required
def manage_users(request):
    if not request.user.is_staff:
        messages.error(request, 'Access Denied.')
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    users = User.objects.annotate(
        complaint_count=Count('complaints', distinct=True),
        assigned_count=Count('assigned_complaints', distinct=True),
    ).order_by('-is_staff', 'username')

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
        )

    return render(request, 'complaints/manage_users.html', {
        'managed_users': users,
        'query': query,
        'total_users': User.objects.count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
        'active_reporters': User.objects.filter(complaints__isnull=False).distinct().count(),
    })


@login_required
@require_POST
def delete_complaint(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Access Denied.')
        return redirect('dashboard')

    complaint = get_object_or_404(Complaint, pk=pk)
    complaint_title = complaint.title
    complaint_user = complaint.user
    complaint.delete()
    _notify_user_and_email(
        complaint_user,
        f'Complaint Removed: "{complaint_title}"',
        f'Your complaint "{complaint_title}" was removed by an administrator.',
        f'Complaint "{complaint_title}" was removed by an administrator.',
        f'Complaint removed by admin: {complaint_title}.',
    )
    messages.success(request, f'Complaint "{complaint_title}" deleted successfully.')
    return redirect('dashboard')
