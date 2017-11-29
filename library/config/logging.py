from lykops.settings import BASE_DIR

level_list = ('error', 'warning', 'info', 'debug')
# level_list = ('error', 'warning', 'info', 'debug')
# 可用日志级别，用于管理不同级别的日志。
# 稳定的话，去掉debug

dest_list = ['mongo', 'file']
# 存储目标地址

log_dir = BASE_DIR + '/logs/'

log_category_dict = {
    'default' :{  # 默认方式
        'level':'info',
        'dest' : 'file',
        'mongo' : 'log.default',
        'file' : log_dir + 'info.log',
        },
    'ansible' : {
        'default' : {
            'level':'info',
            'dest' : 'file',
            'file' : 'ansible.log',
            'mongo' : False,
            },
        }
    }
