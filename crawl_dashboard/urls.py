
from django.contrib import admin
from django.conf.urls import url
from django.contrib.auth import views as auth_views

from accounts import views as accounts_views
from crawls import views as crawl_views
from domains import views as domain_views
from accounts import views as accounts_views
from . import views as main_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^crawlers/$', crawl_views.index, name='crawl_index'),
    url(r'^$', main_views.index, name='home'),
    url(r'^crawlers/(?P<host>[0-9\.]+)/(?P<crawl_date>[0-9\-]+)/$', crawl_views.view_summary, name='crawl_summary'),
    url(r'^crawlers/(?P<host>[0-9\.]+)/(?P<crawl_date>[0-9\-]+)/(?P<domain>[A-Za-z0-9\&\-\_\.]+)/$', crawl_views.view_inventory, name='crawl_inventory'),
    url(r'^domains/$', domain_views.index, name='domain_index'),
    url(r'^domains/(?P<domain>[A-Za-z0-9\-\_\.\&]+)/(?P<crawl_date>[0-9\-]+)/$', domain_views.domain_summary, name='domain_summary'),
    url(r'^domains/test_domain/$', domain_views.test_domain, name='test_domain'),
    url(r'^domains/test_cancel/$', domain_views.test_cancel, name='test_cancel'),
    url(r'^domains/view_test/(?P<dealer_id>[A-Za-z0-9\-\_\.\&]+)/$', domain_views.view_test, name='view_test'),
    url(r'^domains/view_test/(?P<dealer_id>[A-Za-z0-9\-\_\.\&]+)/test_detail/(?P<id>[0-9]+)/$', domain_views.test_detail, name='test_detail'),

    # accounts
    url(r'^signup/$', accounts_views.signup, name='signup'),
    url(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset.html',
            email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt'
        ),
        name='password_reset'),
    url(r'^reset/done/$',
        auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
        name='password_reset_confirm'),
    url(r'^reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
        name='password_reset_complete'),
    
    url(r'^settings/password/$', auth_views.PasswordChangeView.as_view(template_name='password_change.html'),
        name='password_change'),
    url(r'^settings/password/done/$', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'),
        name='password_change_done'),


]
