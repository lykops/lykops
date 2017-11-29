import logging
from library.connecter.database.mongo import Op_Mongo
from library.utils.time_conv import timestamp2datetime


class Parse_Cblog():
    def __init__(self, oper, log_router=False, mongoclient=None):
        
        '''
        根据condition_dict读取所有的callback日志
        :parm
            condition_dict:查询条件
        '''
        
        self.logger = logging.getLogger("ansible")
        if mongoclient is None :
            self.mongoclient = Op_Mongo()
        else :
            self.mongoclient = mongoclient
            
        if not log_router:
            from library.storage.logging import Routing_Logging
            log_router = Routing_Logging()
        
        self.log_router = log_router
        self.collect = oper + '.ansible.callback'
        self.log_dict = { 
            'level':'info',
            'dest' : 'mongo',
            'mongo' : self.collect,
            }
        

    def parse(self, uuid_str):
        
        '''
        根据uuid_str读取callback日志
        '''
        
        log_prefix = '查询uuid为' + uuid_str + '的ansible任务执行报表'
        result = self.log_router.read(condition_dict={'uuid':uuid_str}, log_dict=self.log_dict, limit=0, lastest_field=False)
        self.readlog_list = result[1]
        if not result[0] :
            self.logger.error(log_prefix + '失败，原因：' + result[1])
            return (False, log_prefix + '失败，' + result[1])
        
        try :
            name = self.readlog_list[0]['name']
            exec_mode = self.readlog_list[0]['mode']
            describe = self.readlog_list[0]['describe']
            options = self.readlog_list[0]['options']
            # create_time = self.readlog_list[0]['create_time']
            create_date = self.readlog_list[0]['create_date']
            inventory_content = self.readlog_list[0]['inventory_content']
            create_ts = self.readlog_list[0]['add_time']       
            finish_ts = self.readlog_list[-1]['add_time']       
        except Exception as e:
            self.logger.error(log_prefix + '失败，原因：该任务还没有开始执行或者数据错误，' + str(e))
            return (False, '该任务还没有开始执行或者数据错误')
            
        pattern = self.readlog_list[0].get('pattern', None)
        module_name = self.readlog_list[0].get('module_name', None)
        module_args = self.readlog_list[0].get('module_args', None)
        yaml_content = self.readlog_list[0].get('yaml_content', None)
        play = self.readlog_list[0].get('play', {})
        task = self.readlog_list[0].get('task', {})
        
        newlog_dict = {
            'name' : name,
            'mode' : exec_mode,
            'describe' : describe,
            'create_time' : timestamp2datetime(create_ts),
            'create_date' : create_date,
            'options' : options,
            'uuid' : uuid_str,
            'inventory_content' : inventory_content,
            'end_time':timestamp2datetime(finish_ts),
            'duration' : round((finish_ts - create_ts), 3),
        }
        
        if exec_mode == 'adhoc' :
            newlog_dict['pattern'] = pattern
            newlog_dict['module_name'] = module_name
            newlog_dict['module_args'] = module_args
        else :
            newlog_dict['yaml_content'] = yaml_content
        
        get_field_list = ['uuid' , 'play_id' , 'task_id']
        result = self.mongoclient.group_by(self.collect, get_field_list)
        if not result[0] :
            self.logger.error(log_prefix + '失败，原因：该任务还没有开始执行或者数据错误，' + result[1])
            return (False, '该任务还没有开始执行或者数据错误')
        
        tempplay_dict = {}
        for playid in result[1] :
            if playid['uuid'] == uuid_str :
                play_id = playid['play_id']
                task_id = playid.get('task_id', '')
                if task_id == '' :
                    continue
            else :
                continue
                
            if play_id not in tempplay_dict :
                tempplay_dict[play_id] = []
                    
            taskid_list = tempplay_dict[play_id]
            taskid_list.append(task_id)
            taskid_list = tempplay_dict[play_id]
            taskid_list = list(set(taskid_list))
            taskid_list = sorted(taskid_list)
            # 对taskid执行先后顺序排序
            tempplay_dict[play_id] = taskid_list
            
        playid_dict = {}
        for play_id in sorted(tempplay_dict) :
            playid_dict[play_id] = tempplay_dict[play_id]
            # 对play执行先后顺序排序

        play_dict = {}
        # 下面这个循环用于：根据play_id获取下面所有的task_id，并获取的每个task_id的最后日志和执行结果信息
        for playid, taskid_list in playid_dict.items() :
            play_dict[playid] = {}
            for taskid in taskid_list :
                task_list = []   
                for line in self.readlog_list :
                    if line['play_id'] == playid and line.get('task_id', '') == taskid :
                        summary = line.get('summary', {})
                        if not summary :
                            task_list.append(line)
   
                last_log = task_list[-1]
                # 求这个任务执行的最后一条日志
                play_dict[playid]['play']=last_log.get('play', {})
                play_dict[playid]['summary'] = summary

                task_dict = {
                    'task' : last_log.get('task', {}),
                    'detail' : last_log.get('detail', {}),
                    }
                
                try:
                    play_dict[playid]['task'][taskid] = task_dict
                except:
                    play_dict[playid]['task'] = {}
                    play_dict[playid]['task'][taskid] = task_dict

        if not play_dict or not isinstance(play_dict, dict) :
            self.logger.error(log_prefix + '失败，原因：该任务还没有开始执行或者查询条件错误，' + result[1])
            return (False, {'result' : '该任务还没有开始执行或者查询条件错误'})

        result_dict = {}
        for play_uuid, logline in play_dict.items() :
            result_dict[play_uuid] = {}
            summary = logline.get('summary', {})
            task_dict = logline.get('task', {})
            
            if 'tasks' not in result_dict[play_uuid]:
                result_dict[play_uuid]['tasks'] = {}
            
            play = logline.get('play', {})
            pattern = play.get('name', {})
            
            for task_id, line in task_dict.items() :
                task = line.get('task', {})
                task_name = task.get('name', '')
                taskmodule = task.get('module', '')
                # task_args = task.get('args', {})
                if exec_mode == 'playbook' and task_name not in result_dict[play_uuid]['tasks'] :
                    result_dict[play_uuid]['tasks'][task_name] = {}
                    new_task = {
                        'module' : task['module'],
                        }
                    result_dict[play_uuid]['tasks'][task_name]['tasks'] = new_task
                
                detail = line.get('detail', {})
                if not isinstance(detail, dict) or not detail:
                    continue
                
                for host , value in detail.items() :   
                    end_ts = value['end_ts']
                    start_ts = value['start_ts']
                    duration = end_ts - start_ts
                    duration = round(duration, 2)
                    
                    '''
                    if taskmodule == 'yum' and 'invocation' in value :
                        # 在yum模块中，在没有使用循环的情况下，value也含有results的key
                        results = [value]
                    else :
                        results = value.get('results', {})
                        
                    if results :
                        data_list = results
                    else :
                        data_list = [value]
                        
                    # data_list = [value]
                    '''
                    data_list = [value]
        
                    for data in data_list :
                        
                        from library.connecter.ansible.callback.module import Parse_Result
                        parse_module = Parse_Result()
                        if taskmodule == 'command' :
                            result = parse_module.command(data, task)
                        elif taskmodule == 'yum' :
                            if 'invocation' in data :
                                result = parse_module.yum(data, task)
                            else:
                                try:
                                    temp_dict = data['results'][0]
                                    del data['results']
                                    data.update(temp_dict)
                                    result = parse_module.yum(data, task)
                                except :
                                    self.logger.error(data)
                                    result = parse_module.common_module(data, task, {})
                        elif taskmodule == 'service' or taskmodule == 'systemd':
                            result = parse_module.service(data, task)
                        elif taskmodule == 'script' :
                            result = parse_module.script(data, task)
                        elif taskmodule == 'cron' :
                            result = parse_module.cron(data, task)
                        elif taskmodule == 'user' :
                            result = parse_module.user(data, task)
                        elif taskmodule == 'copy' :
                            result = parse_module.copy(data, task)
                        elif taskmodule == 'get_url' :
                            result = parse_module.get_url(data, task)
                        elif taskmodule == 'raw' :
                            result = parse_module.command(data, task)
                        else :
                            result = parse_module.common_module(data, task, {})
                          
                        if taskmodule == '' :
                            print(result)
                    
                        if exec_mode == 'playbook' :
                            try :
                                del result['模块名']
                            except :
                                pass 
                            
                            if 'detail' not in result_dict[play_uuid]['tasks'][task_name] :
                                result_dict[play_uuid]['tasks'][task_name]['detail'] = {}
                            
                            result_dict[play_uuid]['tasks'][task_name]['detail'][host] = result
                            result_dict[play_uuid]['pattern'] = pattern
                        else :
                            try :
                                del result['模块名']
                                del result_dict[play_uuid]
                            except :
                                pass 
                            result_dict[host] = result
            
            if exec_mode == 'playbook' :
                result_dict[play_uuid]['summary'] = {}
                      
                if isinstance(summary, dict):
                    for host in summary :
                        ok = summary[host].get('ok', 0)
                        failures = summary[host].get('failures', 0)
                        unreachable = summary[host].get('unreachable', 0)
                        changed = summary[host].get('changed', 0)
                        skipped = summary[host].get('skipped', 0)

                        if ok == 0 :
                            if unreachable == 1:
                                summary_str = '该任务在该主机上执行失败，无法连接远程主机'
                            else :
                                summary_str = '该任务在该主机上执行失败，失败数为' + str(failures) + '，跳过数为' + str(skipped) + '，可能产生变化数为' + str(changed)
                        else :
                            summary_str = '该任务在该主机上执行部分或者全部成功，成功数为' + str(ok) + '，失败数为' + str(failures) + '，跳过数为' + str(skipped) + '，可能产生变化数为' + str(changed)

                        '''
                        result_dict[play_uuid]['summary'][host] = summary[host]
                        原文输出
                        '''
                        result_dict[play_uuid]['summary'][host] = summary_str
                        
                if not result_dict[play_uuid]['summary'] :
                    result_dict[play_uuid]['summary'] = '该任务还没有执行完成'

        newlog_dict['exec_result'] = result_dict
        self.logger.info(log_prefix + '成功')
        return (True, newlog_dict)
    
    
    def get_abs(self):
        
        '''
        获取该用户下所有的执行任务的摘要
        '''
        
        get_field_list = ['name', 'uuid' , 'mode' , 'create_time' , 'describe', 'create_date']
        result = self.mongoclient.group_by(self.collect, get_field_list)
        if not result[0] :
            self.logger.error('ansible任务执行报表清单查询失败，原因：' + result[1])
            return result

        work_list = result[1]
        if len(work_list) == 0 :
            self.logger.warn('ansible任务执行报表清单为空')
            return (True, [])
            
        date_list = []
        for work in work_list :
            create_date = work['create_time']
            if create_date not in date_list :
                date_list.append(create_date)
                
        date_list = sorted(date_list)
        date_list.reverse()
        
        new_list = []
        for date_str in date_list :
            for work_dict in work_list :
                if date_str == work_dict['create_time'] :
                    new_list.append(work_dict)

        return (True, new_list)
