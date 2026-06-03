"""
Tests for the task comment system.

Covers:
- CRUD operations for personal task comments
- Role-based access control for project task comments
- Edge cases: nonexistent task, unauthorized access, empty text
"""

from django.urls import reverse
from rest_framework import status

from projects.models import Project, Role, ProjectMembership
from tasks.models import Task, TaskComment

from .test_setup import BaseAPITestCase
from .utils import TestHelper


# ---------------------------------------------------------------------------
# Helper mixins
# ---------------------------------------------------------------------------

class CommentTestMixin:
    """Shared URL helpers for comment tests."""

    @staticmethod
    def comment_list_url(task_pk):
        return reverse("task-comments-list", kwargs={"task_pk": task_pk})

    @staticmethod
    def comment_detail_url(task_pk, comment_pk):
        return reverse("task-comments-detail", kwargs={"task_pk": task_pk, "pk": comment_pk})

    @staticmethod
    def project_comment_list_url(project_pk, task_pk):
        return reverse(
            "project-task-comments-list",
            kwargs={"project_pk": project_pk, "task_pk": task_pk},
        )

    @staticmethod
    def project_comment_detail_url(project_pk, task_pk, comment_pk):
        return reverse(
            "project-task-comments-detail",
            kwargs={"project_pk": project_pk, "task_pk": task_pk, "pk": comment_pk},
        )

    def auth_as(self, token):
        """Switch the test client to use the given JWT token."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def unauth(self):
        """Remove credentials (simulate unauthenticated request)."""
        self.client.credentials()


# ---------------------------------------------------------------------------
# Personal task comment tests
# ---------------------------------------------------------------------------

class PersonalTaskCommentTests(CommentTestMixin, BaseAPITestCase):
    """
    Tests for comments on personal (non-project) tasks.
    Only the task owner may read and create comments.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.other_user, cls.other_token, _ = TestHelper.create_test_user_via_orm(
            email="other_personal@example.com", password="otherpassword123"
        )
        cls.task = Task.objects.create(
            title="Personal Task",
            user=cls.user,
            due_date="2099-01-01T00:00:00Z",
            priority="M",
        )

    # -- CREATE --------------------------------------------------------------

    def test_create_comment_as_owner(self):
        self.auth_as(self.token)
        url = self.comment_list_url(self.task.pk)
        response = self.client.post(url, {"text": "My first comment"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "My first comment")
        self.assertEqual(response.data["author"], self.user.id)
        self.assertIn("author_name", response.data)
        self.assertIn("created_at", response.data)

    def test_create_comment_unauthenticated(self):
        self.unauth()
        url = self.comment_list_url(self.task.pk)
        response = self.client.post(url, {"text": "Hi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_comment_non_owner_forbidden(self):
        self.auth_as(self.other_token)
        url = self.comment_list_url(self.task.pk)
        response = self.client.post(url, {"text": "Sneaky comment"}, format="json")
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_create_comment_empty_text(self):
        self.auth_as(self.token)
        url = self.comment_list_url(self.task.pk)
        response = self.client.post(url, {"text": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_comment_missing_text(self):
        self.auth_as(self.token)
        url = self.comment_list_url(self.task.pk)
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("text", response.data)

    def test_create_comment_on_nonexistent_task(self):
        self.auth_as(self.token)
        url = self.comment_list_url(99999)
        response = self.client.post(url, {"text": "Hello"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # -- READ ----------------------------------------------------------------

    def test_list_comments_as_owner(self):
        self.auth_as(self.token)
        TaskComment.objects.create(task=self.task, author=self.user, text="First")
        TaskComment.objects.create(task=self.task, author=self.user, text="Second")
        url = self.comment_list_url(self.task.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_list_comments_non_owner_forbidden(self):
        self.auth_as(self.other_token)
        url = self.comment_list_url(self.task.pk)
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_retrieve_comment_as_owner(self):
        self.auth_as(self.token)
        comment = TaskComment.objects.create(task=self.task, author=self.user, text="Detail me")
        url = self.comment_detail_url(self.task.pk, comment.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Detail me")

    # -- UPDATE --------------------------------------------------------------

    def test_update_own_comment(self):
        self.auth_as(self.token)
        comment = TaskComment.objects.create(task=self.task, author=self.user, text="Original")
        url = self.comment_detail_url(self.task.pk, comment.pk)
        response = self.client.patch(url, {"text": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Updated")

    def test_update_comment_empty_text(self):
        self.auth_as(self.token)
        comment = TaskComment.objects.create(task=self.task, author=self.user, text="Original")
        url = self.comment_detail_url(self.task.pk, comment.pk)
        response = self.client.patch(url, {"text": "  "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -- DELETE --------------------------------------------------------------

    def test_delete_own_comment(self):
        self.auth_as(self.token)
        comment = TaskComment.objects.create(task=self.task, author=self.user, text="Delete me")
        url = self.comment_detail_url(self.task.pk, comment.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TaskComment.objects.filter(pk=comment.pk).exists())

    def test_delete_nonexistent_comment(self):
        self.auth_as(self.token)
        url = self.comment_detail_url(self.task.pk, 99999)
        response = self.client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    # -- ORDERING ------------------------------------------------------------

    def test_comments_ordered_by_created_at(self):
        self.auth_as(self.token)
        task = Task.objects.create(
            title="Ordering Task", user=self.user,
            due_date="2099-01-01T00:00:00Z", priority="M",
        )
        c1 = TaskComment.objects.create(task=task, author=self.user, text="First")
        c2 = TaskComment.objects.create(task=task, author=self.user, text="Second")
        url = self.comment_list_url(task.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in response.data]
        self.assertIn(c1.pk, ids)
        self.assertIn(c2.pk, ids)
        self.assertLess(ids.index(c1.pk), ids.index(c2.pk))


# ---------------------------------------------------------------------------
# Project task comment tests
# ---------------------------------------------------------------------------

class ProjectTaskCommentSetup(CommentTestMixin, BaseAPITestCase):
    """
    Base setup for project task comment tests.
    Creates project + roles + memberships for Viewer, Member, Moderator, Admin.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Extra users with unique emails
        cls.viewer_user, cls.viewer_token, _ = TestHelper.create_test_user_via_orm(
            email="proj_viewer@example.com", password="password123"
        )
        cls.member_user, cls.member_token, _ = TestHelper.create_test_user_via_orm(
            email="proj_member@example.com", password="password123"
        )
        cls.moderator_user, cls.moderator_token, _ = TestHelper.create_test_user_via_orm(
            email="proj_moderator@example.com", password="password123"
        )
        cls.outsider_user, cls.outsider_token, _ = TestHelper.create_test_user_via_orm(
            email="proj_outsider@example.com", password="password123"
        )

        # Roles
        cls.viewer_role = Role.objects.get_or_create(name="Viewer")[0]
        cls.member_role = Role.objects.get_or_create(name="Member")[0]
        cls.moderator_role = Role.objects.get_or_create(name="Moderator")[0]
        cls.admin_role = Role.objects.get_or_create(name="Admin")[0]

        # Project owned by cls.user
        cls.project = Project.objects.create(name="Comment Test Project", owner=cls.user)

        # Memberships
        ProjectMembership.objects.create(project=cls.project, user=cls.viewer_user, role=cls.viewer_role)
        ProjectMembership.objects.create(project=cls.project, user=cls.member_user, role=cls.member_role)
        ProjectMembership.objects.create(project=cls.project, user=cls.moderator_user, role=cls.moderator_role)

        # Task inside the project
        cls.proj_task = Task.objects.create(
            title="Project Comment Task",
            user=cls.user,
            project=cls.project,
            due_date="2099-01-01T00:00:00Z",
            priority="M",
        )


class ProjectTaskCommentCRUDTests(ProjectTaskCommentSetup):
    """CRUD tests for project task comments."""

    # -- CREATE --------------------------------------------------------------

    def test_owner_can_create_comment(self):
        self.auth_as(self.token)
        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.post(url, {"text": "Owner comment"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "Owner comment")

    def test_member_can_create_comment(self):
        self.auth_as(self.member_token)
        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.post(url, {"text": "Member comment"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_viewer_cannot_create_comment(self):
        self.auth_as(self.viewer_token)
        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.post(url, {"text": "Viewer comment"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_create_comment(self):
        self.auth_as(self.outsider_token)
        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.post(url, {"text": "Outsider comment"}, format="json")
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_cannot_create_comment(self):
        self.unauth()
        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.post(url, {"text": "Anon comment"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # -- READ ----------------------------------------------------------------

    def test_viewer_can_list_comments(self):
        self.auth_as(self.token)
        TaskComment.objects.create(task=self.proj_task, author=self.user, text="Listed comment")
        self.auth_as(self.viewer_token)
        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_can_list_comments(self):
        self.auth_as(self.member_token)
        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_cannot_list_comments(self):
        self.auth_as(self.outsider_token)
        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    # -- UPDATE --------------------------------------------------------------

    def test_author_can_update_own_comment(self):
        self.auth_as(self.member_token)
        # Create comment as member
        comment = TaskComment.objects.create(
            task=self.proj_task, author=self.member_user, text="Original member comment"
        )
        url = self.project_comment_detail_url(self.project.pk, self.proj_task.pk, comment.pk)
        response = self.client.patch(url, {"text": "Updated member comment"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Updated member comment")

    def test_non_author_cannot_update_comment(self):
        # moderator tries to patch member comment
        comment = TaskComment.objects.create(
            task=self.proj_task, author=self.member_user, text="Member comment"
        )
        self.auth_as(self.moderator_token)
        url = self.project_comment_detail_url(self.project.pk, self.proj_task.pk, comment.pk)
        response = self.client.patch(url, {"text": "Hacked"}, format="json")
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_moderator_cannot_update_others_comment(self):
        """PUT/PATCH is restricted to author only - Moderator cannot edit another user's comment."""
        comment = TaskComment.objects.create(
            task=self.proj_task, author=self.member_user, text="Protected comment"
        )
        self.auth_as(self.moderator_token)
        url = self.project_comment_detail_url(self.project.pk, self.proj_task.pk, comment.pk)
        response = self.client.patch(url, {"text": "Moderator edit"}, format="json")
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    # -- DELETE --------------------------------------------------------------

    def test_author_can_delete_own_comment(self):
        comment = TaskComment.objects.create(
            task=self.proj_task, author=self.member_user, text="Delete me"
        )
        self.auth_as(self.member_token)
        url = self.project_comment_detail_url(self.project.pk, self.proj_task.pk, comment.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TaskComment.objects.filter(pk=comment.pk).exists())

    def test_moderator_can_delete_any_comment(self):
        comment = TaskComment.objects.create(
            task=self.proj_task, author=self.member_user, text="Moderable comment"
        )
        self.auth_as(self.moderator_token)
        url = self.project_comment_detail_url(self.project.pk, self.proj_task.pk, comment.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TaskComment.objects.filter(pk=comment.pk).exists())

    def test_viewer_cannot_delete_comment(self):
        comment = TaskComment.objects.create(
            task=self.proj_task, author=self.user, text="Owner comment to guard"
        )
        self.auth_as(self.viewer_token)
        url = self.project_comment_detail_url(self.project.pk, self.proj_task.pk, comment.pk)
        response = self.client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertTrue(TaskComment.objects.filter(pk=comment.pk).exists())

    def test_member_cannot_delete_others_comment(self):
        comment = TaskComment.objects.create(
            task=self.proj_task, author=self.user, text="Owner comment"
        )
        self.auth_as(self.member_token)
        url = self.project_comment_detail_url(self.project.pk, self.proj_task.pk, comment.pk)
        response = self.client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertTrue(TaskComment.objects.filter(pk=comment.pk).exists())

    def test_owner_can_delete_any_comment(self):
        """Project owner has full access."""
        comment = TaskComment.objects.create(
            task=self.proj_task, author=self.member_user, text="Member comment"
        )
        self.auth_as(self.token)
        url = self.project_comment_detail_url(self.project.pk, self.proj_task.pk, comment.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class CommentEdgeCaseTests(ProjectTaskCommentSetup):

    def test_comment_on_nonexistent_project_task(self):
        self.auth_as(self.token)
        url = self.project_comment_list_url(self.project.pk, 99999)
        response = self.client.post(url, {"text": "Ghost"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_on_task_from_wrong_project(self):
        """Task belongs to another project - accessing via wrong project_pk should 404."""
        other_project = Project.objects.create(name="Other Comment Project", owner=self.user)
        other_task = Task.objects.create(
            title="Other Task",
            user=self.user,
            project=other_project,
            due_date="2099-01-01T00:00:00Z",
            priority="M",
        )
        self.auth_as(self.token)
        # Access via wrong project_pk
        url = self.project_comment_list_url(self.project.pk, other_task.pk)
        response = self.client.post(url, {"text": "Cross-project"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_returns_only_task_comments(self):
        """Comments from a different task do not appear in the current task list."""
        task2 = Task.objects.create(
            title="Another Task In Project",
            user=self.user,
            project=self.project,
            due_date="2099-01-01T00:00:00Z",
            priority="L",
        )
        self.auth_as(self.token)
        c1 = TaskComment.objects.create(task=self.proj_task, author=self.user, text="Comment on proj_task")
        TaskComment.objects.create(task=task2, author=self.user, text="Comment on task2")

        url = self.project_comment_list_url(self.project.pk, self.proj_task.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in response.data]
        self.assertIn(c1.pk, ids)

    def test_comment_text_validator_rejects_special_chars(self):
        """TEXT_FIELD_VALIDATOR rejects characters outside the allowed set."""
        self.auth_as(self.token)
        task = Task.objects.create(
            title="Validator Task",
            user=self.user,
            due_date="2099-01-01T00:00:00Z",
            priority="M",
        )
        url = self.comment_list_url(task.pk)
        response = self.client.post(url, {"text": "<script>alert(1)</script>"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
