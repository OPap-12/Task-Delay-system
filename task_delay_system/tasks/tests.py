from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import Task
from .forms import TaskForm


class TaskModelTest(TestCase):
    """Tests for the Task model business logic methods."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def _create_task(self, due_offset_days=5, completed=False, priority='medium'):
        """Helper to create a task with a due date offset from today."""
        task = Task(
            user=self.user,
            title='Test Task',
            description='Test description',
            due_date=timezone.now().date() + timedelta(days=due_offset_days),
            priority=priority,
            status='PENDING',
        )
        task.save()
        
        if completed:
            task.status = 'READY_FOR_REVIEW'
            task.save()
            task.status = 'APPROVED'
            task.save()
        return task

    # --- is_delayed ---

    def test_is_delayed_overdue_incomplete(self):
        """An incomplete task past its due date is delayed."""
        task = self._create_task(due_offset_days=-3)
        self.assertTrue(task.is_delayed())

    def test_is_delayed_not_overdue(self):
        """A task due in the future is not delayed."""
        task = self._create_task(due_offset_days=5)
        self.assertFalse(task.is_delayed())

    def test_is_delayed_completed_on_time(self):
        """A task completed before its due date is not delayed."""
        task = self._create_task(due_offset_days=5, completed=True)
        self.assertFalse(task.is_delayed())

    # --- is_at_risk ---

    def test_is_at_risk_due_tomorrow(self):
        """A task due tomorrow is at risk."""
        task = self._create_task(due_offset_days=1)
        self.assertTrue(task.is_at_risk())

    def test_is_at_risk_due_today(self):
        """A task due today is at risk."""
        task = self._create_task(due_offset_days=0)
        self.assertTrue(task.is_at_risk())

    def test_is_at_risk_due_far_future(self):
        """A task due in 10 days is not at risk."""
        task = self._create_task(due_offset_days=10)
        self.assertFalse(task.is_at_risk())

    def test_is_at_risk_completed_task(self):
        """A completed task is never at risk."""
        task = self._create_task(due_offset_days=1, completed=True)
        self.assertFalse(task.is_at_risk())





    # --- progress_percentage ---

    def test_progress_percentage_pending(self):
        task = self._create_task(due_offset_days=5)
        self.assertEqual(task.progress_percentage, 0)

    def test_progress_percentage_approved(self):
        task = self._create_task(due_offset_days=5, completed=True)
        self.assertEqual(task.progress_percentage, 100)

    def test_progress_percentage_ready_for_review(self):
        task = self._create_task(due_offset_days=5)
        task.status = 'READY_FOR_REVIEW'
        task.save()
        self.assertEqual(task.progress_percentage, 60)

    # --- days_until_due ---

    def test_days_until_due_positive(self):
        task = self._create_task(due_offset_days=7)
        self.assertEqual(task.days_until_due(), 7)

    def test_days_until_due_negative(self):
        task = self._create_task(due_offset_days=-2)
        self.assertEqual(task.days_until_due(), -2)

    # --- str ---

    def test_str_representation(self):
        task = self._create_task()
        self.assertEqual(str(task), 'Test Task')


class TaskViewTest(TestCase):
    """Tests for task views — auth enforcement, CRUD, and permissions."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', password='otherpass123'
        )
        self.task = Task.objects.create(
            user=self.user,
            title='User Task',
            due_date=timezone.now().date() + timedelta(days=5),
            priority='medium',
        )

    # --- Authentication enforcement ---

    def test_task_list_requires_login(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_task_list_authenticated(self):
        """Authenticated users can access the task list."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

    # --- CRUD operations ---

    def test_create_task_get(self):
        """GET create_task renders the form."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_task'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Task')

    def test_create_task_post_valid(self):
        """A valid POST creates a task and redirects."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('create_task'), {
            'title': 'New Task',
            'description': 'Description',
            'due_date': (timezone.now().date() + timedelta(days=3)).isoformat(),
            'priority': 'high',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title='New Task', user=self.user).exists())

    def test_create_task_post_past_date(self):
        """A task with a past due date is rejected."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('create_task'), {
            'title': 'Past Task',
            'due_date': (timezone.now().date() - timedelta(days=1)).isoformat(),
            'priority': 'medium',
        })
        self.assertEqual(response.status_code, 200)  # Re-renders form with error
        self.assertFalse(Task.objects.filter(title='Past Task').exists())

    # --- Ownership enforcement ---

    def test_cannot_update_other_users_task(self):
        """Users cannot edit tasks belonging to other users."""
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('update_task', args=[self.task.id]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_other_users_task(self):
        """Users cannot delete tasks belonging to other users."""
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.post(reverse('delete_task', args=[self.task.id]))
        self.assertEqual(response.status_code, 404)

    # --- Workflow ---

    def test_manager_approves_task(self):
        """Manager can approve task."""
        self.client.login(username='testuser', password='testpass123')
        self.assertFalse(self.task.is_completed)
        
        # Managers can approve
        from django.contrib.auth.models import Group
        from .models import ROLE_MANAGER
        manager_group, _ = Group.objects.get_or_create(name=ROLE_MANAGER)
        self.user.groups.add(manager_group)
        
        self.task.status = 'READY_FOR_REVIEW'
        self.task.save()
        
        self.client.post(reverse('approve_task', args=[self.task.id]))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'APPROVED')
        self.assertTrue(self.task.is_completed)
        self.assertIsNotNone(self.task.completed_at)

    def test_submit_task_for_review(self):
        """Submit shifts status to READY_FOR_REVIEW."""
        from django.contrib.auth.models import Group
        from .models import ROLE_EMPLOYEE
        employee_group, _ = Group.objects.get_or_create(name=ROLE_EMPLOYEE)
        self.user.groups.add(employee_group)

        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('submit_task', args=[self.task.id]))
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'READY_FOR_REVIEW')

    # --- Dashboard ---

    def test_dashboard_renders(self):
        """Dashboard loads with stats context."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_count', response.context)
        self.assertIn('overdue_count', response.context)

    # --- Logout ---

    def test_logout_get_not_allowed(self):
        """Logout only accepts POST (returns 405 on GET)."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout_post_works(self):
        """POST to logout logs the user out and redirects."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class TaskFormTest(TestCase):
    """Tests for TaskForm validation."""

    def test_valid_form(self):
        form = TaskForm(data={
            'title': 'Test Task',
            'description': 'Description',
            'due_date': (timezone.now().date() + timedelta(days=5)).isoformat(),
            'priority': 'high',
        })
        self.assertTrue(form.is_valid())

    def test_missing_title(self):
        form = TaskForm(data={
            'due_date': (timezone.now().date() + timedelta(days=5)).isoformat(),
            'priority': 'medium',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_missing_due_date(self):
        form = TaskForm(data={
            'title': 'Task With No Date',
            'priority': 'medium',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)

    def test_past_due_date_rejected(self):
        form = TaskForm(data={
            'title': 'Past Task',
            'due_date': (timezone.now().date() - timedelta(days=1)).isoformat(),
            'priority': 'medium',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)

    def test_priority_field_present(self):
        """Priority field must be in the form."""
        form = TaskForm()
        self.assertIn('priority', form.fields)

    def test_invalid_priority_rejected(self):
        form = TaskForm(data={
            'title': 'Bad Priority',
            'due_date': (timezone.now().date() + timedelta(days=5)).isoformat(),
            'priority': 'critical',  # Not a valid choice
        })
        self.assertFalse(form.is_valid())
        self.assertIn('priority', form.errors)
