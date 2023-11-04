import calendar
from datetime import datetime

from utils.config import ConfigK8sProcess
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_async_method, handle_exceptions_method


class VeleroChecker:
    """
    The class allows to process the data received from k8s APIs
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 queue=None,
                 dispatcher_queue=None,
                 dispatcher_max_msg_len=8000,
                 dispatcher_alive_message_hours=24,
                 k8s_key_config: ConfigK8sProcess = None):

        self.print_helper = PrintHelper('velero_checker', logger)
        self.debug_on = debug_on

        self.print_helper.debug_if(self.debug_on,
                                   f"__init__")

        self.queue = queue

        self.dispatcher_max_msg_len = dispatcher_max_msg_len
        self.dispatcher_queue = dispatcher_queue

        self.k8s_config = ConfigK8sProcess()
        if k8s_key_config is not None:
            self.k8s_config = k8s_key_config

        self.old_schedule_status = {}
        self.old_backup = {}

        self.alive_message_seconds = dispatcher_alive_message_hours * 3600
        self.last_send = calendar.timegm(datetime.today().timetuple())

        self.cluster_name = ""
        self.force_alive_message = False

        self.send_config = False

        self.final_message = ""
        self.unique_message = False

    @handle_exceptions_async_method
    async def __put_in_queue__(self,
                               queue,
                               obj):
        """
        Add new element to the queue
        :param queue: reference to a queue
        :param obj: objet to add
        """
        self.print_helper.info_if(self.debug_on, "__put_in_queue__")

        await queue.put(obj)

    @handle_exceptions_async_method
    async def send_to_dispatcher(self, message):
        """
        Send message to dispatcher engine
        @param message: message to send
        """
        self.print_helper.info(f"send_to_dispatcher. msg len= {len(message)}-unique {self.unique_message} ")
        if len(message) > 0:
            if not self.unique_message:
                self.last_send = calendar.timegm(datetime.today().timetuple())
                await self.__put_in_queue__(self.dispatcher_queue,
                                            message)
            else:

                if len(self.final_message) > 0:
                    self.print_helper.info(f"send_to_dispatcher. concat message- len({len(self.final_message)})")
                    self.final_message = f"{self.final_message}\n{'-' * 20}\n{message}"
                else:
                    self.print_helper.info(f"send_to_dispatcher. start message")
                    self.final_message = f"{message}"

    @handle_exceptions_async_method
    async def send_to_dispatcher_summary(self):
        """
        Send summary message to dispatcher engine
        """

        self.print_helper.info(f"send_to_dispatcher_summary. message-len= {len(self.final_message)}")
        # Chck if the final message is not empty
        if len(self.final_message) > 10:
            self.final_message = f"Start report\n{self.final_message}\nEnd report"
            self.last_send = calendar.timegm(datetime.today().timetuple())
            await self.__put_in_queue__(self.dispatcher_queue,
                                        self.final_message)

        self.final_message = ""
        self.unique_message = False

    @handle_exceptions_async_method
    async def __unpack_data__(self, data):
        """
         Check the key received and calls the procedure associated with the key type
        :param data:
        """
        self.print_helper.debug_if("__unpack_data")
        try:
            if isinstance(data, dict):
                if self.k8s_config.cluster_name_key in data:
                    await self.__process_cluster_name__(data)

                elif self.k8s_config.schedule_key in data:
                    await self.__process_schedule_report(data[self.k8s_config.schedule_key])

                elif self.k8s_config.backup_key in data:
                    await self.__process_last_backup_report(data[self.k8s_config.backup_key])

                elif self.k8s_config.disp_msg_key_start in data:
                    self.unique_message = True
                    self.final_message = ""

                elif self.k8s_config.disp_msg_key_end in data:
                    await self.send_to_dispatcher_summary()
                else:
                    self.print_helper.info(f"key not defined")
            else:
                self.print_helper.info(f"__unpack_data.the message is not a type of dict")

            # dispatcher alive message
            if self.alive_message_seconds > 0:
                diff = calendar.timegm(datetime.today().timetuple()) - self.last_send

                if diff > self.alive_message_seconds or self.force_alive_message:
                    self.print_helper.info(f"__unpack_data.send alive message")
                    await self.send_to_dispatcher(f"Cluster: {self.cluster_name}"
                                                  f"\nvelero-watchdog is running."
                                                  f"\nThis is an alive message"
                                                  f"\nNo warning/errors were triggered in the last "
                                                  f"{int(self.alive_message_seconds / 3600)} "
                                                  f"hours ")
                    self.force_alive_message = False

        except Exception as err:
            self.print_helper.error_and_exception(f"__unpack_data", err)

    @handle_exceptions_method
    def _extract_days_from_str(self, str_number):
        self.print_helper.info("_extract_days_from_str")
        value = -1

        index = str_number.find('d')

        if index != -1:
            value = int(str_number.strip()[:index])

        if value > 0:
            return value
        else:
            return None

    @handle_exceptions_method
    def _get_backup_error_message(self, message):
        # self.print_helper.info("_get_backup_error_message")
        if message == '[]':
            return ''
        else:
            return f'{message}'

    @handle_exceptions_method
    def _extract_days_from_str(self, str_number):
        # self.print_helper.info("_extract_days_from_str")
        value = -1

        index = str_number.find('d')

        if index != -1:
            value = int(str_number.strip()[:index])

        if value > 0:
            return value
        else:
            return None

    async def __process_last_backup_report(self, data):
        self.print_helper.info("__last_backup_report")
        backups = data['backups']
        unscheduled = data['us_ns']
        try:
            if self.old_backup == data:
                self.print_helper.info("__last_backup_report. do nothing same data")
                return

            message = ''

            # counter
            backup_count = len(backups)
            backup_completed = 0
            backup_in_progress = 0
            backup_failed = 0
            backup_partially_failed = 0
            backup_in_errors = 0
            backup_in_wrn = 0
            expired_backup = 0
            backup_not_retrieved = 0

            # message strings
            backup_in_progress_str = ''
            error_str = ''
            wrn_str = ''
            backup_failed_str = ''
            backup_partially_failed_str = ''
            backup_expired_str = ''

            point = '\u2022'

            for backup_name, backup_info in backups.items():
                self.print_helper.debug_if(self.debug_on, f'Backup schedule: {backup_name}')

                #
                # build current state string
                #
                current_state = str(backup_name) + '\n'

                current_state += '\t schedule name=' + str(backup_info['schedule']) + '\n'

                # add end at field
                if len(backup_info['completion_timestamp']) > 0:
                    current_state += '\t end at=' + str(backup_info['completion_timestamp']) + '\n'

                # add expire field
                if len(backup_info['expire']) > 0:
                    current_state += '\t expire=' + str(backup_info['expire'])

                    day = self._extract_days_from_str(str(backup_info['expire']))
                    if day is None:
                        backup_not_retrieved += 1
                        current_state += f'**IS NOT VALID{backup_info["expire"]}'
                    elif day < self.k8s_config.EXPIRES_DAYS_WARNING:
                        expired_backup += 1
                        backup_expired_str += f'\n\t{str(backup_name)}'
                        current_state += '**WARNING'

                    current_state += '\n'

                # add status field
                if len(backup_info['phase']) > 0:
                    current_state += '\t status=' + str(backup_info['phase']) + '\n'
                    if backup_info['phase'].lower() == 'completed':
                        backup_completed += 1
                    elif backup_info['phase'].lower() == 'inprogress':
                        backup_in_progress_str += f'\n\t{str(backup_name)}'
                        backup_in_progress += 1
                    elif backup_info['phase'].lower() == 'failed':
                        backup_failed_str += f'\n\t{str(backup_name)}'
                        backup_failed += 1
                    elif backup_info['phase'].lower() == 'partiallyfailed':
                        backup_partially_failed_str += f'\n\t{str(backup_name)}'
                        backup_partially_failed += 1

                # add error field
                error = self._get_backup_error_message(str(backup_info['errors']))
                if len(error) > 0:
                    error_str += f'\t{str(backup_name)}'
                    current_state += '\t' + ' error=' + error + ' '
                    backup_in_errors += 1

                # add warning field
                wrn = self._get_backup_error_message(str(backup_info['warnings']))
                if len(wrn) > 0:
                    wrn_str += f'\t{str(backup_name)}'
                    current_state += '\t' + 'warning=' + wrn + '\n'
                    backup_in_wrn += 1

                current_state += '\n'
                message += current_state

            message = f'Backup details [{backup_count}/{unscheduled["counter_all"]}]:\n{message}'

            message_header = (f'{point} Namespaces={unscheduled["counter_all"]} \n'
                              f'{point} Unscheduled namespaces={unscheduled["counter"]}\n'
                              f'Backups Stats based on last backup for every schedule and backup without schedule'
                              f'\n{point} Total={backup_count}'
                              f'\n{point} Completed={backup_completed}')

            if backup_in_progress > 0:
                message_header += f'\n{point} In Progress={backup_in_progress}{backup_in_progress_str}'
            if backup_in_errors > 0:
                message_header += f'\n{point} With Errors={backup_in_errors}\n{error_str}'
            if backup_in_wrn > 0:
                message_header += f'\n{point} With Warnings={backup_in_wrn}\n{wrn_str}'
            if backup_failed > 0:
                message_header += f'\n{point} Failed={backup_failed}{backup_failed_str}'
            if backup_partially_failed > 0:
                message_header += f'\n{point} Partially Failed={backup_partially_failed}{backup_partially_failed_str}'

            if expired_backup > 0:
                message_header += (f'\n{point} Number of backups in warning period={expired_backup} '
                                   f'[expires day less than {self.k8s_config.EXPIRES_DAYS_WARNING}d]'
                                   f'{backup_expired_str}')

            if len(unscheduled['difference']) > 0:
                str_namespace = ''
                for name_s in unscheduled['difference']:
                    str_namespace += f'\t{name_s}\n'
                if len(str_namespace) > 0:
                    message = (f'Namespace without active backup [{unscheduled["counter"]}/{unscheduled["counter_all"]}]'
                               f':\n{str_namespace}')

            out_message = f"{message_header}\n{message}"

            if len(out_message) > 10:
                await self.send_to_dispatcher(out_message)

            self.old_backup = data

        except Exception as err:
            # self.print_helper.error(f"consumer error : {err}")
            self.print_helper.error_and_exception(f"__last_backup_report", err)

    @staticmethod
    def find_dict_difference(dict1, dict2):
        # Find keys that are unique to each dictionary
        keys_only_in_dict1 = set(dict1.keys()) - set(dict2.keys())
        keys_only_in_dict2 = set(dict2.keys()) - set(dict1.keys())

        # Find keys that are common to both dictionaries but have different values
        differing_keys = [key for key in dict1 if key in dict2 and dict1[key] != dict2[key]]

        # Create dictionaries containing the differing key-value pairs
        differing_dict1 = {key: dict1[key] for key in differing_keys}
        differing_dict2 = {key: dict2[key] for key in differing_keys}

        return {
            "removed": list(keys_only_in_dict1),
            "added": list(keys_only_in_dict2),
            "old_values": differing_dict1,
            "new_values": differing_dict2,
        }

    async def __process_schedule_report(self, data):
        self.print_helper.info("__process_schedule_report")

        try:
            if self.old_schedule_status == data:
                self.print_helper.info("__process_schedule_report. do nothing same data")
                return
            message = ''
            diff = self.find_dict_difference(self.old_schedule_status, data)

            if len(diff) > 0:
                if len(diff['removed']) > 0:
                    message += 'Removed scheduled:'
                    for rem in diff['removed']:
                        message += '\n' + rem

                if len(self.old_schedule_status) > 0 and len(diff['added']) > 0:
                    message += '\nAdded scheduled:'
                    for add in diff['added']:
                        message += '\n' + add

                if len(diff['old_values']) > 0:
                    message += '\nUpdate scheduled:'
                    for schedule_name in diff['old_values']:
                        message += "Schedule name:" + schedule_name + "\n"
                        for field in diff['old_values'][schedule_name]:
                            if diff['old_values'][schedule_name][field] != diff['new_values'][schedule_name][field]:
                                message += f"{field}: {diff['old_values'][schedule_name][field]} -> {diff['new_values'][schedule_name][field]}"

            await self.send_to_dispatcher(message)

            self.old_schedule_status = data

        except Exception as err:
            # self.print_helper.error(f"consumer error : {err}")
            self.print_helper.error_and_exception(f"__process_schedule_report", err)

    async def __process_cluster_name__(self, data):
        """
        Obtain cluster name
        @param data:
        """
        self.print_helper.info(f"__process_cluster_name__")

        nodes_name = data[self.k8s_config.cluster_name_key]

        self.print_helper.info(f"cluster name {nodes_name}")
        if nodes_name is not None:
            self.print_helper.info_if(self.debug_on, f"Flush last message")
            # LS 2023.11.04 Send configuration separately
            if self.send_config:
                await self.send_to_dispatcher(f"Cluster name= {nodes_name}")
            else:
                await self.send_active_configuration(f"Cluster name= {nodes_name}")

        self.cluster_name = nodes_name

    @handle_exceptions_async_method
    async def send_active_configuration(self, sub_title=None):
        """
        Send a message to Telegram engine of the active setup
        """
        title = "velero-watchdog is restarted"
        if sub_title is not None and len(sub_title) > 0:
            title = f"{title}\n{sub_title}"

        self.print_helper.info_if(self.debug_on, f"send_active_configuration")

        msg = f'Configuration setup:\n'
        if self.k8s_config is not None:
            msg = msg + f"  . backup status= {'ENABLE' if self.k8s_config.backup_enable else '.'}\n"
            msg = msg + f"  . scheduled status= {'ENABLE' if self.k8s_config.schedule_enable else '.'}\n"

            if self.alive_message_seconds >= 3600:
                msg = msg + f"\nAlive message every {int(self.alive_message_seconds / 3600)} hours"
            else:
                msg = msg + f"\nAlive message every {int(self.alive_message_seconds / 60)} minutes"
        else:
            msg = "Error init config class"

        msg = f"{title}\n\n{msg}"
        await self.send_to_dispatcher(msg)

    @handle_exceptions_async_method
    async def run(self):
        """
        Main loop of consumer k8s status_run
        """
        try:
            self.print_helper.info("checker run")
            if self.send_config:
                await self.send_active_configuration()

            while True:
                # get a unit of work
                item = await self.queue.get()

                # check for stop signal
                if item is None:
                    break

                self.print_helper.info_if(self.debug_on,
                                          f"checker new element received")

                if item is not None:
                    await self.__unpack_data__(item)

        except Exception as err:
            self.print_helper.error_and_exception(f"run", err)
