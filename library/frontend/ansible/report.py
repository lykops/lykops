from library.connecter.ansible.callback.read import Parse_Cblog
from library.frontend import Base
from library.utils.dict import value_replace

class Manager_Report(Base):
    def get_abs(self, username, force=False):
        
        '''
        获取该用户所有工作列表摘要
        :parm
            force：是否强制刷新
        '''
        
        redis_key = 'lykops:' + username + ':ansible:report:abs'
            
        if force:
            self.logger.warn('获取用户' + username + '的ansible执行报告摘要信息时，删除缓存')
            self.redisclient.delete(redis_key)
        else :
            result = self.redisclient.get(redis_key, fmt='obj')
            if result[0] and (result[1] is not None or result[1]) :
                return result
        
        reportapi = Parse_Cblog(username, mongoclient=self.mongoclient)
        result = reportapi.get_abs()
        if not result[0] :
            self.logger.error('获取用户' + username + '的ansible执行报告摘要信息失败，解析时出错，原因：' + result[1])
            return (False, '解析时出错，原因：' + result[1])
        
        abs_dict = result[1]
        set_dict = {
            'name' : redis_key,
            'value' : abs_dict,
            'ex':self.expiretime
            }
        result = self.redisclient.set(set_dict, fmt='obj')
        return (True, abs_dict)


    def get_options_dict(self, username, force=False):
        result = self.get_abs(username, force=force) 
        
        if not result[0] :
            self.logger.error('获取用户' + username + '的ansible执行报告摘要信息失败，解析时出错，原因：' + result[1])
            return (False, '解析时出错，原因：' + result[1])
            
        work_list = result[1]
        if len(work_list) == 0 :
            return (True, {})
            
        options_dict = {}
        for work in work_list :
            create_date = work['create_date']
            op_mode = work['mode']

            if create_date not in options_dict :
                options_dict[create_date] = ['all']
            else :
                if op_mode not in options_dict[create_date]:
                    options_dict[create_date].append(op_mode)
        
        return (True, options_dict)
        
       
    def get_date_list(self, username, force=False):
        result = self.get_abs(username, force=force) 
        
        if not result[0] :
            self.logger.error('获取用户' + username + '的ansible执行报告摘要信息失败，解析时出错，原因：' + result[1])
            return (False, '解析时出错，原因：' + result[1])
            
        work_list = result[1]
        if len(work_list) == 0 :
            return (True, [])
            
        date_list = []
        for work in work_list :
            create_date = work['create_date']
            if create_date not in date_list :
                date_list.append(create_date)
        
        return (True, date_list)
        
        
    def summary(self, username, dt=None, mode='all'):
        result = self.get_abs(username) 
        
        if not result[0] :
            self.logger.error('获取用户' + username + '的ansible执行报告列表失败，解析时出错，原因：' + result[1])
            return (False, '解析时出错，原因：' + result[1])
        
        work_list = result[1]
        if len(work_list) == 0 :
            return (True, {})
        
        if dt is None :
            return (True, work_list)
        
        get_work_list = []
        for work in work_list :
            create_date = work['create_date']
            op_mode = work['mode']
            
            if create_date == dt :
                if mode == 'all' :
                    get_work_list.append(work)
                else :
                    if op_mode == mode :
                        get_work_list.append(work)
                        
        return (True, get_work_list)
        
        
    def detail(self, username, uuid_str, force=False, orig_content=False):
        
        redis_key = 'lykops:' + username + ':ansible:report:' + uuid_str
            
        if force:
            self.redisclient.delete(redis_key)
            reportapi = Parse_Cblog(username, mongoclient=self.mongoclient)
            result = reportapi.parse(uuid_str)
        else :
            result = self.redisclient.get(redis_key, fmt='obj')
            if result[0] and (result[1] is not None or result[1]) :
                pass
            else :
                reportapi = Parse_Cblog(username, mongoclient=self.mongoclient)
                result = reportapi.parse(uuid_str)
            
        if not result[0] :
            self.logger.error('获取用户' + username + '的uuid为' + uuid_str + '的ansible执行报告失败，解析时出错，原因：' + result[1])
            return (False, '解析时出错，原因：' + result[1])
        
        report_data = result[1]
        if not orig_content :
            '''
            inventory_content = report_data['inventory_content']
            exec_result = report_data['exec_result']
            inventory_content = inventory_content.replace('\n', '</br>')
            report_data['inventory_content'] = inventory_content.replace(' ', '&nbsp;')
            exec_result = report_data['exec_result']
            report_data['exec_result'] = value_replace(exec_result, replace_dict={'\n': '</br>', ' ':'&nbsp;'})
            '''
            report_data = value_replace(report_data, replace_dict={'\n': '</br>', ' ':'&nbsp;'})
        
        set_dict = {
            'name' : redis_key,
            'value' : report_data,
            'ex':self.expiretime
            }
        result = self.redisclient.set(set_dict, fmt='obj')
        self.logger.info('获取用户' + username + '的uuid为' + uuid_str + '的ansible执行报告成功')
        return (True, report_data)
        
