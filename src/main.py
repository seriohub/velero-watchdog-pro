import asyncio
import os

from utils.print_helper import PrintHelper, LLogger
from utils.config import ConfigProgram
from utils.config import ConfigK8sProcess
from utils.config import ConfigDispatcher
from libs.kubernetes_status_run import KubernetesStatusRun
from libs.velero_checker import VeleroChecker
from libs.dispatcher import Dispatcher
from libs.dispatcher_telegram import DispatcherTelegram
from libs.dispatcher_email import DispatcherEmail
from utils.handle_error import handle_exceptions_async_method
from utils.version import __version__
from utils.version import __date__

# init logger engine
init_logger = LLogger()
logger = None
debug_on = True
print_helper = PrintHelper('K8s', None)


# entry point coroutine
@handle_exceptions_async_method
async def main_start(seconds=1800,
                     load_kube_config=False,
                     config_file=None,
                     disp_class: ConfigDispatcher = None,
                     k8s_class: ConfigK8sProcess = None):
    """

    :param seconds: time to scrapy the k8s system
    :param load_kube_config: load kube config ( if False use in cluster method)
    :param config_file: optional config file
    :param disp_class: class dispatcher configuration
    :param k8s_class: class k8s configuration
    """
    # create the shared queue
    queue = asyncio.Queue()
    queue_dispatcher = asyncio.Queue()
    queue_dispatcher_telegram = asyncio.Queue()
    queue_dispatcher_mail = asyncio.Queue()

    k8s_stat_read = KubernetesStatusRun(kube_load_method=load_kube_config,
                                        kube_config_file=config_file,
                                        debug_on=debug_on,
                                        logger=logger,
                                        queue=queue,
                                        cycles_seconds=seconds,
                                        k8s_key_config=k8s_class)

    velero_stat_checker = VeleroChecker(debug_on=debug_on,
                                        logger=logger,
                                        queue=queue,
                                        dispatcher_queue=queue_dispatcher,
                                        dispatcher_max_msg_len=disp_class.max_msg_len,
                                        dispatcher_alive_message_hours=disp_class.alive_message,
                                        k8s_key_config=k8s_class
                                        )

    dispatcher_main = Dispatcher(debug_on=debug_on,
                                 logger=logger,
                                 queue=queue_dispatcher,
                                 queue_telegram=queue_dispatcher_telegram,
                                 queue_mail=queue_dispatcher_mail,
                                 dispatcher_config=disp_class,
                                 k8s_key_config=k8s_class
                                 )

    dispatcher_telegram = DispatcherTelegram(debug_on=debug_on,
                                             logger=logger,
                                             queue=queue_dispatcher_telegram,
                                             dispatcher_config=disp_class,
                                             k8s_key_config=k8s_class
                                             )

    dispatcher_mail = DispatcherEmail(debug_on=debug_on,
                                      logger=logger,
                                      queue=queue_dispatcher_mail,
                                      dispatcher_config=disp_class,
                                      k8s_key_config=k8s_class
                                      )

    try:
        while True:
            print_helper.info("try to restart the service")

            # run the producer and consumers
            await asyncio.gather(k8s_stat_read.run(),
                                 velero_stat_checker.run(),
                                 dispatcher_main.run(),
                                 dispatcher_telegram.run(),
                                 dispatcher_mail.run())

            print_helper.info("the service is not in run")

    except KeyboardInterrupt:
        print_helper.wrn("user request stop")
        pass
    except Exception as e:
        print_helper.error_and_exception(f"main_start", e)


if __name__ == "__main__":
    print(f"INFO    [SYSTEM] start application version {__version__} release date {__date__}")
    path_script = os.path.dirname(os.path.realpath(__file__))
    config_prg = ConfigProgram(debug_on=debug_on)
    debug_on = config_prg.internal_debug_enable()
    clk8s_setup = ConfigK8sProcess(config_prg)

    clk8s_setup_disp = ConfigDispatcher(config_prg)

    # kube config method
    k8s_load_kube_config_method = config_prg.k8s_load_kube_config_method()
    kube_config_file = config_prg.k8s_config_file()
    loop_seconds = config_prg.process_run_sec()

    logger = init_logger.init_logger_from_config(cl_config=config_prg)

    print_helper.set_logger(logger)
    if logger is None:
        print("[ERROR]   Logger does not start")
    else:
        print_helper.info("start Check service")

    print_helper.info("start Watchdog")
    asyncio.run(main_start(loop_seconds,
                           k8s_load_kube_config_method,
                           kube_config_file,
                           clk8s_setup_disp,
                           clk8s_setup
                           ))
