from django.http.response import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.urls.base import reverse

from lykops.forms import Form_Login
from lykops.views import Base


class Options(Base):
    def detail(self, request):
        
        '''
        查看用户的ansible的option数据
        '''
        
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
    
        vault_password = request.session['vault_password']
        result = self.ansible_option_api.detail(username, vault_password)
        if result[0] :
            data = result[1]
            error_message = ''
            self.logger.info(self.username + ' 查看用户' + username + '的ansible配置成功')
        else :
            data = {}
            error_message = self.username + ' 查看用户' + username + '的ansible配置失败，查询时发生错误，原因：' + result[1]
            self.logger.error(error_message) 
            error_message = result[1]
            
        return render_to_response('option_detail.html', {'data':data, 'login_user':username, 'error_message':error_message, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
    

    def edit(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        vault_password = request.session['vault_password']
        
        if request.method == 'GET' :
            html_code = self.ansible_option_api.edit_get(username, vault_password)
            self.logger.info(self.username + ' 编辑用户' + username + '的ansible配置，查询成功')
            return render(request, 'option_edit.html', {'html_code': html_code, 'login_user':username, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                field_list = self.ansible_option_api.init_parm(username)
                user_mess_dict = {}
                for field in field_list :
                    try :
                        value = request.POST.get(field)
                        if value :
                            user_mess_dict[field] = value
                    except :
                        pass
                        
                result = self.ansible_option_api.edit_post(username, vault_password, user_mess_dict)
                if not result[0] :
                    error_message = self.username + ' 编辑用户' + username + '的ansible配置失败，提交保存时发生错误，原因：' + result[1]
                    self.logger.error(error_message) 
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 编辑用户' + username + '的ansible配置，提交保存成功')
                    return HttpResponseRedirect(reverse('ansible_option')) 
