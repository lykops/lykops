# lykops

lykops是一套web可视化的运维自动化项目，基于python3+django开发的。

# 已实现功能

## 1、用户管理

[详情](https://github.com/lykops/lykops/wiki/%E7%94%A8%E6%88%B7%E7%AE%A1%E7%90%86 "用户管理")

## 2、主机管理

主要功能：收录主机，为其他模块（例如：执行任务）直接调用提供便利。

[详情](https://github.com/lykops/lykops/wiki/%E4%B8%BB%E6%9C%BA%E7%AE%A1%E7%90%86 "主机管理")

## 3、任务执行

已实现基于ansible执行运维任务。

可视化、简化执行ansible（[github地址](https://github.com/lykops/ansible "github地址")，该系统称之为原生ansible，和本系统的ansible进行区分）任务，并提供详细的任务执行报告。

[详情](https://github.com/lykops/lykops/wiki/%E7%AE%A1%E7%90%86ansible "管理ansible")


# 关于vault密码

## 什么是vault密码

vault密码用于加解密用户的机密数据。

加密数据有：

	远程主机的ssh、sudo等密码
	ansible配置的ssh、sudo等密码
	......

它从原生ansible的vault密码中引申而来，加解密算法同ansible的vault，但修改了vault数据的头部。它支持解密使用原生ansible的vault方式加密的数据。

## 为什么不使用登陆密码？

解决扩展问题。后续版本中会增加不同用户之间数据的引用问题（例如：A用户的主机直接给B用户）、超级管理员统一管理主机等功能。

如果直接使用登陆密码将会造成用户繁乱和无法隔离用户等问题。

# 说明

1、**在使用前，请仔细阅读[wiki](https://github.com/lykops/lykops/wiki "wiki")**

2、当前版本主要基于ansible，故你应到具备ansible基本知识

3、**请记住：谨慎应用到各种生产环境（包括业务系统的测试、生产等环境）**，因为：

	1）、在发布前，虽本开发者经过比较严谨的测试，但无法担保不存在任何bug
	2）、当你点击“执行”按钮后，主机会按照你的意愿执行相关操作，这些操作很多情况下不可逆

4、本项目测试情况如下

	yaml文件例子：位于https://github.com/lykops/lykops/tree/master/example/ansible
	客户端操作系统如下：
		CentOS 5、6、7（其中5绝大部分情况下报主机无法连接）
		Fedora 24、25、26
		Ubuntu 12.04、14.04、15.04、16.04、17.04（12.04、14.04很多情况下报主机无法连接）