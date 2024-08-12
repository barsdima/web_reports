from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
from reports.views import ReportsView, ReportCreateView, ReportDetailView, UpdateReportView, DeleteReportView, DatapacksView, UpdateDatapackView, view_file, download_file, DatapackHistoryView, filter_stats

urlpatterns = [
    path("", ReportsView.as_view(), name="reports"),
    path("report/<pk>/", ReportDetailView.as_view(), name="report_detail"),
    path("submit_report/", ReportCreateView.as_view(), name="submit_report"),
    path("api/submit_report/", views.submit_report_api, name="submit_report_api"),
    path("update_report/<pk>/", UpdateReportView.as_view(), name="update_report"),
    path("delete_report/<pk>/", DeleteReportView.as_view(), name="delete_report"),
    path("dptracking/", DatapacksView.as_view(), name="dptracking"),
    path("update_datapack/<pk>/", UpdateDatapackView.as_view(), name="update_datapack"),
    path('view_file/<int:report_id>/', view_file, name='view_file'),
    path('download_file/<int:report_id>/', download_file, name='download_file'),
    path('datapack_history/<str:datapack_name>/', DatapackHistoryView.as_view(), name='datapack_history'),
    path('filter_stats/', filter_stats, name='filter_stats')
]
