from ansible import constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.playbook import Playbook
from ansible.template import Templar
from ansible.utils.helpers import pct_to_int
from ansible.utils.ssh_functions import check_for_controlpersist

from library.connecter.ansible.callback.write import Write_Storage
from library.connecter.ansible.v2_3 import Base
from library.connecter.ansible.yaml.read2file import Read_File
from library.storage.logging import Routing_Logging

class playbook(Base):
    def run(self, yamlfile, vault_passwd, inventory_content):
        self.vault_passwd = vault_passwd
        self.inventory_content = inventory_content
        if not isinstance(yamlfile, str) :
            self.logger.error(self.log_prefix + '准备工作失败，原因：参数yamlfile必须是一个文件')
            return (False, '参数yamlfile必须是一个文件')
        
        result = self._run_playbook(yamlfile, is_checksyntax=True)
        if not result :
            self.logger.error(self.log_prefix + '准备工作失败，原因：经过ansible原生工具检测，文件' + yamlfile + '语法错误')
            return (False, '经过ansible原生工具检测，文件' + yamlfile + '语法错误')

        if self.options.listhosts or self.options.listtasks or self.options.listtags or self.options.syntax:
            self.logger.warn(self.log_prefix + '准备工作失败，原因：处理一个list，无需执行任务')
            return (False, '处理一个list，无需执行任务')

        result = self._run_playbook(yamlfile)
        self.logger.info(self.log_prefix + '发送成功')
        return result
    

    def _run_playbook(self, yamlfile, is_checksyntax=False):
        if not is_checksyntax :
            if self.options.flush_cache:
                self._flush_cache()
                    
            self._loading_callback(yamlfile)
            # self._unreachable_hosts = dict()
            
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.callback,
            )
        
            check_for_controlpersist(C.ANSIBLE_SSH_EXECUTABLE)
        else :
            tqm = None
            
        try :   
            pb = Playbook.load(
                yamlfile,
                variable_manager=self.variable_manager,
                loader=self.loader
            )
            self.inventory.set_playbook_basedir(yamlfile)
    
            if tqm is not None :
                tqm.load_callbacks()
                tqm.send_callback('v2_playbook_on_start', pb)
                self.logger.debug(self.log_prefix + '任务开始执行')
    
            plays = pb.get_plays()
    
            for play in plays:
                if play._included_path is not None:
                    self.loader.set_basedir(play._included_path)
                else:
                    self.loader.set_basedir(pb._basedir)
    
                self.inventory.remove_restriction()
                all_vars = self.variable_manager.get_vars(loader=self.loader, play=play)
    
                templar = Templar(loader=self.loader, variables=all_vars)
                new_play = play.copy()
                new_play.post_validate(templar)
                
                if is_checksyntax or tqm is None:
                    return True
    
                # tqm._unreachable_hosts.update(self._unreachable_hosts)
                            
                batches = self._get_serialized_batches(new_play)
                if len(batches) == 0:
                    tqm.send_callback('v2_playbook_on_play_start', new_play)
                    tqm.send_callback('v2_playbook_on_no_hosts_matched')
                    self.logger.debug(self.log_prefix + '任务开始执行，但没有匹配主机')
                    # 需要写日志,需要写该模块
                    continue
                               
                for batch in batches:
                    self.inventory.restrict_to_hosts(batch)
                    try :
                        tqm.run(play)
                    except Exception as e:
                        print(e)
                        pass
                                    
                # self._unreachable_hosts.update(tqm._unreachable_hosts)
    
            tqm.send_callback('v2_playbook_on_stats', tqm._stats)
            self.logger.debug(self.log_prefix + '任务执行完比')
            # self.host_list = self.inventory.get_hosts(play.hosts)
                        
            tqm.cleanup()
            self.loader.cleanup_all_tmp_files()
            return True
        except Exception as e:
            print(e)
            if is_checksyntax :
                return False
            else :
                return False


    def _flush_cache(self):
        for host in self.inventory.list_hosts():
            hostname = host.get_name()
            self.variable_manager.clear_facts(hostname)
            

    def _get_serialized_batches(self, play):

        '''
        把主机列表分批次
        '''
        
        all_hosts = self.inventory.get_hosts(play.hosts)
        all_hosts_len = len(all_hosts)

        serial_batch_list = play.serial
        if len(serial_batch_list) == 0:
            serial_batch_list = [-1]

        cur_item = 0
        serialized_batches = []

        while len(all_hosts) > 0:
            serial = pct_to_int(serial_batch_list[cur_item], all_hosts_len)
            if serial <= 0:
                serialized_batches.append(all_hosts)
                break
            else:
                play_hosts = []
                for x in range(serial):
                    print(x)
                    if len(all_hosts) > 0:
                        play_hosts.append(all_hosts.pop(0))

                serialized_batches.append(play_hosts)

            cur_item += 1
            if cur_item > len(serial_batch_list) - 1:
                cur_item = len(serial_batch_list) - 1

        return serialized_batches


    def _loading_callback(self, yamlfile):
        if not self.log_router:
            self.log_router = Routing_Logging()

        read2file_api = Read_File(self.username, vault_passwd=self.vault_passwd, mongoclient=self.mongoclient)
        result = read2file_api.main(yamlfile, preserve=False, together=True)
        if result[0] :
            yaml_content = result[1]
        else :
            yaml_content = {}

        self.callback = Write_Storage(
            self.work_uuid,
            self.work_name,
            self.username,
            self.exec_mode,
            self._show_protectfield(),
            self.inventory_content,
            self.describe,
            yaml_content=yaml_content,
            log_router=self.log_router,
            )

        if self.callback:
            self.logger.info(self.log_prefix + '使用程序自己编写的callback函数')
            pass
        elif self.options.one_line:
            self.callback = 'oneline'
        else:
            self.callback = 'minimal'
