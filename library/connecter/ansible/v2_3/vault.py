import os, re, time, logging

from ansible.parsing.vault import VaultEditor

from library.security.encryption.AES256.api import Using_AES256
from library.utils.file import write_file, read_file, write_random_file
from library.utils.type_conv import string2bytes, obj2bytes, obj2string


class Op_Vault():
    def __init__(self, password):
        self.logger = logging.getLogger("ansible")
        self.password = password
        
        from library.config.security import vault_header
        tmp_header = vault_header + ';date:' + str(time.time())
        self.vault_header = tmp_header
        result = obj2bytes(tmp_header)
        if result[0] :
            temp_header = result[1]
        else :
            temp_header = string2bytes(tmp_header)
        self.b_vault_header = temp_header
        self.cipher = Using_AES256(self.password,self.b_vault_header)


    def _handle_ciphertext(self,data=None,filename=None):
        
        '''
        对加密数据/文件内容的头部进行判断使用哪种方式加密
        data或者filename其中一个可以为空，至少一个不能为空
        如果两个均不为空，默认使用filename
        :parm
            data：加密数据
            filename：加密文件
        :return
            算法或者False
        '''
                  
        if data is None and filename is None :
            self.logger.error('解密ansible加密数据时出错，原因：参数data和filename不能同时为空')
            return (False, False, '参数data和filename不能同时为空')
          
        if filename is not None :
            result = read_file(filename)
            if result[0] :
                data = result[1]
            else :
                if data is None :
                    self.logger.error('解密ansible文件' + filename + '时出错，无法读取文件，原因：' + result[1])
                    return (False,False,'无法读取文件')

        result = obj2bytes(data)
        if result[0] :
            b_data = result[1]
        else :
            b_data = string2bytes(data)
        
        b_data = b_data.split(b'\n')
        b_vault_header = b_data[0].strip()
        b_ciphertext = b''.join(b_data[1:])
        
        vault_header = obj2string(b_vault_header)[1]
        
        if b_vault_header in self.b_vault_header :
            #这是自定义加密数据
            self.logger.info('解密ansible加密数据成功，注：加密数据使用本系统自定义方法加密的')
            return (True,True,b_data)
        elif re.search('ANSIBLE_VAULT;1.1;', vault_header) :
            #这是ansible2.3版本加密数据
            # return (False, True, data)

            #在ansible 2.3版本中，vault加密后头部为'$ANSIBLE_VAULT;1.1;AES256'，其他版本未知
            if vault_header == '$ANSIBLE_VAULT;1.1;AES256' :
                #说明加密方式为AES256，自定义加密算法一直，直接使用自定义方式进行解密
                data = self.b_vault_header + b'\n' + b_ciphertext
                result = obj2bytes(data)
                if result[0] :
                    self.logger.info('解密ansible加密数据成功，注：加密数据使用ansible2.3版本加密的')
                    return (True, False, result[1])
                else :
                    self.logger.error('解密ansible加密数据时失败，原因：加密数据使用ansible2.3版本加密的，' + str(result[1]))
                    return (False, True, data)
            else :
                self.logger.error('解密ansible加密数据时失败，原因：未知格式的加密方法')
                return (False,True,data)
        else :
            self.logger.error('解密ansible加密数据时失败，原因：未知格式的加密方法')
            return (False,False,'未知格式的加密数据')


    def encrypt_file(self,filename):
        result = self.cipher.encrypt_file(filename)
        if result[0] :
            self.logger.info('加密ansible文件' + filename + '成功')
        else :
            self.logger.info('加密ansible文件' + filename + '失败，原因：' + result[1])
        return result
        

    def encrypt(self, data):
        result = self.cipher.encrypt(data) 
        if result[0] :
            self.logger.info('加密ansible数据成功')
        else :
            self.logger.info('加密ansible数据失败，原因：' + result[1])
        return result


    def encrypt_file2text(self, filename):
        result = self.cipher.encrypt_file2text(filename)
        if result[0] :
            self.logger.info('加密ansible文件' + filename + '成功')
        else :
            self.logger.info('加密ansible文件' + filename + '失败，原因：' + result[1])
        return result


    def decrypt(self, data):
        result = self._handle_ciphertext(data=data)
        if not result[0] :
            if not result[1] :
                return (False,result[2])
            else :
                # 这是一个ansible-vault加密的数据，使用ansible-vault进行处理
                result = self._ansible_vault_encrpyt(result[2])
                if result[0] :
                    data = result[1]
                    self.logger.info('解密ansible数据成功，注：使用ansible2.3版本方法')
                    return (True, data)
                else :
                    self.logger.error('解密ansible数据失败，原因：' + result[1] + '，注：使用ansible2.3版本方法')
                    return result
        else :
            result = self.cipher.decrypt(result[2])
            if result[0] :
                self.logger.info('解密ansible数据成功，注：使用本系统自定义方法')
            else :
                self.logger.error('解密ansible数据失败，原因：' + result[1] + '，注：使用本系统自定义方法')
            return result

     
    def decrypt_file(self, filename):
        result = self._handle_ciphertext(filename=filename)
        if not result[0] :
            if not result[1] :
                return (False, result[2])
            else :
                # 这是一个ansible-vault加密的数据，使用ansible-vault进行处理
                result = self._ansible_vault_encrpyt(result[2])
                if result[0] :
                    data = result[1]
                    result = write_file(filename, 'w', data, force=True, backup=False)
                    if result[1] :
                        self.logger.info('解密ansible文件' + filename + '成功，注：使用ansible2.3版本方法')
                    else :
                        self.logger.error('解密ansible数据' + filename + '失败，无法写入文件，原因：' + result[1] + '，注：使用ansible2.3版本方法')
                    return result
                else :
                    self.logger.error('解密ansible数据' + filename + '失败，原因：' + result[1] + '，注：使用ansible2.3版本方法')
                    return result
        else :
            if not result[1] : 
                result = write_file(filename, 'w', result[2], force=True, backup=False)
                if not result[0] :
                    self.logger.error('解密ansible数据' + filename + '失败，无法写入文件，原因：' + result[1] + '，注：使用本系统自定义方法')
                    return result
 
            result = self.cipher.decrypt_file(filename)
            if result[0] :
                self.logger.info('解密ansible文件' + filename + '成功，注：使用本系统自定义方法')
            else :
                self.logger.error('解密ansible数据' + filename + '失败，原因：' + result[1] + '，注：使用本系统自定义方法')
            return result
        
        
    def decrypt_file2text(self, filename):
        result = self._handle_ciphertext(filename=filename)
        if not result[0] :
            if not result[1] :
                return (False, result[2])
            else :
                # 这是一个ansible-vault加密的数据，使用ansible-vault进行处理
                result = self._ansible_vault_encrpyt(result[2])
                if result[0] :
                    self.logger.info('解密ansible文件' + filename + '成功，注：使用ansible2.3版本方法')
                    data = result[1]
                    return (True, data)
                else :
                    self.logger.error('解密ansible数据' + filename + '失败，原因：' + result[1] + '，注：使用ansible2.3版本方法')
                    return result
        else :
            if result[1] : 
                result = self.cipher.decrypt_file2text(filename)
                if result[0] :
                    self.logger.info('解密ansible文件' + filename + '成功，注：使用本系统自定义方法')
                else :
                    self.logger.error('解密ansible数据' + filename + '失败，原因：' + result[1] + '，注：使用本系统自定义方法')
                return result
            else :
                result = self.cipher.decrypt(result[2])
                if result[0] :
                    self.logger.info('解密ansible文件' + filename + '成功，注：使用本系统自定义方法')
                else :
                    self.logger.error('解密ansible数据' + filename + '失败，原因：' + result[1] + '，注：使用本系统自定义方法')
                return result
    

    def create_file(self, data, filename):
        result = self.cipher.create_file(data, filename)
        if result[0] :
            self.logger.info('加密ansible数据，并写入文件' + filename + '成功')
        else :
            self.logger.info('加密ansible数据，并写入文件' + filename + '失败，原因：' + result[1])
        return result


    def edit_file(self, new_data, filename):
        result = self.cipher.edit_file(new_data, filename)
        if result[0] :
            self.logger.info('编辑加密ansible文件' + filename + '成功')
        else :
            self.logger.info('编辑加密ansible文件' + filename + '失败，原因：' + result[1])
        return result


    def rekey(self, data, new_password):
        result = self._handle_ciphertext(data=data)
        if not result[0] :
            if not result[1] :
                return (False, result[2])
            else :
                # 这是一个ansible-vault加密的数据，使用ansible-vault进行处理
                result = self._ansible_vault_encrpyt(result[2])
                if result[0] :
                    this_cipher = Using_AES256(new_password, self.b_vault_header)
                    data = result[1]
                    self.logger.info('修改ansible加密数据的vault密码成功，注：使用ansible2.3版本方法')
                    return this_cipher.encrypt(data)
                else :
                    self.logger.error('修改ansible加密数据的vault密码失败，原因：' + result[1] + '，注：使用ansible2.3版本方法')
                    return result
        else :
            result = self.cipher.rekey(result[2], new_password)
            if result[0] :
                self.logger.info('修改ansible数据的vault密码成功，注：使用本系统自定义方法')
            else :
                self.logger.error('修改ansible数据的vault密码失败，原因：' + result[1] + '，注：使用本系统自定义方法')
            return result


    def rekey_file(self, filename, new_password):
        result = self._handle_ciphertext(filename=filename)
        if not result[0] :
            if not result[1] :
                return (False, result[2])
            else :
                # 这是一个ansible-vault加密的数据，使用ansible-vault进行处理
                result = self._ansible_vault_encrpyt(result[2])
                if result[0] :
                    self.logger.info('修改ansible加密文件' + filename + '的vault密码成功，注：使用ansible2.3版本方法')
                    return self.cipher.encrypt_file(filename)
                else :
                    self.logger.error('修改ansible加密文件' + filename + '的vault密码失败，原因：' + result[1] + '，注：使用ansible2.3版本方法')
                    return result
        else :
            if not result[1] : 
                result = write_file(filename, 'w', result[2], force=True, backup=False)
                if not result[0] :
                    self.logger.error('修改ansible加密文件' + filename + '的vault密码失败，无法写入文件，原因：' + result[1] + '，注：使用本系统自定义方法')
                    return result
            
            result = self.cipher.rekey_file(filename, new_password)
            if result[0] :
                self.logger.info('修改ansible加密文件' + filename + '的vault密码成功，注：使用本系统自定义方法')
            else :
                self.logger.error('修改ansible加密文件' + filename + '的vault密码失败，原因：' + result[1] + '，注：使用本系统自定义方法')
            return result
        

    def _ansible_vault_encrpyt(self, data):
        '''
        while True :
            vault_tempfile = tempdir + '/vault' + random_str(ranlen=20) + '_' + str(int(time.time()))
            result = write_file(vault_tempfile, 'w', data)
            if result[0] :
                break
        '''
        result = write_random_file(data)
        if not result[0] :
            return result
        
        vault_tempfile = result[1]
                
        ansible_vault = VaultEditor(self.password)    
        ansible_vault.decrypt_file(vault_tempfile)
        result = read_file(vault_tempfile)
        os.remove(vault_tempfile)
        return result
