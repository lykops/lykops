from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse

from lykops.forms import Form_Login
from lykops.views import Base


class Inventory(Base):

    def summary(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))

        result = self.inventory_api.summary(username)
        if result[0] :
            title_list = result[1]
            query_list = result[2]
            http_referer = self.uri_api.get_httpreferer(username, no=-1)
            self.logger.info(self.username + ' 查看用户' + username + '的主机列表，查询数据成功')
            return render(request, 'inve_list.html', {'title_list':title_list, 'query_list':query_list, 'login_user':username, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            error_message = self.username + ' 查看用户' + username + '的主机列表失败，查询时发生错误，原因：' + result[1]
            self.logger.error(error_message) 
            http_referer = self.uri_api.get_httpreferer(username, no=-1)
            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
  
    
    def add(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        if request.method == 'GET' :
            html_code = self.inventory_api.add_get(username)
            return render(request, 'inve_add.html', {'html_code': html_code, 'login_user':username, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                user_mess_dict = self.post_handle(request)
                vault_password = request.session['vault_password']
                result = self.inventory_api.add_post(username, vault_password, user_mess_dict)
                if not result[0] :
                    error_message = self.username + ' 为用户' + username + '新增主机时失败，提交保存时发生错误，原因：' + result[1]
                    self.logger.error(error_message) 
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 为用户' + username + '新增主机，提交保存成功')
                    return HttpResponseRedirect(reverse('inventory_list')) 


    def detail(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        vault_password = request.session['vault_password']
        name = request.GET.get('name')
        result = self.inventory_api.detail(username, vault_password, name)
        if result[0] :
            self.logger.info(self.username + ' 查看用户' + username + '的名为' + name + '的主机，查询成功')
            return render(request, 'inve_detail.html', {'name':name, 'detail_dict':result[1] , 'login_user':username, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            error_message = self.username + ' 查看用户' + username + '的名为' + name + '的主机，查询时发生错误，原因：' + result[1]
            self.logger.error(error_message) 
            return HttpResponseRedirect(reverse('inventory_list'))


    def edit(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        vault_password = request.session['vault_password']
        name = request.GET.get('name')
        
        if request.method == 'GET' :
            html_code = self.inventory_api.edit_get(username, vault_password, name)
            if not result[0] :  
                error_message = self.username + ' 编辑用户' + username + '的名为' + name + '的主机失败，查询时发生错误，原因：' + result[1]
                self.logger.error(error_message) 
            else :
                self.logger.info(self.username + ' 编辑用户' + username + '的名为' + name + '的主机，查询成功')
            return render(request, 'inve_edit.html', {'html_code': html_code, 'login_user':username, 'name':name, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html}) 
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                user_mess_dict = self.post_handle(request) 
                result = self.inventory_api.edit_post(username, name, vault_password, user_mess_dict)
                if not result[0] :                    
                    error_message = self.username + ' 编辑用户' + username + '的名为' + name + '的主机失败，提交保存时发生错误，原因：' + result[1]
                    self.logger.error(error_message) 
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 编辑用户' + username + '的名为' + name + '的主机，提交保存成功')
                    return HttpResponseRedirect(reverse('inventory_list')) 


    def delete(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        name = request.GET.get('name')
        result = self.inventory_api.delete(username, name)
        http_referer = self.uri_api.get_httpreferer(username, no=-1)
        if not result[0] :               
            error_message = self.username + ' 删除用户' + username + '的名为' + name + '的主机失败，提交保存时发生错误，原因：' + result[1]
            self.logger.error(error_message) 
            return render(request, 'result.html', {'name':name , 'login_user':username, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            self.logger.info(self.username + ' 删除用户' + username + '的名为' + name + '的主机，提交保存成功')
            return HttpResponseRedirect(reverse('inventory_list'))
        
        
    def post_handle(self, request):
        username = request.session['username']
        post_key_list = self.inventory_api.init_para(username)
        user_mess_dict = {}
        
        group_list = request.POST.getlist('group')
        addgroup = request.POST.get('group_add')
        for group in addgroup.split(',') :
            if group :
                group_list.append(group)
            
        group_list = list(set(group_list))
        user_mess_dict['group'] = group_list
        
        for key in post_key_list :
            if key != 'group' and key != 'group_add':
                try :
                    user_mess_dict[key] = request.POST.get(key)
                except :
                    pass
        return user_mess_dict
