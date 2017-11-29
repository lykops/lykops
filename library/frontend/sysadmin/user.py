import time

from library.config.frontend import adminuser
from library.frontend import Base
from library.frontend.ansible.options import Manager_Option
from library.frontend.sysadmin.inventory import Manager_Inventory
# from library.frontend.sysadmin.privacy import Manager_Privacy
from library.utils.time_conv import timestamp2datetime


class Manager_User(Base):
    
    def is_has(self, username):
        
        '''
        查看用户是否存在
        '''
        
        result = self.mongoclient.find(self.userinfo_mongocollect, condition_dict={'username':username})
        if not result[0] or (result[1] is None or not result[1]) :
            return False
        else :
            return True 
        
    
    def summary(self):
        
        '''
        用户列表
        '''
        
        result = self.get_userinfo()
        get_field = ['username', 'name', 'isalive' , 'lastlogin_time']
        if not result :
            self.logger.info('查询失败或者没有用户，原因：' + str(result[1]))
            return (False, result[1])
        else :
            query_list = []
            for data in result:
                temp_list = []
                
                if 'lastlogin_time' not in data :
                    data['lastlogin_time'] = ''
                
                for key, vaule in data.items() :
                    if key == 'lastlogin_time' :
                        vaule = timestamp2datetime(vaule)
                        if not vaule :
                            vaule = '-'

                    if key == 'isalive' :
                        if vaule :
                            vaule = '是'
                        else :
                            vaule = '否'
                            
                    if key in get_field :
                        temp_list.append(vaule)
            
                query_list.append(temp_list)    
            
            return (True, query_list)
        
    
    def isalive(self,username):
        userinfo = self.get_userinfo(username=username)
        if not userinfo :
            content = '用户' + username + '不存在'
            self.logger.error(content)
            return (False, content)
        else :
            try :
                isalive = userinfo['isalive']
                if not isalive :
                    content = '用户' + username + '已被禁止登陆'
                    self.logger.warn(content)
                    return (False, content)
                else :
                    return (True,userinfo)
            except :
                content = '用户' + username + '不存在'
                self.logger.error(content)
                return (False, content)
        

    def login(self, username, password, vault_password):
        
        '''
        用户登陆
        '''
        
        result = self.isalive(username)
        if not result[0] :
            return result
        user_dict = result[1]
        cipher_pwd = user_dict['password']
        
        result = self.password_api.verify(password, cipher_pwd)
        if not result :
            self.logger.error('用户' + username + '登陆失败，原因：输入的登陆密码不正确')
            return (False, '输入的登陆密码不正确')
        
        cipher_pwd = user_dict['vault_password']
        result = self.password_api.verify(vault_password, cipher_pwd)
        if not result :
            self.logger.error('用户' + username + '登陆失败，原因：输入的vault密码不正确')
            return (False, '输入的vault密码不正确')
        
        update_dict = {'collect':self.userinfo_mongocollect, 'data':{"$set": {'lastlogin_time':time.time()}}}
        self.mongoclient.update({'username':username}, update_dict, addtime=True)
        self.redisclient.delete(self.userinfo_rediskey)
        return (True, '登录成功')
    
    
    def delete(self, username, editer=False):
        
        '''
        删除用户，暂时只是禁用
        '''
        
        userinfo = self.get_userinfo(username=username)
        if not userinfo :
            content = '删除用户' + username + '失败，原因：用户不存在'
            self.logger.error(content)
            return (False, content)
        
        if username == adminuser :
            self.logger.warn('删除用户' + username + '失败，原因：该用户是超级管理员，不能被禁用')
            return (False, '该用户是超级管理员，不能被禁用')
        
        if editer and editer == username :
            self.logger.warn('删除用户' + username + '失败，原因：该用户是当前登陆者（即自己不能禁用自己），不能被禁用')
            return (False, '该用户是当前登陆者（即自己不能禁用自己），不能被禁用')
        
        if not editer :
            editer = username

        update_dict = {
            'collect':self.userinfo_mongocollect,
            'data':{
                "$set": {
                    'lastediter' : editer,
                    'lastedit_time' : time.time(),
                    'isalive':False,
                    }
                }
            }
        result = self.mongoclient.update({'username':username}, update_dict, addtime=True)
        self.redisclient.delete(self.userinfo_rediskey)
        if result[0] :
            content = '用户' + username + '删除成功'
            self.logger.info(content)
            return (True, content)
        else :
            self.logger.error('用户' + username + '删除失败，原因：' + result[1])
            return (False, result[1])
        

    def disable(self, username, editer=False):
        
        '''
        禁用用户
        '''
        
        userinfo = self.get_userinfo(username=username)
        if not userinfo :
            content = '禁用用户' + username + '失败，原因：用户不存在'
            self.logger.error(content)
            return (False, content)
        
        if username == adminuser :
            self.logger.warn('禁用用户' + username + '失败，原因：该用户是超级管理员，不能被禁用')
            return (False, '该用户是超级管理员，不能被禁用')
        
        if editer and editer == username :
            self.logger.warn('禁用用户' + username + '失败，原因：该用户是当前登陆者（即自己不能禁用自己），不能被禁用')
            return (False, '该用户是当前登陆者（即自己不能禁用自己），不能被禁用')
        
        if not editer :
            editer = username

        update_dict = {
            'collect':self.userinfo_mongocollect,
            'data':{
                "$set": {
                    'lastediter' : editer,
                    'lastedit_time' : time.time(),
                    'isalive':False,
                    }
                }
            }
        result = self.mongoclient.update({'username':username}, update_dict, addtime=True)
        self.redisclient.delete(self.userinfo_rediskey)
        if result[0] :
            content = '用户' + username + '禁用成功'
            self.logger.info(content)
            return (True, content)
        else :
            self.logger.error('用户' + username + '禁用失败，原因：' + result[1])
            return (False, result[1])
        
        
    def enable(self, username, editer=False):
        
        '''
        启用用户
        '''
        
        userinfo = self.get_userinfo(username=username)
        if not userinfo :
            self.logger.error('激活用户' + username + '失败，原因：用户不存在')
            return (False, '用户不存在')
        
        if not editer :
            editer = username

        update_dict = {
            'collect':self.userinfo_mongocollect,
            'data':{
                "$set": {
                    'lastediter' : editer,
                    'lastedit_time' : time.time(),
                    'isalive':True,
                    }
                }
            }
        result = self.mongoclient.update({'username':username}, update_dict, addtime=True)
        self.redisclient.delete(self.userinfo_rediskey)
        if result[0] :
            content = '用户' + username + '激活成功'
            self.logger.info(content)
            return (True, content)
        else :
            self.logger.error('用户' + username + '激活失败，原因：' + result[1])
            return (False, result[1])
        

    def edit(self, user_mess_dict):
        
        '''
        编辑用户信息
        '''
        
        set_dict = {}

        if isinstance(user_mess_dict, dict) and not user_mess_dict :
            self.logger.error('编辑用户基本信息失败，原因：参数user_mess_dict不是一个非空字典')
            return (False, '参数user_mess_dict不是一个非空字典')

        if 'username' not in user_mess_dict :
            self.logger.error('编辑用户基本信息失败，原因：参数user_mess_dict不包含username')
            return (False, '参数user_mess_dict不包含username')
        
        username = user_mess_dict['username']
        condition_dict = {'username' : username}
            
        old_user_dict = self.get_userinfo(username=username)
        if not old_user_dict :
            self.logger.error('编辑用户' + username + '基本信息失败，原因：用户不存在')
            return (False, '用户不存在')

        if 'isalive' in user_mess_dict and user_mess_dict['isalive']:
            if 'isalive' in old_user_dict :
                if user_mess_dict['isalive'] != old_user_dict['isalive'] :
                    set_dict['isalive'] = user_mess_dict['isalive']
            else :
                set_dict['isalive'] = user_mess_dict['isalive']
                
        if 'contact' in user_mess_dict and user_mess_dict['contact'] :
            if 'contact' in old_user_dict :
                if user_mess_dict['contact'] != old_user_dict['contact'] :
                    set_dict['contact'] = user_mess_dict['contact']
            else :
                set_dict['contact'] = user_mess_dict['contact']
                
        if 'name' in user_mess_dict and user_mess_dict['name']:
            if 'name' in old_user_dict :
                if user_mess_dict['name'] != old_user_dict['name'] :
                    set_dict['name'] = user_mess_dict['name']
            else :
                set_dict['name'] = user_mess_dict['name']
                
        if not set_dict :
            self.logger.warn('编辑用户' + username + '用户基本信息失败，原因：没有任何数据需要更新')
            return (False, '没有任何数据需要更新')
        
        set_dict['lastedit_time'] = time.time()
        set_dict['lastediter'] = user_mess_dict['lastediter']
        
        update_dict = {'collect':self.userinfo_mongocollect, 'data':{"$set": set_dict}}
        result = self.mongoclient.update(condition_dict, update_dict, addtime=True)
        self.redisclient.delete(self.userinfo_rediskey)
        if result[0] :
            content = '编辑用户' + username + '基本信息成功'
            self.logger.info(content)
            return (True, content)
        else :
            self.logger.info('编辑用户' + username + '基本信息失败，原因：' + result[1])
            return (False, result[1])


    def change_pwd(self, user_mess_dict):
        
        '''
        修改用户登陆密码
        '''
        
        set_dict = {}
        if isinstance(user_mess_dict, dict) and not user_mess_dict :
            self.logger.error('修改用户登陆密码失败，原因：参数user_mess_dict不是一个非空字典')
            return (False, '参数user_mess_dict不是一个非空字典')

        if 'username' not in user_mess_dict :
            self.logger.error('修改用户登陆密码失败，原因：参数user_mess_dict不包含username')
            return (False, '参数user_mess_dict不包含username')
        
        username = user_mess_dict['username']
        condition_dict = {'username' : username}
            
        old_user_dict = self.get_userinfo(username=username)
        if not old_user_dict :
            self.logger.error('修改用户' + username + '登陆密码失败，原因：用户不存在')
            return (False, '用户不存在')
            
        password = user_mess_dict['password']
        passwordconfirm = user_mess_dict['password-confirm']

        if (password and not passwordconfirm) or (not password and passwordconfirm) or password != passwordconfirm:
            self.logger.error('修改用户' + username + '登陆密码失败，原因：两次输入的登陆密码不一致')
            return (False, '两次输入的登陆密码不一致')

        if password and passwordconfirm:
            result = self.password_api.encryt(password)
            if not result[0] :
                self.logger.error('修改用户' + username + '登陆密码失败，原因：无法加密登陆密码，' + result[1])
                return (False, '无法加密登陆密码，' + result[1])
                    
            if old_user_dict['password'] != result[1] :
                set_dict['password'] = result[1]
                
            if old_user_dict['vault_password'] == result[1] :
                self.logger.error('修改用户' + username + '登陆密码失败，原因：登陆密码不能和vault密码相同')
                return (False, '登陆密码不能和vault密码相同')
                
        if not set_dict :
            self.logger.warn('修改用户' + username + '登陆密码失败，原因：没有任何数据需要更新')
            return (False, '没有任何数据需要更新')
        
        set_dict['lastedit_time'] = time.time()
        set_dict['lastediter'] = user_mess_dict['lastediter']
        
        update_dict = {'collect':self.userinfo_mongocollect, 'data':{"$set": set_dict}}
        result = self.mongoclient.update(condition_dict, update_dict, addtime=True)
        self.redisclient.delete(self.userinfo_rediskey)
        if result[0] :
            content = '修改用户' + username + '登陆密码成功'
            self.logger.info(content)
            return (True, content)
        else :
            self.logger.info('修改用户' + username + '登陆密码失败，原因：' + result[1])
            return (False, result[1])


    def change_vaultpwd(self, user_mess_dict):
        
        '''
        修改用户vault密码
        '''
        
        set_dict = {}
        if isinstance(user_mess_dict, dict) and not user_mess_dict :
            self.logger.error('修改用户vault密码失败，原因：参数user_mess_dict不是一个非空字典')
            return (False, '参数user_mess_dict不是一个非空字典')

        if 'username' not in user_mess_dict :
            self.logger.error('修改用户vault密码失败，原因：参数user_mess_dict不包含username')
            return (False, '参数user_mess_dict不包含username')
        
        username = user_mess_dict['username']
        condition_dict = {'username' : username}
            
        old_user_dict = self.get_userinfo(username=username)
        if not old_user_dict :
            self.logger.error('修改用户' + username + 'vault密码失败，原因：用户不存在')
            return (False, '用户不存在')
        
        currvaultpassword = user_mess_dict['currvaultpassword']
        vaultpassword = user_mess_dict['vaultpassword']
        vaultpasswordconfirm = user_mess_dict['vaultpassword-confirm']
        
        if (vaultpassword and not vaultpasswordconfirm) or (not vaultpassword and vaultpasswordconfirm) or vaultpassword != vaultpasswordconfirm:
            self.logger.error('修改用户' + username + 'vault密码失败，原因：两次输入的登陆密码不一致')
            return (False, '两次输入的vault密码不一致')
        
        if not currvaultpassword :
            self.logger.error('修改用户' + username + 'vault密码失败，原因：请输入当前的vault密码')
            return (False, '请输入当前的vault密码')
        
        if currvaultpassword == vaultpassword :
            self.logger.error('修改用户' + username + 'vault密码失败，原因：当前的vault密码不能和新vault密码相同')
            return (False, '当前的vault密码不能和新vault密码相同')

        result = self.password_api.verify(currvaultpassword, old_user_dict['vault_password'])
        if not result :
            self.logger.error('修改用户' + username + 'vault密码失败，原因：用户输入的vault密码不正确')
            return (False, '用户输入的vault密码不正确')
        
        if vaultpassword and vaultpasswordconfirm :
            result = self.password_api.encryt(vaultpassword)
            if not result[0] :
                self.logger.error('修改用户' + username + 'vault密码失败，原因：无法加密vault密码，' + result[1])
                return (False, '无法加密vault密码，' + result[1])
                      
            if old_user_dict['vault_password'] != result[1] :
                set_dict['vault_password'] = result[1]
                
            if old_user_dict['password'] == result[1] :
                self.logger.error('修改用户' + username + 'vault密码失败，原因：vault密码不能和登陆密码相同')
                return (False, 'vault密码不能和登陆密码相同')
                
        if not set_dict :
            self.logger.error('修改用户' + username + 'vault密码失败，原因：没有任何数据需要更新')
            return (False, '没有任何数据需要更新')
        
        set_dict['lastedit_time'] = time.time()
        set_dict['lastediter'] = user_mess_dict['lastediter']
        
        '''
        # 修改vault前期工作
        该功能用于保存用户的机密数据，但该版本暂时不需要使用，故暂时不做展示
        privacyapi = Manager_Privacy(mongoclient=self.mongoclient, redisclient=self.redisclient)
        result = privacyapi.change_vault_password(username, currvaultpassword, vaultpassword)
        if not result[0] :
            self.logger.error('修改用户' + username + 'vault密码失败，修改用户机密数据时失败，原因：没有任何数据需要更新')
            return (False, '修改用户机密数据时失败，原因：' + result[1])
        '''
        
        inventoryapi = Manager_Inventory(mongoclient=self.mongoclient, redisclient=self.redisclient)
        result = inventoryapi.change_vault_password(username, currvaultpassword, vaultpassword)
        if not result[0] :
            self.logger.error('修改用户' + username + 'vault密码失败，修改用户主机信息时失败，原因：没有任何数据需要更新')
            return (False, '修改用户主机信息时失败，原因：' + result[1])
        
        ansible_option_api = Manager_Option(mongoclient=self.mongoclient, redisclient=self.redisclient)
        result = ansible_option_api.change_vault_password(username, currvaultpassword, vaultpassword)
        if not result[0] :
            self.logger.error('修改用户' + username + 'vault密码失败，修改用户的ansible的配置信息时失败，原因：没有任何数据需要更新')
            return (False, '修改用户的ansible的配置信息时失败，原因：' + result[1])
        
        update_dict = {'collect':self.userinfo_mongocollect, 'data':{"$set": set_dict}}
        result = self.mongoclient.update(condition_dict, update_dict, addtime=True)
        if not result[0] :
            self.logger.error('修改用户' + username + 'vault密码失败，原因：在写入数据库时出现错误，原因：' + result[1])
            return (False, '在写入数据库时出现错误，原因：' + result[1])

        # 修改vault后期工作
        '''
        该功能用于保存用户的机密数据，但该版本暂时不需要使用，故暂时不做展示
        update_dict = {'collect':self.userinfo_mongocollect, 'data':{"$set": old_user_dict}}
        result = privacyapi.save_vault(username)
        if not result[0] :
            self.mongoclient.update(condition_dict, update_dict, addtime=True)
            self.logger.error('修改用户' + username + 'vault密码失败，用户机密数据写入时出现错误，原因：' + str(result[1]) + '；vault密码已恢复')
            return (False, '用户机密数据写入时出现错误，原因：' + str(result[1]) + '；vault密码已恢复')
        '''
        
        result = inventoryapi.save_vault(username)
        if not result[0] :
            self.mongoclient.update(condition_dict, update_dict, addtime=True)
            self.logger.error('修改用户' + username + 'vault密码失败，用户主机信息写入时出现错误，原因：' + str(result[1]) + '；vault密码已恢复')
            return (False, '用户主机信息写入时出现错误，原因：' + str(result[1]) + '；vault密码已恢复')
        
        result = ansible_option_api.save_vault(username)
        if not result[0] :
            self.mongoclient.update(condition_dict, update_dict, addtime=True)
            self.logger.error('修改用户' + username + 'vault密码失败，用户的ansible配置信息写入时出现错误，原因：' + str(result[1]) + '；vault密码已恢复')
            return (False, '用户的ansible配置信息写入时出现错误，原因：' + str(result[1]) + '；vault密码已恢复')
        
        self.redisclient.delete(self.userinfo_rediskey)
        self.logger.info('修改用户' + username + 'vault密码成功')
        return (True, '修改vault密码成功')

 
    def create(self, user_mess_dict):
        
        '''
        创建用户
        '''
        
        if isinstance(user_mess_dict, dict) and not user_mess_dict :
            self.logger.error('创建用户失败，原因：参数user_mess_dict不是一个非空字典')
            return (False, '参数user_mess_dict不是一个非空字典')

        if 'username' in user_mess_dict :
            username = user_mess_dict['username']
        else :
            self.logger.error('创建用户失败，原因：参数user_mess_dict不包含username')
            return (False, '参数user_mess_dict不包含username')
            
        old_user_dict = self.get_userinfo(username=username)
        if old_user_dict :
            self.logger.error('创建用户' + username + '失败，原因：用户已存在')
            return (False, '用户' + username + '已存在')
            
        if 'password' in user_mess_dict :
            password = user_mess_dict['password']
        else :     
            self.logger.error('创建用户' + username + '失败，原因：请输入用户的登陆密码')
            return (False, '请输入用户密码')
        
        if 'password-confirm' in user_mess_dict :
            passwordconfirm = user_mess_dict['password-confirm']
        else :
            self.logger.error('创建用户' + username + '失败，原因：请输入用户的登陆密码')
            return (False, '请输入用户密码')

        if 'vaultpassword' in user_mess_dict  :
            vaultpassword = user_mess_dict['vaultpassword']
        else :
            self.logger.error('创建用户' + username + '失败，原因：请输入用户的vault密码')
            return (False, '请输入用户的vault密码')
        
        if 'vaultpassword-confirm' in user_mess_dict  :
            vaultpasswordconfirm = user_mess_dict['vaultpassword-confirm']
        else :
            self.logger.error('创建用户' + username + '失败，原因：请输入用户的vault密码')
            return (False, '请输入用户的vault密码')

        if password != passwordconfirm :  
            self.logger.error('创建用户' + username + '失败，原因：两次输入的登陆密码不一致')
            return (False, '两次输入的登陆密码不一致')
                
        if vaultpassword != vaultpasswordconfirm :  
            self.logger.error('创建用户' + username + '失败，原因：两次输入的vault密码不一致')
            return (False, '两次输入的vault密码不一致')
        
        result = self.password_api.encryt(password)
        if not result[0] :
            self.logger.error('创建用户' + username + '失败，原因：无法加密登陆密码' + result[1])
            return (False, '无法加密登陆密码' + result[1])
        cipher_lpwd = result[1]

        result = self.password_api.encryt(vaultpassword)
        if not result[0] :
            self.logger.error('创建用户' + username + '失败，原因：无法加密vault密码' + result[1])
            return (False, '无法加密vault密码' + result[1])            
        cipher_vpwd = result[1]

        insert_data = {
            'username' : username,
            'name' : user_mess_dict['name'],
            'contact' : user_mess_dict['contact'],
            'password': cipher_lpwd,
            'vault_password': cipher_vpwd,
            'isalive': True,
            'create_time': time.time(),
            'creater' : user_mess_dict['creater'],
            }

        insert_dict = {
            'collect' : self.userinfo_mongocollect,
            'data' : insert_data
            }
        
        result = self.mongoclient.insert(insert_dict, addtime=True)
        self.redisclient.delete(self.userinfo_rediskey)        
        if not result[0] :
            self.logger.error('创建用户' + username + '失败，原因：' + result[1])
        else :
            self.logger.info('创建用户' + username + '成功')
        return result


    def detail(self, username):
        
        '''
        查看用户详细信息
        '''
        
        old_user_dict = self.get_userinfo(username=username)
        if not old_user_dict :
            self.logger.error('查看用户' + username + '详细信息失败，原因：用户不存在')
            return (False, '用户' + username + '不存在')
        
        result = self.mongoclient.find(self.userinfo_mongocollect, condition_dict={'username':username})
        if not result[0] :
            self.logger.error('查看用户' + username + '详细信息失败，原因：' + str(result[1]))
            return (False, '查询用户失败，' + str(result[1]))
        
        detail_mess = result[1][0]
        if detail_mess['isalive'] :
            isalive = '是'
        else :
            isalive = '否'
        
        if 'create_time' in detail_mess:
            create_date = timestamp2datetime(detail_mess['create_time'])
        else:
            create_date = timestamp2datetime(detail_mess['add_time'])
        
        if 'lastlogin_time' in detail_mess :
            lastlogin_time = timestamp2datetime(detail_mess['lastlogin_time'])
        else :
            lastlogin_time = '-'
        
        if 'lastedit_time' in detail_mess :
            lastedit_time = timestamp2datetime(detail_mess['lastedit_time'])
        else :
            lastedit_time = '-'

        if 'creater' in detail_mess :
            creater = detail_mess['creater']
        else :
            creater = '-'
        
        if 'lastediter' in detail_mess :
            lastediter = detail_mess['lastediter']
        else :
            lastediter = '-'
        
        detail_dict = {
            '真实姓名' : detail_mess['name'],
            '联系方式' : detail_mess['contact'],
            '是否激活' : isalive,
            '创建者' : creater,
            '创建时间' : create_date,
            '上次登录时间' : lastlogin_time,
            '上次编辑用户' : lastediter,
            '上次编辑时间' : lastedit_time,
            '是否激活' : isalive,
            }

        self.logger.info('查看用户' + username + '详细信息成功')
        return (True, detail_dict)

