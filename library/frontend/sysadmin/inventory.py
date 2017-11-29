import time

from library.frontend import Base
from library.utils.file import write_file
from library.utils.type_conv import random_str


class Manager_Inventory(Base):
    def get_init_para(self, username):
        self.inve_mongocollect = 'user.' + username + '.inventory'
        self.group_mongocollect = 'user.' + username + '.inventory.group'
        self.inve_rediskey = 'lykops:' + username + ':inventory'
        self.group_rediskey = 'lykops:' + username + ':inventory:group'
        self.invetemp_rediskey = 'lykops:' + username + ':inventory:temp'
        self.host_ansible_list = ['ssh_host', 'ssh_port', 'ssh_user', 'ssh_pass', 'sudo_pass', 'sudo_exec', 'ssh_private_key_file', 'shell_type', 'connection', 'python_interpreter']
        self.host_vault_list = ['ssh_pass', 'sudo_pass', 'ssh_private_key_file']
        self.reqfield_list = ['name', 'ssh_host']
        self.host_name_dict = {
            'name' : '主 机 名 称',
            'ssh_host':'主 机 地 址',
            'os' : 'O S&nbsp;&nbsp;&nbsp;类 型',
            'os_ver' : 'O S&nbsp;&nbsp;&nbsp;版 本',
            'group' : '主&nbsp;&nbsp;&nbsp;机&nbsp;&nbsp;&nbsp;组',
            'ssh_port':'S S H 端口',
            'ssh_user':'S S H 账号',
            'ssh_pass':'S S H 密码',
            'sudo_pass':'sudo&nbsp;密&nbsp;码',
            'sudo_exec':'sudo&nbsp;路&nbsp;径',
            'ssh_private_key_file':'SSH&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;key',
            'shell_type':'shell 类 型',
            'connection':'连 接 方 式',
            'python_interpreter':'python命令路径'
            }


    def init_para(self, username):    
        self.get_init_para(username)
        self.group_list = self.get_grouplist(username, force=False)
        self.host_default_dict = {
            'ssh_port':'22',
            'ssh_user':'root',
            'sudo_exec':'/usr/bin/sudo',
            'group':self.group_list,
            'shell_type':'shell',
            'connection':'ssh',
            'connection' : ['', 'paramiko', 'ssh', 'local'],
            'os' : ['CentOS', 'Ubuntu', 'Fedora', 'Windows'],
            'python_interpreter':'/usr/bin/python'
            }
        
        for key in self.host_name_dict:
            if key not in self.host_default_dict :
                self.host_default_dict[key] = ''
        
        post_key_list = list(self.host_name_dict.keys())
        post_key_list.append('group_add')
        return post_key_list
    
        
    def add_get(self, username):
        self.init_para(username)
        html_code = ''
        for key, value in self.host_name_dict.items():
            default_value = self.host_default_dict[key]
            if isinstance(default_value, (list, tuple)) :
                if key != 'group' :
                    option_html = '<select id="' + key + '" name="' + key + '">\n</br>'
                    for k in default_value :
                        option_html = option_html + '<option id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                    option_html = option_html + '</select>\n</br>\n</br>'
                else :
                    option_html = '<input type="text" name="group_add" class="" placeholder="">\n'
                    option_html = option_html + '<select multiple id="' + key + '" name="' + key + '">\n</br>'
                    for k in default_value :
                        option_html = option_html + '<option id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                    option_html = option_html + '</select>\n</br>\n</br>'
                
            if not isinstance(default_value, (list, tuple)) :
                if key in self.reqfield_list :
                    html_code = html_code + value + '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="text" name="' + key + '" class="" placeholder="' + default_value + '" required="length[2~16]">\n</br>\n</br>\n'
                else :
                    html_code = html_code + value + '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="text" name="' + key + '" class="" placeholder="' + default_value + '">\n</br>\n</br>\n'
            else :
                html_code = html_code + value + '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + option_html
        
        return html_code
                
                
    def add_post(self, username, vault_password , data):
        self.init_para(username)
        
        if not isinstance(data, dict) :
            self.logger.error('用户' + username + '新增主机时发生错误，原因：提供的数据错误')
            return (False, '提供的数据错误')

        for key in self.reqfield_list :
            if not data[key] or data[key] == '':
                self.logger.error('用户' + username + '新增主机时发生错误，原因：部分必填字段没有填写')
                return (False, '部分必填字段没有填写')

        result = self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=True, mongoshare=False)
        if result[0] :
            all_data = result[1]
            for hostdict in all_data :
                try :
                    if hostdict['name'] == data['name'] :
                        self.logger.error('用户' + username + '新增主机时发生错误，原因：主机名重复')
                        return (False, '主机名重复')
                    
                    if hostdict['ssh_host'] == data['ssh_host'] :
                        self.logger.error('用户' + username + '新增主机时发生错误，原因：主机地址重复')
                        return (False, '主机地址重复')
                except :
                    pass

        result = self.encryp_dict(username, vault_password, data, self.host_vault_list)
        if result[0] :
            save_dict = result[1]
        else :
            self.logger.error('用户' + username + '新增主机时发生错误，原因：' + result[1])
            return result

        update_dict = {
            'collect' : self.inve_mongocollect,
            'data' : save_dict
            }
        result = self.mongoclient.insert(update_dict, addtime=True)
        self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=True, mongoshare=False)
        self.redisclient.delete(self.group_rediskey)
        if result[0] :
            self.logger.info('用户' + username + '新增主机' + data['name'] + '成功')
        else :
            self.logger.error('用户' + username + '新增主机' + data['name'] + '时发生错误，原因：' + result[1])
        return result


    def summary(self, username):
        self.init_para(username)
        result = self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=False, mongoshare=False)
        if result[0] :
            title_list = []
            display_list = ('name', 'ssh_host', 'os', 'os_ver')
            for key in display_list :
                name = self.host_name_dict[key]
                name = name.replace(' ', '')
                name = name.replace('&nbsp;', '')
                title_list.append(name)
            
            allhost_data = result[1]
            query_list = [] 
            for host_dict in allhost_data :
                host_data = []
                for key in display_list :
                    try :
                        value = host_dict[key]
                    except :
                        value = '-'
                    host_data.append(value)
                    
                query_list.append(host_data)
        
        return (True, title_list, query_list)
        

    def detail(self, username, vault_password, name):
        result = self.get_host_data(username, vault_password, name)
        if result[0] :
            host_dict = result[1]
        else :
            return result
             
        grouplist = host_dict['group']
        group_str = ''
        for group in grouplist :
            if group_str :
                group_str = group_str + '\n</br>\n' + group
            else :
                group_str = group
            
        host_dict['group'] = group_str

        host_data = {}
        for key, hz in self.host_name_dict.items() :
            hz = hz.replace(' ', '')
            hz = hz.replace('&nbsp;', '')
            if key in host_dict :
                host_data[hz] = host_dict[key]
                    
        return (True, host_data)
        
 
    def get_host_data(self, username, vault_password, name):
        self.init_para(username)
        result = self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=False, mongoshare=False)
        if result[0] :
            allhost_data = result[1]
            for data in allhost_data :
                try :
                    if data['name'] == name :
                        result = self.decryp_dict(username, vault_password, data, self.host_vault_list)
                        if not result[0] :
                            return result
                        
                        host_data = result[1]
                        try :
                            del host_data['add_time']
                        except :
                            pass
                        
                        return (True, host_data)
                except :
                    pass
        
        self.logger.error('用户' + username + '获取主机' + name + '时发生错误，原因：' + str(result[1]))
        return (False, '数据库中没有该记录')
    
 
    def edit_get(self, username, vault_password, name):
        result = self.get_host_data(username, vault_password, name)
        if result[0] :
            host_data = result[1]
        else :
            return result
              
        html_code = ''  
        for key in self.host_name_dict:
            name = self.host_name_dict[key]
            value = self.host_default_dict[key]
            if key in host_data :
                old_value = host_data[key]
                if isinstance(old_value, (list, tuple)):
                    old_value = list(set(old_value))
            else :
                old_value = ''
            
            if isinstance(value, (list, tuple)) :
                if key == 'group' :
                    group_list = []
                    for group in old_value :
                        if group and group != 'all' :
                            group_list.append(group)
                    # old_value = ['all'] + group_list
                    old_value = group_list
                    
                    option_html = '<input type="text" name="group_add" class="" placeholder="">\n'
                    option_html = option_html + '<select multiple id="' + key + '" name="' + key + '">\n</br>'
                    if key in host_data :
                        for k in value :
                            if k in old_value :
                                option_html = option_html + '<option selected="selected" id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                            else :
                                option_html = option_html + '<option id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                    else :
                        for k in value :
                            option_html = option_html + '<option id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                    option_html = option_html + '</select>\n</br>\n</br>'
                else :
                    option_html = '<select id="' + key + '" name="' + key + '">\n</br>'
                    if key in host_data :
                        for k in value :
                            if k == old_value :
                                option_html = option_html + '<option selected="selected" id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                            else :
                                option_html = option_html + '<option id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                    else :
                        for k in value :
                            option_html = option_html + '<option id="' + k + '" value="' + k + '">' + k + '</option>\n</br>'
                    option_html = option_html + '</select>\n</br>\n</br>'
            
            if not isinstance(value, (list, tuple)) :  
                html_code = html_code + name + '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="text" name="' + str(key) + '" class="" value="' + str(old_value) + '">\n</br>\n</br>\n'
            else :
                html_code = html_code + name + '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + option_html

        return html_code
      

    def edit_post(self, username, old_name, vault_password, data):
        if not isinstance(data, dict) :
            self.logger.error('用户' + username + '修改主机时发生错误，提供的数据错误')
            return (False, '提供的数据错误')

        if not data :
            self.logger.info('用户' + username + '修改主机时无需更新，数据保存不变')
            return (False, '数据保存不变，无需更新')

        result = self.get_host_data(username, vault_password, old_name)
        if result[0] :
            old_data = result[1]
        else :
            return result
        
        for key in self.reqfield_list :
            if not data[key] or data[key] == '':
                return (False, '部分必填字段没有填写')
        
        try :
            old_host = old_data['ssh_host']
            new_name = data['name']
            new_host = data['ssh_host']
        except :
            self.logger.error('用户' + username + '修改主机时发生错误，部分必填字段没有填写')
            return (False, '部分必填字段没有填写')

        result = self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=True, mongoshare=False)
        if result[0] :
            all_data = result[1]
            for hostdict in all_data :
                try :
                    if hostdict['name'] == new_name and new_name != old_name:
                        self.logger.error('用户' + username + '修改主机' + new_name + '时发生错误，主机名重复')
                        return (False, '主机名重复')
                    
                    if hostdict['ssh_host'] == new_host and new_host != old_host:
                        self.logger.error('用户' + username + '修改主机' + new_name + '时发生错误，主机地址重复')
                        return (False, '主机地址重复')
                except :
                    pass

        result = self.encryp_dict(username, vault_password, data, self.host_vault_list)
        if result[0] :
            save_dict = result[1]
        else :
            return result

        update_dict = {
            'collect' : self.inve_mongocollect,
            'data' : save_dict
            }

        if old_host == data['ssh_host'] :
            result = self.mongoclient.update({'ssh_host':old_host}, update_dict, addtime=True)
        else :
            if old_name == data['name'] :
                result = self.mongoclient.update({'name':old_name}, update_dict, addtime=True)
            else :
                result = self.mongoclient.remove(self.inve_mongocollect, {'name':old_name, 'ssh_host':old_host})
                if not result[0] :
                    self.logger.error('用户' + username + '修改主机' + new_name + '时发生错误，原因：' + result[1])
                    return result
                
                result = self.mongoclient.insert(update_dict, addtime=True)
                
        self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=True, mongoshare=False)
        self.redisclient.delete(self.group_rediskey)
        if not result[0] :
            self.logger.error('用户' + username + '修改主机' + new_name + '时发生错误，原因：' + result[1])
        else :
            self.logger.info('用户' + username + '修改主机' + new_name + '成功')
        return result


    def delete(self, username, name):
        self.init_para(username)
        result = self.mongoclient.remove(self.inve_mongocollect, {'name':name})
        if result[0] :
            self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=True, mongoshare=False)
            self.logger.info('用户' + username + '删除主机' + name + '成功')
            return (True, '删除成功')
        else :
            self.logger.error('用户' + username + '删除主机' + name + '失败，原因：' + result[1])
            return (False, '删除失败')


    def save_vault(self, username):
        
        '''
        把privacy数据（明文）加密后写入mongo中
        :parm
            username：用户名
            data：加密前的privacy数据字典
            vault_password：vault密码
        '''
        
        self.init_para(username)
        result = self.redisclient.get(self.invetemp_rediskey, fmt='obj')
        if not result[0] :
            if not self.redisclient.haskey(self.temp_rediskey):
                self.logger.error('用户' + username + '为主机修改vault密码后写入数据库失败，原因：' + result[1])
                return (True, '没有数据')
            
            self.logger.error('用户' + username + '为主机修改vault密码后写入数据库失败，读取缓存失败，原因：' + result[1])
            return (False, '读取缓存失败' + result[1])
        
        data = result[1]
        new_collect = self.inve_mongocollect + '_chvltpwd_bk' + str(time.time())
        result = self.mongoclient.rename_collect(self.inve_mongocollect, new_collect)
        if not result[0] :
            self.logger.error('用户' + username + '为主机修改vault密码后写入数据库失败，删除旧数据失败，原因：' + result[1])
            return (False, '删除旧数据失败' + result[1])
        
        for host_data in data :
            insert_dict = {
                'collect' : self.inve_mongocollect,
                'data' : host_data
                }
            result = self.mongoclient.insert(insert_dict)
            if not result[0] :
                self.mongoclient.drop_collect(self.inve_mongocollect)
                self.mongoclient.rename_collect(new_collect, self.inve_mongocollect)
                self.logger.error('用户' + username + '为主机修改vault密码后写入数据库失败，写入新数据失败，原因：' + result[1])
                return (False, '写入新数据失败' + result[1])
            else :
                self.mongoclient.drop_collect(new_collect)

        self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=True, mongoshare=False)
        self.logger.info('用户' + username + '为主机修改vault密码后写入数据库成功')
        return (True, '')


    def change_vault_password(self, username, old_pwd, new_pwd):

        '''
        修改用户的vault密码，对机密数据进行更换密码
        :parm
            username：用户名
            old_pwd：旧vault密码
            new_pwd：新vault密码
        '''
        
        self.init_para(username)
        result = self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=True, mongoshare=False)
        new_data = []
        if result[0] :
            allhost_data = result[1]
            for data in allhost_data :
                result = self.change_vltpwd_dict(username, old_pwd, new_pwd, data, self.host_vault_list)
                if not result[0] :
                    return result
                        
                new_data.append(result[1])
                 
        if new_data : 
            result = self.write_cache(self.invetemp_rediskey, new_data, expire=60 * 5)
            if result[0] :
                self.logger.info('用户' + username + '为主机修改vault密码成功，并写缓存成功')
                return (True, '写缓存成功')
            else :
                self.logger.error('用户' + username + '为主机修改vault密码成功，写缓存失败，原因：' + result[1])
                return (False, '写缓存失败' + result[1])
        else :
            self.logger.info('用户' + username + '为主机修改vault密码成功')
            return (True, '')


    def get_grouplist(self, username, force=False):
        self.get_init_para(username)
        
        if force :
            self.redisclient.delete(self.group_rediskey)
        else :
            result = self.redisclient.get(self.group_rediskey, fmt='str')
            if result[0] :
                if isinstance(result[1], (list, tuple)) :
                    return result[1]
        
        group_list = []
        result = self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=force, mongoshare=False)
        if result[0] :
            inve_data = result[1]
        else :
            return ['all']
            
        for host_dict in inve_data :
            try :
                group_list = group_list + host_dict['group']
            except :
                pass

        group_list = list(set(group_list))
        new_group_list = []
        for group in group_list :
            if group and group != 'all' :
                new_group_list.append(group)

        # new_group_list = ['all'] + new_group_list 
        
        set_dict = {
            'name' : self.group_rediskey,
            'value' : new_group_list,
            'ex':self.expiretime
            }
        self.redisclient.set(set_dict, fmt='str')
            
        return new_group_list


    def write_file(self, username, vault_password, group_list=[]):
        self.init_para(username)
        result = self.get_data(username, self.inve_rediskey, self.inve_mongocollect, force=False, mongoshare=False)
        
        if not group_list or not (isinstance(group_list, (list, tuple)) or group_list == 'all') or 'all' in group_list:
            group_list = self.group_list
        
        used_hosts_list = []
        group_dict = {}
        
        if result[0] :
            allhost_data = result[1]
            
            for data in allhost_data :
                result = self.decryp_dict(username, vault_password, data, self.host_vault_list)
                if not result[0] :
                    return result
                    
                data = result[1]
                group = data.get('group', [])

                try :
                    for g in group :
                        if g in group_list :
                            name = data.get('name', '')
                            
                            if g not in group_dict :
                                if g != 'all' :
                                    group_dict[g] = []
                            
                            if name not in used_hosts_list :
                                ansible_ssh_host = data['ssh_host']
                                ansible_ssh_port = data.get('ssh_port', '')
                                ansible_ssh_user = data.get('ssh_user', '')
                                ansible_ssh_pass = data.get('ssh_pass', '')
                                ansible_sudo_pass = data.get('sudo_pass', '')
                                ansible_sudo_exec = data.get('sudo_exec', '')
                                ansible_ssh_private_key_file = data.get('ssh_private_key_file', '')
                                ansible_shell_type = data.get('shell_type', '')
                                ansible_connection = data.get('connection', '')
                                ansible_python_interpreter = data.get('python_interpreter', '')
                                
                                host_str = str(name) + ' ansible_ssh_host=' + str(ansible_ssh_host)
                                protect_str = str(name) + ' ansible_ssh_host=' + str(ansible_ssh_host)
                                if ansible_ssh_port :
                                    host_str = host_str + ' ansible_ssh_port=' + str(ansible_ssh_port)
                                    protect_str = protect_str + ' ansible_ssh_port=' + str(ansible_ssh_port)
                                    
                                if ansible_ssh_user :
                                    host_str = host_str + ' ansible_ssh_user=' + str(ansible_ssh_user)
                                    protect_str = protect_str + ' ansible_ssh_user=' + str(ansible_ssh_user)
                                    
                                if ansible_ssh_pass :
                                    host_str = host_str + ' ansible_ssh_pass=' + str(ansible_ssh_pass)
                                    protect_str = protect_str + ' ansible_ssh_pass=' + '***hidden***'

                                if ansible_sudo_pass :
                                    host_str = host_str + ' ansible_sudo_pass=' + str(ansible_sudo_pass)
                                    protect_str = protect_str + ' ansible_sudo_pass=' + '***hidden***'
                                    
                                if ansible_sudo_exec :
                                    host_str = host_str + ' ansible_sudo_exec=' + str(ansible_sudo_exec)
                                    protect_str = protect_str + ' ansible_sudo_exec=' + str(ansible_sudo_exec)
                                    
                                if ansible_ssh_private_key_file :
                                    host_str = host_str + ' ansible_ssh_private_key_file=' + str(ansible_ssh_private_key_file)
                                    protect_str = protect_str + ' ansible_ssh_private_key_file=' + '***hidden***'
                                    
                                if ansible_shell_type :
                                    host_str = host_str + ' ansible_shell_type=' + str(ansible_shell_type)
                                    protect_str = protect_str + ' ansible_shell_type=' + str(ansible_shell_type)
                                    
                                if ansible_connection :
                                    host_str = host_str + ' ansible_connection=' + str(ansible_connection)
                                    protect_str = protect_str + ' ansible_connection=' + str(ansible_connection)
                                    
                                if ansible_python_interpreter :
                                    host_str = host_str + ' ansible_python_interpreter=' + str(ansible_python_interpreter)
                                    protect_str = protect_str + ' ansible_python_interpreter=' + str(ansible_python_interpreter)
                                                   
                                group_dict[g].append((host_str, protect_str))
                                used_hosts_list.append(name)
                except :
                    pass
            
        content_str = ''
        protect_content_str = ''
        for group in group_dict :
            content_list = group_dict[group]
            if content_str :
                content_str = content_str + '\n[' + group + ']'
                protect_content_str = protect_content_str + '\n[' + group + ']'
            else :
                content_str = '[' + group + ']'
                protect_content_str = '[' + group + ']'
                
            for content in content_list :
                host_str = content[0]
                protect_str = content[1]
                content_str = content_str + '\n' + host_str
                protect_content_str = protect_content_str + '\n' + protect_str
                
            content_str = content_str + '\n'
            protect_content_str = protect_content_str + '\n'
            
        inve_file = '/dev/shm/lykops/ansible/inventory_' + random_str()
        result = write_file(inve_file , 'w' , content_str)
        if result[0] :
            self.logger.info('将用户' + username + '主机按照ansible的hosts.conf格式写入临时文件成功')
            return (True, inve_file, protect_content_str)
        else :
            self.logger.info('将用户' + username + '主机按照ansible的hosts.conf格式写入临时文件失败，原因：' + result[1])
            return result

