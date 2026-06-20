from django.contrib.auth.models import User
from django.core import mail
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import Comment, Complaint, Notification, Profile


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    SECURE_HSTS_SECONDS=0,
)
class ComplaintSystemTests(TestCase):
    def setUp(self):
        self.password = 'StrongPass123!'
        self.user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password=self.password,
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password=self.password,
        )
        self.staff_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password=self.password,
            is_staff=True,
        )
        self.staff_user_two = User.objects.create_user(
            username='supportstaff',
            email='support@example.com',
            password=self.password,
            is_staff=True,
        )
        self.complaint = Complaint.objects.create(
            user=self.user,
            title='Water pipe leak',
            category='Water Leakage',
            description='Pipe is leaking near the lab.',
            location='Science Block',
            priority='High',
        )

    def login_user(self, user=None):
        user = user or self.user
        self.client.login(username=user.username, password=self.password)

    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newstudent',
                'email': 'newstudent@example.com',
                'password1': 'VeryStrongPass123!',
                'password2': 'VeryStrongPass123!',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('login'))
        created_user = User.objects.get(username='newstudent')
        self.assertTrue(Profile.objects.filter(user=created_user).exists())

    def test_dashboard_renders_for_authenticated_user(self):
        self.login_user()

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SmartFix Dashboard')
        self.assertContains(response, self.complaint.title)

    def test_home_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse('home'))

        self.assertRedirects(response, reverse('login'))

    def test_home_redirects_authenticated_user_to_dashboard(self):
        self.login_user()

        response = self.client.get(reverse('home'))

        self.assertRedirects(response, reverse('dashboard'))

    def test_login_page_preserves_next_redirect(self):
        response = self.client.get(reverse('login'), {'next': reverse('complaint_detail', args=[self.complaint.pk])})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="next"')
        self.assertContains(response, reverse('complaint_detail', args=[self.complaint.pk]))

    def test_register_page_preserves_next_redirect(self):
        response = self.client.get(reverse('register'), {'next': reverse('create_complaint')})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="next"')
        self.assertContains(response, reverse('create_complaint'))

    def test_login_redirects_to_requested_protected_page(self):
        target_url = reverse('complaint_detail', args=[self.complaint.pk])
        response = self.client.post(
            reverse('login'),
            {
                'username': self.user.username,
                'password': self.password,
                'next': target_url,
            },
            follow=True,
        )

        self.assertRedirects(response, target_url)
        self.assertContains(response, self.complaint.title)

    def test_register_redirects_to_login_with_next_value(self):
        target_url = reverse('create_complaint')
        response = self.client.post(
            reverse('register'),
            {
                'username': 'redirectstudent',
                'email': 'redirectstudent@example.com',
                'password1': 'VeryStrongPass123!',
                'password2': 'VeryStrongPass123!',
                'next': target_url,
            },
        )

        self.assertRedirects(response, f"{reverse('login')}?next=%2Fcomplaint%2Fcreate%2F", fetch_redirect_response=False)

    def test_user_can_create_complaint_and_notification(self):
        self.login_user()

        response = self.client.post(
            reverse('create_complaint'),
            {
                'title': 'Internet down',
                'category': 'Internet Issue',
                'description': 'Wi-Fi is not working in the hostel.',
                'location': 'Hostel A',
                'priority': 'Emergency',
                'is_anonymous': True,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('dashboard'))
        created = Complaint.objects.get(title='Internet down')
        self.assertEqual(created.user, self.user)
        self.assertTrue(created.is_anonymous)
        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                message__icontains='raised successfully',
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.staff_user,
                message__icontains='Emergency complaint',
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 2)

    def test_owner_can_view_detail_page(self):
        self.login_user()

        response = self.client.get(reverse('complaint_detail', args=[self.complaint.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.complaint.description)
        self.assertContains(response, 'Activity Timeline')

    def test_other_user_cannot_view_someone_elses_complaint(self):
        self.login_user(self.other_user)

        response = self.client.get(
            reverse('complaint_detail', args=[self.complaint.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertContains(response, 'You do not have permission to view that complaint.')

    def test_staff_can_update_status_assign_and_comment(self):
        self.login_user(self.staff_user)

        status_response = self.client.post(
            reverse('update_status', args=[self.complaint.pk]),
            {
                'status': 'In Progress',
                'assigned_to': str(self.staff_user.pk),
            },
            follow=True,
        )

        self.assertRedirects(status_response, reverse('complaint_detail', args=[self.complaint.pk]))
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'In Progress')
        self.assertEqual(self.complaint.assigned_to, self.staff_user)
        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                message__icontains='status updated to In Progress',
            ).exists()
        )

        comment_response = self.client.post(
            reverse('complaint_detail', args=[self.complaint.pk]),
            {'message': 'Technician assigned and inspection scheduled.'},
            follow=True,
        )

        self.assertRedirects(comment_response, reverse('complaint_detail', args=[self.complaint.pk]))
        self.assertTrue(
            Comment.objects.filter(
                complaint=self.complaint,
                admin=self.staff_user,
                message='Technician assigned and inspection scheduled.',
            ).exists()
        )
        self.assertGreaterEqual(len(mail.outbox), 2)

    def test_invalid_status_update_is_rejected(self):
        self.login_user(self.staff_user)

        response = self.client.post(
            reverse('update_status', args=[self.complaint.pk]),
            {'status': 'Broken'},
            follow=True,
        )

        self.assertRedirects(response, reverse('complaint_detail', args=[self.complaint.pk]))
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'Pending')
        self.assertContains(response, 'Invalid complaint status selected.')

    def test_resolved_complaint_can_be_reopened_with_post(self):
        self.complaint.status = 'Resolved'
        self.complaint.save()
        self.login_user()

        response = self.client.post(
            reverse('reopen_complaint', args=[self.complaint.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse('complaint_detail', args=[self.complaint.pk]))
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'In Progress')
        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                message__icontains='has been reopened',
            ).exists()
        )

    def test_notifications_page_marks_items_as_read(self):
        Notification.objects.create(user=self.user, message='Test notification')
        self.login_user()

        response = self.client.get(reverse('notifications'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test notification')
        self.assertFalse(self.user.notifications.filter(is_read=False).exists())

    def test_password_reset_pages_render(self):
        reset_form = self.client.get(reverse('password_reset'))
        reset_done = self.client.get(reverse('password_reset_done'))
        reset_complete = self.client.get(reverse('password_reset_complete'))

        self.assertEqual(reset_form.status_code, 200)
        self.assertEqual(reset_done.status_code, 200)
        self.assertEqual(reset_complete.status_code, 200)

    def test_password_change_pages_render_for_logged_in_user(self):
        self.login_user()

        change_form = self.client.get(reverse('password_change'))
        change_done = self.client.get(reverse('password_change_done'))

        self.assertEqual(change_form.status_code, 200)
        self.assertEqual(change_done.status_code, 200)

    def test_admin_reports_and_csv_export_work(self):
        Complaint.objects.create(
            user=self.other_user,
            title='Security gate issue',
            category='Security Issue',
            description='The gate lock is broken.',
            location='Main Gate',
            priority='Emergency',
            status='Resolved',
        )
        self.login_user(self.staff_user)

        reports_response = self.client.get(reverse('reports'))
        export_response = self.client.get(reverse('export_csv'))

        self.assertEqual(reports_response.status_code, 200)
        self.assertContains(reports_response, 'Admin Reports')
        self.assertContains(reports_response, 'Heatmap Hotspots')
        self.assertContains(reports_response, 'Top Complaint Reporters')
        self.assertEqual(export_response.status_code, 200)
        self.assertEqual(export_response['Content-Type'], 'text/csv')
        self.assertIn(self.complaint.title, export_response.content.decode())

    def test_dashboard_filters_by_location_and_date(self):
        Complaint.objects.create(
            user=self.user,
            title='Hostel Wi-Fi issue',
            category='Internet Issue',
            description='Internet is unstable.',
            location='Hostel Block',
            priority='Medium',
        )
        self.login_user()

        response = self.client.get(
            reverse('dashboard'),
            {'location': 'Science', 'date_from': '2000-01-01', 'date_to': '2100-01-01'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Water pipe leak')
        self.assertNotContains(response, 'Hostel Wi-Fi issue')
        self.assertContains(response, 'Hotspot Heatmap')

    def test_manage_users_page_is_available_to_staff(self):
        self.login_user(self.staff_user)

        response = self.client.get(reverse('manage_users'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Management')
        self.assertContains(response, self.user.username)

    def test_export_csv_respects_filters(self):
        Complaint.objects.create(
            user=self.user,
            title='Class projector issue',
            category='Classroom Issue',
            description='Projector is not turning on.',
            location='Auditorium',
            priority='Low',
            status='Resolved',
        )
        self.login_user(self.staff_user)

        response = self.client.get(reverse('export_csv'), {'status': 'Resolved'})

        exported = response.content.decode()
        self.assertIn('Class projector issue', exported)
        self.assertNotIn('Water pipe leak', exported)

    def test_staff_can_delete_complaint(self):
        self.login_user(self.staff_user)

        response = self.client.post(
            reverse('delete_complaint', args=[self.complaint.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(Complaint.objects.filter(pk=self.complaint.pk).exists())
        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                message__icontains='was removed by an administrator',
            ).exists()
        )

    @override_settings(SMS_WEBHOOK_URL='https://sms.example.test/api')
    @patch('complaints.views.urlopen')
    def test_sms_hook_is_used_when_phone_and_sms_are_configured(self, mock_urlopen):
        self.user.profile.phone = '+1234567890'
        self.user.profile.save()
        self.staff_user.profile.phone = '+1987654321'
        self.staff_user.profile.save()

        self.login_user()
        self.client.post(
            reverse('create_complaint'),
            {
                'title': 'Emergency lift issue',
                'category': 'Maintenance',
                'description': 'Lift is stuck and unsafe.',
                'location': 'Tower A',
                'priority': 'Emergency',
                'is_anonymous': False,
            },
            follow=True,
        )

        self.assertTrue(mock_urlopen.called)

    def test_logout_view_accepts_post(self):
        self.login_user()

        response = self.client.post(reverse('logout'), follow=True)

        self.assertRedirects(response, reverse('login'))
