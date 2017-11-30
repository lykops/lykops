# 写在前面

## yaml数据规则

本系统除了检测是否匹配ansible原生规则外，还增加了一下规则：

	1、roles、include的命名规则：只能为相对路径，而且只能使用字母、数字、_、-等字符；
	2、入口文件、include文件不能含有include字段

本系统提供了各个模块和roles的例子，[详情](https://github.com/lykops/lykops/tree/master/example/ansible)

## 关于yaml数据展示

编辑和展示yaml时完全根据类型（main是入口文件）和文件进行展示的，会过滤掉重复的文件名。

建议

	1、尽量简化，少使用include
	2、复杂的roles在展示时页面过于庞大，每次最好只写一个playbook/roles

# 查看

![ansible的yaml列表](https://github.com/lykops/lykops/blob/master/doc/screenshot/%E6%9F%A5%E7%9C%8Bansible%E7%9A%84yaml%E5%88%97%E8%A1%A8.png?raw=true)

# 新增

![新增ansible yaml](https://github.com/lykops/lykops/blob/master/doc/screenshot/%E6%96%B0%E5%A2%9Eansible%20yaml.png?raw=true)

**注：只能添加单个yaml文件内容，不能含有roles或者include等字段**

# 导入

![导入](https://github.com/lykops/lykops/blob/master/doc/screenshot/%E5%AF%BC%E5%85%A5ansible%20yaml.png?raw=true)

这里支持两种方式：

	1、上传文件方式（上面部分），只支持导入*.yaml、zip格式的文件
	2、输入路径方式，将读取服务器本地指定路径的yaml数据，支持*.yaml和zip格式的文件和文件夹

# 编辑

![编辑](https://github.com/lykops/lykops/blob/master/doc/screenshot/%E7%BC%96%E8%BE%91ansible%20yaml.png?raw=true)

# 查看详细信息

## 简单

![](https://github.com/lykops/lykops/blob/master/doc/screenshot/%E6%9F%A5%E7%9C%8Bansible%E7%9A%84yaml%E8%AF%A6%E7%BB%86%E5%86%85%E5%AE%B9%EF%BC%88%E5%8D%95%E6%96%87%E4%BB%B6%EF%BC%89.png?raw=true)

## 复杂
![查看](https://github.com/lykops/lykops/blob/master/doc/screenshot/%E6%9F%A5%E7%9C%8Bansible%E7%9A%84yaml%E8%AF%A6%E7%BB%86%E4%BF%A1%E6%81%AF%EF%BC%88%E5%AE%8C%E6%95%B4%E7%9A%84roles%EF%BC%89.png?raw=true)
