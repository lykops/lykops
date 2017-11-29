"""lykops URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
# from django.contrib import admin

from library.connecter.database.mongo import Op_Mongo
from library.connecter.database.redis_api import Op_Redis
# from lykops import settings
from lykops.ansible.execute import Exec
from lykops.ansible.options import Options
from lykops.ansible.report import Report 
from lykops.ansible.yaml import Yaml 
from lykops.sysadmin.inventory import Inventory
# from lykops.sysadmin.privacy import Privacy
from lykops.sysadmin.user import User
from lykops.views import Login 


mongoclient = Op_Mongo()
redisclient = Op_Redis()

urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r'^$', User(mongoclient=mongoclient, redisclient=redisclient).summary, name='index'),
    url(r'^login.html', Login(mongoclient=mongoclient, redisclient=redisclient).login, name='login'),
    url(r'^logout.html', Login(mongoclient=mongoclient, redisclient=redisclient).logout, name='logout'),
    
    url(r'^user/create_admin', Login(mongoclient=mongoclient, redisclient=redisclient).create_admin, name='create_admin'),
    url(r'^user/detail', User(mongoclient=mongoclient, redisclient=redisclient).detail),
    url(r'^user/list', User(mongoclient=mongoclient, redisclient=redisclient).summary, name='user_list'),
    url(r'^user/add', User(mongoclient=mongoclient, redisclient=redisclient).add, name='user_add'),
    url(r'^user/edit', User(mongoclient=mongoclient, redisclient=redisclient).edit),
    url(r'^user/chgpwd', User(mongoclient=mongoclient, redisclient=redisclient).change_pwd),
    url(r'^user/chgpvltwd', User(mongoclient=mongoclient, redisclient=redisclient).change_vaultpwd),
    url(r'^user/del', User(mongoclient=mongoclient, redisclient=redisclient).delete),
    url(r'^user/disable', User(mongoclient=mongoclient, redisclient=redisclient).disable),
    url(r'^user/enable', User(mongoclient=mongoclient, redisclient=redisclient).enable),
    url(r'^user/$', User(mongoclient=mongoclient, redisclient=redisclient).summary),
    
    # url(r'^privacy/edit', Privacy(mongoclient=mongoclient, redisclient=redisclient).edit, name='privacy_edit'),
    # url(r'^privacy/detail', Privacy(mongoclient=mongoclient, redisclient=redisclient).detail, name='privacy_detail'),
    # url(r'^privacy/$', Privacy(mongoclient=mongoclient, redisclient=redisclient).detail),
    # 该功能用于保存用户的机密数据，但该版本暂时不需要使用，故暂时不做展示
    
    url(r'^inventory/add$', Inventory(mongoclient=mongoclient, redisclient=redisclient).add, name='inventory_add'),
    url(r'^inventory/list$', Inventory(mongoclient=mongoclient, redisclient=redisclient).summary, name='inventory_list'),
    url(r'^inventory/$', Inventory(mongoclient=mongoclient, redisclient=redisclient).summary),
    url(r'^inventory/detail$', Inventory(mongoclient=mongoclient, redisclient=redisclient).detail, name='inventory_detail'),
    url(r'^inventory/edit$', Inventory(mongoclient=mongoclient, redisclient=redisclient).edit, name='inventory_edit'),
    url(r'^inventory/del$', Inventory(mongoclient=mongoclient, redisclient=redisclient).delete, name='inventory_del'),
    
    url(r'^ansible/$', Report(mongoclient=mongoclient, redisclient=redisclient).summary, name='ansible'),
    
    url(r'^ansible/report/$', Report(mongoclient=mongoclient, redisclient=redisclient).summary, name='ansible_report'),
    
    url(r'^ansible/report/list$', Report(mongoclient=mongoclient, redisclient=redisclient).summary, name='ansible_report_list'),
    url(r'^ansible/report/detail$', Report(mongoclient=mongoclient, redisclient=redisclient).detail),
    

    url(r'^ansible/yaml/add$', Yaml(mongoclient=mongoclient, redisclient=redisclient).add, name='ansible_yaml_add'),
    url(r'^ansible/yaml/import$', Yaml(mongoclient=mongoclient, redisclient=redisclient).import_file, name='ansible_yaml_import'),
    url(r'^ansible/yaml/list$', Yaml(mongoclient=mongoclient, redisclient=redisclient).summary, name='ansible_yaml_list'),
    url(r'^ansible/yaml/detail$', Yaml(mongoclient=mongoclient, redisclient=redisclient).detail, name='ansible_yaml_detail'),
    url(r'^ansible/yaml/edit$', Yaml(mongoclient=mongoclient, redisclient=redisclient).edit),
    url(r'^ansible/yaml/$', Yaml(mongoclient=mongoclient, redisclient=redisclient).summary, name='ansible_yaml'),
    
    url(r'^ansible/exec/adhoc$', Exec(mongoclient=mongoclient, redisclient=redisclient).adhoc, name='ansible_exec_adhoc'),
    url(r'^ansible/exec/playbook$', Exec(mongoclient=mongoclient, redisclient=redisclient).playbook, name='ansible_exec_playbook'),
    
    url(r'^ansible/option/$', Options(mongoclient=mongoclient, redisclient=redisclient).detail, name='ansible_option'),
    url(r'^ansible/option/edit$', Options(mongoclient=mongoclient, redisclient=redisclient).edit),
    url(r'^ansible/option/detail$', Options(mongoclient=mongoclient, redisclient=redisclient).detail),
    
    # url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.STATICFILES_DIRS, 'show_indexes':False}),
    # url(r'^file/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.MEDIA_ROOT, 'show_indexes':False}),
]
