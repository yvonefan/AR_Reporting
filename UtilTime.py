# HIT @ EMC Corporation
# UtilTime.py
# Purpose: Provides database access functions
# Author: Youye Sun
# Version: 1.0 04/20/2015
import time, datetime

class TimeHelper:
    def __init__(self,log=None):
        self.logger = log

    def get_mtime(self):
        """
        Gets the machine time
        :return: machine time in ms
        """
        return time.time()

    def mtime_to_local_time(self,mtime=None):
        """
        Coverts machine time to local time
        :param mtime: machine time
        :return: local time in '%m/%d/%Y %H:%M' format
        """
        if mtime is None:
            return ""
        return time.strftime('%m/%d/%Y %H:%M', time.localtime(mtime))


    def mtime_to_local_date(self,mtime=None):
        """
        Gets local date from machine time
        :param mtime: machine time
        :return: local date
        """
        if mtime is None:
            return ""
        return time.strftime('%m/%d/%Y', time.localtime(mtime))

    def mtime_to_radar_date(self, mtime=None):
        return "" if mtime is None else time.strftime('%Y-%m-%d', time.localtime(mtime))

    def get_day_start(self,mtime):
        """
        Gets the start of the day in local time
        :param mtime: machine time
        :return: machine time of the start of the day
        """
        if mtime is None:
            return ""
        else:
            local_date = self.mtime_to_local_date(mtime)
            local_mtime_struct = time.strptime(local_date,'%m/%d/%Y')
            return time.mktime(local_mtime_struct)

    def julain_day_to_calendar_date(self,julian):
        """
        Converts julian date to calendar date
        :param julian: days in julian date
        :return: calendar date
        """
        if julian is None:
            return ""
        else:
            mtime = 946746000 + (julian - 2451545)*24*60*60
            return self.mtime_to_local_date(self.get_day_start(mtime))

    def get_weekly_interval(self,i):
        """
        Gets i number of previous weekly intervals from current time
        :param i: number of previous weekly intervals
        :return: list of weekly interval dates
        """
        res = []
        current_time = self.get_mtime()
        week = 7*24*60*60
        for j in range(0,i):
            res.append(self.mtime_to_local_date(current_time - j*week))
        return res

    def current_weekday(self):
        """
        Get current weekday. Monday is 0 and so on.
        """
        cur_date = self.mtime_to_local_date(self.get_mtime())
        cur_date = time.strptime(cur_date,'%m/%d/%Y')
        cur_date = datetime.date(cur_date.tm_year,cur_date.tm_mon,cur_date.tm_mday)
        return cur_date.weekday()

    def get_weekday(self, mtime):
        """
        Get the weekday of mtime. Monday is 0.
        """
        cur_date = self.mtime_to_local_date(mtime)
        cur_date = time.strptime(cur_date,'%m/%d/%Y')
        cur_date = datetime.date(cur_date.tm_year,cur_date.tm_mon,cur_date.tm_mday)
        return cur_date.weekday()

    def get_week_start(self, mtime):
        """
        Gets the start of the week containing mtime in local time
        :param mtime: machine time
        :return: machine time of the start of the week
        """
        weekday = self.get_weekday(mtime)
        daystart = self.get_day_start(mtime)
        return daystart - weekday*24*60*60

    def date_str_to_date_obj(self, dstr):
        dat = time.strptime(dstr,'%m/%d/%Y')
        dat = datetime.date(dat.tm_year,dat.tm_mon,dat.tm_mday)
        return dat