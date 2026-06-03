from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers

from .views import TaskViewSet, CategoryViewSet, TaskCommentViewSet

router = SimpleRouter()
router.register(r"", TaskViewSet, basename="task")

management_router = SimpleRouter()
management_router.register(r"categories", CategoryViewSet, basename="category")

# Nested router: /tasks/{task_pk}/comments/
tasks_router = routers.NestedSimpleRouter(router, r"", lookup="task")
tasks_router.register(r"comments", TaskCommentViewSet, basename="task-comments")

urlpatterns = [
    path("", include(router.urls)),
    path("manage/", include(management_router.urls)),
    path("", include(tasks_router.urls)),
]
