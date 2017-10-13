# HIT @ EMC Corporation
# UtilTime.py
# Purpose: Provides database access functions
# Author: Youye Sun
# Version: 1.0 04/20/2015
import time, datetime
import re

class TimeHelper:
    def __init__(self,log=None):
        self.logger = log

    def get_mtime(self):
        """
        Gets the machine time
        :return: machine time in s
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

    def mtime_to_local_file_time(self,mtime=None):
        """
        Coverts machine time to local time
        :param mtime: machine time
        :return: local time in '%m/%d/%Y %H:%M' format
        """
        if mtime is None:
            return ""
        return time.strftime('%Y%m%d_%H%M', time.localtime(mtime))

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

    def get_first_week_start(self):
        """
        Gets the start of the week in the current year. Monday is 0.
        :return: timestamp: the first Monday of this year
        """
        cur_datetime = datetime.datetime.now()
        start_day = datetime.datetime(cur_datetime.year, 1, 1)
        start_day += datetime.timedelta( 7 - start_day.weekday())
        #change datetime to timestamp, unit is second.
        start_day = time.mktime(start_day.timetuple())
        return start_day

    def date_str_to_date_obj(self, dstr):
        dat = time.strptime(dstr,'%m/%d/%Y')
        dat = datetime.date(dat.tm_year,dat.tm_mon,dat.tm_mday)
        return dat

    def strtime_to_datetime(self, strtime):
        '''
        Change strtime like '2016-02-25 20:21:04.242' to datetime like 2016-02-25 20:21:04.242000.
        :param strtime:
        :return:local_datetime
        '''
        local_datetime = datetime.datetime.strptime(strtime, "%Y-%m-%d %H:%M:%S.%f")
        return local_datetime

    def datetime_to_timestamp(self, datetime_obj):
        '''
        Change datetime like 2016-02-25 20:21:04.242000 to timestamp like 1456402864
        :param datetime_obj:
        :return: local_timestamp: unit is s
        '''
        local_timestamp = long(time.mktime(datetime_obj.timetuple()) + datetime_obj.microsecond / 1000.0 / 1000.0)
        return local_timestamp

    def cyc_strtime_to_timestamp(self, strtime):
        '''
        Change strtime like '2017-10-06T15:35:06.000-0400' to timestamp like 1234567.
        :param strtime:
        :return: create_date:unit is s
        '''
        # create_date_str = platformCycloneAR.fields.created  # u'2017-10-06T15:35:06.000-0400'
        match = re.search(r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+).(\d+)-(\d+)', strtime)
        strtime = match.group(1) + '-' + match.group(2) + '-' + match.group(3) + ' ' + match.group(
            4) + ':' + match.group(5) + ':' + match.group(6) + '.' + match.group(7)
        # strtime_to_datetime
        # local_datetime = datetime.strptime(create_date_str, "%Y-%m-%d %H:%M:%S.%f")
        local_datetime = self.strtime_to_datetime(strtime)

        # datetime_to_timestamp
        # local_timestamp = long(time.mktime(local_datetime.timetuple()) * 1000.0 + local_datetime.microsecond / 1000.0)
        # create_date = local_timestamp / 1000.0  # unit is s
        create_date = self.datetime_to_timestamp(local_datetime)
        return create_date