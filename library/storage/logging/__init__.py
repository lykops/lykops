import os, sys

from library.config.logging import log_category_dict, level_list, dest_list
from library.utils.time_conv import timestamp2datetime


class Routing_Logging():
    def __init__(self):
        
        '''
        日志路由功能，最终读取或者写入指定位置
        '''
        
        from library.storage.logging.file import Logging_File
        from library.storage.logging.mongo import Logging_Mongo
        self.mongo_logging = Logging_Mongo()
        self.file_logging = Logging_File()
        

    def read(self, get_field=[], condition_dict={}, log_dict={}, limit=0, lastest_field=False):
        
        '''
        读取日志路由
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
            
        try :
            dest = log_dict['dest']
        except Exception as e:
            return (False, '参数log_dict配置错误，提供的内容为' + str(log_dict) + '，失败原因为' + str(e))
            
        if dest == 'mongo' :
            result = self.mongo_logging.read(get_field=get_field, condition_dict=condition_dict, log_dict=log_dict, limit=limit, lastest_field=lastest_field)
        elif dest == 'file' :
            result = self.file_logging.read(get_field=get_field, condition_dict=condition_dict, log_dict=log_dict, limit=limit, lastest_field=lastest_field)   
        else :
            result = self.mongo_logging.read(get_field=get_field, condition_dict=condition_dict, log_dict=log_dict, limit=limit, lastest_field=lastest_field)
            if not result[0] :
                result = self.file_logging.read(get_field=get_field, condition_dict=condition_dict, log_dict=log_dict, limit=limit, lastest_field=lastest_field)
            
        return result 
        
        
    def write(self, content, oper, log_dict={}):
        
        '''
        写日志
        :参数
            content:内容
            oper:操作者
            log_dict:日志记录位置
            isdubug:是否为debug日志
        ：返回
            一个元组，(False,原因)或者(True, 目的地)
        '''
     
        default_log_dict = log_category_dict['default']
        # 在写入时，默认是写入文件
        
        if not content :
            return (False , '日志内容为空!!!!')
        
        if log_dict == {} or not log_dict or not isinstance(log_dict, dict) :
            log_dict = default_log_dict
        
        try :
            dest = log_dict['dest']
            if dest not in dest_list :
                dest = default_log_dict['dest']
        except :
            dest = default_log_dict['dest']
                
        if not oper :
            oper = 'unknown'
        
        if dest == 'mongo' :
            result = self.mongo_logging.write(content, oper, log_dict=log_dict)
            if not result[0] :
                result = self.file_logging.write(content, oper, log_dict=log_dict)
                return (result[0], 'file')
            else :
                return (result[0], 'mongo')
        else :
            result = self.file_logging.write(content, oper, log_dict=log_dict)
            return (result[0], 'file')
    
        return (False, False)
