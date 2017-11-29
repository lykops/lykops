import logging, os, sys, re, time, uuid

from library.config.security import vault_header
from library.connecter.database.mongo import Op_Mongo
from library.security.encryption.AES256.api import Using_AES256
from library.utils.file import check_fileaccessible, read_file, path_isexists, write_file
from library.utils.match_string import contain_zh, contain_spec_symbol, contain_only_letter_number
from library.utils.type_conv import random_str
from library.utils.yaml import yaml_loader 


class Yaml_Base():
    def __init__(self, username, vault_passwd=None, mongoclient=None):
        
        self.logger = logging.getLogger("ansible")
        self.yaml_mongocollect = username + '.ansible.yaml'
        self.temp_basedir = '/dev/shm/lykops/ansible/yaml/'
        self.username = username
        self.vault_passwd = vault_passwd
        
        if mongoclient is None :
            self.mongoclient = Op_Mongo()
            self.logger.warn('无法继承，需要初始化mongodb连接')
        else :
            self.mongoclient = mongoclient
        
        if vault_passwd is None or not vault_passwd :
            self.this_cipher = None
            # self.logger.warn('没有提供vault密码，不加载加解密模块')
        else :
            self.logger.warn('提供vault密码，加载加解密模块')
            self.this_cipher = Using_AES256(vault_passwd, vault_header)
        
        self.vault_header = vault_header
    
    
    def check_main(self, yaml_data):
        includefile_dict = {}
        roles_list = []
        log_prefix = '校验类型为main或者是full_roles的ansible yaml语法规则，'
        
        for data in yaml_data :
            if not isinstance(data, dict) :
                self.logger.error(log_prefix + '未通过语法检测，原因：可能不是ansible格式的yaml文件')
                return (False, '可能不是ansible格式的yaml文件')
            
            key_list = data.keys()
            # if not ('hosts' in key_list and ('tasks' in key_list or 'roles' in key_list)) and 'include' not in key_list:
            if not ('hosts' in key_list and ('tasks' in key_list or 'roles' in key_list)):
                self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：缺少hosts、tasks或者roles等必要的字段')
                return (False, '未通过ansible原生语法检测，缺少hosts、tasks或者roles等必要的字段')
            
            for key, value in data.items() :
                if key == 'include' :
                    self.logger.error(log_prefix + '未通过本系统特定语法检测，原因：本系统禁止在入口文件中含有"- include:"字段。注：虽然原生ansible支持这样写')
                    return (False, '未通过本系统特定的语法检测，本系统禁止在入口文件中含有"- include:"字段')
                        
                if key == 'tasks' :
                    if not isinstance(value, (list, tuple)) :
                        self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：tasks部分为空。')
                        return (False, '未通过ansible原生语法检测，tasks部分为空。')
                    
                    for v in value :
                        if not isinstance(v, dict) :
                            self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：tasks部分异常。')
                            return (False, '未通过ansible原生语法检测，tasks部分异常。')
                        
                        for name , task in v.items() :
                            if name == 'include' :
                                result = self._isinclude(task)
                                if not result[0] :
                                    return result
                                    
                                includefile_dict[task] = 'tasks'
                                
                                '''
                                for file in task :
                                    result = self._isinclude(file)
                                    if not result[0] :
                                        return result
                                    
                                    includefile_dict[file] = 'tasks'
                                '''
                                    
                if key == 'roles' :
                    if not isinstance(value, (list, tuple)) :
                        self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：roles部分为空。')
                        return (False, '未通过ansible原生语法检测，roles部分为空。')
                    
                    for v in value :
                        if not isinstance(v, dict) :
                            self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：roles部分异常。')
                            return (False, '未通过ansible原生语法检测，roles部分异常。')
                        
                        kv = list(v.keys())
                        if not (len(kv) == 1 and 'role' in kv) :
                            self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：roles部分缺少role。')
                            return (False, '未通过ansible原生语法检测，roles部分缺少role。')
                        
                        try :
                            roles_name = v['role']
                            if not self._isrolesname(roles_name):
                                self.logger.error(log_prefix + '未通过本系统特定语法检测，原因：roles名不符合本系统要求的，本系统要求roles只能是大小写、数字以及:。注：虽然原生ansible支持这样写。')
                                return (False, '未通过本系统特定语法检测，roles名不符合本系统要求的，本系统要求roles只能是大小写、数字以及:。')
                            
                            roles_list.append(roles_name)
                        except :
                            self.logger.error(log_prefix + '未通过语法检测，原因：roles部分异常。')
                            return (False, '未通过语法检测，roles部分异常。')
        
        self.logger.info(log_prefix + '通过语法检测')
        return (True, roles_list, includefile_dict)
        
            
    def check_include(self, yaml_data, file_type='main'):
        log_prefix = '校验类型为include的ansible yaml语法规则，'
        if file_type == 'main' :
            self.logger.error(log_prefix + '未通过本系统特定语法检测，原因：本系统禁止在入口文件中含有"- include:"字段。注：虽然原生ansible支持这样写。')
            return (False, '未通过本系统特定语法检测，本系统禁止在入口文件中含有"- include:"字段')
        
        if file_type == 'var' :
            if not isinstance(yaml_data, dict) :
                self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：变量文件格式必须是键值对')
                return (False, '未通过ansible原生语法检测，变量文件格式必须是键值对')
            else :
                self.logger.info(log_prefix + '通过语法检测')
                return (True, '')
        
        for data in yaml_data :
            if not isinstance(data, dict) :
                self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：语法错误')
                return (False, '未通过ansible原生语法检测，语法错误')
            
            if file_type != 'main' :
                deny_list = ('hosts', 'tasks', 'roles')
                key_list = data.keys()
                for deny in deny_list :
                    if deny in key_list :
                        self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：含有非法字段' + deny)
                        return (False, '未通过ansible原生语法检测，含有非法字段' + deny)

            for key in data :
                if key == 'include' :
                    self.logger.error(log_prefix + '未通过本系统特定语法检测，原因：本系统不允许嵌套使用include。注：虽然原生ansible支持这样写。')
                    return (False, '未通过本系统特定语法检测，本系统不允许嵌套使用include')

        self.logger.info(log_prefix + '通过语法检测')
        return (True, '')
           
           
    def check_roles(self, content_dict):
        
        '''
        检测roles语法是否正确
        '''

        log_prefix = '校验类型为roles的ansible yaml语法规则，'
        if 'tasks' not in content_dict :
            self.logger.error(log_prefix + '未通过ansible原生语法检测，原因：tasks/main.yaml不存在')
            return (False, '未通过ansible原生语法检测，tasks/main.yaml不存在')

        include_dict = {}
        for this_dir , content in content_dict.items() :

            result = self.yaml_loader(content, data_type='data')
            if result[0] :
                yaml_data = result[-1]
            else :
                self.logger.error(log_prefix + this_dir + '/main.yaml转化成yaml数据时失败，原因：' + result[1])
                return (False, this_dir + '/main.yaml转化成yaml数据时失败，' + result[1])
            
            result = self.check_roles_singlefile(yaml_data, this_dir)
            if result[0] :
                include_dict.update(result[1])
            else :
                self.logger.error(log_prefix + this_dir + '/main.yaml未通过语法检测，原因：' + result[1])
                return (False, this_dir + '/main.yaml未通过语法检测，' + result[1])
        
        self.logger.info(log_prefix + '通过语法检测')
        return (True, include_dict)
           
           
    def check_roles_singlefile(self, yaml_data, this_dir):
        
        '''
        解析roles的每个文件
        :parm
            yaml_data：yaml数据
            this_dir：roles下的标准目录名
        '''

        include_dict = {}
        log_prefix = '校验' + this_dir + '/main.yaml语法规则，'
        if this_dir in ('handlers', 'tasks') :
            file_type = 'tasks'
        else :
            file_type = 'var'

        if this_dir == 'templates' :
            self.logger.info(log_prefix + '通过语法检测')
            return (True, include_dict)

        if file_type == 'var' :
            if isinstance(yaml_data, (list, tuple)) :
                return (False, '在role中' + this_dir + '文件不能含有键值对')
            else :
                self.logger.info(log_prefix + '通过语法检测')
                return (True, include_dict)
        
        if not isinstance(yaml_data, (list, tuple)) :
            return (False, '在role中' + this_dir + '文件语法错误')

        for data in yaml_data :
            if not isinstance(data, dict) :
                return (False, '在role中该文件不能含有键值对')

            for key, value in data.items() :
                if key == 'hosts' or key == 'tasks' or key == 'roles' :
                    return (False, '在role中' + this_dir + '/main.yaml文件不能含有' + key + '关键字')
                    
                if key == 'include':
                    if this_dir == 'handlers' :
                        return (False, '在role中' + this_dir + '/main.yaml文件不能含有' + key + '关键字')
                    else :
                        result = self._isinclude(value)
                        if not result[0] :
                            return result
                        
                        include_dict[value] = 'tasks'
        
        self.logger.info(log_prefix + '通过语法检测')
        return (True, include_dict)

                
    def yaml_loader(self, data, data_type='file'):
        
        '''
        将文件或者原始数据解析成yaml数据，如果是vault数据，将在这里解密
        :parm
            data：路径或者原始数据
            data_type：指定类型，文件或者原始数据
        '''
        
        
        if data_type == 'file' :
            log_prefix = '将yaml文件' + data + '的内容（必须为原始数据）解析为yaml格式的数据，'
            result = check_fileaccessible(data)
            if result[0] :
                filename = result[1]
            else :
                self.logger.error(log_prefix + '读取文件时失败，原因：' + result[1])
                return (False, '读取文件时失败，' + result[1])
            
            result = read_file(filename)
            if result[0] :
                content = result[1]
            else :
                self.logger.error(log_prefix + '读取文件时失败，原因：' + result[1])
                return (False, '读取文件时失败，' + result[1])
        else :
            log_prefix = '将原始yaml数据解析为yaml格式的数据，'
            content = data
            filename = ''
            # 是否写入文件中
        
        result = yaml_loader(content, data_type='data')
        if result[0] :
            yaml_data = result[1]
        else :
            self.logger.error(log_prefix + '解析失败，原因：' + result[1])
            return (False, '解析成yaml失败，' + result[1])
        
        if not isinstance(yaml_data, (dict, list, tuple)) :
            self.logger.error(log_prefix + '解析失败，原因：该文件内容不是ansible支持的yaml数据')
            return (False, '解析成yaml失败，该文件内容不是ansible支持的yaml数据')
        
        self.logger.info(log_prefix + '解析成功')
        return (True, filename, content, yaml_data)


    def write2db(self, name, content, yaml_type, describe=''):
    # def write2db(self, this_path, content, yaml_type, describe='', name=''):
        
        '''
        把yaml原始数据写入数据库中
        :parm
            this_path：通用该yaml（方式为roles或者include）的文件中写入的实际路径
            content：yaml文件原始数据（可能是字典，也可能为字符串）
            yaml_type：yaml类型
            name：yaml文件内容写入数据的名称
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        '''
        
        if not isinstance(name, str) :
            self.logger.error('将yaml原始数据写入数据库失败，原因：参数name必须为字符串')
            return (False, '参数name必须为字符串')

        log_prefix = '将名为' + name + '的yaml原始数据写入数据库，'
        result = self.get_name_list()
        if not result[0] :
            return result
        else :
            nametype_dict = result[1]
            if nametype_dict :
                try :
                    if name in nametype_dict[yaml_type] :
                        self.logger.error(log_prefix + '解析失败，原因：名称重复')
                        return (False, '名称重复，请修改名称在保存，谢谢')
                except :
                    pass
        
        insert_data = {
            'name' : name,
            'uuid' : str(uuid.uuid4()),
            # UUID不能作为roles或include名，只能用于查找标识
            'content' : content,
            'type' : yaml_type,
            'describe' :describe,
            'lastedit_ts' : 0
            }
        
        insert_dict = {
            'collect' : self.yaml_mongocollect,
            'data' : insert_data
            }
        
        result = self.mongoclient.insert(insert_dict, addtime=True)
        self.logger.info('将名为' + name + '的yaml原始数据写入数据库成功')
        return result

          
    def edit2db(self, uuid_str, content, describe='', name=''):
        
        '''
        把修改后的yaml原始数据写入数据库中
        :parm
            uuid_str：需要修改的UUID
            content：yaml文件原始数据（可能是字典，也可能为字符串）
            name：yaml文件内容写入数据的名称
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        '''

        log_prefix = '编辑数据库中uuid为' + uuid_str + '的yaml数据，'
        if not isinstance(name, str) :
            self.logger.error('编辑数据库中uuid为' + uuid_str + '的yaml数据失败，原因：参数name必须为字符串')
            return (False, '参数name必须为字符串')
        
        if not re.search('^[a-z|A-Z|0-9]{8}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{12}$', uuid_str) :
            self.logger.error(log_prefix + '参数提供错误，原因：参数uuid不是一个标准的UUID，标准的UUID格式为^[a-z|A-Z|0-9]{8}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{12}$')
            return (False, '参数uuid不是一个标准的UUID，标准的UUID格式为^[a-z|A-Z|0-9]{8}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{12}$')
        
        update_data = {'content' : content}
        
        result = self.read2db(uuid_str, word_field='uuid')
        if result[0] : 
            try :
                yaml_type = result[1]['type']
                old_name = result[1]['name']
            except :
                return (False, '从数据库读取时出错')
        else :
            return result
        
        if name and old_name != name :
            result = self.get_name_list()
            if not result[0] :
                return result
            else :
                nametype_dict = result[1]
                if nametype_dict :
                    if name in nametype_dict[yaml_type] :
                        self.logger.error(log_prefix + '解析失败，原因：名称重复')
                        return (False, '名称重复，请修改名称在保存，谢谢')
            update_data['name'] = name
            
        if describe and isinstance(describe, str):
            update_data['describe'] = describe

        update_data['lastedit_ts'] = time.time()
        update_dict = {
            'collect' : self.yaml_mongocollect,
            'data' : {"$set": update_data}
            }
        
        result = self.mongoclient.update({'uuid':uuid_str}, update_dict, addtime=False)
        self.logger.info(log_prefix + '写入数据库成功')
        return result
    
            
    def _write2file(self, content, filename):
        
        '''
        写入文件，如果处理加密数据等，应该放在这里
        :parm
            content：写入的内容
            filename：指定文件名
        '''
        
        if not isinstance(content, str) :
            self.logger.error('将yaml原始数据写入文件' + filename + '失败，原因：参数错误，content必须为字符串')
            return (False, '参数错误，content必须为字符串')
                
        result = write_file(filename , 'w' , content, force=True)
        if result[0] :
            self.logger.error('将yaml原始数据写入文件' + filename + '成功')
            return (True, filename)
        else :
            self.logger.error('将yaml原始数据写入文件' + filename + '失败，原因：' + result[1])
            return (False, '写入文件失败，' + result[1])


    def _isrolesname(self, roles_name):
        
        '''
        判断传入字符串是否符合本系统要求的roles名
        :param 
            word: 待判断字符串
        :return: 
            True:包含 
            False:不包含
        '''
        
        word_list = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789:'
    
        if not isinstance(roles_name, str) :
            return False
        
        for s in roles_name :
            if s not in word_list :
                return False
    
        return True


    def _isinclude(self,filename):
        
        '''
        判断传入字符串是否符合本系统要求的include
        :param 
            word: 待判断字符串
        :return: 
            True:包含 
            False:不包含
        '''
        
        if re.search('^/', filename) :
            self.logger.error('检测include文件名是否符合本系统要求，' + filename + '不符合，原因：include文件不能为绝对路径')
            return (False, 'include文件不能为绝对路径') 
                                    
        if re.search('^main\.', os.path.basename(filename)) :
            self.logger.error('检测include文件名是否符合本系统要求，' + filename + '不符合，原因：include文件名不能含有"main."字符')
            return (False, 'include文件名不能含有"main."字符')
        
        return (True, '')


    def get_abs(self):
        
        '''
        获取摘要信息
        '''
        
        get_field_list = ['name', 'uuid' , 'type' , 'describe']
        result = self.mongoclient.find(self.yaml_mongocollect, get_field=get_field_list)
        return result
        
        
    def get_name_list(self):
        
        '''
        获取DB中的所有name和yaml_type
        '''
        
        get_field_list = ['name', 'type']
        result = self.mongoclient.find(self.yaml_mongocollect, get_field=get_field_list)
        
        if not result[0] :
            self.logger.error('从数据库中获取所有yaml数据的name和yaml_type时发生错误，原因：' + result[1])
            return (False, '从数据库中获取所有yaml数据的name和yaml_type时发生错误，原因：' + result[1])
        
        name_type_dict = {}
        name_list = result[1]
        for name_dict in name_list :
            name = name_dict['name']
            yaml_type = name_dict['type']
            
            if yaml_type not in name_type_dict :    
                name_type_dict[yaml_type] = []
                name_type_dict[yaml_type].append(name)
            else :
                name_type_dict[yaml_type].append(name)
                    
        return (True, name_type_dict)
        
        
    def read2db(self, word, word_field='name'):
        
        '''
        从数据库读取
        :parm
            word：关键字
            word_field：根据那个字段（name或者UUID）作为关键字查找
        '''
        
        if word is None or not word or not isinstance(word, str) :
            self.logger.error('从数据库通过关键字查找的yaml数据失败，原因：参数word必须为不为空字符串')
            return (False, '参数word必须为不为空字符串')

        if re.search('^[a-z|A-Z|0-9]{8}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{4}-[a-z|A-Z|0-9]{12}$', word) :
            word_field = 'uuid'

        if word_field == 'uuid' :
            result = self.mongoclient.find(self.yaml_mongocollect, condition_dict={word_field:word})
        elif word_field in ('name') :
            result = self.mongoclient.find(self.yaml_mongocollect, limits=1, condition_dict={word_field:word}, sort_dict={'add_time':-1})
        else :
            result = self.mongoclient.find(self.yaml_mongocollect, limits=1, condition_dict={word_field:word}, sort_dict={'add_time':-1})
                
        if not result[0] :
            self.logger.error('从数据库查找关键字类型为' + word_field + ',关键字为' + word + '的yaml数据失败，原因：' + str(result[1]))
            return (False, '查询失败，' + str(result[1]))
        
        try :
            get_dict = result[1][0]
            return (True, get_dict)
        except :
            if not result[1] :
                self.logger.error('从数据库查找关键字类型为' + word_field + ',关键字为' + word + '的yaml数据失败，原因：查询结果为空')
                return (False, '查询结果为空')
            else :
                self.logger.error('从数据库查找关键字类型为' + word_field + ',关键字为' + word + '的yaml数据失败，原因：查询结果数据类型异常')
                return (False, '查询结果数据类型异常')
        

    def data2file(self, content, this_path='', yaml_type='main', name='main'):
        
        '''
        写入临时文件
        :parm
            content：yaml的原始内容
            this_path：写入的目录，如果提供按照指定目录写入，如果不指定随机目录
            yaml_type：yaml类型。main、include、roles、full_roles四种
            name：用于确认include和roles的文件名
        '''
        
        if not this_path or not re.search('^/', this_path):
            this_path = self.temp_basedir + '/' + random_str() + str(int(time.time())) + '/'
        
        def type_roles(content_dict, roles_name):
            
            '''
            专用于类型为roles的数据写入
            '''
            
            for this_dir in content_dict :
                # roles_path = this_path + '/roles/' + os.path.basename(roles_name) + '/' + this_dir
                roles_path = this_path + '/roles/' + roles_name + '/' + this_dir
                
                if this_dir == 'templates'  :
                    for temp_file , temp_content in content_dict[this_dir].items() :
                        filename = roles_path + '/' + temp_file
                        result = self._write2file(temp_content, filename)
                        if not result[0] :
                            self.logger.error('将roles名为' + roles_name + '中的文件名为' + this_dir + '/' + temp_file + 'yaml数据内容写入文件' + filename + '失败，' + result[1])
                            return (False, '将roles名为' + roles_name + '中的文件名为' + this_dir + '/' + temp_file + 'yaml数据内容写入文件' + filename + '失败，' + result[1])
                        else :
                            self.logger.info('将roles名为' + roles_name + '中的文件名为' + this_dir + '/' + temp_file + 'yaml数据内容写入文件' + filename + '成功')
                else :
                    filename = roles_path + '/main.yaml'
                    result = self._write2file(content_dict[this_dir], filename)
                    if not result[0] :
                        self.logger.error('将roles名为' + roles_name + '中的文件名为' + this_dir + '/main.yaml数据内容写入文件' + filename + '失败，' + result[1])
                        return (False, '将roles名为' + roles_name + '中的文件名为' + this_dir + '/main.yaml数据内容写入文件' + filename + '失败，' + result[1])
                    else :
                        self.logger.info('将roles名为' + roles_name + '中的文件名为' + this_dir + '/main.yaml数据内容写入文件' + filename + '成功')
            return (True, this_path)
        
        log_prefix = '将yaml数据内容写入文件'
        if isinstance(content, str) :
            filename = this_path + name + '.yaml'
            result = self._write2file(content, filename)
            return result
        
        if not isinstance(content, dict) :
            self.logger.error(log_prefix + '失败，原因：数据写入数据库时出现错误')
            return (False, '数据写入数据库时出现错误')
        
        if yaml_type == 'roles' :
            result = type_roles(content, name)
        else :
            try :
                roles_dict = content['roles']
                for roles_name in roles_dict :
                    roles_content_dict = roles_dict[roles_name]
                    result = type_roles(roles_content_dict, roles_name)
            except Exception as e :
                print(e)
                roles_dict = {}
                
            try :
                include_dict = content['include']
                for incluce_file , incluce_content in include_dict.items() :
                    filename = this_path + '/' + incluce_file
                    result = self._write2file(incluce_content, filename)
                    if not result[0] :
                        self.logger.error(log_prefix + '失败，路径为' + filename + '，原因：' + str(result[1]))
                        return (False, log_prefix + '失败，路径为' + filename + '，' + str(result[1]))
            except Exception as e :
                print(e)
                include_dict = {}
    
            try :
                main_content = content['main']
                filename = this_path + '/main.yaml'
                result = self._write2file(main_content, filename)
                if not result[0] :
                    self.logger.error(log_prefix + '失败，路径为' + filename + '，原因：' + str(result[1]))
                    return (False, log_prefix + '失败，路径为' + filename + '，原因：' + str(result[1]))
            except Exception as e :
                print(e)
                main_content = ''
            
        self.logger.info(log_prefix + '成功，路径为' + this_path)
        return (True, this_path)
