from library.config.logging import level_list, log_category_dict

class Logging_Mongo():
    def __init__(self) :
        
        '''
        该class用于写日志到mongodb服务器中
        __init__()用于初始化mongo
        '''
        
        from library.connecter.database.mongo import Op_Mongo
        self.mongoclient = Op_Mongo(dest='log')
        self.default_log_dict = log_category_dict['default']

    
    def write(self, content, oper, log_dict={}):
                
        '''
        写入mongo数据库
        :参数
            log_dict : 存储信息
            oper : 操作者
            content : 日志内容
            isdubug:是否为debug日志
        :返回
            一个元组，(False,原因)或者(True, 结果)
        '''
        
        if not log_dict or not isinstance(log_dict, dict) :
            log_dict = self.default_log_dict
        
        try :
            dest = log_dict['dest']
            if dest != 'mongo':
                level = self.default_log_dict['level']
                collect = self.default_log_dict['mongo']
            else :
                level = log_dict['level']
                if level not in level_list :
                    level = self.default_log_dict['level']
                
                collect = log_dict['mongo']
        except Exception as e:
            return (False, str(e))
    
        if not oper :
            oper = 'unknown'
        
        if not content :
            return (False , '日志内容为空!!!!')

        msg_dict = {
            }
    
        if isinstance(content, dict) :
            msg_dict.update(content)
        else :
            msg_dict['content'] = content

        insert_dict = {
            'collect':collect,
            'data':msg_dict
            }
        
        result = self.mongoclient.insert(insert_dict, addtime=True)
        return result


    def read(self, get_field=[], condition_dict={}, log_dict={}, limit=0, lastest_field=False):
                
        '''
        读取mongo数据库的日志
        :参数
            log_dict : 日志存储信息
            condition_dict : 查询条件
            get_field_list : 获取字段列表
            limit : 限制获取多少条数据
            lastest_field : 获取该字段最新一条数据
        '''
        
        if log_dict == {} or not log_dict or not isinstance(log_dict, dict) :
            return (False, '参数log_dict配置错误，必须是一个不为空的字典')
        
        if condition_dict == {} or not condition_dict or not isinstance(condition_dict, dict) :
            return (False, '参数condition_dict必须是一个不为空的字典，查询条件')
            
        if not isinstance(get_field, (list, tuple, dict)) :
            get_field = []
        
        try :
            collect = log_dict['mongo']
        except Exception as e:
            return (False, '参数log_dict配置错误，提供的内容为' + str(log_dict) + '，失败原因为' + str(e))

        try :
            limit = int(limit)
        except :
            limit = 0
            
        if lastest_field :
            limit = 0
            
        result = self.mongoclient.find(collect, get_field=get_field, condition_dict=condition_dict, limits=limit, sort_dict={'add_time':1})
    
        if not result[0] :
            return result
        
        content_list = result[1]
        content_len = len(content_list)
        if content_len == 0 :
            return (True , [])
        elif content_len == 1 :
            return (True , [content_list[0]])
        else :
            if not lastest_field : 
                return (True , content_list)
        
        results = ''
        lastest_time = 0.0
        for line in content_list :
            if lastest_field in line :
                addtime = line[lastest_field]
    
                try :
                    addtime = float(addtime)
                except :
                    addtime = str(addtime)
                    from library.utils.time_conv import datetime2timestamp
                    addtime = datetime2timestamp(addtime)
                    
                if not addtime :
                    addtime = 0.0
                else :
                    addtime = float(addtime)
                    if addtime >= lastest_time :
                        lastest_time = addtime
                        results = line
        
        if results == '' :
            return (True , [content_list[-1]])
    
        return (True , [results])
