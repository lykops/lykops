from __future__ import absolute_import

from celery import Celery, platforms

from library.config.database import redis_config
platforms.C_FORCE_ROOT = True

celery_redis_conf = redis_config['session']
BROKER_URL = 'redis://:' + celery_redis_conf['pwd'] + '@' + celery_redis_conf['host'] + ':' + str(celery_redis_conf['port']) + '/' + str(celery_redis_conf['db'])
CELERY_RESULT_BACKEND = BROKER_URL

app = Celery('lykops', backend=BROKER_URL, broker=BROKER_URL, include=['lykops.tasks'])

app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)
