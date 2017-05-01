from datetime import datetime
import logging

BASE_FORMAT = "[%(name)s][%(levelname)-6s] %(message)s"
FILE_FORMAT = "[%(asctime)s]" + BASE_FORMAT

def setup():
    root_logger = logging.getLogger()

    root_logger.setLevel(logging.DEBUG)

    date = datetime.strftime(datetime.utcnow(), '%Y-%m-%d')

    # File Logger
    fh = logging.FileHandler('ceph-doctor-%s.log' % date)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(FILE_FORMAT))

    root_logger.addHandler(fh)
