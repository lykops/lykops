import os,re

from library.connecter.ansible.yaml.data2db import Data_DB
from library.connecter.ansible.yaml.read2db import Read_DB
from library.connecter.ansible.yaml.read2file import Read_File
from library.frontend import Base
from library.utils.compress import uncompress
from library.utils.dict import value_replace
from library.utils.file import upload_file, get_filetype
from library.utils.type_conv import random_str


class Manager_Yaml(Base):
    def __init__(self, username, vault_passwd=None, mongoclient=None, redisclient=None):
        
        self.read2file_api = Read_File(username, vault_passwd=vault_passwd, mongoclient=mongoclient)
        self.read2db_api = Read_DB(username, vault_passwd=vault_passwd, mongoclient=mongoclient)
        self.data2db_api = Data_DB(username, vault_passwd=vault_passwd, mongoclient=mongoclient)
        self.yaml_rediskey_prefix = 'lykops:' + username + 'ansible:yaml:'
        self.username = username
            
        super(Manager_Yaml, self).__init__(mongoclient=mongoclient, redisclient=redisclient)
    
    
    def add(self, content, name, yaml_tpye='main', file_type='tasks', describe=''):
        result = self.data2db_api.router(content, name, yaml_tpye=yaml_tpye, file_type=file_type, preserve=True, together=True, describe=describe)
        if result[0] :
            self.logger.info('为用户' + self.username + '的名为' + name + '，类型为' + yaml_tpye + '的ansible yaml数据成功')
        else :
            self.logger.error('为用户' + self.username + '的名为' + name + '，类型为' + yaml_tpye + '的ansible yaml数据失败，原因：' + str(result[1]))
        return result
    
    
    def detail(self, uuid_str, isedit=False):
        result = self.read2db_api.read2db(uuid_str, word_field='uuid')        
        if result[0] : 
            try :
                new_dict = result[1]
                content = result[1]['content']
                name = result[1]['name']
            except :
                self.logger.error('查看用户' + self.username + '的uuid为' + uuid_str + '的ansible yaml数据的内容失败，原因：' + str(result[1]))
                return (False, '数据存储错误')
        else :
            self.logger.error('查看用户' + self.username + '的uuid为' + uuid_str + '的ansible yaml数据的内容失败，原因：' + str(result[1]))
            return result
        
        self.logger.info('查看用户' + self.username + '的uuid为' + uuid_str + '的ansible yaml数据的内容成功')
        if not isedit :
            new_content_dict = value_replace(content, replace_dict={'\n': '</br>', ' ':'&nbsp;'})
            new_dict['content'] = new_content_dict
            new_dict['name'] = name
            
            return (True, new_dict)
        else :
            return (True, new_dict)
            
    
    def edit(self, uuid_str, content, describe='', name=''):
        content_dict = {}
        for key , value in content.items() :
            key_list = re.split(':', key)
            key_len = len(key_list)
            if key_len <= 1 :
                content_dict[key] = value
            else :
                for ids in range(key_len) :
                    if ids > 0  :
                        parte = key_list[ids - 1]
                        
                        if ids == 1 :
                            if parte not in content_dict :
                                content_dict[key_list[0]] = {}
                        elif ids == 2 :
                            if parte not in content_dict[key_list[0]] :
                                content_dict[key_list[0]][key_list[1]] = {}
                        elif ids == 3 :
                            if parte not in content_dict[key_list[0]][key_list[1]] :
                                content_dict[key_list[0]][key_list[1]][key_list[2]] = {}
                        elif ids == 4 :
                            if parte not in content_dict[key_list[0]][key_list[1]][key_list[2]] :
                                content_dict[key_list[0]][key_list[1]][key_list[2]][key_list[3]] = {}
                            
                    if ids == key_len - 1 :
                        if key_len == 2 :
                            content_dict[key_list[0]][key_list[1]] = value
                        elif key_len == 3 :
                            content_dict[key_list[0]][key_list[1]][key_list[2]] = value
                        elif key_len == 4 :
                            content_dict[key_list[0]][key_list[1]][key_list[2]][key_list[3]] = value
                        elif key_len == 5 :
                            content_dict[key_list[0]][key_list[1]][key_list[2]][key_list[3]][key_list[4]] = value
                            
        result = self.read2db_api.edit2db(uuid_str, content_dict, describe=describe, name=name)
        # result = self.read2db_api.edit2db(uuid_str, content, describe=describe, name=name)
        
        if result[0] :
            self.logger.info('编辑用户' + self.username + '的uuid为' + uuid_str + '的ansible yaml数据写入数据库成功')
        else :
            self.logger.error('编辑用户' + self.username + '的uuid为' + uuid_str + '的ansible yaml数据写入数据库失败，交由后端解析和写入数据库时失败，原因：' + str(result[1]))
        return (True, '交由后端解析和写入数据库时失败，原因：' + str(result[1]))
    
    
    def import_path(self, this_path, name, yaml_tpye='main', file_type='tasks', describe=''):

        if yaml_tpye == 'roles' :
            if os.path.isdir(this_path) :
                roles_path = this_path
            elif os.path.isfile(this_path):
                roles_path = '/dev/shm/lykops/ansible/yaml/' + random_str(ranlen=16)
                result = uncompress(this_path, roles_path)
                if not result[0] :
                    self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：不是一个压缩文件。注：系统要求导入类型为roles时，文件格式必须是zip格式的压缩文件、目录或者文件名等其中之一')
                    return (False, '路径为' + this_path + '不是一个格式为zip格式的压缩文件')
            else :
                self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：不是目录或者文件。注：系统要求导入类型为roles时，文件格式必须是zip格式的压缩文件、目录或者文件名等其中之一')
                return (False, '路径为' + this_path + '文件格式不是zip格式的压缩文件、目录或者文件名等其中之一')

            result = self.read2file_api.roles(roles_path, preserve=True, together=True, name=name, describe=describe)
            if result[0]:
                self.logger.info('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据成功')
                return (True, '对yaml文件进行语法验证等处理工作成功')
            else :
                self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
                return (False, '对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
        elif yaml_tpye in ('main','full_roles') :
            if os.path.isdir(this_path) :
                this_path = this_path + '/main.yaml'
                if not os.path.exists(this_path) :
                    self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：指定的路径为目录，无法找到main.yaml。注：系统要求导入类型为main或者full_roles时，如果路径是目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                    return (False, '指定的路径为目录，但无法找到main.yaml。注：系统要求导入类型为main或者full_roles时，如果路径是目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
            else :
                result = get_filetype(this_path)
                if not result[0] :
                    self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：指定的路径为文件，但不是文本文件。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                    return (False, '指定的路径为文件，但不是文本文件。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                
                if result[1] == 'txt' :
                    pass
                elif result[1] == 'zip' :
                    dest_dir = '/dev/shm/lykops/ansible/yaml/' + random_str(ranlen=16)
                    result = uncompress(this_path, dest_dir)
                    if not result[0] :
                        self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：路径为' + this_path + '不是一个格式为zip的压缩文件。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                        return (False, '路径为' + this_path + '不是一个格式为zip的压缩文件')
                    
                    this_path = dest_dir + '/main.yaml'
                    if not os.path.exists(this_path) :
                        self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：压缩文件解压后发现无法找到mai.yamln。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                        return (False, '压缩文件解压后发现无法找到main.yaml')
                else :
                    self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：暂时只支持txt或者zip格式文件。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                    return (False, '暂时只支持txt或者zip格式文件')
                
            result = self.read2file_api.main(this_path, preserve=True, together=True, name=name, describe=describe)
            if result[0]:
                self.logger.info('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据成功')
                return (True, '对yaml文件进行语法验证等处理工作成功')
            else :
                self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
                return (False, '对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
        else :
            result = get_filetype(this_path)
            if not result[0] :
                self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：不是文本文件。注：系统要求导入类型为include时，暂时只支持文本格式文件')
                return (False, '指定的路径为文件，但不是文本文件。注：系统要求导入类型为include时，暂时只支持文本格式文件')
            
            if result[1] == 'txt' :
                result = self.read2file_api.include(this_path, file_type=file_type, preserve=True, name=name, describe=describe)
                if result[0]:
                    self.logger.info('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据成功')
                    return (True, '对yaml文件进行语法验证等处理工作成功')
                else :
                    self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
                    return (False, '对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
            else :
                self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，原因：不是txt格式文件。注：系统要求导入类型为include时，暂时只支持文本格式文件')
                return (False, '暂时只支持文本格式文件')

    
    def import_upload(self, file, name, yaml_tpye='main', file_type='tasks', describe=''):
        
        result = upload_file(file)
        if not result :
            self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，上传文件失败,原因：' + result[1])
            return (False, '上传文件失败，' + result[1])
        else :
            this_path = result[1]

        if yaml_tpye == 'roles' : 
            roles_path = '/dev/shm/lykops/ansible/yaml/' + random_str(ranlen=16)
            result = uncompress(this_path, roles_path)
            if not result[0] :
                self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，原因：不是一个压缩文件。注：系统要求导入类型为roles时，文件格式必须是zip格式的压缩文件、目录或者文件名等其中之一')
                return (False, '上传文件不是一个格式为zip格式的压缩文件')

            result = self.read2file_api.roles(roles_path, preserve=True, together=True, name=name, describe=describe)
            if result[0]:
                self.logger.info('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据成功')
                return (True, '对yaml文件进行语法验证等处理工作成功')
            else :
                self.logger.error('为用户' + self.username + '从服务器本地路径为' + this_path + '导入ansible yaml数据失败，对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
                return (False, '对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
        elif yaml_tpye in ('main', 'full_roles') :
            result = get_filetype(this_path)
            if not result[0] :
                self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，原因：指定的路径为文件，但不是文本文件。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                return (False, '指定的路径为文件，但不是文本文件。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
            
            if result[1] == 'txt' :
                pass
            elif result[1] == 'zip' :
                dest_dir = '/dev/shm/lykops/ansible/yaml/' + random_str(ranlen=16)
                result = uncompress(this_path, dest_dir)
                if not result[0] :
                    self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，原因：路径为' + this_path + '不是一个格式为zip的压缩文件。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                    return (False, '路径为' + this_path + '不是一个格式为zip的压缩文件')
                
                this_path = dest_dir + '/main.yaml'
                if not os.path.exists(this_path) :
                    self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，原因：压缩文件解压后发现无法找到mai.yamln。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                    return (False, '压缩文件解压后发现无法找到main.yaml')
            else :
                self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，原因：暂时只支持txt或者zip格式文件。注：系统要求导入类型为main或者full_roles时，如果路径是目录或者是压缩文件解压后的目录，必须带有main.yaml；如果是文件，必须是一个格式为zip格式的压缩文件或者是文本文件')
                return (False, '暂时只支持txt或者zip格式文件')
            
            result = self.read2file_api.main(this_path, preserve=True, together=True, name=name, describe=describe)
            if result[0]:
                self.logger.info('为用户' + self.username + '上传文件方式导入ansible yaml数据成功')
                return (True, '对yaml文件进行语法验证等处理工作成功')
            else :
                self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
                return (False, '对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
        else :
            result = get_filetype(this_path)
            if not result[0] :
                self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，原因：不是文本文件。注：系统要求导入类型为include时，暂时只支持文本格式文件')
                return (False, '指定的路径为文件，但不是文本文件。注：系统要求导入类型为include时，暂时只支持文本格式文件')
            
            if result[1] == 'txt' :
                result = self.read2file_api.include(this_path, file_type=file_type, preserve=True, name=name, describe=describe)
                if result[0]:
                    self.logger.info('为用户' + self.username + '上传文件方式导入ansible yaml数据成功')
                    return (True, '对yaml文件进行语法验证等处理工作成功')
                else :
                    self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
                    return (False, '对yaml文件进行语法验证等处理工作时失败，原因：' + result[1])
            else :
                self.logger.error('为用户' + self.username + '上传文件方式导入ansible yaml数据失败，原因：不是txt格式文件。注：系统要求导入类型为include时，暂时只支持文本格式文件')
                return (False, '暂时只支持文本格式文件')
    

    def get_abs(self, force=False):
        
        '''
        获取该用户所有yaml文件（从数据库中）的摘要信息
        :parm
            force：是否强制刷新
        '''
        
        result = self.data2db_api.get_abs()
        if not result[0] :
            abs_list = []
        else :
            abs_list = result[1]

        return abs_list

        '''
        redis_key = self.yaml_rediskey_prefix + 'abs'
        if force:
            self.redisclient.delete(redis_key)
        
        result = self.redisclient.get(redis_key, fmt='obj')
        if not result[0] or (result[0] and not result[1]) :
            result = self.data2db_api.get_abs()
            if not result[0] :
                abs_list = []
            else :
                abs_list = result[1]
                
            self.write_cache(redis_key, abs_list, expire=self.expiretime)
        else :
            abs_list = result[1]
            
        return abs_list
        '''
         
