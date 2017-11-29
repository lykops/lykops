from library.frontend import Base

class Manager_Privacy(Base):
    
    '''
    该功能用于保存用户的机密数据，但该版本暂时不需要使用，故暂时不做展示
    '''
    
    def get(self, username, vault_password=None, force=False):

        '''
        获取用户privacy数据
        :parm
            username：用户名
            vault_password：用户的vault密码
            force：是否强制从mongo中获取数据
        '''
        
        redis_key = self.rediskey_prefix + username + ':privacy'
        result = self.get_data(username, redis_key, self.privacy_mongocollect, force=force)
        
        if vault_password is None :
            return result
        else :
            vault_result = self.verify_vaultpassword(username, vault_password)
            if not vault_result[0] :
                return vault_result 
            
            if result[0] :
                try :
                    data = result[1][0]
                except :
                    return (True, {})
            
                if not isinstance(data, dict) :
                    return (True, {})
            
                try :
                    del data['username']
                    del data['add_time']
                except :
                    pass
            
                result = self.decryp_dict(username, vault_password, data, [])
                if not result[0] :
                    return result
                data_dict = result[1]
                return (True, data_dict)
            else :
                self.logger.error('获取用户' + username + '的机密数据失败，原因：' + result[1])
                return result
            
    
    def save_vault(self, username):
        
        '''
        把privacy数据（加密后的）写入mongo中
        :parm
            username：用户名
        '''
        
        temp_rediskey = self.rediskey_prefix + username + ':privacy:temp'
        result = self.redisclient.get(temp_rediskey, fmt='obj')
        if not result[0] :
            if not self.redisclient.haskey(self.temp_rediskey):
                self.logger.warn('没有任何用户' + username + '的机密数据写入数据库【上级任务：更改用户的vault密码】')
                return (True, '没有数据')
            
            self.logger.error('用户' + username + '的机密数据写入数据库失败【上级任务：更改用户的vault密码】，读取缓存信息失败，原因：' + result[1])
            return (False, '读取缓存失败' + result[1])
        
        data = result[1]
        
        if data == {}:
            self.logger.warn('没有任何用户' + username + '的机密数据写入数据库【上级任务：更改用户的vault密码】')
            return (True, '没有数据')
                    
        update_dict = {
            'collect' : self.privacy_mongocollect,
            'data' : data
            }
        result = self.mongoclient.update({'username' : username}, update_dict, addtime=True)
        if result[0] :
            self.logger.info('用户' + username + '的机密数据写入数据库成功【上级任务：更改用户的vault密码】')
        else :
            self.logger.error('用户' + username + '的机密数据写入数据库失败【上级任务：更改用户的vault密码】，原因：' + result[1])
        return result
        
    
    def save(self, username, data, vault_password):
        
        '''
        把privacy数据（明文）加密后写入mongo中
        :parm
            username：用户名
            data：加密前的privacy数据字典
            vault_password：vault密码
        '''
        
        vault_result = self.verify_vaultpassword(username, vault_password)
        if not vault_result[0] :
            return vault_result 
        
        if not isinstance(data, dict) :
            self.logger.error('用户' + username + '的机密数据写入数据库失败【来源于web页面更改机密数据】，原因：数据格式不正确，必须是字典格式')
            return (False, '数据格式不正确，必须是字典格式')
        
        result = self.encryp_dict(username, vault_password, data, [])
        if not result[0] :
            self.logger.error('用户' + username + '的机密数据写入数据库失败【来源于web页面更改机密数据】，原因：' + result[1])
            return result
        vault_dict = result[1]
        vault_dict['username'] = username
        
        condition_dict = {'username':username}
        update_dict = {
            'collect' : self.privacy_mongocollect,
            'data' : vault_dict
            }

        result = self.mongoclient.update(condition_dict, update_dict, addtime=True)
        redis_key = self.rediskey_prefix + username + ':privacy'
        self.get_data(username, redis_key, self.privacy_mongocollect, force=True)
        if result[0] :
            self.logger.info('用户' + username + '的机密数据写入数据库成功【上级任务：来源于web页面更改机密数据】')
        else :
            self.logger.error('用户' + username + '的机密数据写入数据库失败【上级任务：来源于web页面更改机密数据】，原因：' + result[1])
        return result


    def change_vault_password(self, username, old_pwd, new_pwd):

        '''
        修改用户的vault密码，对privacy数据进行更换密码
        :parm
            username：用户名
            old_pwd：旧vault密码
            new_pwd：新vault密码
        '''
        
        result = self.mongoclient.find(self.privacy_mongocollect, condition_dict={'username' : username})
        if not result[0] :
            self.logger.error('用户' + username + '的机密数据更改vault密码失败，原因：查询数据错误')
            return (False, '查询数据错误')
        
        try : 
            vault_dict = result[1][0]
        except :
            return (True, {})

        if not isinstance(vault_dict, dict) :
            self.logger.error('用户' + username + '的机密数据更改vault密码失败，原因：查询数据错误')
            return (False, '查询数据错误')

        try :
            del vault_dict['username']
            del vault_dict['add_time']
        except :
            pass
        
        result = self.change_vltpwd_dict(username, old_pwd, new_pwd, vault_dict, [])
        if not result[0] :
            return result
        
        new_vault_dict = result[1]
        new_vault_dict['username'] = username
        
        result = self.write_cache(self.rediskey_prefix + username + ':privacy:temp', new_vault_dict, expire=60 * 5)
        redis_key = self.rediskey_prefix + username + ':privacy'
        self.redisclient.delete(redis_key)
        if result[0] :
            self.logger.info('用户' + username + '的机密数据更改vault密码成功，并写入临时缓存中')
            return (True, '写缓存成功')
        else :
            self.logger.error('用户' + username + '的机密数据更改vault密码成功，但写入临时缓存失败，原因：' + result[1])
            return (False, '写缓存失败，' + result[1])
                
