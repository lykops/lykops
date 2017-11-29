from django.http.response import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.urls.base import reverse

from lykops.forms import Form_Login
from lykops.views import Base


class Privacy(Base):
    
    '''
    该功能用于保存用户的机密数据，但该版本暂时不需要使用，故暂时不做展示
    '''
    
    def detail(self, request):
        
        '''
        查看用户的privacy数据
        '''
        
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
    
        vault_password = request.session['vault_password']
    
        try :
            force = request.GET['force']
        except :
            force = False
    
        result = self.privacy_api.get(username, vault_password=vault_password, force=force)
        if result[0] :
            data_dict = result[1]
            error_message = ''
            self.logger.info(self.username + ' 查看用户' + username + '的机密数据，查询数据成功')
        else :
            data_dict = {}
            error_message = self.username + ' 查看用户' + username + '的机密数据失败，原因：' + result[1]
            self.logger.error(error_message)
            
        return render_to_response('privacy_detail.html', {'data_dict':data_dict, 'login_user':username, 'error_message':error_message, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
    

    def edit(self, request):
        
        '''
        编辑用户的privacy数据
        '''
        
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        vault_password = request.session['vault_password']
        http_referer = 'detail'
    
        result = self.privacy_api.get(username, vault_password=vault_password, force=True)
        if result[0] :
            data_dict = result[1]
            error_message = ''
        else :
            data_dict = {}
            error_message = result[1]
        
        if not data_dict or data_dict == {} :
            ranges = range(0, 10)
        else :
            ranges = range(0, 5)
            
        if request.method == 'GET' :
            form = Form_Login()
            if error_message :
                error_message = self.username + ' 编辑用户' + username + '的机密数据失败，查询时发生错误，原因：' + result[1]
                self.logger.error(error_message)
            else :
                self.logger.info(self.username + ' 编辑用户' + username + '的机密数据，查询数据成功')
                
            return render(request, 'privacy_edit.html', {'data_dict': data_dict, 'login_user':username, 'error_message':error_message, 'form':form, 'new_list':list(ranges), 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else:
            form = Form_Login(request.POST)
            if form.is_valid():
                update_dict = {}
                for key , vaule in data_dict.items() :
                    keys = request.POST.get('key:' + key)
                    vaules = request.POST.get('vaule:' + key + ':' + vaule)
                    
                    if not (keys == '' or not keys) :
                        new_key = keys
                    else :
                        new_key = key
                        
                    if not (vaules == '' or not vaules) :
                        new_vaule = vaules
                    else :
                        new_vaule = vaule
                    
                    if new_key in update_dict :
                        error_message = self.username + ' 编辑用户' + username + '的机密数据失败，原因：键' + new_key + '出现重复'
                        self.logger.error(error_message)
                        return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                    
                    update_dict[new_key] = new_vaule
                                
                for i in ranges :
                    keys = request.POST.get('key:' + str(i))
                    if not (keys == '' or not keys) :
                        if keys in update_dict :
                            error_message = self.username + ' 编辑用户' + username + '的机密数据失败，原因：键' + new_key + '出现重复'
                            self.logger.error(error_message)
                            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                        
                        vaules = request.POST.get('vaule:' + str(i))
                        if keys == vaules :
                            error_message = self.username + ' 编辑用户' + username + '的机密数据失败，原因：键和值不能重复'
                            self.logger.error(error_message)
                            return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                        
                        update_dict[keys] = vaules
                
                result = self.privacy_api.save(username, update_dict, vault_password)
                if not result[0] :
                    error_message = self.username + ' 编辑用户' + username + '的机密数据失败，提交数据时发生错误，原因：' + result[1]
                    self.logger.error(error_message)
                    return render(request, 'result.html', {'error_message' : error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
                else :
                    self.logger.info(self.username + ' 编辑用户' + username + '的机密数据，提交并保存成功')
                    return HttpResponseRedirect(reverse('privacy_detail')) 
