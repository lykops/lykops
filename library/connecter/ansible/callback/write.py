import time
from ansible.plugins.callback import CallbackBase
from library.storage.logging import Routing_Logging
from library.utils.time_conv import timestamp2datetime


class Write_Storage(CallbackBase):

    '''
    实现回调信息写入MongoDB等后端，进行持久化
    '''
    
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'storage'

    def __init__(self, work_uuid, work_name, oper, exec_mode, options, inventory_content, describe, yaml_content='', log_router=None, module_name=None, module_args=None, pattern=None , display=None, mongoclient=None):
        
        '''
        实现回调信息写入MongoDB等后端，进行持久化
        :parm
            work_name：工作名称
            oper:操作者
            op_mode：操作类型，adhoc、playbook等
            prov_parm：用户提供的参数，对机密数据进行简单处理
            handled_para：用户提供的参数处理后的数据
            yamlfile：yaml文件，仅局限于playbook
            log_router：写入日志路由
            yamldata：yaml文件数据
        '''

        if not log_router:
            self.log_router = Routing_Logging(mongoclient=mongoclient)
        else :
            self.log_router = log_router
            
        self.work_uuid = work_uuid
        self.work_name = work_name
        self.exec_mode = exec_mode
        self.oper = oper
        self.yaml_content = yaml_content
        self.pattern = pattern
        self.module_name = module_name
        self.module_args = module_args
        self.options = options
        self.inventory_content = inventory_content
        self.result = {
            'mode' : self.exec_mode,
            'name' : self.work_name,
            'uuid' : self.work_uuid,
            'describe' : describe,
            'create_date' : timestamp2datetime(stamp=time.time() , fmt='%Y-%m-%d'),
            'create_time' : timestamp2datetime(stamp=time.time() , fmt='%Y-%m-%d %H:%M'),
            'options':self.options,
            'inventory_content': self.inventory_content,
            'create_ts': round(time.time(), 3),
            }
        
        if self.exec_mode == 'adhoc' :
            self.result['pattern'] = self.pattern
            self.result['module_name'] = self.module_name
            self.result['module_args'] = self.module_args
            
        if self.exec_mode == 'playbook' :
            self.result['yaml_content'] = self.yaml_content
        
        self.log_dict = { 
            'level':'info',
            'dest' : 'mongo',
            'mongo' : self.oper + '.ansible.callback',
            }
        super(Write_Storage, self).__init__(display)


    def v2_playbook_on_play_start(self, play): 
        self.result['play'] = {
            'name': play.name,
            'id': str(play._uuid),
        }
        self.result['play_id'] = str(play._uuid)
        self.log_router.write(self.result, self.oper, log_dict=self.log_dict)
        

    def v2_playbook_on_task_start(self, task, is_conditional):
        if self.exec_mode == 'adhoc' :
            # taskname = self.work_name
            taskname = str(task)
        elif self.exec_mode == 'playbook' :
            taskname = task.name
        
        args_dict = task.args
        
        self.result['task'] = {
            'name': taskname,
            'module' : task.action,
            'args' : args_dict,
            # 请看ansible/lib/ansible/plugins/strategy/linear.py
            'id': str(task._uuid),
            'start_ts' : round(time.time(), 3),
        }
        self.result['task_id'] = str(task._uuid)
        self.result['detail'] = {}
        self.log_router.write(self.result, self.oper, log_dict=self.log_dict)
        

    def v2_runner_on_ok(self, result, **kwargs):
        host = result._host
        hstnm = host.get_name()
        self.result['detail'][hstnm] = result._result
        self.result['detail'][hstnm]['start_ts'] = self.result['task']['start_ts']
        self.result['detail'][hstnm]['end_ts'] = round(time.time(), 3)
        self.result['finish_ts'] = round(time.time(), 3)
        self.log_router.write(self.result, self.oper, log_dict=self.log_dict)


    def v2_playbook_on_no_hosts_matched(self):
        self.result['finish_ts'] = round(time.time(), 3)
        self.result['stats'] = '没有匹配的主机'
        self.log_router.write(self.result, self.oper, log_dict=self.log_dict)


    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())

        summary = {}
        for h in hosts:
            s = stats.summarize(h)
            summary[h] = s
            
        self.result['summary'] = summary
        self.result['finish_ts'] = round(time.time(), 3)
        self.log_router.write(self.result, self.oper, log_dict=self.log_dict)


    v2_runner_on_failed = v2_runner_on_ok
    v2_runner_on_unreachable = v2_runner_on_ok
    v2_runner_on_skipped = v2_runner_on_ok
