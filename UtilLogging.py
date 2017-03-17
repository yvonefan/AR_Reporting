# HIT @ EMC Corporation
# UtilLogging.py
# Purpose: Provides database access functions
# Author: Ming Yao
# Date: 08/01/2016

import logging,time,os

fpath = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = fpath+'\\log\\' + time.strftime('%Y%m%d%H%M',time.localtime(time.time())) + '.txt'

class LogHelper:
    def __init__(self, logfile=LOG_FILE):
        self.log_file = logfile

    def debug(self, message):
        """
        Writes the message into log file
        :param logg_file: path to the log file
        :param message: message to be written
        :return:
        """
        logging.basicConfig(filename=self.log_file,filemode='w',level=logging.DEBUG,)
        t = time.localtime()
        print message
        logging.debug('%s - %s' % (time.asctime(t),message))

    def error(self, message):
        """
        Writes the message into log file
        :param logg_file: path to the log file
        :param message: message to be written
        :return:
        """
        logging.basicConfig(filename=self.log_file,filemode='w',level=logging.ERROR,)
        t = time.localtime()
        print message
        logging.exception('%s - %s' % (time.asctime(t),message))


if __name__ == '__main__':
    #logger = LogHelper()
    logger =None
    logger.debug('This message should go to the log file') if logger else "No"

