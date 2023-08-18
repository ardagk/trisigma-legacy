from trisigma.integration import utils
from . import translations
from . import config
import time



def setup(conf):
    config.setup(conf)

def loop(callback = lambda: None):
    while True:
        tasks = prepare_tasks()
        results = utils.workers.dispatch(tasks, config.DISPATCH_VOLUME)
        for acc_name, orders in results:
            converted_orders = process_resp(orders)
            utils.accounts.update_orders(converted_orders, acc_name, "binance")
        callback()
        time.sleep(config.LOOP_DELAY)
