import asyncio

from utils.config import ConfigK8sProcess
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_async_method
from libs.velero_status import VeleroStatus


class KubernetesStatusRun:
    """
    Invoke the state of k8s items cyclically
    """

    def __init__(self,
                 kube_load_method=False,
                 kube_config_file=None,
                 debug_on=True,
                 logger=None,
                 queue=None,
                 cycles_seconds: int = 120,
                 k8s_key_config: ConfigK8sProcess = None):

        self.print_helper = PrintHelper('k8s_status_run', logger)
        self.print_debug = debug_on

        self.print_helper.debug_if(self.print_debug,
                                   f"__init__")

        self.queue = queue

        self.cycle_seconds = cycles_seconds
        self.loop = 0

        self.velero_stat = VeleroStatus(k8s_key_config,
                                        debug_on,
                                        logger,
                                        self.print_helper)

        self.k8s_config = ConfigK8sProcess()
        if k8s_key_config is not None:
            self.k8s_config = k8s_key_config

    @handle_exceptions_async_method
    async def __put_in_queue(self, obj):
        """
        Add object to a queue
        @param obj: data to add in the queue
        """
        self.print_helper.info_if(self.print_debug, "__put_in_queue__")

        await self.queue.put(obj)

    @handle_exceptions_async_method
    async def run(self):
        """
        Main loop
        """
        self.print_helper.info(f"start main procedure seconds {self.cycle_seconds}")

        seconds_waiting = self.cycle_seconds + 1
        index = 0

        # add wait
        await asyncio.sleep(2)

        cluster_name = self.k8s_config.cluster_name

        data_res = {self.k8s_config.cluster_name_key: cluster_name}
        await self.__put_in_queue(data_res)

        while True:
            try:
                if seconds_waiting > self.cycle_seconds:
                    if index == 0:
                        self.loop += 1
                        self.print_helper.info(f"start run status. loop counter {self.loop} - index {index}")
                        if self.loop > 500000:
                            self.loop = 1

                    data_res = {}

                    self.print_helper.info(f"index request {index}-{index}")
                    match index:
                        case 0:
                            # send start data key for capturing the state in one message
                            if self.k8s_config.disp_msg_key_unique:
                                data_res[self.k8s_config.disp_msg_key_start] = "start"

                        case 1:
                            if self.k8s_config.schedule_enable:
                                schedule_list = self.velero_stat.get_k8s_velero_schedules()
                                data_res[self.k8s_config.schedule_key] = schedule_list

                        case 2:
                            if self.k8s_config.backup_enable:
                                backups_list = self.velero_stat.get_k8s_last_backup_status()
                                data_res[self.k8s_config.backup_key] = backups_list

                        case 3:
                            # send end data key for sending message
                            if self.k8s_config.disp_msg_key_unique:
                                data_res[self.k8s_config.disp_msg_key_end] = "end"

                        case _:
                            seconds_waiting = 0
                            index = 0

                    if seconds_waiting > 0:
                        index += 1
                        if data_res:
                            await self.__put_in_queue(data_res)

                    else:
                        index = 0
                        self.print_helper.info(f"end read.{index}")

                if seconds_waiting % 30 == 0:
                    self.print_helper.info(f"...wait next check in {self.cycle_seconds - seconds_waiting} sec")

                await asyncio.sleep(1)
                seconds_waiting += 1

            except Exception as e:
                self.print_helper.error(f"run.{e}")
