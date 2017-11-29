from library.config.ansible import option_dict
from library.frontend import Base

class Manager_Option(Base):
    def init_parm(self, username):
        self.ansi_option_mongocollect = 'ansible.option'
        self.ansi_option_rediskey = 'lykops:' + username + ':ansible:option'
        self.temp_rediskey = self.ansi_option_rediskey + ':temp'
        self.vault_list = ['ask_pass', 'ask_su_pass', 'ask_sudo_pass', 'ask_vault_pass', 'become_ask_pass', 'private_key_file', 'new_vault_password', 'new_vault_password_file']
        field_list = option_dict.keys()
        return field_list
    
    
    def get_default(self, username, field, isall=True, exe_mode=''):
        
        '''
        从self.option_dict获取匹配的key
        :parm
            field：通过filed（即字典中的key，只能为'edit', 'visual', 'run'）查找数据
            isall：是否所有的，如果isall为False时，只列出value[field]中为True，否则全部列出
            exe_mode：执行模式，adhoc或者playbook、空
        '''
        
        if field not in ('edit', 'visual', 'run') :
            field = 'edit'

        if exe_mode not in ('adhoc', 'playbook', '') :
            exe_mode = ''
            
        redis_key = 'lykops:' + username + ':ansible:option:default:' + exe_mode + ':' + field + ':' + str(isall)
        result = self.redisclient.get(redis_key, fmt='obj')
        if result[0] and result[1] :
            return result[1]
        
        new_dict = {}
        for key, value in option_dict.items():
            if exe_mode :
                if exe_mode == value['mode'] or value['mode'] == 'ad_pb' :
                    pass
                else :
                    continue
            else :
                pass
            
            new_value = {
                'name':value['name'], 
                'value':value['default'],
                'mode':value['mode'], 
                'option':value['option']
                }
            
            if not isall :
                if value[field]:
                    new_dict[key] = new_value
            else :
                new_dict[key] = new_value
     
        set_dict = {
            'name' : redis_key,
            'value' : new_dict,
            'ex':self.expiretime
        }
        self.redisclient.set(set_dict, fmt='obj')
                    
        return new_dict
                        
        
    def detail(self, username, vault_password):
        self.init_parm(username)
        default_dict = self.get_default(username, 'edit', isall=False)
        
        result = self.get_data(username, self.ansi_option_rediskey, self.ansi_option_mongocollect, force=False)
        if not result[0] :
            user_dict = {}
        else :
            try :
                user_dict = result[1][0]
            except :
                user_dict = {}

        new_data = []
        for key , value in default_dict.items() :
            mode = value['mode']
            if mode in ('adhoc' , 'playbook') :
                name = value['name'] + '，注：仅适用于' + mode
            else :
                name = value['name']
                
            default_value = value['value']
            default_value = str(default_value)
            
            try :
                user_value = user_dict[key]
                if not user_value :
                    value = default_value
                else :
                    if key in self.vault_list :
                        result = self.decryp_string(username, vault_password, user_value)
                        if result[0] :
                            value = result[1]
                        else :
                            return result
                    else :
                        value = user_value
            except :
                value = default_value

            if value == 'None' or value is None or not value :
                value = ''
            new_data.append([key, value, name])
            
        return (True, new_data)


    def exec_gen(self, username, vault_password, exe_mode):
        if exe_mode not in ('adhoc', 'playbook') :
            return (False, '参数exe_mode只能为adhoc、playbook')
        
        self.init_parm(username)
        default_dict = self.get_default(username, 'run', exe_mode=exe_mode)
        
        result = self.get_data(username, self.ansi_option_rediskey, self.ansi_option_mongocollect, force=False)
        if not result[0] :
            user_dict = {}
        else :
            try :
                user_dict = result[1][0]
            except :
                user_dict = {}
                
        new_dict = {}
        for key , value in default_dict.items() :
            default_value = value['value']
            
            try :
                user_value = user_dict[key]
                if not user_value :
                    value = default_value
                else :
                    if key in self.vault_list :
                        result = self.decryp_string(username, vault_password, user_value)
                        if result[0] :
                            value = result[1]
                        else :
                            self.logger.error('为用户' + username + '生成ansible option时失败，解密过程中时出错，原因：' + result[1])
                            return (False, '解密过程中时出错，原因：' + result[1])
                    else :
                        value = user_value
            except :
                value = default_value

            isdigit = True
            if isinstance(value, str) :
                for t in value :
                    if t not in '0123456789' :
                        isdigit = False
                        
            if isdigit :
                try :
                    value = int(value)
                except :
                    pass

            new_dict[key] = value
            
        return (True, new_dict)


    def edit_get(self, username, vault_password):
        self.init_parm(username)
        default_dict = self.get_default(username, 'edit', isall=False)
        
        result = self.get_data(username, self.ansi_option_rediskey, self.ansi_option_mongocollect, force=False, mongoshare=True)
        if not result[0] :
            user_dict = {}
        else :
            try :
                user_dict = result[1][0]
            except :
                user_dict = {}
                
        html_code = '<table class="table table-striped table-bordered table-hover "  id="editable" ></br>\n'  
        html_code = html_code + "<tbody>\n"
        html_code = html_code + "<tr>\n"
        html_code = html_code + "<th>名称</th>\n"
        html_code = html_code + "<td>值</td>\n"
        html_code = html_code + "<td>中文含义</td>\n"
        html_code = html_code + "</tr>\n"
        html_code = html_code + "</tbody>\n"
        html_code = html_code + "<tbody>\n"
        
        for key in default_dict:
            value_dict = default_dict[key]
            if key in user_dict :
                value = user_dict[key]
            else :
                value = value_dict['value']
                
            try :
                result = self.decryp_string(username, vault_password, value)
                if result[0] :
                    value = result[1]
            except :
                pass
    
            if isinstance(value, bool) :
                value = str(value)
    
            option_list = value_dict['option']
            mode = value_dict['mode']
            if mode in ('adhoc' , 'playbook') :
                name = value_dict['name'] + '，注：仅适用于' + mode
            else :
                name = value_dict['name']
                
            if option_list :
                option_html = '<select id="' + key + '" name="' + key + '">\n</br>'
                for k in option_list :
                    k = str(k)
                        
                    if k == value :
                        option_html = option_html + '<option selected="selected" id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                    else :
                        option_html = option_html + '<option id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                    
                option_html = option_html + '</select>\n</br>\n</br>'
                html_code = html_code + "<tr><td>" + key + "</td><td>" + option_html + "</td><td>" + name + "</td></tr>\n"
            else :
                if value is None :
                    html_code = html_code + "<tr><td>" + key + "</td><td>" + '<input type="text" name="' + key + '" class="" value="">\n</br>\n</br>\n' + "</td><td>" + name + "</td></tr>\n"
                else :
                    html_code = html_code + "<tr><td>" + key + "</td><td>" + '<input type="text" name="' + key + '" class="" value="' + str(value) + '">\n</br>\n</br>\n' + "</td><td>" + name + "</td></tr>\n"

        html_code = html_code + "</tbody>\n"
        html_code = html_code + "</table>\n"

        return html_code


    def edit_post(self, username, vault_password, data):
        
        if not isinstance(data, dict) :
            self.logger.error('编辑用户' + username + '的ansible option时失败，原因：提供的数据错误')
            return (False, '提供的数据错误')

        if not data :
            self.logger.error('编辑用户' + username + '的ansible option时失败，原因：数据保存不变，无需更新')
            return (False, '数据保存不变，无需更新')

        result = self.encryp_dict(username, vault_password, data, self.vault_list)
        if result[0] :
            save_dict = result[1]
        else :
            self.logger.error('编辑用户' + username + '的ansible option时失败，加密数据时出错，原因：' + result[1])
            return (False, '加密数据时出错，原因：' + result[1])
        
        save_dict['username'] = username
        update_dict = {
            'collect' : self.ansi_option_mongocollect,
            'data' : save_dict
            }
        result = self.mongoclient.update({'username':username}, update_dict, addtime=True)
        self.get_data(username, self.ansi_option_rediskey, self.ansi_option_mongocollect, force=True)
        
        if not result[1] :
            self.logger.error('编辑用户' + username + '的ansible option失败，写入数据库出错，原因：' + result[1])
            return (False, '加密数据时出错，原因：' + result[1])
        else :
            self.logger.info('编辑用户' + username + '的ansible option成功')
            return (True, '成功')
        
        return result
       

    def change_vault_password(self, username, old_pwd, new_pwd):

        '''
        修改vault密码的预处理，对数据进行更换密码
        :parm
            username：用户名
            old_pwd：旧vault密码
            new_pwd：新vault密码
        '''
        
        self.init_parm(username)
        result = self.mongoclient.find(self.ansi_option_mongocollect, condition_dict={'username' : username})
        if not result[0] :
            self.logger.error('为用户' + username + '更改ansible option的密码失败，读出数据时出错，原因：' + result[1])
            return (False, '读出数据时出错，' + result[1])
        
        try : 
            vault_dict = result[1][0]
        except :
            return (True, {})

        if not isinstance(vault_dict, dict) :
            self.logger.error('为用户' + username + '更改ansible option的密码失败，读出数据时出错，原因：' + result[1])
            return (False, '读出数据时出错' + result[1])

        try :
            del vault_dict['username']
            del vault_dict['add_time']
        except :
            pass
        
        result = self.change_vltpwd_dict(username, old_pwd, new_pwd, vault_dict, self.vault_list)
        if not result[0] :
            self.logger.error('为用户' + username + '更改ansible option的密码失败，原因：' + result[1])
            return result
        
        new_vault_dict = result[1]
        new_vault_dict['username'] = username
        
        result = self.write_cache(self.temp_rediskey, new_vault_dict, expire=60 * 5)
        if result[0] :
            # self.logger.error('为用户' + username + '更改ansible option的密码失败，写入缓存失败,原因：' + result[1])
            return (True, '写缓存成功')
        else :
            self.logger.error('为用户' + username + '更改ansible option的密码失败，写入缓存失败,原因：' + result[1])
            return (False, '写缓存失败' + result[1])
                

    def save_vault(self, username):
        
        '''
        修改vault密码的保存数据
        :parm
            username：用户名
        '''
        
        self.init_parm(username)
        result = self.redisclient.get(self.temp_rediskey, fmt='obj')
        if not result[0] :
            if not self.redisclient.haskey(self.temp_rediskey):
                self.logger.error('为用户' + username + '更改ansible option的密码失败，读取缓存失败,原因：' + result[1])
                return (True, '读取缓存失败,原因：' + result[1])
        
        data = result[1]
        
        if data == {}:
                self.logger.error('为用户' + username + '更改ansible option的密码失败，读取缓存失败,原因：' + result[1])
                return (True, '读取缓存失败,原因：' + result[1])
                    
        update_dict = {
            'collect' : self.ansi_option_mongocollect,
            'data' : data
            }
        result = self.mongoclient.update({'username' : username}, update_dict, addtime=True)
        self.get_data(username, self.ansi_option_rediskey, self.ansi_option_mongocollect, force=True)
        if result[0] :
            # self.logger.error('为用户' + username + '更改ansible option的密码失败，写入缓存失败,原因：' + result[1])
            return (True, '写入数据库成功')
        else :
            self.logger.error('为用户' + username + '更改ansible option的密码失败，写入数据库时出错,原因：' + result[1])
            return (False, '写入数据库时出错，' + result[1])
