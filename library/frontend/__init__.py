import logging

from library.config.frontend import adminuser
from library.config.security import vault_header
from library.connecter.database.mongo import Op_Mongo
from library.connecter.database.redis_api import Op_Redis
from library.security.encryption.AES256.api import Using_AES256
from library.security.password import Manager_Password
from library.utils.time_conv import timestamp2datetime
from library.utils.type_conv import str2dict


class Base():
    def __init__(self, mongoclient=None, redisclient=None):
        
        '''
        这是用户管理部分的MVC中的C
        '''
        
        self.logger = logging.getLogger("lykops")
        self.userinfo_mongocollect = 'user.login.info'
        self.userinfo_rediskey = 'lykops:userinfo'
        self.privacy_mongocollect = 'user.privacy'
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

        self.password_api = Manager_Password()
        self.expiretime = 60 * 60 * 24
        self.rediskey_prefix = 'lykops:'
            

    def get_userinfo(self, force=False, username=None):
        
        '''
        获取userinfo数据
        '''
        
        if force :
            self.logger.warn('强制删除用户信息缓存')
            self.redisclient.delete(self.userinfo_rediskey)
        
        result = self.redisclient.get(self.userinfo_rediskey, fmt='obj')
        if result[0] and (result[1] is not None or result[1]) :
            userinfo = result[1]
        else : 
            result = self.mongoclient.find(self.userinfo_mongocollect)
            if result[0] :
                userinfo = result[1]

                set_dict = {
                    'name' : self.userinfo_rediskey,
                    'value' : userinfo,
                    'ex':self.expiretime
                    }
                self.redisclient.set(set_dict, fmt='obj')
            else :
                userinfo = {}
            
        if username is None :
            return userinfo
        else :
            try :
                for u_dict in userinfo :
                    if username == u_dict['username'] :
                        us = u_dict
                    else :
                        continue
            except :
                us = {}
            
            try : 
                return us
            except :
                return {}


    def verify_vaultpassword(self, username, vault_password):
        
        '''
        验证用户的vault密码是否正确
        :parm
            username：用户名
            vault_password：vault密码
        '''
        
        user_dict = self.get_userinfo(username=username)
        if not user_dict :
            content = '用户' + username + '不存在'
            self.logger.error(content)
            return (False, content)
        
        try :
            cipher_pwd = user_dict['vault_password']
        except :
            content = '从数据库中没有查询到用户' + username + '的vault密码'
            self.logger.error(content)
            return (False, content)
        
        result = self.password_api.verify(vault_password, cipher_pwd)
        if not result :
            content = '用户' + username + '输入的vault密码与数据库中vault密码不匹配'
            self.logger.error(content)
            return (False, content)
        else :
            content = '用户' + username + '输入的vault密码与数据库中vault密码匹配成功'
            # self.logger.info(content)
            return (True, content)


    def get_data(self, username, redis_key, mongo_collect, force=False, mongoshare=True):
        
        '''
        获取用户数据
        :parm
            username：用户名
            redis_key：redis缓存key名
            mongo_collect：mongo的集合名
            force：强制刷新
        '''
        
        if force:
            self.logger.warn('强制删除指定缓存')
            self.redisclient.delete(redis_key)
        
        result = self.redisclient.get(redis_key, fmt='obj')
        if not result[0] or (result[0] and not result[1]) :
            if mongoshare :
                result = self.mongoclient.find(mongo_collect, condition_dict={'username' : username})
            else :
                result = self.mongoclient.find(mongo_collect)

            if result[0] :
                data_dict = result[1]
                self.write_cache(redis_key, data_dict)
            else :
                self.logger.error('从数据库中查询数据失败，原因：' + result[1])
                return result
        else :
            data_dict = result[1]
                    
        try :
            del data_dict['username']
        except :
            pass
            
        return (True, data_dict)


    def encryp_dict(self, username, vault_password, data, vault_list, isverify=True):
        
        '''
        对用户的数据字典中的某些字段进行加密
        '''
        
        encryp_api = Using_AES256(vault_password, vault_header)
        if isverify :
            vault_result = self.verify_vaultpassword(username, vault_password)
            if not vault_result[0] :
                self.logger.error('加密用户' + username + '的指定数据时失败，原因：输入的vault密码与数据库中vault密码不匹配')
                return (False, '输入的vault密码与数据库中vault密码不匹配') 
        
        if not vault_list :
            vault_list = data.keys()
        
        encryp_dict = {}
        for key , value in data.items() :
            if not value :
                encryp_dict[key] = value
            
            if key in vault_list :
                result = encryp_api.encrypt(value)
                if result[0] :
                    encryp_dict[key] = result[1]
                else :
                    self.logger.error('加密用户' + username + '的指定数据时失败，键名' + key + '的值加密失败，原因：' + result[1])
                    return (False, '加密用户' + username + '的指定数据时失败，键名' + key + '的值加密失败，' + result[1]) 
            else :
                if value == 'False' :
                    value = False
                
                if value == 'True' :
                    value = True
                
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
                
                encryp_dict[key] = value
        
        # content = '加密用户' + username + '的指定数据成功'
        # self.logger.info(content)
        return (True, encryp_dict)


    def decryp_dict(self, username, vault_password, data, vault_list, isverify=True):
        
        '''
        对用户的数据字典中的某些字段进行解密
        '''
        
        encryp_api = Using_AES256(vault_password, vault_header)
        if isverify :
            vault_result = self.verify_vaultpassword(username, vault_password)
            if not vault_result[0] :
                self.logger.error('解密用户' + username + '的指定数据时失败，原因：输入的vault密码与数据库中vault密码不匹配')
                return (False, '输入的vault密码与数据库中vault密码不匹配') 

        if not vault_list :
            vault_list = data.keys()

        decryp_dict = {}
        for key , value in data.items() :
            if not value :
                decryp_dict[key] = value
            
            if key in vault_list :
                result = encryp_api.decrypt(value)
                if result[0] :
                    decryp_dict[key] = result[1]
                else :
                    self.logger.error('解密用户' + username + '的指定数据时失败，键名' + key + '的值加密失败，原因：' + result[1])
                    return (False, '解密用户' + username + '的指定数据时失败，键名' + key + '的值加密失败，' + result[1]) 
            else :
                if value == 'False' :
                    value = False
                
                if value == 'True' :
                    value = True
                
                decryp_dict[key] = value
                
        # content = '解密用户' + username + '的指定数据成功'
        # self.logger.info(content)
        return (True, decryp_dict)


    def encryp_string(self, username, vault_password, data, isverify=True):
        
        '''
        对用户的数据进行加密
        '''
        
        encryp_api = Using_AES256(vault_password, vault_header)
        if isverify :
            vault_result = self.verify_vaultpassword(username, vault_password)
            if not vault_result[0] :
                self.logger.error('加密用户' + username + '数据时失败，原因：输入的vault密码与数据库中vault密码不匹配')
                return (False, '加密用户' + username + '数据时失败，输入的vault密码与数据库中vault密码不匹配') 

        result = encryp_api.encrypt(data)
        if result[0] :
            # content = '加密用户' + username + '数据成功'
            # self.logger.info(content)
            return (True, result[1])
        else :
            self.logger.error('加密用户' + username + '数据失败，原因：' + result[1])
            return (False, '加密用户' + username + '数据失败，' + result[1])
        
        
    def decryp_string(self, username, vault_password, data, isverify=True):
        
        '''
        对用户的数据进行解密
        '''
        
        decryp_api = Using_AES256(vault_password, vault_header)
        if isverify :
            vault_result = self.verify_vaultpassword(username, vault_password)
            if not vault_result[0] :
                self.logger.error('解密用户' + username + '数据时失败，原因：输入的vault密码与数据库中vault密码不匹配')
                return (False, '解密用户' + username + '数据时失败，输入的vault密码与数据库中vault密码不匹配') 

        result = decryp_api.decrypt(data)
        if result[0] :
            # content = '解密用户' + username + '数据成功'
            # self.logger.info(content)
            return (True, result[1])
        else :
            self.logger.error('解密用户' + username + '数据失败，原因：' + result[1])
            return (False, result[1])
        
        
    def change_vltpwd_dict(self, username, old_pwd, new_pwd, vault_dict, vault_list, isverify=False):
        
        '''
        修改用户的vault数据（字典）的vault密码
        '''
        
        try :
            del vault_dict['add_time']
        except :
            pass
        
        if not vault_list :
            vault_list = vault_dict.keys()
        
        # 不要使用encryp_dict和decryp_dict来更换密码，否则无法修改密码
        
        new_data = {}
        for key, value in vault_dict.items() :
            if key in vault_list :
                result = self.decryp_string(username, old_pwd, value, isverify=isverify)
                if not result[0] :
                    self.logger.error('更改用户' + username + '的vault密码时失败，解密数据时出错，原因：' + result[1])
                    return (False, '更改用户' + username + '的vault密码时失败，解密数据时出错，' + result[1])
                
                new_value = result[1]
                result = self.encryp_string(username, new_pwd, new_value, isverify=isverify)
                if not result[0] :
                    self.logger.error('更改用户' + username + '的vault密码时失败，解密后再次加密数据时出错，原因：' + result[1])
                    return (False, '更改用户' + username + '的vault密码时失败，解密后再次加密数据时出错，' + result[1])
                
                new_data[key] = result[1]
            else :
                new_data[key] = value
        
        # content = '更改用户' + username + '的vault密码成功'
        # self.logger.info(content)
        return (True, new_data)


    def write_cache(self, redis_key, data, expire=60 * 60, ftm='obj'):
        try :
            self.logger.warn('强制删除缓存')
            self.redisclient.delete(redis_key)
        except :
            pass
        
        set_dict = {
            'name' : redis_key,
            'value' : data,
            'ex':expire
            }
                
        result = self.redisclient.set(set_dict, fmt=ftm)
        if result[0] :
            content = '写缓存成功'
            # self.logger.info(content)
            return (True, content)
        else :
            self.logger.info('写缓存失败，原因：' + result[1])
            return (False, '写缓存失败，' + result[1])
