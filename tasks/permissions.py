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
            logger.error(f"Object {type(obj).__name__} has no ownership attribute")
            raise PermissionDenied("Access denied: missing ownership information")

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
    """Allows access only to the comment author."""

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class ProjectCommentPermission(BasePermission):
    """
    Permission for comments on project tasks.

    obj is a TaskComment. We use obj.task.project for role checks.

    - GET/HEAD/OPTIONS: Viewer+
    - POST: Member+  (enforced in the viewset create() before get_object is called)
    - PUT/PATCH: comment author only
    - DELETE: comment author OR Moderator+
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        task = obj.task
        project = getattr(task, "project", None)

        if project is None:
            # personal task fallback — treated as owner-only
            return task.user_id == request.user.pk

        def _min_role(role):
            return IsProjectMinRole(role).has_object_permission(request, view, project)

        if request.method in SAFE_METHODS:
            return _min_role("Viewer")

        if request.method == "POST":
            return _min_role("Member")

        if request.method in ("PUT", "PATCH"):
            return obj.author_id == request.user.pk

        if request.method == "DELETE":
            if obj.author_id == request.user.pk:
                return True
            return _min_role("Moderator")

        return False
