可视化、简化执行ansible（[github地址](https://github.com/lykops/ansible "github地址")，该系统称之为原生ansible，和本系统的ansible进行区分）任务，并提供详细的任务执行报告。

# 特点

	1、基于原生态ansible： 执行任务功能直接调用底层，其他功能深度改造
	2、执行任务使用后台任务管理器celery，保证web端发送任务后立即返回，任务能正常执行
	3、yaml文件的新增、编辑等操作检测语法，保证yaml数据准确无误，
	4、集中管理主机、统一ansible配置，快速组织ansible任务
	5、重写callback，详细的任务执行报告记录着任务执行前后的各种数据

# 功能

## 配置管理

管理当前用户执行ansible任务时常见有用配置。具体详见命令ansible[-playbook] -h。

[详情](https://github.com/lykops/lykops/wiki/ansible%E9%85%8D%E7%BD%AE%E7%AE%A1%E7%90%86 "配置管理")

## yaml管理

[详情](https://github.com/lykops/lykops/wiki/ansible-yaml%E7%AE%A1%E7%90%86 "yaml管理")

## 任务执行

可视化执行命令ansible[-playbook]

[详情](https://github.com/lykops/lykops/wiki/ansible%E6%89%A7%E8%A1%8C%E4%BB%BB%E5%8A%A1%E7%AE%A1%E7%90%86 "任务执行")


## 任务执行报告

展示历史ansible任务执行报告

[详情](https://github.com/lykops/lykops/wiki/ansible%E4%BB%BB%E5%8A%A1%E6%89%A7%E8%A1%8C%E6%8A%A5%E5%91%8A "任务执行报告")