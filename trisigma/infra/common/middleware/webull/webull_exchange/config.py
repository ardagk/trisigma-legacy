import datetime
from webull import webull

TIMEZONE = "America/New_York"

DEFAULT_PAIRS = []
DEFAULT_LOOP_DELAY = 10
DEFAULT_START_DATE = "2021-01-01"
DEFAULT_DISPATCH_VOLUME = 1
DEFAULT_LATEST_ROW_SIZE = 1

LOOP_DELAY: int
COMPLETION_ROW_COUNT: int
DISPATCH_VOLUME: int
START_DATE: datetime.datetime
LATEST_ROW_SIZE: int

pairs: list
wb: webull

def setup(conf):
    global LOOP_DELAY
    global COMPLETION_ROW_COUNT
    global DISPATCH_VOLUME
    global START_DATE
    global LATEST_ROW_SIZE
    global wb
    global pairs

    LOOP_DELAY = conf.get('loop_delay', DEFAULT_LOOP_DELAY)
    COMPLETION_ROW_COUNT = conf.get('completion_row_count')
    DISPATCH_VOLUME = conf.get('dispatch_volume', DEFAULT_DISPATCH_VOLUME)
    START_DATE = datetime.datetime.strptime(conf.get('start_date', DEFAULT_START_DATE), "%Y-%m-%d")
    LASTEST_ROW_SIZE = conf.get('latest_row_size', DEFAULT_LATEST_ROW_SIZE)

    pairs = conf.get('pairs', DEFAULT_PAIRS)
    wb = webull()

