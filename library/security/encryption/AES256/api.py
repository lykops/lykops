import os, logging

from library.security.encryption.AES256 import AES256_Algorithm
from library.utils.file import write_file, read_file
from library.utils.type_conv import string2bytes, obj2bytes, obj2string, bytes2string

class Using_AES256():
    def __init__(self, password, header):
        
        '''
        对数据/文件进行加解密
        :parm 
            password : 加解密密码
        :return
            返回一个元组，(是否执行成功,成功加密数据/失败原因)
        '''
        
        self.logger = logging.getLogger("security")
        self.password = password
        self.this_cipher = AES256_Algorithm(self.password)
        
        result = obj2bytes(header)
        if result[0] :
            temp = result[1]
        else :
            temp = string2bytes(header)
        self.b_header = temp

        result = obj2string(header)
        if result[0] :
            temp = result[1]
        else :
            temp = bytes2string(header)
        self.header = temp
        

    def encrypt(self, data):
        
        '''
        加密数据
        :parm
            data为需要加密的数据
        '''
        
        try :
            ciphertext = self.this_cipher.encrypt(data)
        except Exception as e:
            self.logger.error('加密数据失败，原因：' + str(e))
            return (False, '加密数据失败，' + str(e))
        
        if not ciphertext[0] :
            self.logger.error('加密数据失败，原因：' + ciphertext[1])
            return (False, '加密数据失败，' + ciphertext[1])
            return ciphertext
        else :
            ciphertext = ciphertext[1]
            ciphertext = self._format_output(ciphertext)
            self.logger.info('加密数据成功')
            
        return (True, ciphertext)


    def decrypt(self, data):
        
        '''
        解密数据
        :parm
            data为需要解密的数据
        '''

        if not self._is_encrypt(data) :
            self.logger.error('解密数据失败，原因：加密数据格式不正确（可能使用非本系统加解密算法加密的）')
            return (False, "解密数据失败，加密数据格式不正确（可能使用非本系统加解密算法加密的）")

        ciphertext_list = self._split_header(data)
        ciphertext = ciphertext_list[1]
        
        plaintext = self.this_cipher.decrypt(ciphertext)
        self.logger.info('解密数据成功')
        return plaintext
    
    
    def _is_encrypt(self, data):
        
        '''
        判断加密数据是否使用使用非本系统加解密算法加密的
        '''
        
        ciphertext_list = self._split_header(data)

        temp_header = ciphertext_list[0]
        
        result = obj2bytes(temp_header)
        if result[0] :
            temp = result[1]
        else :
            temp = string2bytes(temp_header)
        b_header = temp

        result = obj2string(temp_header)
        if result[0] :
            temp = result[1]
        else :
            temp = bytes2string(temp_header)
        header = temp
        
        if b_header in self.b_header or header in self.header:
            return True
        else :
            return False
    
    
    def rekey(self, data, new_password):
        
        '''
        更改加密数据的valut密码
        :parm
            data加密数据
        '''
        
        if not new_password or new_password is None:
            self.logger.error('更改加密数据的valut密码失败，原因：新密码为空')
            return (False, "更改加密数据的valut密码失败，新密码为空")

        plaintext = self.decrypt(data)
        
        if not plaintext[0] :
            self.logger.error('更改加密数据的valut密码失败，原因：' + plaintext[1])
            return (False, "更改加密数据的valut密码失败，" + plaintext[1])
        else :
            plaintext = plaintext[1]

        new_op = Using_AES256(new_password, self.header)
        new_ciphertext = new_op.encrypt(plaintext)
        
        if not plaintext[0] :
            self.logger.error('更改加密数据的valut密码失败，在加密过程中出错，原因：' + new_ciphertext[1])
            return (False, "更改加密数据的valut密码失败，在加密过程中出错，" + new_ciphertext[1])
        else :
            self.logger.info('更改加密数据的valut密码成功')
        
        return new_ciphertext


    def encrypt_file(self, filename):
        
        '''
        加密文件
        :parm
            filename：需要加密的文件
        '''

        content = read_file(filename)
        if content[0] :
            plaintext = content[1]
        else :
            self.logger.error('加密文件' + filename + '失败，在读取文件过程中出错，原因：' + content[1])
            return (False, "加密文件失败，在读取文件过程中出错，" + content[1])

        ciphertext = self.encrypt(plaintext)
        
        if not ciphertext[0] :
            self.logger.error('加密文件' + filename + '失败，在加密过程中出错，原因：' + ciphertext[1])
            return (False, "加密文件失败，在加密过程中出错，" + ciphertext[1])       
        else :
            ciphertext = ciphertext[1]
        
        result = self._write_file(filename, ciphertext)
        if not result[0] :
            self.logger.error('加密文件' + filename + '失败，在加密后回写文件过程中出错，原因：' + result[1])
            return (False, "加密文件失败，在加密后回写文件过程中出错，" + result[1])       
        else :
            self.logger.info('加密文件' + filename + '成功')
            return (True, "加密文件成功") 
        
    
    def encrypt_file2text(self, filename):
        
        '''
        加密文件的内容，成功后直接输出
        :parm
            filename：需要加密的文件
        '''

        content = read_file(filename)
        if content[0] :
            plaintext = content[1]
        else :
            self.logger.error('加密文件' + filename + '的内容（成功后直接输出）失败，在读取文件过程中出错，原因：' + content[1])
            return (False, "加密文件的内容（成功后直接输出）失败，在读取文件过程中出错，" + content[1])
        
        ciphertext = self.encrypt(plaintext)
        if not ciphertext[0] :
            self.logger.error('加密文件' + filename + '的内容（成功后直接输出）失败，在加密过程中出错，原因：' + ciphertext[1])
            return (False, "加密文件的内容（成功后直接输出）失败，在加密过程中出错，" + ciphertext[1])       
        else :
            self.logger.info('加密文件' + filename + ' 的内容（成功后直接输出）成功')
            return (True, "加密文件的内容（成功后直接输出）成功") 
    

    def decrypt_file(self, filename):

        '''
        解密文件
        :parm
            filename：需要解密的文件
        '''

        content = read_file(filename)
        if content[0] :
            ciphertext = content[1]
        else :
            self.logger.error('解密文件' + filename + '失败，在读取文件过程中出错，原因：' + content[1])
            return (False, "解密文件失败，在读取文件过程中出错，" + content[1])

        plaintext = self.decrypt(ciphertext)
        if not plaintext[0] :
            self.logger.error('解密文件' + filename + '失败，在解密过程中出错，原因：' + plaintext[1])
            return (False, "解密文件失败，在解密过程中出错，" + plaintext[1])     
        
        result = self._write_file(filename, plaintext[1])
        if not result[0] :
            self.logger.error('解密文件' + filename + '失败，在解密后回写文件过程中出错，原因：' + result[1])
            return (False, "解密文件失败，在解密后回写文件过程中出错，" + result[1])       
        else :
            self.logger.info('解密文件' + filename + '成功')
            return (True, "解密文件成功") 
        
        
    def decrypt_file2text(self, filename):
        
        '''
        解密文件的内容，成功后直接输出
        :parm
            filename：需要解密的文件
        '''

        content = read_file(filename)
        if content[0] :
            ciphertext = content[1]
        else :
            self.logger.error('解密文件' + filename + '的内容（成功后直接输出）失败，在读取文件过程中出错，原因：' + content[1])
            return (False, "解密文件的内容（成功后直接输出）失败，在读取文件过程中出错，" + content[1])

        plaintext = self.decrypt(ciphertext)
        if not plaintext[0] :
            self.logger.error('解密文件' + filename + '的内容（成功后直接输出）失败，在解密过程中出错，原因：' + ciphertext[1])
            return (False, "解密文件的内容（成功后直接输出）失败，在解密过程中出错，" + plaintext[1])       
        else :
            self.logger.info('解密文件' + filename + ' 的内容（成功后直接输出）成功')
            return (True, "解密文件的内容（成功后直接输出）成功") 


    def create_file(self, data, filename):

        '''
        把加密数据写入到文件
        :parm
            data：需要加密的数据内容
            filename：需要解密写入到文件
        '''

        if os.path.isfile(filename):
            self.logger.error('加密数据后写入文件失败，原因：文件' + filename + '已存在')
            return (False, '加密数据后写入文件失败，文件已存在')
        
        ciphertext = self.encrypt(data)
        if not ciphertext[0] :
            self.logger.error('加密数据后写入文件失败，在加密过程中失败，原因：' + str(ciphertext[1]))
            return (False, '加密数据后写入文件失败，在加密过程中失败，原因：' + str(ciphertext[1]))        
        else :
            ciphertext = ciphertext[1]
            
        result = self._write_file(filename, ciphertext)
        if not result[0] :
            self.logger.error('加密数据后写入文件失败，在写入文件过程中出错，原因：' + result[1])
            return (False, "加密数据后写入文件失败，在写入文件过程中出错，" + result[1])       
        else :
            self.logger.info('加密数据后写入文件成功')
            return (True, "加密数据后写入文件成功") 
        
    
    '''
    def edit_file(self, data, filename):

        编辑加密文件
        :parm
            data：需要加密的数据内容
            filename：需要解密写入到文件

        ciphertext = self.encrypt(data)

        if not ciphertext[0] :
            self.logger.error('编辑加密文件失败，在加密过程中出错，原因：' + ciphertext[1])
            return (False, '加密文件失败，原因' + str(ciphertext[1]))
        else :
            ciphertext = ciphertext[1]
        
        result = self._write_file(filename, ciphertext)
        if not result[0] :
            self.logger.error('编辑加密文件失败，在写入文件过程中出错，原因：' + result[1])
            return (False, "编辑加密文件失败，在写入文件过程中出错，" + result[1])       
        else :
            self.logger.info('编辑加密文件成功')
            return (True, "编辑加密文件成功") 
        '''


    def rekey_file(self, filename, new_password):

        '''
        更改加密文件的valut密码
        :parm
            new_password：新密码
            filename：需要更换的文件
        '''
        
        if not new_password or new_password is None:
            self.logger.error('更改加密文件' + filename + '的valut密码失败，原因：新密码为空')
            return (False, "更改加密文件的valut密码失败，新密码为空")
        
        content = read_file(filename)
        if content[0] :
            ciphertext = content[1]
        else :
            self.logger.error('更改加密文件' + filename + '的valut密码失败，在读取文件过程中出错，原因：' + content[1])
            return (False, "更改加密文件失败，在读取文件过程中出错，" + content[1])
        
        new_ciphertext = self.rekey(ciphertext, new_password)
        
        if not new_ciphertext[0] :
            self.logger.error('更改加密文件' + filename + '的valut密码失败，在加密过程中出错，原因：' + str(new_ciphertext[1]))
            return (False, '更改加密文件的valut密码失败，在加密过程中出错，' + str(new_ciphertext[1]))
        else :
            new_ciphertext = new_ciphertext[1]

        result = self._write_file(filename, new_ciphertext)
        if not result[0] :
            self.logger.error('更改加密文件' + filename + '的valut密码失败，在写入文件过程中出错，原因：' + result[1])
            return (False, "更改加密文件的valut密码失败，在写入文件过程中出错，" + result[1])       
        else :
            self.logger.info('更改加密文件' + filename + '的valut密码成功')
            return (True, "更改加密文件的valut密码成功") 
    

    def _format_output(self, data):
        
        '''
        对加密数据进行格式化，仅用于写入文件
        :parm
            ciphertext ：需要格式化的数据
        '''

        result = obj2bytes(data)
        if result[0] :
            b_ciphertext = result[1]
        else :
            b_ciphertext = string2bytes(data)
        
        b_new_ciphertext = [self.b_header]
        b_new_ciphertext += [b_ciphertext[i:i + 80] for i in range(0, len(b_ciphertext), 80)]
        b_new_ciphertext += [b'']
        b_new_ciphertext = b'\n'.join(b_new_ciphertext)

        return b_new_ciphertext
    

    def _split_header(self, data):
        
        '''
        对加密数据进行分割，分为加密头和加密数据
        :parm
            data ：需要分割的加密数据
        '''
        
        result = obj2bytes(data)
        if result[0] :
            data = result[1]
        else :
            data = string2bytes(data)
        
        b_data = data.split(b'\n')
        b_header = b_data[0].strip()
        b_ciphertext = b''.join(b_data[1:])

        return (b_header, b_ciphertext)

        
    def _write_file(self, filename, data):
        
        '''
        把数据写入文件
        :parm
            filename：文件名
            data：数据
        
        '''
        
        result = write_file(filename, 'w', data, force=True, backup=False)
        if not result[0] :
            return (False, result[1])
        return (True, filename)
