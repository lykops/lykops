from binascii import hexlify
from binascii import unhexlify
import os, sys, logging

try:
    from Crypto.Hash import SHA256, HMAC
    HAS_HASH = True
except ImportError:
    HAS_HASH = False
        
# Counter import fails for 2.0.1, requires >= 2.6.1 from pip
try:
    from Crypto.Util import Counter
    HAS_COUNTER = True
except ImportError:
    HAS_COUNTER = False
        
# KDF import fails for 2.0.1, requires >= 2.6.1 from pip
try:
    from Crypto.Protocol.KDF import PBKDF2
    HAS_PBKDF2 = True
except ImportError:
    HAS_PBKDF2 = False
        
# AES IMPORTS
try:
    from Crypto.Cipher import AES
    HAS_AES = True
except ImportError:
    HAS_AES = False

# OpenSSL pbkdf2_hmac
try:
    from cryptography.hazmat.primitives.hashes import SHA256 as c_SHA256
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    HAS_PBKDF2HMAC = True
except:
    HAS_PBKDF2HMAC = False

HAS_ANY_PBKDF2HMAC = HAS_PBKDF2 or HAS_PBKDF2HMAC
        
def check_module():
    if not HAS_AES or not HAS_COUNTER or not HAS_ANY_PBKDF2HMAC or not HAS_HASH:
        return False
    else :
        return True

from library.utils.type_conv import string2bytes, bytes2string, obj2bytes, obj2string


class AES256_Algorithm():
    def __init__(self, b_password):
        
        '''
        使用AES256加解密数据
        '''

        self.check_result = check_module()
        self.logger = logging.getLogger("security")
        self.b_password = string2bytes(b_password)
        self.err_msg = "可能您的python3环境中，pycrypto模块版本太低或者没有安装，请升级/安装，请SSH登陆到服务器上，执行pip3 install pycrypto或者pip3 install --upgrade pycrypto"
        

    @staticmethod
    def _create_key(b_password, b_salt, keylength, ivlength):
        hash_function = SHA256

        pbkdf2_prf = lambda p, s: HMAC.new(p, s, hash_function).digest()

        b_derivedkey = PBKDF2(
            b_password,
            b_salt,
            dkLen=(2 * keylength) + ivlength,
            count=10000,
            prf=pbkdf2_prf)
        return b_derivedkey


    @classmethod
    def _gen_key_initctr(cls, b_password, b_salt):
        # 16 for AES 128, 32 for AES256
        keylength = 32

        # match the size used for counter.new to avoid extra work
        ivlength = 16
        b_password = string2bytes(b_password)

        if HAS_PBKDF2HMAC:
            backend = default_backend()
            kdf = PBKDF2HMAC(
                algorithm=c_SHA256(),
                length=2 * keylength + ivlength,
                salt=b_salt,
                iterations=10000,
                backend=backend)
            b_derivedkey = kdf.derive(b_password)
        else:
            b_derivedkey = cls._create_key(
                b_password,
                b_salt,
                keylength,
                ivlength)

        b_key1 = b_derivedkey[:keylength]
        b_key2 = b_derivedkey[keylength:(keylength * 2)]
        b_iv = b_derivedkey[(keylength * 2):(keylength * 2) + ivlength]
        
        return b_key1, b_key2, hexlify(b_iv)


    def encrypt(self, data):
        if not self.check_result :
            self.logger.error('使用AES256解密加密数据失败，原因：' + self.err_msg)
            return (False, self.err_msg)
        
        if not self.b_password or self.b_password is None :
            return (False, "加密密码为空")
        
        data = obj2bytes(data)
        if data[0] :
            b_plaintext = data[1]
        else :
            return data
        
        b_salt = os.urandom(32)
        b_key1, b_key2, b_iv = self._gen_key_initctr(self.b_password, b_salt)

        bs = AES.block_size
        padding_length = (bs - len(data) % bs) or bs
        temp = obj2bytes(padding_length * chr(padding_length))
        if temp[0] :
            temp = temp[1]
        else :
            return temp
        
        b_plaintext += temp

        ctr = Counter.new(128, initial_value=int(b_iv, 16))

        cipher = AES.new(b_key1, AES.MODE_CTR, counter=ctr)

        b_ciphertext = cipher.encrypt(b_plaintext)

        hmac = HMAC.new(b_key2, b_ciphertext, SHA256)
        b_temp_ciphertext = b'\n'.join([hexlify(b_salt), string2bytes(hmac.hexdigest()), hexlify(b_ciphertext)])
        b_new_ciphertext = hexlify(b_temp_ciphertext)
        
        return self._handle_result(b_new_ciphertext)


    def decrypt(self, data):
        if not self.check_result :
            self.logger.error('使用AES256解密加密数据失败，原因：' + self.err_msg)
            return (False, self.err_msg)
        
        if not self.b_password or self.b_password is None :
            return (False, "加密密码为空")
        
        data = obj2bytes(data)
        if data[0] :
            data = data[1]
        else :
            return data
        
        ciphertext = unhexlify(data)
        b_salt, b_cryptedHmac, b_ciphertext = ciphertext.split(b"\n", 2)
        b_salt = unhexlify(b_salt)
        b_ciphertext = unhexlify(b_ciphertext)
        b_key1, b_key2, b_iv = self._gen_key_initctr(self.b_password, b_salt)

        hmacDecrypt = HMAC.new(b_key2, b_ciphertext, SHA256)
        if not self._is_equal(b_cryptedHmac, bytes2string(hmacDecrypt.hexdigest())):
            self.logger.error('使用AES256解密加密数据失败，原因：密码错误')
            return (False, "解密失败，密码错误")
        
        ctr = Counter.new(128, initial_value=int(b_iv, 16))
        cipher = AES.new(b_key1, AES.MODE_CTR, counter=ctr)

        b_plaintext = cipher.decrypt(b_ciphertext)

        padding_length = b_plaintext[-1]

        b_plaintext = b_plaintext[:-padding_length]
        return self._handle_result(b_plaintext)
        
        
    def _handle_result(self, data):
        new_data = obj2string(data)
        if new_data[0] :
            result = new_data[1]
        else :
            result = bytes2string(data)
        
        return (True, result)


    @staticmethod
    def _is_equal(b_a, b_b):
        b_b = string2bytes(b_b)
        b_a = string2bytes(b_a)
        
        if not (isinstance(b_a, bytes) and isinstance(b_b, bytes)):
            return False

        if len(b_a) != len(b_b):
            return False

        result = 0
        for b_x, b_y in zip(b_a, b_b):
            result |= b_x ^ b_y
            
        return result == 0
