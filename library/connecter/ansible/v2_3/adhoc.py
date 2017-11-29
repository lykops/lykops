import os
from ansible import constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.splitter import parse_kv
from ansible.playbook.play import Play
from ansible.plugins import get_all_plugin_loaders

from library.connecter.ansible.callback.write import Write_Storage
from library.connecter.ansible.v2_3 import Base
from library.storage.logging import Routing_Logging

class adhoc(Base):
    def run(self, inventory_content, pattern='all'):
        
        '''
        运行adhoc
        '''
        
        self.pattern = pattern
        self.inventory_content = inventory_content
        if not self.options.module_name :
            self.logger.error(self.log_prefix + '准备工作失败，原因：执行模块不能为空')
            return (False, '执行模块不能为空，请输入模块名')
        else: 
            if self.options.module_name in C.MODULE_REQUIRE_ARGS and not self.options.module_args :
                self.logger.error(self.log_prefix + '准备工作失败，原因：执行模块参数为空')
                return (False, '执行模块参数为空，请输入模块参数')

        for name, obj in get_all_plugin_loaders():
            name = name
            if obj.subdir:
                plugin_path = os.path.join('.', obj.subdir)
                if os.path.isdir(plugin_path):
                    obj.add_directory(plugin_path)
        
        self._gen_tasks()

        play = Play().load(self.tasks_dict, variable_manager=self.variable_manager, loader=self.loader)

        try :
            self.host_list = self.inventory.list_hosts(self.pattern)
        except :
            self.host_list = []
            
        if len(self.host_list) == 0 :
            self.logger.error(self.log_prefix + '准备工作失败，原因：没有匹配主机名')
            return (False, '执行失败，没有匹配主机名')
        
        self._loading_callback()
        
        self._tqm = None
        try:
            self._tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.callback,
                # run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
                # run_tree=False,
            )
            self._tqm.run(play)
        finally:
            if self._tqm:
                self._tqm.cleanup()
                
            if self.loader:
                self.loader.cleanup_all_tmp_files()

        self.logger.info(self.log_prefix + '发送成功')
        return True


    def _gen_tasks(self):
        '''
        生成tasks
        '''
        check_raw = self.options.module_name in ('command', 'win_command', 'shell', 'win_shell', 'script', 'raw')
        args = parse_kv(self.options.module_args, check_raw=check_raw)
        
        action_obj = {
            'module' :self.options.module_name,
            'args' : args
        }
        
        self.task_list = [{
            'action':action_obj,
            'async':self.options.seconds,
            'poll':self.options.poll_interval
            }]
        
        self.tasks_dict = {
            'name':self.work_name,
            'hosts':self.pattern,
            'gather_facts':'no',
            'tasks':self.task_list
        }


    def _loading_callback(self):
        if not self.log_router:
            self.log_router = Routing_Logging()
            
        self.callback = Write_Storage(
            self.work_uuid,
            self.work_name,
            self.username,
            self.exec_mode,
            self._show_protectfield(),
            self.inventory_content,
            self.describe,
            module_name=self.options.module_name,
            module_args=self.options.module_args,
            log_router=self.log_router,
            pattern=self.pattern,
            mongoclient=self.mongoclient
            )
        if self.callback:
            self.logger.info(self.log_prefix + '使用程序自己编写的callback函数')
            pass
        elif self.options.one_line:
            self.callback = 'oneline'
        else:
            self.callback = 'minimal'
