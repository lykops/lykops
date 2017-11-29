version = 'v2.3'
tempdir = '/dev/shm/ansible_' + version

bools = [True, False]
option_dict = {
    # 说明：'option名': {'name':'中文名，用于编辑、查看option等web页面显示', 'mode':'标记该字段用于ansible的那种模式，adhoc、playbook、ad_pb(可以用于adhoc和playbook)', 'default':'默认值' , 'option':'可选字段, 'edit':'是否可以编辑', 'visual':'在页面上是否可以展示', 'run':'在配置任务时是否可以展示并配置'},
    'connection': {'name':'连接远程主机方式', 'mode':'ad_pb', 'default':'smart' , 'option':['smart', 'ssh', 'paramiko', 'local'], 'edit':True, 'visual':True, 'run':True},
    'forks': {'name':'默认forks数', 'mode':'ad_pb', 'default':25 , 'option':[5, 10, 25, 50], 'edit':True, 'visual':True, 'run':True},
    'inventory': {'name':'inventory文件路径', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':True},

    'remote_user': {'name':'SSH用户', 'mode':'ad_pb', 'default':'root' , 'option':[], 'edit':True, 'visual':True, 'run':True},
    'ask_pass': {'name':'SSH密码', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':True, 'visual':True, 'run':True},
    'private_key_file': {'name':'SSH证书', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    
    'su': {'name':'是否切换用户', 'mode':'ad_pb', 'default':False , 'option':bools, 'edit':True, 'visual':True, 'run':True},
    'su_user': {'name':'切换用户名', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':True, 'visual':True, 'run':True},
    'ask_su_pass': {'name':'su密码', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':True, 'visual':True, 'run':True},
    
    'sudo': {'name':'是否使用sudo', 'mode':'ad_pb', 'default':False , 'option':bools, 'edit':True, 'visual':True, 'run':True},
    'sudo_user': {'name':'sudo用户名', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':True, 'visual':True, 'run':True},
    'ask_sudo_pass': {'name':'sudo密码', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':True, 'visual':True, 'run':True},
    
    'ask_vault_pass': {'name':'vault密码', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'new_vault_password': {'name':'新的vault密码', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'new_vault_password_file': {'name':'新的vault密码文件', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    
    'become': {'name':'是否切换用户', 'mode':'ad_pb', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'become_ask_pass': {'name':'切换用户的密码', 'mode':'ad_pb', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'become_user': {'name':'切换用户名', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'become_method': {'name':'切换用户模式', 'mode':'ad_pb', 'default':'sudo' , 'option':['sudo', 'su'], 'edit':False, 'visual':False, 'run':False},
        
    'poll_interval': {'name':'异步运行轮询间隔', 'mode':'adhoc', 'default':15 , 'option':[10, 15, 30], 'edit':False, 'visual':False, 'run':False},
    'seconds': {'name':'异步运行多少秒后表示失败', 'mode':'adhoc', 'default':150 , 'option':[60, 120, 150, 300], 'edit':False, 'visual':False, 'run':False},
    'timeout': {'name':'连接超时时间', 'mode':'ad_pb', 'default':30 , 'option':[30, 60, 120, 300], 'edit':True, 'visual':True, 'run':False},
    
    'flush_cache': {'name':'刷新cache', 'mode':'playbook', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'force_handlers': {'name':'任务失败也要运行handler', 'mode':'playbook', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'subset': {'name':'subset', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    
    'module_name': {'name':'默认模块', 'mode':'adhoc', 'default':'command' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'module_args': {'name':'默认模块参数', 'mode':'adhoc', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'module_path': {'name':'模块路径', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    
    'one_line': {'name':'是否启用one_line回调', 'mode':'adhoc', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'tree': {'name':'是否启用回调tree回调', 'mode':'adhoc', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'output_file': {'name':'输出到文件', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'verbosity': {'name':'bug级别', 'mode':'ad_pb', 'default':0 , 'option':[0, 1, 2, 3, 4, 5], 'edit':False, 'visual':False, 'run':False},
    
    'scp_extra_args': {'name':'scp额外参数', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'sftp_extra_args': {'name':'sftp额外参数', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'ssh_common_args': {'name':'ssh通用参数', 'mode':'ad_pb', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'ssh_extra_args': {'name':'ssh额外参数', 'mode':'ad_pb', 'default':'-C -o ControlMaster=auto -o ControlPersist=24h -o PreferredAuthentications=password,publickey,keyboard-interactive' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'extra_vars': {'name':'额外变量', 'mode':'ad_pb', 'default':[] , 'option':[], 'edit':False, 'visual':False, 'run':False},
    
    'listtags': {'name':'只列出tags，不执行playbook', 'mode':'playbook', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'listtasks': {'name':'只列出tasks，不执行playbook', 'mode':'playbook', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'skip_tags': {'name':'跳过的tags', 'mode':'playbook', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'start_at_task': {'name':'是否一步一步执行task', 'mode':'playbook', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'step': {'name':'从第几步开始执行', 'mode':'playbook', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'tags': {'name':'仅执行哪些tags', 'mode':'playbook', 'default':'' , 'option':[], 'edit':False, 'visual':False, 'run':False},
    'check': {'name':'仅检查', 'mode':'ad_pb', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'syntax': {'name':'仅检查yaml语法', 'mode':'ad_pb', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'listhosts': {'name':'只显示主机列表', 'mode':'ad_pb', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
    'diff': {'name':'对比', 'mode':'ad_pb', 'default':False , 'option':bools, 'edit':False, 'visual':False, 'run':False},
}
