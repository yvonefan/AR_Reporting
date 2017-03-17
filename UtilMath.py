# HIT @ EMC Corporation
# UtilMath.py
# Purpose: Provides database access functions
# Author: Youye Sun
# Version: 1.0 04/23/2015


from UtilLogging import *


class MathHelper:
    def __init__(self,log=None):
        self.logger = log

    def ffloor(self,num,gap):
        """
        Gets the floor of a number according to the gap
        :param num: number to get floor for
        :param gap: floor interval
        :return: floor
        """
        try:
            return (num/gap)*gap
        except Exception,e:
            self.logger.error(LOG_FILE,e) if self.logger else ""
            raise

    def rroof(self,num,gap):
        """
        Gets the roof of a number according to the gap
        :param num: number to get roof for
        :param gap: roof interval
        :return: roof
        """
        try:
            return (num/gap + 1)*gap
        except Exception,e:
            self.logger.error(LOG_FILE,e) if self.logger else ""
            raise
