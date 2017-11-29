import re

from library.utils.dict import key2value
from library.utils.time_conv import datetime2timestamp

class Parse_Result():
    def command(self, data, task):
        result_dict = {}
        # result_dict['命令'] = key2value(data, ['invocation', 'module_args', '_raw_params'])
        
        result_dict['执行输出结果'] = key2value(data, 'stdout')
        result_dict['错误输出'] = key2value(data, 'stderr')
    
        rc = key2value(data, 'rc')
        if rc != 0 :
            result_dict['执行返回错误代码'] = rc
            
        run_warning = ''
        run_warning_list = key2value(data, 'warnings')
        if isinstance(run_warning_list, (tuple, list)) and len(run_warning_list) > 0 :
            for warn in run_warning_list :
                if not run_warning :
                    run_warning = warn
                else :
                    run_warning = run_warning + '\n\t' + warn
        else :
            run_warning = run_warning_list
                        
        result_dict['警告'] = run_warning
    
        start_time = key2value(data, 'start')
        try :
            start_time = re.split('.', start_time)[0]
        except :
            pass
        start_ts = datetime2timestamp(start_time)
        end_time = key2value(data, 'end')
        try :
            end_time = re.split('.', end_time)[0]
        except :
            pass
        end_ts = datetime2timestamp(end_time)
        run_time = end_ts - start_ts
        run_time = round(run_time, 2)
        result_dict['开始执行时间'] = start_time
        result_dict['执行完成时间'] = end_time
        result_dict['执行时长'] = str(run_time) + '秒'
    
        new_dict = self.common_module(data, task, result_dict)
        return new_dict
    
    
    def script(self, data, task):
        result_dict = {}
        rc = key2value(data, 'rc')
        if rc != 0 :
            result_dict['执行返回错误代码'] = rc
        result_dict['执行输出结果'] = key2value(data, 'stdout')
        result_dict['错误输出'] = key2value(data, '')
        result_dict['脚本路径'] = key2value(task, ['args', '_raw_params'])
        new_dict = self.common_module(data, task, result_dict)
        return new_dict
    
    
    def get_url(self, data, task):
        result_dict = {}
        
        result_dict['访问URL地址'] = key2value(data, ['invocation', 'module_args', 'url'])
        result_dict['下载文件的路径'] = key2value(data, ['invocation', 'module_args', 'dest'])
        
        '''
        result_dict['下载文件的用户组'] = key2value(data, ['invocation', 'module_args', 'group'])
        result_dict['下载文件的用户'] = key2value(data, ['invocation', 'module_args', 'owner'])
        result_dict['下载文件的权限'] = key2value(data, ['invocation', 'module_args', 'mode'])
        result_dict['访问URL的headers'] = key2value(data, ['invocation', 'module_args', 'headers'])
        result_dict['访问URL的用户名'] = key2value(data, ['invocation', 'module_args', 'url_username'])
        # url_password = key2value(data, ['invocation', 'module_args', 'url_password'])
        timeout = key2value(data, ['invocation', 'module_args', 'timeout'])
        if not timeout or int(timeout) != 0:
            result_dict['访问URL的超时秒数'] = timeout
        
        result_dict['用于检验下载文件的sha256sum'] = key2value(data, ['invocation', 'module_args', 'sha256sum'])
        result_dict['用于检验下载文件的checksum'] = key2value(data, ['invocation', 'module_args', 'checksum'])
        validate_certs = key2value(data, ['invocation', 'module_args', 'validate_certs'])
        if validate_certs == 'yes' or not validate_certs:
            result_dict['是否要求对https证书验证'] = '是'
        else :
            result_dict['是否要求对https证书验证'] = '否'
        
        use_proxy = key2value(data, ['invocation', 'module_args', 'use_proxy'])
        if use_proxy == 'not' or not use_proxy:
            result_dict['是否使用use_proxy访问URL'] = '否'
        else :
            result_dict['是否使用use_proxy访问URL'] = '是'
        '''
        
        msg = key2value(data, 'msg')
        
        failed = key2value(data, 'failed')
        if failed :
            result_dict['执行失败原因'] = msg
                
            result_dict['执行结果'] = '失败'
            new_dict = self.common_module(data, task, result_dict)
            return new_dict
        
        status_code = key2value(data, 'status_code')
        if not isinstance(status_code, int) or status_code >= 400 :
            result_dict['执行结果'] = '失败'
            result_dict['执行失败原因'] = msg
            
            new_dict = self.common_module(data, task, result_dict)
            return new_dict
        
        '''
        result_dict['下载文件的用户组'] = key2value(data, 'group')
        result_dict['下载文件的用户UID'] = key2value(data, 'uid')
        result_dict['下载文件的用户GID'] = key2value(data, 'gid')
        result_dict['下载文件的用户'] = key2value(data, 'owner')
        result_dict['下载文件的权限'] = key2value(data, 'mode')
        result_dict['文件大小B'] = key2value(data, 'size')
        result_dict['checksum'] = key2value(data, 'checksum')
        result_dict['下载文件的隐藏权限chattr'] = key2value(data, ['invocation', 'module_args', 'attributes'])
        '''
       
        content = key2value(data, ['invocation', 'module_args', 'content'])
        if content == 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER' :
            result_dict['执行结果'] = '在之前已经下载完成，下载文件和页面内容完全一致，无需下载'
            result_dict['下载文件路径'] = key2value(task, ['args', 'path'])
            new_dict = self.common_module(data, task, result_dict)
            return new_dict
        
        result_dict['执行结果'] = '成功'
        # result_dict['md5sum'] = key2value(data, 'md5sum')
        # result_dict['URL返回信息'] = msg
        result_dict['下载文件路径'] = key2value(data, 'path')
    
        new_dict = self.common_module(data, task, result_dict)
        return new_dict
    
    
    def copy(self, data, task):
        result_dict = {}
        
        dest = key2value(data, ['invocation', 'module_args', 'dest'])
        src = key2value(data, ['invocation', 'module_args', 'src'])
        '''
        group = key2value(data, ['invocation', 'module_args', 'group'])
        owner = key2value(data, ['invocation', 'module_args', 'owner'])
        mode = key2value(data, ['invocation', 'module_args', 'mode'])
        '''
        
        if src :
            result_dict['本地源文件路径'] = src
                
        if dest :
            result_dict['远程主机文件路径'] = dest
              
        '''  
        if group :
            result_dict['远程主机文件归属用户组'] = group
        
        if owner :
            result_dict['远程主机文件归属用户'] = owner
        
        if mode :
            result_dict['远程主机文件权限'] = mode
        '''
        
        failed = key2value(data, 'failed')
        if failed :
            result_dict['执行失败原因'] = key2value(data, 'msg')
            
            details = key2value(data, 'details')
            if details :
                result_dict['执行失败详细信息'] = details
                
            result_dict['执行结果'] = '失败'
            new_dict = self.common_module(data, task, result_dict)
            return new_dict
        
        '''
        result_dict['远程主机文件归属用户组'] = key2value(data, 'group')
        result_dict['远程主机文件归属用户UID'] = key2value(data, 'uid')
        result_dict['远程主机文件归属用户GID'] = key2value(data, 'gid')
        result_dict['远程主机文件归属用户'] = key2value(data, 'owner')
        result_dict['远程主机文件权限'] = key2value(data, 'mode')
        result_dict['文件大小B'] = key2value(data, 'size')
        result_dict['checksum'] = key2value(data, 'checksum')
        result_dict['远程主机文件隐藏权限chattr'] = key2value(data, ['invocation', 'module_args', 'attributes'])
        '''
        
        content = key2value(data, ['invocation', 'module_args', 'content'])
        if content == 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER' :
            result_dict['执行结果'] = '源、目标文件完全一致，无需拷贝'
            result_dict['远程主机文件路径'] = key2value(task, ['args', 'path'])
            new_dict = self.common_module(data, task, result_dict)
            return new_dict
        
        result_dict['执行结果'] = '成功'
        result_dict['远程主机文件路径'] = key2value(data, 'path')
    
        new_dict = self.common_module(data, task, result_dict)
        return new_dict
    
    
    def user(self, data, task):
        result_dict = {}
        result_dict['用户名'] = key2value(data, 'name')
        
        changed = key2value(data, 'changed')
        state = key2value(data, 'state')
        if state == 'present' :
            result_dict['动作'] = '新增用户或者修改用户信息'
            if changed :
                result_dict['备注'] = key2value(data, 'comment')
                result_dict['shell命令'] = key2value(data, 'shell')
                result_dict['home目录'] = key2value(data, 'home')
                result_dict['ssh_fingerprint'] = key2value(data, 'ssh_fingerprint')
                # result_dict['ssh_public_key'] = key2value(data, 'ssh_public_key')
                result_dict['ssh_key_file'] = key2value(data, 'ssh_key_file')
                result_dict['ssh_key_bits'] = key2value(data, 'ssh_key_bits')
                result_dict['ssh_key_type'] = key2value(data, 'ssh_key_type')
                result_dict['ssh_key_passphrase'] = key2value(data, 'ssh_key_passphrase')
                result_dict['ssh_key_comment'] = key2value(data, 'ssh_key_comment')
                result_dict['用户过期时间'] = key2value(data, 'expires')
                result_dict['警告信息'] = key2value(data, 'stderr')
                password = key2value(data, 'password')
                if password :
                    result_dict['用户密码是否执行设置或者修改'] = '是'
                else :
                    result_dict['用户密码是否执行设置或者修改'] = '否'
            else :
                result_dict['错误信息'] = key2value(data, 'stderr')
        else :
            result_dict['动作'] = '删除用户'
            if changed :
                result_dict['警告信息'] = key2value(data, 'stderr')
                force = key2value(data, 'force')
                if force :
                    result_dict['是否强制删除掉'] = '是'
                else :
                    result_dict['是否强制删除掉'] = '否'
                    
                remove = key2value(data, 'remove')
                if remove :
                    result_dict['home目录是否被删除'] = '是'
                else :
                    result_dict['home目录是否被删除'] = '否'
            else :
                result_dict['错误信息'] = key2value(data, 'stderr')
                
            
        result_dict['GID'] = key2value(data, 'group')
        result_dict['UID'] = key2value(data, 'uid')
    
        new_dict = self.common_module(data, task, result_dict)
        return new_dict
    
    
    def yum(self, data, task):
        result_dict = {}
        
        package_list = key2value(data, ['invocation', 'module_args', 'name'])
        package = None
        for pack in package_list :
            if package is None :
                package = pack
            else :
                package = package + ' ' + pack
                
        state = key2value(data, ['invocation', 'module_args', 'state'])
        if state in ('present', 'installed', 'latest'): 
            if package == '*' :
                state = 'upgrade'
                result_dict['动作'] = '升级系统' 
            else :
                result_dict['动作'] = '安装' 
                state = 'install'
        elif state in ('removed', 'absent'):
            result_dict['动作'] = '卸载'
            state = 'remove'
        else :
            result_dict['动作'] = '未知动作'
            state = 'unknown action'
        
        '''
        disable_gpg_check = key2value(data, ['invocation', 'module_args', 'disable_gpg_check'])
        disablerepo = key2value(data, ['invocation', 'module_args', 'disablerepo'])
        enablerepo = key2value(data, ['invocation', 'module_args', 'enablerepo'])
        exclude = key2value(data, ['invocation', 'module_args', 'exclude'])
        skip_broken = key2value(data, ['invocation', 'module_args', 'skip_broken'])

        if state == 'upgrade' :
            cmd = 'yum upgrade'
        else :
            cmd = 'yum ' + state + ' ' + package
    
        if enablerepo :
            cmd = cmd + ' --enablerepo=' + enablerepo
        if disablerepo :
            cmd = cmd + ' --disablerepo=' + disablerepo
        if exclude :
            cmd = cmd + ' --exclude=' + exclude
        if skip_broken :
            cmd = cmd + ' --skip_broken'
        if disable_gpg_check :
            cmd = cmd + ' --nogpgcheck'
            
        result_dict['模拟命令行'] = cmd
        '''
        
        results = key2value(data, 'results')
        result_str = None
        for result in results :
            if result_str is None:
                result_str = str(result)
            else :
                result_str = result_str + '\n' + str(result)
            
        result_dict['执行结果'] = result_str
    
        new_dict = self.common_module(data, task, result_dict)
        return new_dict
            
    
    def service(self, data, task):
        result_dict = {}
        name = key2value(data, ['invocation', 'module_args', 'name'])
         
        state = key2value(data, 'state')
        if state == 'started' :
            result_dict['执行动作'] = '启动服务' 
            # result_dict['模拟执行动作命令'] = 'service ' + name + ' start'
        elif state == 'stoped' :
            result_dict['执行动作'] = '停止服务' 
            # result_dict['模拟执行动作命令'] = 'service ' + name + ' stop'
        elif state == 'restarted' :
            result_dict['执行动作'] = '重启服务' 
            # result_dict['模拟执行动作命令'] = 'service ' + name + ' restart'
        elif state == 'reloaded' :
            result_dict['执行动作'] = '重载服务'
            # result_dict['模拟执行动作命令'] = 'service ' + name + ' reload'
            
        try :
            enabled = data['enabled']
            if enabled :
                result_dict['下次开机'] = '服务' + name + '启动' 
            else :
                result_dict['下次开机'] = '服务' + name + '不启动' 
        except :
            pass
        
        new_dict = self.common_module(data, task, result_dict)
        return new_dict
    
    
    def cron(self, data, task):
        result_dict = {}
        
        user = key2value(data, ['invocation', 'module_args', 'user'])
        if user is None or not user :
            user = 'root'
        state = key2value(data, ['invocation', 'module_args', 'state'])
        
        result_dict['备份文件位置'] = key2value(data, 'backup_file')
        changed = key2value(data, 'changed')
        failed = key2value(data, 'failed')
        
        if changed :
            if state == 'present' :
                result_dict['动作'] = '增加计划任务' 
        
                if not failed :
                    result_dict['执行结果'] = '新增成功'
        
                    result_dict['计划名称'] = key2value(data, ['invocation', 'module_args', 'name'])
                    '''
                    minute = key2value(data, ['invocation', 'module_args', 'minute'])
                    weekday = key2value(data, ['invocation', 'module_args', 'weekday'])
                    month = key2value(data, ['invocation', 'module_args', 'month'])
                    day = key2value(data, ['invocation', 'module_args', 'day'])
                    hour = key2value(data, ['invocation', 'module_args', 'hour'])
                    job = key2value(data, ['invocation', 'module_args', 'job'])
                    result_dict['模拟命令'] = 'crontab -e -u ' + user
                    result_dict['模拟计划任务'] = "%s %s %s %s %s %s" % (minute , hour , day , month , weekday , job)
                    '''
                else :
                    result_dict['执行结果'] = '新增失败'
            else :
                result_dict['动作'] = '删除计划任务' 
                if not failed :
                    result_dict['执行结果'] = '删除成功'
                else :
                    result_dict['执行结果'] = '删除失败'
            
        new_dict = self.common_module(data, task, result_dict)

        return new_dict
    
    
    def common_module(self, data, task, resultdict):
        result_dict = {}
        result_dict['模块名'] = key2value(task, 'module')
        
        # task_dict = {}
        # for key in ('name', 'module', 'id', 'create_time', 'create_ts') :
        # for key in ('id', 'module') :
        #    task_dict[key] = task[key]
        # result_dict['name'] = task_dict
        # result_dict['taskargs'] = key2value(task, ['args', '_raw_params'])
        # result_dict['命令'] = key2value(data, ['invocation', 'module_args', '_raw_params'])
        
        unreachable = key2value(data, 'unreachable')
        if unreachable :
            result_dict['执行结果'] = '无法到达目标主机'
            msg = key2value(data, 'msg')
            result_dict['错误信息'] = msg
            return result_dict
        
        stdouts = key2value(data, 'stdout')
        if stdouts :
            result_dict['标准输出'] = stdouts
            
        stderrs = key2value(data, 'stderr')
        if stderrs :
            result_dict['错误输出'] = stderrs
    
        rc = key2value(data, 'rc')
        changed = key2value(data, 'changed')
        if rc != 0 and isinstance(rc, int):
            # result_dict['执行返回错误代码'] = rc
            result_dict['执行结果'] = '执行过程中发生异常，错误代码为' + str(rc)
        else :
            if not changed :
                result_dict['执行结果'] = '没有对系统造成任何影响'
                
        msg = key2value(data, 'msg')
        result_dict['输出信息'] = msg

        finish_ts = key2value(data, 'end_ts')
        create_ts = key2value(data, 'start_ts')
        duration = finish_ts - create_ts
        duration = round(duration, 2)
        result_dict['任务总耗时'] = str(duration) + '秒'
        result_dict.update(resultdict)
        
        new_dict = {}
        for k, v in result_dict.items() :
            if v :
                new_dict[k] = v
        return new_dict
