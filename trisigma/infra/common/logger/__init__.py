"""
from .smtp import SMTPHandler
from .amqp import AMQPHandler
from .file import CustomFileHandler
import logging

logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Notifier
notifier = logging.getLogger("notifier")
notifier.setLevel(logging.INFO)
notif_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
notif_handler = CustomSMTPHandler(
    "cakarbill@gmail.com",
    "pgufemogpltrqsgk",
    "ardagkmhs@gmail.com"
)
notif_handler.setFormatter(notif_formatter)
notif_handler.setLevel(logging.INFO)
notifier.addHandler(notif_handler)

# AMQP
logger = logging.getLogger()
logger.setLevel(logging.INFO)
#logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_formatter = CustomFormatter()
logger_handler = RabbitMQHandler()
logger_handler.setFormatter(logger_formatter)
logger_handler.setLevel(logging.INFO)
logger.addHandler(logger_handler)
pikalogger = logging.getLogger("pika")
#pikalogger.setLevel(logging.CRITICAL)

# File
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
"""
