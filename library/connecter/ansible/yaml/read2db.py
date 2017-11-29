import time, re

from library.connecter.ansible.yaml import Yaml_Base
from library.utils.type_conv import random_str

class Read_DB(Yaml_Base):
    def write_file(self, word, word_field='name', this_path='', yaml_type='main'):
        
        '''
        从mongo中读取数据后，写入临时文件
        :parm
            word：关键字
            word_field：根据那个字段（name或者this_path）去关键字
            this_path：写入的目录，如果提供按照指定目录写入，如果不指定随机目录
            yaml_type：yaml类型。main、include、roles、full_roles四种
        '''
        
        if not this_path or not re.search('^/', this_path):
            this_path = self.temp_basedir + '/' + random_str() + str(int(time.time())) + '/'

        result = self.read2db(word, word_field=word_field, yaml_type=yaml_type)
        if result[0] : 
            try :
                content = result[1]['content']
                yaml_type = result[1]['type']
                name = result[1]['name']
            except :
                self.logger.error('通过关键字从数据库中搜索并读取数据失败，原因：数据写入数据库时出现错误')
                return (False, '数据写入数据库时出现错误')
        else :
            return result

        result = self.data2file(content, this_path, yaml_type=yaml_type, name=name)
        return result
