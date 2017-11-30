# 写在前面

模拟命令行ansible[-playbook]

字段说明：

	名称：该任务的名称，用于查看执行报告用的，可以重复
	主机组等同于命令行的pattern，【inventory文件】是从【本系统中的主机列表】获取主机后根据【/etc/ansible/hosts】格式写到一个动态inventory文件
	模块：等同于命令行ansible的-m
	参数：等同于命令行ansible的-a
	yaml文件：等同于命令行ansible-playbook的yaml文件
	描述：用于查看执行报告用的

填写好相关参数，点击“执行”后，前端经过生成【动态inventory文件】、配置参数等操作后，发送给后台任务管理器celery【负责处理ansible任务的程序】，web页面立即跳转到任务执行报告页面。

**celery默认并行数是根据服务器的CPU核心数来确定的**。例如服务器的CPU为4核双线程的话，celery同时能处理8个后台任务，超过8个将进入等待队列。

所以，不管你的ansible将执行多长时间，只要符合ansible的逻辑，**最终**都会被ansible能正常接收执行，并且执行完毕后在执行报告页面中看到相对应的执行报告。

# 执行临时任务

![执行临时任务](https://github.com/lykops/lykops/blob/master/doc/screenshot/%E6%89%A7%E8%A1%8Cansible%E4%B8%B4%E6%97%B6%E4%BB%BB%E5%8A%A1.png?raw=true)

# 执行playbook任务

![执行playbook任务](https://github.com/lykops/lykops/blob/master/doc/screenshot/%E6%89%A7%E8%A1%8Cansible%20playbook%E4%BB%BB%E5%8A%A1.png?raw=true)