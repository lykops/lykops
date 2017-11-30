from ansible.modules.network.junos.junos_command import rpc
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse

from library.frontend.ansible.yaml import Manager_Yaml
from library.utils.dict import get_allkey
from library.utils.list import dimension_multi2one
from lykops.forms import Form_Login
from lykops.views import Base


class Yaml(Base):
    def add(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        self.ansible_yaml_api = Manager_Yaml(username, mongoclient=self.mongoclient, redisclient=self.redisclient)
        
        if request.method == 'GET' :
            form = Form_Login()
            return render(request, 'yaml_add.html', {'login_user':username, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                name = request.POST.get('name')
                content = request.POST['content']
                yaml_tpye = 'main'
                # request.POST['yaml_tpye']
                file_type = request.POST['file_type']
                describe = request.POST['describe']
                
                result = self.ansible_yaml_api.add(content, name, yaml_tpye=yaml_tpye, file_type=file_type, describe=describe)
                if not result[0] :
                    error_message = self.username + ' 为用户' + username + '新增ansible yaml文件时失败，提交保存时发生错误，原因：' + result[1]
                    self.logger.error(error_message) 
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 为用户' + username + '新增ansible yaml文件，提交保存成功')
                    return HttpResponseRedirect(reverse('ansible_yaml')) 


    def import_file(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        self.ansible_yaml_api = Manager_Yaml(username, mongoclient=self.mongoclient, redisclient=self.redisclient)
        
        if request.method == 'GET' :
            form = Form_Login()
            return render(request, 'yaml_import.html', {'login_user':username, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                name = request.POST.get('name')
                describe = request.POST['describe']
                # yaml_tpye = request.POST['yaml_tpye']
                yaml_tpye = 'main'
                
                try :
                    this_path = request.POST.get('path')
                    if this_path is not None :
                        result = self.ansible_yaml_api.import_path(this_path, name, yaml_tpye=yaml_tpye, describe=describe)
                    else :
                        upload_file = request.FILES['file']
                        if upload_file is not None:
                            result = self.ansible_yaml_api.import_upload(upload_file, name, yaml_tpye=yaml_tpye, describe=describe)               
                except :
                    upload_file = request.FILES['file']
                    if upload_file is not None:
                        result = self.ansible_yaml_api.import_upload(upload_file, name, yaml_tpye=yaml_tpye, describe=describe)
                
                if not result[0] :
                    error_message = self.username + ' 为用户' + username + '上传导入ansible yaml时失败，提交保存时发生错误，原因：' + result[1]
                    self.logger.error(error_message) 
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 为用户' + username + '上传导入ansible yaml，提交保存成功')
                    return HttpResponseRedirect(reverse('ansible_yaml')) 


    def summary(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        id_type = request.GET.get('id_type')
        
        self.ansible_yaml_api = Manager_Yaml(username, mongoclient=self.mongoclient, redisclient=self.redisclient)
        abs_list = self.ansible_yaml_api.get_abs()
        
        if id_type is None or id_type == 'None ':
            new_abs_list = abs_list
        else :
            type_list = []
            for name_dict in abs_list :
                d_type = name_dict['type']
                if id_type == d_type:
                    type_list.append(name_dict)
            new_abs_list = type_list
            
        self.logger.info(self.username + ' 为用户' + username + '展现yaml列表成功')
        http_referer = self.uri_api.get_httpreferer(username, no=-1)
        return render(request, 'yaml_list.html', {'abs_list' : new_abs_list, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
    

    def detail(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        uuid_str = request.GET.get('uuid')
        self.ansible_yaml_api = Manager_Yaml(username, mongoclient=self.mongoclient, redisclient=self.redisclient)
        result = self.ansible_yaml_api.detail(uuid_str)
        if not result[0] :
            http_referer = self.uri_api.get_httpreferer(username, no=-1)
            error_message = self.username + ' 查看用户' + username + '的uuid为' + uuid_str + '的ansible yaml时失败，查询时发生错误，原因：' + result[1]
            self.logger.error(error_message) 
            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            content_dict = content_dict = result[1]['content']
            if 'main' in content_dict :
                main_content = content_dict['main']
            else :
                main_content = ''
            
            if 'roles' in content_dict :
                roles_content = content_dict['roles']
            else :
                roles_content = ''
            
            if 'include' in content_dict :
                include_content = content_dict['include']
            else :
                include_content = ''
            
            name = result[1]['name']
            self.logger.info(self.username + ' 查看用户' + username + '的uuid为' + uuid_str + '的ansible yaml成功')
            return render(request, 'yaml_detail.html', {'login_user':username, 'nav_html':self.nav_html, 'main':main_content, 'roles':roles_content, 'include':include_content, 'name':name, 'uuid':uuid_str, 'lately_whereabouts':self.latelywhere_html})
        
        
    def edit(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        uuid_str = request.GET.get('uuid')
        self.ansible_yaml_api = Manager_Yaml(username, mongoclient=self.mongoclient, redisclient=self.redisclient)
        result = self.ansible_yaml_api.detail(uuid_str, isedit=True)
        if not result[0] :
            error_message = self.username + ' 编辑用户' + username + '的uuid为' + uuid_str + '的ansible yaml失败，查询时发生错误，原因：' + result[1]
            self.logger.error(error_message) 
            http_referer = self.uri_api.get_httpreferer(username, no=-1)
            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        
        if request.method == 'GET' :
            content_dict = result[1].get('content', {}) 
            roles_content = content_dict.get('roles', '') 
            main_content = content_dict.get('main', '') 
            include_content = content_dict.get('include', '') 
            
            name = result[1].get('name', '') 
            describe = result[1].get('describe', '') 
            yaml_tpye = result[1].get('type', '') 
            file_type = result[1].get('file_type', '') 
                
            self.logger.info(self.username + ' 编辑用户' + username + '的uuid为' + uuid_str + '的ansible yaml，查询成功')
            return render(request, 'yaml_edit.html', {'login_user':username, 'nav_html':self.nav_html, 'main':main_content, 'roles':roles_content, 'include':include_content, 'name':name, 'describe':describe, 'yaml_tpye':yaml_tpye, 'file_type':file_type, 'uuid':uuid_str, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                content_dict = result[1]['content']
                file_list = get_allkey(content_dict)
                file_list = dimension_multi2one(file_list)
                
                new_content_dict = {}
                for filename in file_list :
                    file_content = request.POST.get(filename, '')
                    if file_content: 
                        new_content_dict[filename] = file_content
                    
                name = request.POST.get('name', '') 
                describe = request.POST.get('describe', '') 
                    
                result = self.ansible_yaml_api.edit(uuid_str, new_content_dict, describe=describe, name=name)
                if not result[0] :
                    error_message = self.username + ' 编辑用户' + username + '的uuid为' + uuid_str + '的ansible yaml失败，提交保存时发生错误，原因：' + result[1]
                    self.logger.error(error_message) 
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'uuid':uuid_str, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 编辑用户' + username + '的uuid为' + uuid_str + '的ansible yaml提交保存成功')
                    return HttpResponseRedirect(reverse('ansible_yaml')) 

