import logging
from django.db.models import Q

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tasks.models import Task
    from users.models import User

logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for task operations

    Handles business logic for toggling favorite/completion status
    and moving tasks between projects
    """

    @staticmethod
    def is_today_filter(request):
        """
        Return True if 'today' query parameter is 'true' (case-insensitive)
        """
        today = request.query_params.get("today")
        return today and today.lower() == "true"

    @staticmethod
    def toggle_favorite(task):
        """
        Toggle the is_favorite flag on a task and save it
        """
        task.is_favorite = not task.is_favorite
        task.save()
        return task

    @staticmethod
    def toggle_completed(task: "Task", user: "User") -> "Task":
        """
        Toggle the completed flag on a task, update timestamps,
        and record the user who completed it
        """
        task.completed = not task.completed
        task.update_completed_at()

        if task.completed:
            task.completed_by = user
        else:
            task.completed_by = None

        task.save(update_fields=["completed", "completed_at", "completed_by"])
        return task

    @staticmethod
    def move_task_to_project(task, project_id, user):
        """
        Move a task to a different project if the user has access

        Raises:
            ValueError: If the project does not exist or access is denied
        """
        from projects.models import Project

        try:
            new_project = (
                Project.objects.filter(
                    Q(id=project_id)
                    & (Q(owner=user) | Q(memberships__user=user))
                )
                .distinct()
                .get()
            )
        except Project.DoesNotExist:
            raise ValueError("Project not found or access denied")

        task.project = new_project
        task.save()

        return task


class CategoryService:
    """
    Service for operations with categories
    """

    @staticmethod
    def get_tasks_for_category(category):
        """
        Return all tasks associated with a given category
        """
        return category.tasks.all()


class CommentService:
    """
    Service for task comment operations.
    """

    @staticmethod
    def create_comment(task, author, text: str):
        """
        Create a new comment on a task.

        Args:
            task: The Task instance to comment on.
            author: The User instance creating the comment.
            text: The comment text.

        Returns:
            TaskComment: The newly created comment.
        """
        from tasks.models import TaskComment

        comment = TaskComment.objects.create(task=task, author=author, text=text)
        logger.info(f"Comment {comment.id} created on task {task.id} by user {author.id}")
        return comment

    @staticmethod
    def update_comment(comment, text: str):
        """
        Update the text of an existing comment.

        Args:
            comment: The TaskComment instance to update.
            text: The new text.

        Returns:
            TaskComment: The updated comment.
        """
        comment.text = text
        comment.save(update_fields=["text", "updated_at"])
        logger.info(f"Comment {comment.id} updated")
        return comment

    @staticmethod
    def delete_comment(comment):
        """
        Delete a comment.

        Args:
            comment: The TaskComment instance to delete.
        """
        comment_id = comment.id
        comment.delete()
        logger.info(f"Comment {comment_id} deleted")
