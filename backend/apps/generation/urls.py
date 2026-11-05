from django.urls import path

from apps.generation import views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("config/", views.ConfigView.as_view(), name="config"),
    path("jobs/", views.JobCreateView.as_view(), name="job-create"),
    path("jobs/<str:job_id>/", views.JobDetailView.as_view(), name="job-detail"),
    path("jobs/<str:job_id>/export/", views.JobExportView.as_view(), name="job-export"),
    path(
        "jobs/<str:job_id>/questions/<str:question_id>/",
        views.QuestionDetailView.as_view(),
        name="question-detail",
    ),
    path(
        "jobs/<str:job_id>/questions/<str:question_id>/regenerate/",
        views.QuestionRegenerateView.as_view(),
        name="question-regenerate",
    ),
]
