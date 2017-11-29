from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse

from lykops.forms import Form_Login
from lykops.views import Base


class User(Base):
    def add(self, request):
        
        '''
        新增用户
        '''
        
        result = self._is_login(request)
        if result[0] :
            creater = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        if request.method == 'GET' :
            form = Form_Login()
            return render(request, 'user_add.html', {'form': form, 'login_user':creater, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                post_key_list = ['username', 'name', 'contact', 'password', 'password-confirm', 'vaultpassword', 'vaultpassword-confirm'] 
                user_mess_dict = {}
                for key in post_key_list :
                    user_mess_dict[key] = request.POST.get(key)
                
                user_mess_dict['creater'] = creater
                    
                result = self.usermanager_api.create(user_mess_dict)
                if not result[0] :
                    error_message = creater + ' 新增用户' + user_mess_dict['username'] + '，提交失败，原因：' + result[1]
                    self.logger.info(error_message)
                    http_referer = self.uri_api.get_httpreferer(creater, no=-2)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(creater + ' 新增用户' + user_mess_dict['username'] + '，提交并保存成功')
                    return HttpResponseRedirect(reverse('user_list')) 
            

    def edit(self, request):
        
        '''
        编辑用户
        '''
        
        result = self._is_login(request)
        if result[0] :
            editer = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        username = request.GET.get('username')
        http_referer = self.uri_api.get_httpreferer(username, no=-2)
        result = self.usermanager_api.detail(username)
        if result[0]:
            data_dict = result[1]
            if not data_dict :
                error_message = self.username + ' 编辑用户' + username + '基础信息失败，原因：用户不存在'
                self.logger.warning(error_message)
                return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            error_message = self.username + ' 编辑用户' + username + '基础信息失败，查询用户信息时发生错误，原因：' + result[1]
            self.logger.error(error_message)
            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})

        if request.method == 'GET' :
            return render(request, 'user_edit.html', {'data_dict': data_dict, 'username':username, 'login_user':editer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                post_key_list = ['name', 'contact'] 
                user_mess_dict = {}
                for key in post_key_list :
                    user_mess_dict[key] = request.POST.get(key)
                
                user_mess_dict['username'] = request.GET.get('username')
                user_mess_dict['lastediter'] = editer
                    
                result = self.usermanager_api.edit(user_mess_dict)
                if not result[0] :
                    error_message = self.username + ' 编辑用户' + username + '基础信息失败，提交时发生错误，原因：' + result[1]
                    self.logger.error(error_message)
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 编辑用户' + username + '基础信息，提交并保存成功')
                    return HttpResponseRedirect(reverse('index'))
                
        
    def change_pwd(self, request):
        
        '''
        修改用户登陆密码
        '''
        
        result = self._is_login(request)
        if result[0] :
            editer = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        username = request.GET.get('username')

        if request.method == 'GET' :
            form = Form_Login()
            return render(request, 'user_chgpwd.html', {'form': form, 'username':username, 'login_user':editer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                user_mess_dict = {}
                user_mess_dict['username'] = request.GET.get('username')
                user_mess_dict['password'] = request.POST.get('password')
                user_mess_dict['password-confirm'] = request.POST.get('password-confirm')
                user_mess_dict['lastediter'] = editer
                    
                result = self.usermanager_api.change_pwd(user_mess_dict)
                if not result[0] :
                    error_message = self.username + ' 编辑用户' + username + '密码失败，提交时发生错误，原因：' + result[1]
                    self.logger.error(error_message)
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 编辑用户' + username + '密码，提交并保存成功')
                    if self.username == user_mess_dict['username'] :
                        return HttpResponseRedirect(reverse('login'))
                    else :
                        return HttpResponseRedirect(reverse('user_list'))
                    
        
    def change_vaultpwd(self, request):
        
        '''
        修改用户vault密码
        '''
        
        result = self._is_login(request)
        if result[0] :
            editer = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        username = request.GET.get('username')

        if request.method == 'GET' :
            form = Form_Login()
            return render(request, 'user_chgvltpwd.html', {'form': form, 'username':username, 'login_user':editer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                user_mess_dict = {}
                user_mess_dict['currvaultpassword'] = request.POST.get('currvaultpassword')
                user_mess_dict['vaultpassword'] = request.POST.get('vaultpassword')
                user_mess_dict['vaultpassword-confirm'] = request.POST.get('vaultpassword-confirm')
                user_mess_dict['lastediter'] = editer
                user_mess_dict['username'] = username
                    
                result = self.usermanager_api.change_vaultpwd(user_mess_dict)
                if not result[0] :
                    error_message = self.username + ' 修改用户' + username + '的vault密码失败，提交时发生错误，原因：' + result[1]
                    self.logger.error(error_message)
                    http_referer = self.uri_api.get_httpreferer(username, no=-1)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 编辑用户' + username + '的vault密码，提交并保存成功')
                    return HttpResponseRedirect(reverse('logout'))
        
                 
    def summary(self, request):
        
        '''
        用户列表
        '''
        
        result = self._is_login(request)
        if not result[0] :
            return HttpResponseRedirect(reverse('login'))
        else :
            username = result[1]
            
        result = self.usermanager_api.summary()

        list_title_list = ['用户', '真实名', '是否激活' , '上次登录时间']
        if result[0] :
            self.logger.info(self.username + ' 获取所有用户信息时成功')
            return render(request, 'user_list.html', {'list_title_list':list_title_list, 'query_list':result[1], 'login_user':username, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            error_message = self.username + ' 获取所有用户信息时失败，原因：' + result[1]
            self.logger.error(error_message)
            return HttpResponseRedirect(reverse('index'))
        

    def detail(self, request):
        
        '''
        查看用户详细信息
        '''
        
        result = self._is_login(request)
        if not result[0] :
            return HttpResponseRedirect(reverse('login'))
        else :
            login_name = result[1]
            
        username = request.GET['username']
        result = self.usermanager_api.detail(username)
        if result[0] :
            self.logger.info(self.username + ' 查看用户' + username + '的详细数据成功')
            return render(request, 'user_detail.html', {'username':username, 'detail_dict':result[1] , 'login_user':login_name, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            error_message = self.username + ' 查看用户' + username + '的详细数据，查询失败，原因：' + result[1]
            self.logger.error(error_message)
            return HttpResponseRedirect(reverse('index'))


    def delete(self, request):
        
        '''
        删除用户
        '''
        
        result = self._is_login(request)
        if result[0] :
            editer = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        username = request.GET.get('username')
                    
        result = self.usermanager_api.delete(username , editer=editer)
        if not result[0] :
            error_message = self.username + ' 删除用户' + username + '，提交失败，原因：' + result[1]
            self.logger.error(error_message)
            http_referer = self.uri_api.get_httpreferer(username, no=-1)
            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            self.logger.info(self.username + ' 删除用户' + username + '成功，注：实际只是标记为删除并非真实删除')
            return HttpResponseRedirect(reverse('user_list'))
                

    def disable(self, request):
        
        '''
        禁用用户登陆
        '''
        
        result = self._is_login(request)
        if result[0] :
            editer = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        username = request.GET.get('username')
                    
        result = self.usermanager_api.disable(username , editer=editer)
        if not result[0] :
            error_message = self.username + ' 禁用用户' + username + '，提交失败，原因：' + result[1]
            self.logger.error(error_message)
            http_referer = self.uri_api.get_httpreferer(username, no=-1)
            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            self.logger.info(self.username + ' 禁用用户' + username + '成功')
            return HttpResponseRedirect(reverse('user_list'))
             
                          
    def enable(self, request):
        
        '''
        允许用户登陆
        '''
        
        result = self._is_login(request)
        if result[0] :
            editer = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        username = request.GET.get('username')
                    
        result = self.usermanager_api.enable(username , editer=editer)
        if not result[0] :
            error_message = self.username + ' 启用用户' + username + '，提交失败，原因：' + result[1]
            self.logger.error(error_message)
            http_referer = self.uri_api.get_httpreferer(username, no=-1)
            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            self.logger.info(self.username + ' 启用用户' + username + '成功')
            return HttpResponseRedirect(reverse('user_list'))
