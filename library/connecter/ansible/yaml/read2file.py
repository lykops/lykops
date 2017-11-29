import os

from library.connecter.ansible.yaml import Yaml_Base
from library.utils.file import read_file
from library.utils.path import get_pathlist

    
class Read_File(Yaml_Base):
    def router(self, this_path, this_basedir=None, yaml_tpye='main', preserve=True, together=False, name='', describe=''):
                
        '''
        
        检测来自文件的yaml语法等是否正确的路由器
        :参数
            filename：文件
            name：名称
            this_basedir：目录
            yaml_tpye：yaml文件类型
            preserve：是否写入数据库
            together：是否返回该main下所有文件内容
            name：yaml文件内容写入数据的名称
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        :return
            元组，第一个为执行结果，
                成功为true，文件内容（格式为字典）)
                失败为False，返回失败原因
        '''
        
        if yaml_tpye in ('full_roles' , 'main') :
            result = self.main(this_path, preserve=preserve, together=together, name=name, describe=describe)
        elif yaml_tpye == 'include' :
            result = self.include(this_path, this_basedir=this_basedir, file_type='tasks', preserve=preserve, name=name, describe=describe)
        elif yaml_tpye == 'roles' :
            result = self.roles(this_path, this_basedir=this_basedir, preserve=preserve, together=together, name=name, describe=describe)
        else :
            self.logger.error('检测yaml文件的语法失败，原因：参数yaml_data' + yaml_tpye + '不是接受值，只能接受full_roles、main、include、roles')
            return (False, '参数yaml_data' + yaml_tpye + '不是接受值，只能接受full_roles、main、include、roles')
        
        return result
    
    
    def main(self, filename, preserve=True, together=False, name='', describe=''):
                
        '''
        检测main文件的语法等是否正确，如果含有include或/和roles，会逐个检查
        include：只能为相对路径
        roles：只能为字母和数字组合
        :参数
            filename：文件
            name：名称
            preserve：是否写入数据库
            together：是否返回该main下所有文件内容
            name：yaml文件内容写入数据的名称
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        :return
            元组，第一个为执行结果，
                成功为true，文件内容（格式为字典）)
                失败为False，返回失败原因
        '''

        if preserve and together:
            sub_preserve = False
        else :
            sub_preserve = preserve

        result = self.yaml_loader(filename)
        if result[0] :
            (filename, content, yaml_data) = result[1:]
        else :
            self.logger.error('检测yaml文件' + filename + '类型为full_roles或者main语法失败，转化成yaml数据时失败，原因：' + result[1])
            return (False, '文件' + filename + '转化成yaml数据时失败，' + result[1])
            
        result = self.check_main(yaml_data)
        if result[0] :
            (roles_list, includefile_dict) = result[1:]
        else :
            self.logger.error('检测yaml文件' + filename + '类型为full_roles或者main语法失败，通过yaml语法检测，原因：' + result[1])
            return (False, '文件' + filename + '未通过yaml语法检测，' + result[1]) 

        this_basedir = os.path.dirname(filename)
        include_content = {}
        roles_content = {}
        
        for file, file_type in includefile_dict.items() : 
            result = self.include(file, this_basedir=this_basedir, file_type=file_type, preserve=sub_preserve)
            if not result[0] :
                self.logger.error('检测yaml文件' + filename + '类型为full_roles或者main语法失败，通过yaml语法检测，原因：' + result[1])
                return (False, '文件' + filename + '中的include文件名为' + file + '未通过yaml语法检测，' + result[1]) 
            else :
                file = os.path.basename(file)
                include_content.update({file:result[1]})
            
        for roles in roles_list :
            result = self.roles(roles, this_basedir=this_basedir, preserve=sub_preserve, together=together)
            if result[0] :
                include_content.update(result[2])
                roles = os.path.basename(roles)
                roles_content.update({roles:result[1]})
            else :
                self.logger.error('检测yaml文件' + filename + '类型为full_roles或者main语法失败，roles名为' + roles + '未通过yaml语法检测，原因：' + result[1])
                return (False, '文件' + filename + '中的roles名为' + roles + '未通过yaml语法检测，' + result[1]) 
            
        data = {
            'main' : content,
            'include': include_content,
            'roles': roles_content,
            }
            
        if preserve :
            result = self.write2db(name, data, 'main', describe=describe)
            if not result[0] :
                self.logger.error('检测yaml文件' + filename + '类型为full_roles或者main语法失败，通过yaml语法检测，但无法写入数据库，原因：' + result[1])
                return (False, '文件' + filename + '通过yaml语法检测，但无法写入数据库' + result[1]) 
    
        self.logger.info('检测yaml文件' + filename + '类型为full_roles或者main语法成功')
        if together :
            return (True, data)
        else :
            return (True, content)
    
    
    def include(self, file, this_basedir=None, file_type='main', preserve=True, name='', describe=''):
                
        '''
        检测include文件的语法等是否正确
        :参数
            this_basedir：引用该文件的上级目录
            file：文件
            this_path：引用时的路径
            file_type：类型
            preserve：是否写入数据库
            name：yaml文件内容写入数据的名称
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        :return
            元组，第一个为执行结果，
                成功为true，include文件内容（格式为字典，可能为空）)
                失败为False，返回失败原因
        '''

        if file_type not in ('main', 'tasks', 'var') :
            self.logger.error('检测yaml文件' + file + '类型为include语法失败，参数file_type错误')
            return (False, '参数file_type错误')

        result = self._isinclude(file)
        if not result[0] :
            self.logger.error('检测yaml文件' + file + '类型为include语法失败，参数file_type错误，原因：' + result[1])
            return result

        if this_basedir is None or not this_basedir :
            filename = file
        else :
            try :
                filename = this_basedir + '/' + file
            except :
                filename = file
        
        result = self.yaml_loader(filename)
        if result[0] :
            (content, yaml_data) = result[2:]
        else :
            self.logger.error('检测yaml文件' + file + '类型为include语法失败，转化为yaml数据时失败，原因：' + result[1])
            return (False, result[1])

        result = self.check_include(yaml_data, file_type=file_type)
        if not result[0] :
            self.logger.error('检测yaml文件' + file + '类型为include语法失败，语法检测未通过，原因：' + result[1])
            return (False, result[1])

        if preserve :
            result = self.write2db(name, content, 'include', describe=describe)
            if not result[0] :
                self.logger.error('检测yaml文件' + file + '类型为include语法失败，但无法写入数据库，原因：' + result[1])
                return (False, '无法写入数据库' + result[1]) 
            
        self.logger.info('检测yaml文件' + filename + '类型为include语法成功')
        return (True, content)
           

    def roles(self, roles_path, this_basedir=None, preserve=True, together=False, name='', describe=''):
        
        '''
        检测单个roles的语法等是否正确
        :参数
            this_basedir：引用该roles的main文件的上级目录，例如/opt/lykops/example/ansible/roles/nginx/main.yaml引用一个roles，那么该值为/opt/lykops/example/ansible/roles/nginx/
            roles_path：引用该roles的main文件写的roles路径
            preserve：是否写入数据库
            together：是否返回该roles下所有文件内容
            name：yaml文件内容写入数据的名称
            describe：yaml文件内容写入数据的描述
            zhname：yaml文件内容写入数据的中文名称，很简短说明
        :return
            元组，第一个为执行结果，
                成功为true，返回内容为(True,roles下所有文件内容（格式为字典，可能为空）, roles下所有文件中include文件内容（格式为字典，可能为空）)
                失败为False，返回失败原因
        '''

        content_dict = {}
        
        if preserve and together:
            sub_preserve = False
        else :
            sub_preserve = preserve
        
        if not name :
            name = roles_path
        
        result = self._isrolesname(name)
        if not result :
            self.logger.error('检测yaml文件roles名为' + roles_path + '失败，roles名不符合本系统要求的，注：虽然原生ansible支持这样写')
            return (False, '语法错误，roles名不符合本系统要求的，注：虽然原生ansible支持这样写')
        else :
            if this_basedir is None or not this_basedir:
                this_roles_path = roles_path
            else :
                try :
                    this_roles_path = this_basedir + '/roles/' + roles_path
                except :
                    this_roles_path = roles_path
        
        include_content = {}   
        for this_dir in ('tasks', 'vars', 'handlers', 'meta', 'defaults') :
            yaml_file = this_roles_path + '/' + this_dir + '/main.yaml'
            result = read_file(yaml_file)
            if not result[0] :
                if this_dir == 'tasks' :
                    self.logger.error('检测yaml文件roles名为' + roles_path + '失败，' + this_dir + '/main.yaml不存在')
                    return (False, this_dir + '/main.yaml不存在')
                continue
            else :
                content_dict[this_dir] = result[1]
            
        temp_dir = this_roles_path + '/templates/'
        content_dict['templates'] = {}
        result = get_pathlist(temp_dir, get_death=0, max_size=4 * 1024 * 1024)
        if result[0] :
            temp_list = result[1]
            for temp in temp_list :
                result = read_file(temp)
                if result[0] :
                    temp_file = os.path.basename(temp)
                    content_dict['templates'][temp_file] = result[1]
        
        if not content_dict['templates'] :
            del content_dict['templates']
                
        result = self.check_roles(content_dict)
        if result[0] :
            includefile_dict = result[1]
            for file, file_type in includefile_dict.items() :
                result = self.include(file, this_basedir=this_basedir, file_type=file_type, preserve=sub_preserve)
                if not result[0] :
                    self.logger.error('检测yaml文件roles名为' + roles_path + '失败，roles包含的include文件' + file + '未通过语法检测，原因：' + result[1])
                    return (False, 'roles包含的include文件' + file + '未通过语法检测，' + result[1])
                else :
                    include_content.update({file:result[1]})
        else :
            self.logger.error('检测yaml文件roles名为' + roles_path + '失败，' + this_dir + '/main.yaml语法错误，原因：' + result[1])
            return (False, this_dir + '/main.yaml语法错误，' + result[1])

        data = {
            'main' : {},
            'include': include_content,
            'roles': {name:content_dict},
            }
        
        if preserve :
            result = self.write2db(name, data, 'roles', describe=describe)
            if not result[0] :
                self.logger.error('检测yaml文件roles名为' + roles_path + '失败，无法写入数据库，' + result[1])
                return (False, '无法写入数据库，' + result[1]) 
            
        self.logger.info('检测yaml文件roles名为' + roles_path + '成功')
        if together :
            return (True, content_dict, include_content)
        else :
            return (True, {}, {})
