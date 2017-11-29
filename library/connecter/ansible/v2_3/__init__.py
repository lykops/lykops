from collections import namedtuple, OrderedDict
import os, time, uuid, logging

from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.utils.vars import load_extra_vars
from ansible.utils.vars import load_options_vars
from ansible.vars import VariableManager

from library.connecter.database.mongo import Op_Mongo
from library.storage.logging import Routing_Logging
from library.utils.file import write_file, read_file, write_random_file
from library.utils.path import make_dir
from library.utils.time_conv import timestamp2datetime
from library.utils.type_conv import list2string, dict2string, string2bytes, random_str

class Base():
    def __init__(self, exec_mode, work_name, username, options_dict, describe, mongoclient=None):
        '''
        ansible的基类，为adhoc、playbook等父类
        :parm:
            exec_mode:ansible工作类型，接受adhoc、palybook等
            work_name:该任务的名称，用于日志
            username:执行者
            options_dict:该任务的特定设置
            mongoclient：初始化mongo连接类
        '''
        
        self.logger = logging.getLogger("ansible")
        if exec_mode in ('adhoc', 'playbook') :
            self.exec_mode = exec_mode
        else :
            self.logger.warn('正在准备执行ansible任务，准备工作失败，原因：参数exec_mode必须是adhoc或者是playbook')
            return (False, '参数exec_mode必须是adhoc或者是playbook')

        if isinstance(work_name, str) and work_name:
            self.work_name = work_name
        else :
            self.logger.warn('正在准备执行ansible任务，准备工作失败，原因：参数work_name必须是非字符串')
            return (False, '参数work_name必须是非字符串')

        if isinstance(username, str) and username:
            self.username = username
        else :
            self.logger.warn('正在准备执行ansible任务，准备工作失败，原因：参数username必须是非字符串')
            return (False, '参数username必须是非字符串')

        if isinstance(options_dict, dict) and options_dict:
            self.options_dict = options_dict
        else :
            self.logger.warn('正在准备执行ansible任务，准备工作失败，原因：参数options_dict必须是非空字典')
            return (False, '参数options_dict必须是非空字典')
        
        if mongoclient is None :
            self.mongoclient = Op_Mongo()
        else :
            self.mongoclient = mongoclient

        self.work_uuid = str(uuid.uuid4())
        self.log_router = Routing_Logging()
        self.describe = describe

        if exec_mode == 'adhoc' :
            self.log_prefix = '正在执行用户' + username + '的名为' + work_name + 'uuid为' + self.work_uuid + '的ansible临时任务，'
        else : 
            self.log_prefix = '正在执行用户' + username + '的名为' + work_name + 'uuid为' + self.work_uuid + '的ansible-playbook任务，'

        # 下面是加载和初始化相关类
        self._parse_options()   
        self.passwords = {'conn_pass':self.options.ask_pass, 'become_pass':self.options.become_ask_pass}
        # 设置passwords
        self.inventory_file = self.options_dict.get('inventory', '')
        
        self.loader = DataLoader()
        self._get_vault_pwd()
        self.variable_manager = VariableManager()
        self.variable_manager.extra_vars = load_extra_vars(loader=self.loader, options=self.options)
        self.variable_manager.options_vars = load_options_vars(self.options)

        self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager, host_list=self.inventory_file)
        self.variable_manager.set_inventory(self.inventory)
        self.inventory.subset(self.options.subset)


    def _get_vault_pwd(self):
        
        '''
        获取vault密码，并初始化vault密码
        '''
        
        vault_pwd_file = self.options_dict.get('vault_password_file', False)
        ask_vault_pass = self.options_dict.get('ask_vault_pass', False)
            
        if ask_vault_pass:
            vault_password = ask_vault_pass
        else :
            if vault_pwd_file:
                this_path = os.path.realpath(os.path.expanduser(vault_pwd_file))
                if os.path.exists(this_path):
                    mode = self.loader.is_executable(this_path)
                    result = read_file(this_path, mode=mode, sprfmt=b'\r\n', outfmt='bytes')
                    if result[0]:
                        vault_password = result[1]
                    else :
                        vault_password = None
                else :
                    vault_password = None
            else :
                vault_password = None
             
        if vault_password :
            b_vault_password = string2bytes(vault_password)
            self.loader.set_vault_password(b_vault_password)
            self.vault_password = vault_password
        else :
            self.vault_password = None
            
          
    def _parse_options(self):
        '''
        获取options字典
        '''

        keys_list = []
        values_list = []
        for key, value in self.options_dict.items() :
            keys_list.append(key)
            values_list.append(value)

        Options = namedtuple('Options', keys_list)
        self.options = Options._make(values_list)


    def _show_protectfield(self):
        protectfield_list = ['ask_pass' , 'ask_su_pass' , 'ask_sudo_pass' , 'ask_vault_pass' , 'become_ask_pass' , 'new_vault_password_file' , 'vault_password_file', 'private_key_file' , ]

        log_options = {}
        for field in self.options_dict :
            if field in protectfield_list :
                log_options[field] = '***hidden***'
            else :
                log_options[field] = self.options_dict[field]
        
        return log_options

