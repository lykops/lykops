import json

from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.urls.base import reverse

from lykops.views import Base


class Report(Base):
    def summary(self,request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        http_referer = self.uri_api.get_httpreferer(username, no=-1)
        force = request.GET.get('force', False) 
        result = self.ansible_report_api.get_date_list(username, force=force)
        if not result[0] :
            return render_to_response('report_list.html', {'login_user':username, 'error_message':result[1], 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            date_list = result[1]
        
        create_date = request.GET.get('create_date', None)
        if create_date == 'None' :
            create_date = None
        mode = request.GET.get('mode', 'all') 
        result = self.ansible_report_api.summary(username, dt=create_date, mode=mode)
        if not result[0] :
            error_message = self.username + ' 查看用户' + username + '的ansible任务执行报告列表失败，提交保存时发生错误，原因：' + result[1]
            self.logger.error(error_message) 
            return render_to_response('report_list.html', {'login_user':username, 'error_message':error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            work_list = result[1]
        
        self.logger.info(self.username + ' 查看用户' + username + '的ansible任务执行报告列表成功')
        return render_to_response('report_list.html', {'login_user':username, 'error_message':{}, 'http_referer':http_referer, 'date_list':date_list, 'work_list':work_list, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})


    def detail(self, request):
        result = self._is_login(request)
        if result[0] :
            username = result[1]
        else :
            return HttpResponseRedirect(reverse('login'))
        
        http_referer = self.uri_api.get_httpreferer(username, no=-1)
        force = request.GET.get('force', False) 
        force = bool(force)
        uuid_str = request.GET.get('uuid', False) 
        exec_mode = request.GET.get('mode', False) 
        orig_content = request.GET.get('orig_content', False) 
        orig_content = bool(orig_content)
        
        result = self.ansible_report_api.detail(username, uuid_str, force=force, orig_content=orig_content)
        if result[0] :
            report_data = result[1]
            if orig_content :
                self.logger.info(self.username + ' 查看用户' + username + '的uuid为' + uuid_str + '的ansible任务执行报告成功（原始数据）')
                return HttpResponse(json.dumps(report_data))
                return render_to_response('result.html', {'login_user':username, 'content':report_data, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
            
            self.logger.info(self.username + ' 查看用户' + username + '的uuid为' + uuid_str + '的ansible任务执行报告成功（格式化数据）')
            if exec_mode == 'adhoc' :
                return render_to_response('report_adhoc.html', {'login_user':username, 'report_data':report_data, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
            else :
                return render_to_response('report_playbook.html', {'login_user':username, 'report_data':report_data, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
        else :
            error_message = self.username + ' 查看用户' + username + '的uuid为' + uuid_str + '的ansible任务执行报告失败，查询时发生错误，原因：' + result[1]
            self.logger.error(error_message) 
            return render_to_response('result.html', {'login_user':username, 'content':error_message, 'http_referer':http_referer, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html, 'nav_html':self.nav_html, 'lately_whereabouts':self.latelywhere_html})
