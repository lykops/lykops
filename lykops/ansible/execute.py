from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse

from library.frontend.ansible.execute import Exec_Tasks
from library.frontend.ansible.yaml import Manager_Yaml
from lykops.forms import Form_Login
from lykops.views import Base


class Exec(Base):
    def adhoc(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))

        if request.method == 'GET' :
            form = Form_Login()
            group_list = self.inventory_api.get_grouplist(username)
            return render(request, 'exec_adhoc.html', {'login_user':username, 'nav_html':self.nav_html, 'group_list':group_list, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                name = request.POST.get('name')
                pattern_list = request.POST.getlist('inve_group')
                module_name = request.POST['module']
                argv = request.POST['argv']
                describe = request.POST['describe']
                
                exec_api = Exec_Tasks(mongoclient=self.mongoclient, redisclient=self.redisclient)
                vault_password = request.session['vault_password']
                result = exec_api.adhoc(username, name, vault_password, pattern_list, module_name, argv, describe)
                        
                if not result[0] :
                    error_message = self.username + ' 下发ansible临时任务失败，任务名为' + name + '，原因：' + result[1]
                    self.logger.error(error_message)
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 下发ansible临时任务成功，任务名为' + name)
                    return HttpResponseRedirect(reverse('ansible_report')) 


    def playbook(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))

        if request.method == 'GET' :
            form = Form_Login()
            
            self.ansible_yaml_api = Manager_Yaml(username, mongoclient=self.mongoclient, redisclient=self.redisclient)
            abs_list = self.ansible_yaml_api.get_abs()
            
            new_dict = {}
            for name_dict in abs_list :
                d_type = name_dict['type']
                if d_type in ('main', 'full_roles'):
                    new_dict[name_dict['uuid']] = name_dict['name']
            
            group_list = self.inventory_api.get_grouplist(username)
            return render(request, 'exec_playbook.html', {'login_user':username, 'nav_html':self.nav_html, 'group_list':group_list, 'yaml_file':new_dict, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                name = request.POST.get('name')
                pattern_list = request.POST.getlist('inve_group')
                uuidstr = request.POST['uuid']
                describe = request.POST['describe']
                
                exec_api = Exec_Tasks(mongoclient=self.mongoclient, redisclient=self.redisclient)
                vault_password = request.session['vault_password']
                result = exec_api.playbook(username, name, vault_password, pattern_list, uuidstr, describe)
                        
                if not result[0] :
                    error_message = self.username + ' 下发ansible playbook任务失败，任务名为' + name + '，原因：' + result[1]
                    self.logger.error(error_message)
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 下发ansible playbook任务成功，任务名为' + name)
                    return HttpResponseRedirect(reverse('ansible_report')) 
