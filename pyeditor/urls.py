from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from views import editor_view, run_code_view

urlpatterns = [
    path('', editor_view, name='editor'),
    path('run/', run_code_view, name='run_code'),
] + staticfiles_urlpatterns()