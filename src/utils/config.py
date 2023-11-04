from dotenv import load_dotenv
import os
from utils.handle_error import handle_exceptions_static_method, handle_exceptions_method


# class syntax
class ConfigProgram:
    def __init__(self, path_env=None, debug_on=True):
        self.debug_on = debug_on
        res = load_dotenv(dotenv_path=path_env)
        print(f"INFO    [Env] Load env={res}")

    @handle_exceptions_static_method
    def load_key(self, key, default, print_out: bool = True, mask_value: bool = False):
        value = os.getenv(key)
        if value is None or \
                len(value) == 0:
            value = default

        if print_out:
            if mask_value and len(value) > 2:
                index = int(len(value) / 2)
                partial = '*' * index
                if self.debug_on:
                    print(f"INFO    [Env] load_key.key={key} value={value[:index]}{partial}")
            else:
                if self.debug_on:
                    print(f"INFO    [Env] load_key.key={key} value={value}")

        return value

    @handle_exceptions_method
    def logger_key(self):
        return self.load_key('LOG_KEY', 'k8s-wdt')

    @handle_exceptions_method
    def logger_msg_format(self):
        default = '%(asctime)s :: [%(levelname)s] :: %(message)s'
        return self.load_key('LOG_FORMAT', default)

    @handle_exceptions_method
    def logger_save_to_file(self):
        res = self.load_key('LOG_SAVE', 'False')
        return True if res.upper() == 'TRUE' else False

    @handle_exceptions_method
    def logger_folder(self):
        return self.load_key('LOG_DEST_FOLDER',
                             './logs')

    @handle_exceptions_method
    def logger_filename(self):
        return self.load_key('LOG_FILENAME',
                             'k8s.log')

    @handle_exceptions_method
    def logger_max_filesize(self):
        return int(self.load_key('LOG_MAX_FILE_SIZE',
                                 4000000))

    @handle_exceptions_method
    def logger_his_backups_files(self):
        return int(self.load_key('LOG_FILES_BACKUP',
                                 '5'))

    @handle_exceptions_method
    def logger_level(self):
        return int(self.load_key('LOG_LEVEL',
                                 '20'))

    @handle_exceptions_method
    def process_run_sec(self):
        res = self.load_key('PROCESS_CYCLE_SEC',
                            '120')

        if len(res) == 0:
            res = '120'
        return int(res)

    @handle_exceptions_method
    def internal_debug_enable(self):
        res = self.load_key('DEBUG', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def telegram_token(self):
        return self.load_key('TELEGRAM_TOKEN', '', mask_value=True)

    @handle_exceptions_method
    def telegram_chat_id(self):
        return self.load_key('TELEGRAM_CHAT_ID', '', mask_value=True)

    @handle_exceptions_method
    def telegram_enable(self):
        res = self.load_key('TELEGRAM_ENABLE', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def telegram_max_msg_len(self):
        res = self.load_key('TELEGRAM_MAX_MSG_LEN',
                            '3000')

        if len(res) == 0:
            res = '2000'
        return int(res)

    @handle_exceptions_method
    def telegram_rate_limit_minute(self):
        res = self.load_key('TELEGRAM_MAX_MSG_MINUTE',
                            '20')

        if len(res) == 0:
            res = '20'
        return int(res)

    @handle_exceptions_method
    def notification_alive_message_hours(self):
        res = self.load_key('NOTIFICATION_ALIVE_MSG_HOURS',
                            '24')
        n_hours = int(res)
        if n_hours < 0:
            n_hours = 0
        elif n_hours > 100:
            n_hours = 100

        return n_hours

    @handle_exceptions_method
    def email_enable(self):
        res = self.load_key('EMAIL_ENABLE', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def email_smtp_server(self):
        return self.load_key('EMAIL_SMTP_SERVER', '')

    @handle_exceptions_method
    def email_smtp_port(self):
        res = self.load_key('EMAIL_SMTP_PORT',
                            '587')
        n_port = int(res)
        return n_port

    @handle_exceptions_method
    def email_recipient(self):
        return self.load_key('EMAIL_RECIPIENTS', '')

    @handle_exceptions_method
    def email_sender_password(self):
        return self.load_key('EMAIL_PASSWORD', '', mask_value=True)

    @handle_exceptions_method
    def email_sender(self):
        return self.load_key('EMAIL_ACCOUNT', '')

    @handle_exceptions_method
    def k8s_load_kube_config_method(self):
        res = self.load_key('PROCESS_LOAD_KUBE_CONFIG', 'True')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_config_file(self):
        return self.load_key('PROCESS_KUBE_CONFIG', None)

    @handle_exceptions_method
    def k8s_cluster_identification(self):
        return self.load_key('PROCESS_CLUSTER_NAME', None)

    @handle_exceptions_method
    def k8s_incluster_mode(self):
        res = self.load_key('K8S_INCLUSTER_MODE', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def velero_backup_enable(self):
        res = self.load_key('BACKUP_ENABLE', 'True')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def velero_schedule_enable(self):
        res = self.load_key('SCHEDULE_ENABLE', 'True')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def velero_expired_days_warning(self):
        res = self.load_key('EXPIRES_DAYS_WARNING',
                            '20')

        if len(res) == 0:
            res = '20'
        return int(res)


class ConfigK8sProcess:
    def __init__(self, cl_config: ConfigProgram = None):
        self.k8s_in_cluster_mode = True
        self.k8s_config_file = None

        self.cluster_name = None
        self.cluster_name_key = 'cluster'

        self.backup_enable = True
        self.backup_key = 'backup'

        self.schedule_enable = True
        self.schedule_key = 'schedule'

        self.disp_msg_key_unique = True  # Fixed True
        self.disp_msg_key_start = 'msg_key_start'
        self.disp_msg_key_end = 'msg_key_end'

        if cl_config is not None:
            self.__init_configuration_app__(cl_config)

    def __print_configuration__(self):
        """
        Print setup class
        """
        print(f"INFO    [Process setup] k8s cluster name= {self.cluster_name}")

        print(f"INFO    [Process setup] k8s in cluster mode={self.k8s_in_cluster_mode}")
        print(f"INFO    [Process setup] k8s config file={self.k8s_config_file}")
        print(f"INFO    [Process setup] velero backup enable={self.backup_enable}")
        print(f"INFO    [Process setup] velero schedule enable={self.schedule_enable}")

        print(f"INFO    [Process setup] k8s send summary message={self.disp_msg_key_unique}")

    def __init_configuration_app__(self, cl_config: ConfigProgram):
        """
        Init configuration class reading .env file
        """
        self.backup_enable = cl_config.velero_backup_enable()
        self.schedule_enable = cl_config.velero_schedule_enable()
        self.EXPIRES_DAYS_WARNING = cl_config.velero_expired_days_warning()
        self.cluster_name = cl_config.k8s_cluster_identification()
        self.k8s_in_cluster_mode = cl_config.k8s_incluster_mode()
        self.k8s_config_file = cl_config.k8s_config_file()

        self.__print_configuration__()


class ConfigDispatcher:
    def __init__(self, cl_config: ConfigProgram = None):
        self.max_msg_len = 50000
        self.alive_message = 24

        self.telegram_enable = False
        self.telegram_chat_id = '0'
        self.telegram_token = ''
        self.telegram_max_msg_len = 2000
        self.telegram_rate_limit = 20

        self.email_enable = True
        self.email_smtp_server = ''
        self.email_smtp_port = 587
        self.email_sender = ''
        self.email_sender_password = '***'
        self.email_recipient = ''

        if cl_config is not None:
            self.__init_configuration_app__(cl_config)

    def __mask_data__(self, data):
        if len(data) > 2:
            index = int(len(data) / 2)
            partial = '*' * index
            return f"{self.telegram_token[:index]}{partial}"
        else:
            return data

    def __print_configuration__(self):
        """
        Print setup class
        """

        print(f"INFO    [Dispatcher setup] telegram={self.telegram_enable}")
        if self.telegram_enable:
            print(f"INFO    [Dispatcher setup] telegram-chat id={self.telegram_chat_id}")
            print(f"INFO    [Dispatcher setup] telegram-token={self.__mask_data__(self.telegram_token)}")
            print(f"INFO    [Dispatcher setup] telegram-max message length={self.telegram_max_msg_len}")
            print(f"INFO    [Dispatcher setup] telegram-rate limit minute={self.telegram_rate_limit}")
            print(f"INFO    [Dispatcher setup] Notification-alive message every={self.alive_message} hour")

        print(f"INFO    [Dispatcher setup] email={self.email_enable}")
        if self.email_enable:
            print(f"INFO    [Dispatcher setup] email-smtp server={self.email_smtp_server}")
            print(f"INFO    [Dispatcher setup] email-port={self.email_smtp_port}")
            print(f"INFO    [Dispatcher setup] email-sender={self.email_sender}")
            # print(f"INFO    [Dispatcher setup] email-password={self.__mask_data__(self.email_sender_password)}")
            print(f"INFO    [Dispatcher setup] email-password={self.email_sender_password}")
            print(f"INFO    [Dispatcher setup] email-recipient={self.email_recipient}")

    def __init_configuration_app__(self, cl_config: ConfigProgram):
        """
        Init configuration class reading .env file
        """
        # telegram section
        self.telegram_enable = cl_config.telegram_enable()
        self.telegram_chat_id = cl_config.telegram_chat_id()
        self.telegram_token = cl_config.telegram_token()
        self.telegram_max_msg_len = cl_config.telegram_max_msg_len()
        self.telegram_rate_limit = cl_config.telegram_rate_limit_minute()

        self.email_enable = cl_config.email_enable()
        self.email_sender = cl_config.email_sender()
        self.email_sender_password = cl_config.email_sender_password()

        self.email_smtp_port = cl_config.email_smtp_port()
        self.email_smtp_server = cl_config.email_smtp_server()
        self.email_recipient = cl_config.email_recipient()

        self.alive_message = cl_config.notification_alive_message_hours()

        # email section
        self.__print_configuration__()
