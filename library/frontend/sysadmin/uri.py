import re, logging

from library.connecter.database.mongo import Op_Mongo
from library.connecter.database.redis_api import Op_Redis
from library.utils.type_conv import str2list

class Manager_Uri():
    def __init__(self, mongoclient=None, redisclient=None):
        
        self.logger = logging.getLogger("lykops")
        if mongoclient is None :
            self.mongoclient = Op_Mongo()
            self.logger.warn('无法继承，需要初始化mongodb连接')
        else :
            self.mongoclient = mongoclient
            
        if redisclient is None :
            self.redisclient = Op_Redis()
            self.logger.warn('无法继承，需要初始化redis连接')
        else :
            self.redisclient = redisclient
    
        self.redis_key_prefix = 'lykops:'
        self.expiretime = 60 * 60 * 24
        
        self.uridict = {
            '/':{'name':'首页', 'nav':False, 'referer' : True, 'level':0, 'parent':'/'},
            '/login.html':{'name':'登陆', 'nav':False, 'referer' : False, 'level':1, 'parent':'/'},
            '/logout.html':{'name':'退出', 'nav':False, 'referer' : False, 'level':1, 'parent':'/'},
            
            '/user/':{'name':'用户管理', 'nav':True, 'referer' : True, 'level':1, 'parent':'/'},
            '/user/create_admin':{'name':'创建管理员', 'nav':False, 'referer' : True, 'level':2, 'parent':'/user/'},
            '/user/detail':{'name':'用户信息', 'nav':False, 'referer' : True, 'level':2, 'parent':'/user/'},
            '/user/list':{'name':'用户列表', 'nav':False, 'referer' : True, 'level':2, 'parent':'user/'},
            '/user/add':{'name':'新增用户', 'nav':False, 'referer' : True, 'level':2, 'parent':'/user/'},
            '/user/edit':{'name':'编辑用户', 'nav':False, 'referer' : True, 'level':2, 'parent':'/user/'},
            '/user/chgpwd':{'name':'修改用户登陆密码', 'nav':False, 'referer' : True, 'level':2, 'parent':'/user/'},
            '/user/chgpvltwd':{'name':'修改用户机密密码 ', 'nav':False, 'referer' : True, 'level':2, 'parent':'/user/'},
            '/user/del':{'name':'删除用户', 'nav':False, 'referer' : False, 'level':2, 'parent':'/user/'},
            '/user/disable':{'name':'禁用用户', 'nav':False, 'referer' : False, 'level':2, 'parent':'/user/'},
            '/user/enable':{'name':'启用用户', 'nav':False, 'referer' : False, 'level':2, 'parent':'/user/'},
            
            # '/privacy/' :{'name':'隐私数据管理', 'nav':True, 'referer' : True, 'level':1, 'parent':'/'},
            # '/privacy/detail' :{'name':'查看隐私数据', 'nav':False, 'referer' : True, 'level':2, 'parent':'/privacy/'},
            # '/privacy/edit' :{'name':'编辑隐私数据', 'nav':False, 'referer' : True, 'level':2, 'parent':'/privacy/'},
            
            '/inventory/' :{'name':' 主机管理', 'nav':True, 'referer' : True, 'level':1, 'parent':'/'},
            '/inventory/list' :{'name':' 主机管理', 'nav':False, 'referer' : True, 'level':2, 'parent':'/inventory/'},
            '/inventory/add' :{'name':' 增加主机', 'nav':False, 'referer' : True, 'level':2, 'parent':'/inventory/'},
            '/inventory/edit' :{'name':' 编辑主机', 'nav':False, 'referer' : True, 'level':2, 'parent':'/inventory/'},
            '/inventory/detail' :{'name':' 主机详细信息', 'nav':False, 'referer' : True, 'level':2, 'parent':'/inventory/'},
            
            '/ansible/' :{'name':'ansible', 'nav':True, 'referer' : True, 'level':1, 'parent':'/'},
            '/ansible/exec/adhoc' :{'name':'执行临时任务', 'nav':True, 'referer' : True, 'level':2, 'parent':'/ansible/'},
            '/ansible/exec/playbook' :{'name':'执行playbook任务', 'nav':True, 'referer' : True, 'level':2, 'parent':'/ansible/'},
            
            '/ansible/option/' :{'name':'查看配置', 'nav':True, 'referer' : True, 'level':2, 'parent':'/ansible/'},
            '/ansible/option/detail' :{'name':'查看配置', 'nav':True, 'referer' : True, 'level':3, 'parent':'/ansible/option/'},
            '/ansible/option/edit' :{'name':'编辑配置', 'nav':False, 'referer' : True, 'level':3, 'parent':'/ansible/option/'},
            
            '/ansible/yaml/' :{'name':'yaml数据列表', 'nav':True, 'referer' : True, 'level':2, 'parent':'/ansible/'},
            '/ansible/yaml/list' :{'name':'yaml数据列表', 'nav':False, 'referer' : True, 'level':3, 'parent':'/ansible/yaml/'},
            '/ansible/yaml/add' :{'name':'新增yaml数据', 'nav':False, 'referer' : False, 'level':3, 'parent':'/ansible/yaml/'},
            '/ansible/yaml/edit' :{'name':'编辑yaml数据', 'nav':False, 'referer' : True, 'level':3, 'parent':'/ansible/yaml/'},
            '/ansible/yaml/detail' :{'name':'查看yaml数据', 'nav':False, 'referer' : True, 'level':3, 'parent':'/ansible/yaml/'},
            '/ansible/yaml/import' :{'name':'导入yaml数据', 'nav':False, 'referer' : True, 'level':3, 'parent':'/ansible/yaml/'},
            
            '/ansible/report/' :{'name':'报告', 'nav':True, 'referer' : True, 'level':2, 'parent':'/ansible/'},
            '/ansible/report/list' :{'name':'报告列表', 'nav':False, 'referer' : True, 'level':3, 'parent':'/ansible/report/'},
            '/ansible/report/detail' :{'name':'单个报告详细信息', 'nav':False, 'referer' : True, 'level':3, 'parent':'/ansible/report/'},
            
            }


    def get_nav(self, username, force=False):
        
        '''
        获取左侧栏信息
        '''
        
        redis_key = 'lykops:' + username + ':uri:nav'
        if force:
            self.logger.warn('强制删除缓存')
            self.redisclient.delete(redis_key)
        else :
            result = self.redisclient.get(redis_key)
            if not result[0] or (result[1] is None or not result[1]) :
                nav_str = result[1]
                return nav_str
            
        nav_str = self.gen_nav(username)
        set_dict = {
            'name' : redis_key,
            'value' : nav_str,
            'ex':self.expiretime
            }
        self.redisclient.set(set_dict, fmt='obj')
        return nav_str
    
    
    def gen_nav(self, username):
        
        '''
        生成左侧栏信息，注意：目前只支持两级
        '''
        
        nav_dict = {}
        for uri, value in self.uridict.items() :
            if value['nav'] :
                nav_dict[uri] = value

        uri_dict = {}
        for key, value in nav_dict.items() :
            level = value['level']
            if level == 1 :
                if key not in uri_dict :
                    uri_dict[key] = {}
                
                for childkey, childvalue in nav_dict.items() :
                    if childvalue['parent'] == key:
                        uri_dict[key][childkey] = {}
                          
        for key, value in nav_dict.items() :
            level = value['level']
            if level == 2 :
                parent = value['parent']
                if key not in uri_dict[parent] :
                    uri_dict[parent][key] = {}
                
                for childkey, childvalue in nav_dict.items() :
                    if childvalue['parent'] == key:
                        uri_dict[parent][key][childkey] = {}
        
        nav_str = ''
        
        for key,value in uri_dict.items() :
            if not value :
                name = self.uridict[key]['name']
                nav_str = nav_str + "<ul class='nav nav-first-level'>" + "\n"
                nav_str = nav_str + "<li class='" + name + "'><a href='" + key + "'>" + name + "</a></li>" + "\n"
            else :
                frist_title =  self.uridict[key]['name']
                nav_str = nav_str + "<ul class='nav nav-first-level'>" + "\n"
                nav_str = nav_str + "<li id='"+frist_title+"'>" + "\n"
                nav_str = nav_str + "<a href='#'><i class='fa fa-group'></i><span class='nav-label'>"+frist_title+"</span><span class='fa arrow'></span></a>" + "\n"
                for k in value :
                    name = self.uridict[k]['name']
                    nav_str = nav_str + "<ul class='nav nav-second-level'>" + "\n"
                    nav_str = nav_str + "<li class='" + name + "'><a href='" + k + "'>" + name + "</a></li>" + "\n"
                    nav_str = nav_str + "</ul>" + "\n"
                    
                nav_str = nav_str + "</li>\n</ul>\n"

        return nav_str
        

    def get_httpreferer(self, username, no=-1):
        
        '''
        返回http_referer
        '''
        
        redis_key = self.redis_key_prefix + username + ':whereabouts'
        result = self.redisclient.get(redis_key, fmt='obj')
        if result[0] :
            whereabouts = result[1]
        else :
            whereabouts = []
        
        try :
            http_referer = whereabouts[no]['http_referer']
        except :
            http_referer = '/'
        
        return http_referer
        
        
    def get_lately_whereabouts(self, username):
        
        '''
        获取最近的访问路劲
        '''
        
        redis_key = self.redis_key_prefix + username + ':whereabouts'
        result = self.redisclient.get(redis_key, fmt='obj')
        if result[0] :
            whereabouts = result[1]
        else :
            whereabouts = []
        
        try :
            lastly = whereabouts[-5:-1]
        except :
            lastly = []
        
        lastly_html = '<strong>最近的访问路径：'
        leng = len(lastly)
        for i in range(leng) :
            path = lastly[i]
            if i + 1 == leng :
                lastly_html = lastly_html + '<a href="' + path['http_referer'] + '">' + path['name'] + '</a>\n'
            else :
                lastly_html = lastly_html + '<a href="' + path['http_referer'] + '">' + path['name'] + '</a>==>\n'

        lastly_html = lastly_html + '</strong>'
        return lastly_html
    
        
    def get_whereabouts(self, username, http_referer, http_host):
        
        '''
        记录访问路径
        '''
        
        if http_referer is not None :
            path_info = http_referer.replace('http://' + http_host, '')
            path_info = path_info.replace('https://' + http_host, '')
            http_referer = path_info
            
            if re.search('\?', path_info) :
                end = re.split('\?', path_info)[-1]
                path_info = path_info.replace('?' + end, '')
        else :
            path_info = '/'
                  
        redis_key = self.redis_key_prefix + username + ':whereabouts'
        result = self.redisclient.get(redis_key, fmt='obj')
        if result[0] :
            whereabouts = result[1]
            result = str2list(whereabouts)
            if result[0] :
                whereabouts = result[1]
                if whereabouts[-1]['http_referer'] == http_referer or http_referer is None:
                    return whereabouts
            else :
                if http_referer is None:
                    return []
                else :
                    whereabouts = []
        else :
            whereabouts = []
        
        try :
            path_dict = self.uridict[path_info]
            if path_dict['referer'] :
                name = path_dict['name']
            else :
                return whereabouts
        except :
            print('请把' + path_info + '加入到self.uridict')
            self.logger.warn('请把' + path_info + '加入到self.uridict')
            return whereabouts
            
        try :
            self.redisclient.delete(redis_key)
        except :
            pass
            
        path_dict = {
            'name' : name ,
            'http_referer' : http_referer
            }
            
        if whereabouts :
            whereabouts.append(path_dict)
        else :
            whereabouts = [path_dict]

        set_dict = {
            'name' : redis_key,
            'value' : whereabouts,
            'ex':self.expiretime
            }
        self.redisclient.set(set_dict, fmt='obj')
        return whereabouts
