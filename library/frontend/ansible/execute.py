from library.connecter.ansible.yaml.read2db import Read_DB
from library.connecter.ansible.yaml.read2file import Read_File
from library.frontend import Base
from library.frontend.ansible.options import Manager_Option
from library.frontend.sysadmin.inventory import Manager_Inventory
from library.utils.yaml import yaml_loader, yaml_dumper


class Exec_Tasks(Base):

    def adhoc(self, username, name, vault_password, pattern_list, module_name, module_args, describe):
        inve_api = Manager_Inventory(mongoclient=self.mongoclient, redisclient=self.redisclient)
        option_api = Manager_Option(mongoclient=self.mongoclient, redisclient=self.redisclient)
        result = inve_api.write_file(username, vault_password, group_list=pattern_list)
        if not result[0] :
            self.logger.error('用户' + username + '构建名为' + name + '的ansible临时任务失败，主机列表写入文件时出错，原因：' + result[1])
            return (False, '主机列表写入文件时出错，' + result[1])
        else :
            inve_file = result[1]
            inve_protect_content = result[2]
            
        result = option_api.exec_gen(username, vault_password, 'adhoc')
        if not result[0] :
            self.logger.error('用户' + username + '构建名为' + name + '的ansible临时任务失败，在组装option时出错，原因：' + result[1])
            return (False, '在组装option时出错，原因：' + result[1])
        else :
            option_dict = result[1]
            
        option_dict['inventory'] = inve_file
        option_dict['module_name'] = module_name
        option_dict['module_args'] = module_args

        from lykops.tasks import ansible_send_adhoc
        result = ansible_send_adhoc.delay(name, username, option_dict, describe, inve_protect_content)
        self.logger.info('用户' + username + '构建名为' + name + '的ansible临时任务成功，并发送给后台执行')
        return (True, '')


    def playbook(self, username, name, vault_password, pattern_list, uuidstr, describe):
        yaml_read2db_api = Read_DB(username, vault_passwd=vault_password, mongoclient=self.mongoclient)
        yaml_result = yaml_read2db_api.read2db(uuidstr, word_field='uuid')
        if yaml_result[0] :
            try :
                content_dict = yaml_result[1]['content']
                main_content = content_dict['main']
                if not main_content :
                    self.logger.error('用户' + username + '构建名为' + name + '的ansible playbook任务失败，原因：没有main.yaml文件')
                    return (False, '没有main.yaml文件')
                
                result = yaml_loader(main_content, data_type='data')
                if not result[0] :
                    self.logger.error('用户' + username + '构建名为' + name + '的ansible playbook任务失败，将main.yaml转化为yaml格式时出错，原因：' + result[1])
                    return (False, '将mail.yaml转化为yaml格式时出错，' + result[1])
                
                yaml_list = result[1]
                new_list = []
                for yaml_dict in yaml_list :
                    yaml_dict['hosts'] = 'all'
                    new_list.append(yaml_dict)
                    
                result = yaml_dumper(new_list)
                if not result[0] :
                    self.logger.error('用户' + username + '构建名为' + name + '的ansible playbook任务失败，更换main.yaml中的主机组时出错，原因：' + result[1])
                    return (False, '更换main.yaml中的主机组时出错，原因：' + result[1])
                    return result
                
                content_dict['main'] = result[1]
            except Exception as e:
                print(e)
                self.logger.error('用户' + username + '构建名为' + name + '的ansible playbook任务失败，更换main.yaml中的主机组时出错，原因：' + str(e))
                return (False, '更换main.yaml中的主机组时出错' + str(e))
        else :
            self.logger.error('用户' + username + '构建名为' + name + '的ansible playbook任务失败，读取yaml数据时出错，原因：' + yaml_result[1])
            return (False, '读取yaml数据时出错，' + result[1])
        # 替换掉yaml文件中的hosts
        
        result = yaml_read2db_api.data2file(content_dict, yaml_type='main')
        if not result[0] :
            return result
        # 写入文件
        
        this_path = result[1]
        main_file = this_path + '/main.yaml'
        
        inve_api = Manager_Inventory(mongoclient=self.mongoclient, redisclient=self.redisclient)
        option_api = Manager_Option(mongoclient=self.mongoclient, redisclient=self.redisclient)
        yaml_read2db_api = Read_DB(username, vault_passwd=vault_password, mongoclient=self.mongoclient)
        read2file_api = Read_File(username, vault_passwd=vault_password, mongoclient=self.mongoclient)
        result = read2file_api.main(main_file, preserve=False)
        if not result[0] :
            self.logger.error('用户' + username + '构建名为' + name + '的ansible playbook任务失败，yaml数据写入文件时出错，原因：' + result[1])
            return (False, 'yaml数据写入文件时出错，' + result[1])
                
        result = inve_api.write_file(username, vault_password, group_list=pattern_list)
        if not result[0] :
            self.logger.error('用户' + username + '构建名为' + name + '的ansible playbook任务失败，主机列表写入文件时出错，原因：' + result[1])
            return (False, '主机列表写入文件时出错，' + result[1])
        else :
            inve_file = result[1]
            inve_protect_content = result[2]
        # inventory数据写入文件
        
        result = option_api.exec_gen(username, vault_password, 'playbook')
        if not result[0] :
            self.logger.error('用户' + username + '构建名为' + name + '的ansible临时任务失败，在组装option时出错，原因：' + result[1])
            return (False, '在组装option时出错，原因：' + result[1])
        else :
            option_dict = result[1]
            
        option_dict['inventory'] = inve_file
        # 获取option数据
        
        from lykops.tasks import ansible_send_playbook
        result = ansible_send_playbook.delay(name, username, option_dict, describe, inve_protect_content, main_file, vault_password) 
        self.logger.info('用户' + username + '构建名为' + name + '的ansible playbook任务成功，并发送给后台执行')
        return (True, '')

