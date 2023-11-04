from datetime import datetime
from kubernetes import client, config
from collections import OrderedDict

from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_method


class VeleroStatus:

    @handle_exceptions_method
    def __init__(self, k8s_config, debug_on, logger, print_helper):

        self.print_helper = PrintHelper('velero_status', logger)
        self.print_debug = debug_on

        self.print_helper.debug_if(self.print_debug, f"__init__")

        self.debug = debug_on

        if k8s_config.k8s_in_cluster_mode:
            config.load_incluster_config()
        else:
            config.load_kube_config(config_file=k8s_config.k8s_config_file)

        self.v1 = client.CoreV1Api()
        self.client = client.CustomObjectsApi()
        self.expires_day_warning = k8s_config.EXPIRES_DAYS_WARNING

    @handle_exceptions_method
    def _get_k8s_namespace(self):
        self.print_helper.debug_if(self.debug, '_get_namespace_list...')

        # Get namespaces list
        namespace_list = self.v1.list_namespace()

        # Extract namespace list
        namespaces = [namespace.metadata.name for namespace in namespace_list.items]

        return namespaces

    @handle_exceptions_method
    def get_k8s_velero_schedules(self, namespace='velero'):

        custom_api = self.client

        # Get schedule from velero namespace
        group = 'velero.io'
        version = 'v1'
        plural = 'schedules'
        schedule_list = custom_api.list_namespaced_custom_object(group, version, namespace, plural)

        schedules = {}

        for schedule in schedule_list.get('items', []):
            schedule_name, \
                included_namespaces, \
                included_resources, \
                default_volumes_to_fs_backup, \
                cron_time = self._extract_resources_from_schedule(schedule)
            schedules[schedule_name] = {
                'included_namespaces': included_namespaces,
                'included_resources': included_resources,
                'default_volumes_to_fs_backup': default_volumes_to_fs_backup,
                'cron_time': cron_time
            }
        return schedules

    @handle_exceptions_method
    def get_k8s_last_backup_status(self, namespace='velero'):
        backups = self._get_k8s_last_backup_status(namespace=namespace)
        difference, counter, counter_all = self._get_unscheduled_namespaces()

        unscheduled = {'difference': difference,
                       'counter': counter,
                       'counter_all': counter_all}
        data = {'backups': backups, 'us_ns': unscheduled}

        return data

    @handle_exceptions_method
    def _get_k8s_last_backup_status(self, namespace='velero'):

        custom_api = self.client

        # Get schedule from velero namespace
        group = 'velero.io'
        version = 'v1'
        plural = 'backups'
        backup_list = custom_api.list_namespaced_custom_object(group, version, namespace, plural)

        last_backup_info = OrderedDict()

        # Extract last backup for every schedule
        for backup in backup_list.get('items', []):
            if backup.get('metadata', {}).get('labels').get('velero.io/schedule-name'):
                schedule_name = backup['metadata']['labels']['velero.io/schedule-name']
            else:
                schedule_name = None

            if backup['status'] != {}:
                if 'phase' in backup['status']:
                    phase = backup['status']['phase']
                else:
                    phase = ''
                errors = backup['status'].get('errors', [])
                warnings = backup['status'].get('warnings', [])
                backup_name = backup['metadata']['name']

                time_expires = ''
                if 'phase' in backup['status']:
                    time_expires = backup['status'].get('expiration', "N/A")
                    time_expire__str = str(
                        (datetime.strptime(time_expires, '%Y-%m-%dT%H:%M:%SZ') - datetime.now()).days) + 'd'
                else:
                    if 'progress' in backup['status']:
                        time_expire__str = 'in progress'
                    else:
                        time_expire__str = 'N/A'

                if 'completionTimestamp' in backup['status']:
                    completion_timestamp = backup['status'].get('completionTimestamp')
                else:
                    completion_timestamp = 'N/A'

                backup_same_schedule_name = None
                schedules = []
                backup_same_schedule_data = {}
                if schedule_name is not None:
                    schedules = [last_backup_info[item]["schedule"] for item in dict(last_backup_info)]
                    backup_same_schedule_name = next(
                        (item for item in last_backup_info if last_backup_info[item]["schedule"] == schedule_name),
                        None)
                    if backup_same_schedule_name is not None:
                        backup_same_schedule_data = last_backup_info[backup_same_schedule_name]

                if schedule_name is None \
                        or (schedule_name is not None and schedule_name not in schedules) \
                        or (schedule_name is not None and backup_same_schedule_data is not None and backup_name >
                            backup_same_schedule_data['backup_name']):

                    if backup_same_schedule_name is not None:
                        del last_backup_info[backup_same_schedule_name]
                    last_backup_info[backup_name] = {
                        'backup_name': backup_name,
                        'phase': phase,
                        'errors': errors,
                        'warnings': warnings,
                        'time_expires': time_expires,
                        'schedule': schedule_name,
                        'completion_timestamp': completion_timestamp,
                        'expire': time_expire__str
                    }

        return last_backup_info

    @handle_exceptions_method
    def _get_scheduled_namespaces(self):
        all_ns = []
        schedules = self.get_k8s_velero_schedules()
        for schedule in schedules:
            all_ns = all_ns + schedules[schedule]['included_namespaces']
        return all_ns

    @handle_exceptions_method
    def _get_unscheduled_namespaces(self):
        namespaces = self._get_k8s_namespace()
        all_included_namespaces = self._get_scheduled_namespaces()
        difference = list(set(namespaces) - set(all_included_namespaces))
        difference.sort()
        return difference, len(difference), len(namespaces)

    @handle_exceptions_method
    def _get_backup_error_message(self, message):
        if message == '[]':
            return ''
        else:
            return f'{message}'

    @handle_exceptions_method
    def _extract_days_from_str(self, str_number):
        value = -1

        index = str_number.find('d')

        if index != -1:
            value = int(str_number.strip()[:index])

        if value > 0:
            return value
        else:
            return None

    @handle_exceptions_method
    def _extract_resources_from_schedule(self, schedule):
        try:
            schedule_name = schedule['metadata']['name']
            included_namespaces = []
            included_resources = []
            default_volumes_to_fs_backup = []
            cron_time = ''
            if 'spec' in schedule:
                cron_time = schedule['spec']['schedule']
                included_resources = schedule['spec'].get('includedResources', [])
                included_namespaces = schedule['spec']['template'].get('includedNamespaces', [])
                default_volumes_to_fs_backup = schedule['spec']['template'].get('defaultVolumesToFsBackup', [])

            return schedule_name, included_namespaces, included_resources, default_volumes_to_fs_backup, cron_time
        except Exception as e:
            self.print_helper.error(f"run.{e}")
