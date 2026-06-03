import logging

from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS

from projects.permissions import IsProjectMinRole

logger = logging.getLogger(__name__)


class IsOwner(BasePermission):
    """
    Checking whether the user is the owner of the object
    """

    def has_object_permission(self, request, view, obj):
        user_field = getattr(obj, "user", None) or getattr(obj, "owner", None)

        if user_field is None:
            logger.error(
                f"Object {type(obj).__name__} has no ownership attribute"
            )
            raise PermissionDenied(
                "Access denied: missing ownership information"
            )

        return user_field == request.user


class ProjectTaskPermission(BasePermission):
    """
    Checking whether the user has the required permission for the project task
    """

    def _get_min_role(self, method):
        if method in SAFE_METHODS:
            return "Viewer"
        if method in ("PUT", "PATCH"):
            return "Member"
        return "Moderator"

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        project = getattr(obj, "project", None)
        if project is None:
            return True

        min_role = self._get_min_role(request.method)

        return IsProjectMinRole(min_role).has_object_permission(request, view, obj)


class IsCommentAuthor(BasePermission):
    """
    Allows access only to the comment author.
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class ProjectCommentPermission(BasePermission):
    """
    Permission for comments on project tasks.

    - GET/HEAD/OPTIONS: Viewer+
    - POST: Member+
    - PUT/PATCH: comment author only
    - DELETE: comment author OR Moderator+
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        """
        obj is a TaskComment. obj.task.project is the project.
        We delegate role checks to IsProjectMinRole, passing obj.task
        (which has a .project attribute) so _get_project_from_obj works.
        """
        task = obj.task
        project = getattr(task, "project", None)
        if project is None:
            # personal task — fall through to personal-task logic
            return task.user == request.user

        if request.method in SAFE_METHODS:
            return IsProjectMinRole("Viewer").has_object_permission(request, view, task)

        if request.method == "POST":
            return IsProjectMinRole("Member").has_object_permission(request, view, task)

        if request.method in ("PUT", "PATCH"):
            return obj.author == request.user

        if request.method == "DELETE":
            if obj.author == request.user:
                return True
            return IsProjectMinRole("Moderator").has_object_permission(request, view, task)

        return False
