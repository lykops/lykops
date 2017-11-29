import json, time

from library.config.logging import level_list, log_category_dict

class Logging_File():
    def __init__(self):
        self.delimiter = '    '
        self.default_log_dict = log_category_dict['default']


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
            log_file = log_dict['file']
        except Exception as e:
            return (False, '参数log_dict配置错误，提供的内容为' + str(log_dict) + '，失败原因为' + str(e))
            
        kw_list = condition_dict.values()
        kw_list = list(kw_list)
        kw_list = ['^[0-9]'] + kw_list
        # 开头为数字的时间
                
        from library.utils.file import read_file_grep
        result = read_file_grep(log_file , kw_list, isrecursion=True, delimiter=self.delimiter, row_list=[1, 2, 5])
    
        if not result[0] :
            return result
           
        line_list = result[1]
        temp_list = []
        for line in line_list :
            if not line or line == [''] or line == [] :
                continue
            
            content = line[-1]
            from library.utils.type_conv import str2dict
            result = str2dict(content)
    
            if result[0] :
                content_dict = result[1]
                
                isskip = False
                for key, value in condition_dict.items() :
                    if key in content_dict :
                        if value != content_dict[key] :
                            isskip = True
                            
                if isskip :
                    continue
                
                content_dict['writelog_time'] = line[0]
                content_dict['writelog_st'] = line[1]
            else :
                content_dict = {
                    'writelog_time' : line[0],
                    'writelog_st' : line[1],
                    'content' : content
                    }
            
            temp_list.append(content_dict)
            
        temp_len = len(temp_list)
        if temp_len == 0 :
            return (True, [])
    
        try : 
            limit = int(limit)
        except :
            limit = 0
            
        if lastest_field :
            return (True, [temp_list[-1]])
            
        if limit > temp_len :
            return (True, temp_list)
        else :
            start_ops = temp_len - limit
            return (True, temp_list[start_ops:])
    
    
    def write(self, content, oper, log_dict={}):
                
        '''
        写入日志，追加方式
        日志格式为
        写入年月日 时分秒        写入时间戳        日志级别        操作用户    日志内容（字符串或者字典）
        :参数
            log_dict : 日志字典
            oper : 操作者
            content : 日志内容
            isdubug:是否为debug日志
        :返回
            一个元组，(False,原因)或者(True, 文件名)
        '''
        
        if not content :
            return (False , '日志内容为空!!!!')
        
        from library.utils.dict import _2dot
        content = _2dot(content)
    
        try :
            content = json.dumps(content)
        except :
            content = str(content)
        # json的标准格式：要求必须 只能使用双引号作为键 或者 值的边界符号，不能使用单引号，而且“键”必须使用边界符（双引号）
        
        if log_dict == {} or not log_dict or not isinstance(log_dict, dict) :
            log_dict = self.default_log_dict
        
        try :
            dest = log_dict['dest']
            if dest != 'file':
                level = self.default_log_dict['level']
                log_file = self.default_log_dict['file']
            else :
                level = log_dict['level']
                if level not in level_list :
                    level = self.default_log_dict['level']
                
                log_file = log_dict['file']
        except :
            level = self.default_log_dict['level']
            log_file = self.default_log_dict['file']

        if not oper :
            oper = 'unknown'
    
        from library.utils.time_conv import timestamp2datetime
        curl_time = timestamp2datetime(fmt='%Y-%m-%d %H:%M:%S')
        
        message = curl_time + self.delimiter + str(time.time()) + self.delimiter + level + self.delimiter + oper + self.delimiter + content + '\n'
        if level == 'debug' :
            from library.utils.traceback import get_traceback
            caller_str = get_traceback()
            message = message + caller_str + '\n'
        
        from library.utils.file import write_file
        result = write_file(log_file , 'a' , message, force=True , backup=False)
        return result
 
