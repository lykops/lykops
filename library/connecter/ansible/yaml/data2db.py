import os

from library.connecter.ansible.yaml import Yaml_Base

class Data_DB(Yaml_Base):
    def router(self, content, name, yaml_tpye='main', file_type='tasks', preserve=True, together=False, describe=''):
                
        '''
        检测yaml数据的语法是否正确，如果含有include或/和roles，将把这些存储在后端数据库中
        :参数
            content：内容
            name：名称，yaml文件内容写入数据的名称
            preserve：是否写入数据库
            together：是否返回该main下所有文件内容=
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        :return
            元组，第一个为执行结果，
                成功为true，文件内容（格式为字典）)
                失败为False，返回失败原因
        '''
        
        if yaml_tpye in ('full_roles' , 'main') :
            result = self.main(content, name, preserve=preserve, together=together, describe=describe)
        elif yaml_tpye == 'include' :
            result = self.include(content, name, file_type=file_type, preserve=preserve, describe=describe)
        elif yaml_tpye == 'roles' :
            result = self.roles(content, name, preserve=preserve, together=together, describe=describe)
        else :
            self.logger.error('动作：检测yaml数据的语法是否正确并将把这些存储在后端数据库中，执行结果：失败，原因：参数yaml_data' + yaml_tpye + '不是接受值，只能接受full_roles、main、include、roles')
            return (False, '参数yaml_data' + yaml_tpye + '不是接受值，只能接受full_roles、main、include、roles')
        
        return result

    
    def main(self, content, name, preserve=True, together=False, describe=''):
                
        '''
        main文件的语法等是否正确，如果含有include或/和roles，将认为这些存储在后端数据库中
        :参数
            content：内容
            name：名称，yaml文件内容写入数据的名称
            preserve：是否写入数据库
            together：是否返回该main下所有文件内容=
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        :return
            元组，第一个为执行结果，
                成功为true，文件内容（格式为字典）)
                失败为False，返回失败原因
        '''

        result = self.yaml_loader(content, data_type='data')
        if result[0] :
            (content, yaml_data) = result[2:]
        else :
            self.logger.error('检测yaml数据名为' + name + '类型为full_roles或者main的语法失败，转化成yaml数据时失败，原因：' + result[1])
            return (False, '转化成yaml数据时失败，' + result[1])
            
        result = self.check_main(yaml_data)
        self.logger.error(result)
        if result[0] :
            (roles_list, includefile_dict) = result[1:]
        else :
            self.logger.error('检测yaml数据名为' + name + '类型为full_roles或者main的语法失败，未通过yaml语法检测，原因：' + result[1])
            return (False, '未通过yaml语法检测，' + result[1]) 

        include_content_dict = {}
        roles_content_dict = {}

        for file in includefile_dict : 
            result = self.read2db(file, word_field='name')
            if not result[0] :
                self.logger.error('检测yaml数据名为' + name + '类型为full_roles或者main的语法失败，名为' + file + '的include查询出错，原因：' + result[1])
                return (False, '名为' + file + '的include查询出错，' + result[1]) 
            else :
                try :
                    include_content = result[1]['content']
                    include_content_dict.update({file:include_content})
                except :
                    self.logger.error('检测yaml数据名为' + name + '类型为full_roles或者main的语法失败，名为' + file + '的include查询出错，原因：查询结果不含content字段')
                    return (False, '名为' + file + '的include查询出错，查询结果不含content字段') 
                
        for roles in roles_list :
            result = self.read2db(roles, word_field='name')
            if result[0] :
                try :
                    content_dict = result[1]['content']
                    if 'include' in content_dict :
                        include_content.update(content_dict['include'])
                        
                    roles_content_dict.update({roles:content_dict['roles']})
                except :
                    self.logger.error('检测yaml数据名为' + name + '类型为full_roles或者main的语法失败，名为' + roles + '的roles查询出错，查询结果不含content字段')
                    return (False, '名为' + roles + '的roles查询出错，查询结果不含content字段') 
            else :
                return (False, '名为' + roles + '的roles查询出错，' + result[1]) 
            
        data = {
            'main' : content,
            'include': include_content_dict,
            'roles': roles_content_dict,
            }
            
        if preserve :
            result = self.write2db(name, data, 'main', describe=describe) 
            if not result[0] :
                self.logger.error('检测yaml数据名为' + name + '类型为full_roles或者main的语法失败，通过yaml语法检测，但无法写入数据库，原因：' + result[1])
                return (False, '通过yaml语法检测，但无法写入数据库' + result[1]) 
    
        self.logger.info('检测yaml数据名为' + name + '类型为full_roles或者main语法成功')
        if together :
            return (True, data)
        else :
            return (True, content)
    
    
    def include(self, content, name, file_type='main', preserve=True, describe=''):

        '''
        main文件的语法等是否正确，如果含有include或/和roles，将认为这些存储在后端数据库中
        :参数
            content：内容
            name：名称，yaml文件内容写入数据的名称
            preserve：是否写入数据库
            file_type：类型
            together：是否返回该main下所有文件内容=
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        :return
            元组，第一个为执行结果，
                成功为true，文件内容（格式为字典）)
                失败为False，返回失败原因
        '''

        result = self.yaml_loader(content, data_type='data')
        if result[0] :
            (content, yaml_data) = result[2:]
        else :
            self.logger.error('检测yaml数据名为' + name + '类型为include的语法失败，转化成yaml数据时失败，原因：' + result[1])
            return (False, '转化成yaml数据时失败，' + result[1])
            
        result = self.check_include(yaml_data, file_type=file_type)
        if not result[0] :
            self.logger.error('检测yaml数据名为' + name + '类型为include的语法失败，未通过yaml语法检测，原因：' + result[1])
            return (False, '未通过yaml语法检测，' + result[1]) 
            
        if preserve :
            result = self.write2db(name, content, 'include', describe=describe)
            if not result[0] :
                self.logger.error('检测yaml数据名为' + name + '类型为include的语法失败，但无法写入数据库，原因：' + result[1])
                return (False, '通过yaml语法检测，但无法写入数据库' + result[1]) 
            
        self.logger.info('检测yaml数据名为' + name + '类型为include语法成功')
        return (True, content)
           

    def roles(self, content, name, preserve=True, together=False, describe=''):
                
        '''
        main文件的语法等是否正确，如果含有include或/和roles，将认为这些存储在后端数据库中
        :参数
            content：内容
            name：名称，yaml文件内容写入数据的名称
            preserve：是否写入数据库
            together：是否返回该main下所有文件内容
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        :return
            元组，第一个为执行结果，
                成功为true，文件内容（格式为字典）)
                失败为False，返回失败原因
        '''

        content_dict = {}
        
        result = self._isrolesname(name)
        if not result :
            self.logger.error('检测yaml数据名为' + name + '类型为roles的语法失败，未通过语法检测，原因：roles名不符合本系统要求的，注：虽然原生ansible支持这样写')
            return (False, '未通过yaml语法检测，roles名不符合本系统要求的，注：虽然原生ansible支持这样写')
        
        if not isinstance(content, dict) :
            self.logger.error('检测yaml数据名为' + name + '类型为roles的语法失败，未通过语法检测，原因：参数content必须是字典格式')
            self.logger.error('roles名为' + str(name) + '未通过语法检测，原因：参数content必须是字典格式')
            return (False, '未通过yaml语法检测，参数content必须是字典格式')

        result = self.check_roles(content)
        include_content_dict = {}
        if result[0] :
            includefile_dict = result[1]
            for file in includefile_dict:
                result = self.read2db(file, word_field='name')
                if not result[0] :
                    self.logger.error('检测yaml数据名为' + name + '类型为roles的语法失败，未通过语法检测，原因：' + 'include名为' + file + '的include查询出错，' + result[1])
                    return (False, '未通过yaml语法检测，名为' + file + '的include查询出错，' + result[1]) 
                else :
                    try :
                        include_content = result[1]['content']
                        include_content_dict.update({file:include_content})
                    except :
                        self.logger.error('检测yaml数据名为' + name + '类型为roles的语法失败，未通过语法检测，原因：' + '名为' + file + '的include查询出错，查询结果不含content关键字段')
                        return (False, '未通过yaml语法检测，名为' + file + '的include查询出错，查询结果不含content关键字段') 
        else :
            self.logger.error('检测yaml数据名为' + name + '类型为roles的语法失败，未通过yaml语法检测，语法错误，原因：' + result[1])
            return (False, '未通过yaml语法检测，语法错误，' + result[1])

        if 'templates' in content :
            temp_content = content['templates']
            if not isinstance(temp_content, dict) :
                self.logger.error('检测yaml数据名为' + name + '类型为roles的语法失败，未通过yaml语法检测，templates查询错误，查询结果的数据类型不为字典')
                return (False, '未通过yaml语法检测，templates查询错误，查询结果的数据类型不为字典')
            
            content_dict['templates'] = {}
            for temp_file , tempfile_content in temp_content.items() :
                temp_file = os.path.basename(temp_file)
                content_dict['templates'][temp_file] = tempfile_content
                
        data = {
            'main' : {},
            'include': include_content_dict,
            'roles': content_dict,
            }
        
        if preserve :
            result = self.write2db(name, data, 'roles', describe=describe)
            if not result[0] :
                self.logger.error('检测yaml数据名为' + name + '类型为roles的语法失败，通过yaml语法检测，无法写入数据库，' + result[1])
                return (False, '通过yaml语法检测，无法写入数据库，' + result[1]) 
            
        self.logger.error('检测yaml数据名为' + name + '类型为roles的语法成功')
        if together :
            return (True, content_dict, include_content)
        else :
            return (True, {}, {})
