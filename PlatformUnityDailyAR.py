# HIT @ EMC Corporation
# PlatformUnityDailyAR.py
# Purpose: Defines Platform Unity AR class
# Author: Youye Sun
# Version: 1.0 03/12/2015

from UtilArrayMap import *
from UtilString import *
from UtilTime import *
from UtilLogging import *

logger = LogHelper()
strer = StringHelper(logger)


class PlatformUnityAR:
    entry_id = None
    summary = None
    assigned_to = None
    direct_manager = None
    reported_by = None
    create_date = None
    create_date_local = None
    status = None
    days_in_status = None
    status_details = None
    blocking = None
    priority = None
    type = None
    estimated_checkin_date = None
    estimated_checkin_date_local = None
    reported_by_group = None
    reported_by_function = None
    product_release = None
    product_family = None
    product_area = None
    major_area = None
    release_buildin = None
    classification = None
    num_dup = None
    owning_ca = None
    version_found = None


    def __init__(self,entry_id,summary,assigned_to,direct_manager,reported_by,create_date,create_date_local,status, \
                 days_in_status, status_details,blocking,priority,type,estimated_checkin_date,estimated_checkin_date_local, \
                 reported_by_group,reported_by_function,product_release,product_family,product_area,major_area,
                 release_buildin,classification,num_dup,version_found):
        self.entry_id = entry_id
        self.summary = summary
        self.assigned_to = assigned_to
        self.direct_manager = direct_manager
        self.reported_by = reported_by
        self.create_date = create_date
        self.create_date_local = create_date_local
        self.status = status
        self.days_in_status = days_in_status
        self.status_details = status_details
        self.blocking = blocking
        self.priority = priority
        self.type = type
        self.estimated_checkin_date = estimated_checkin_date
        self.estimated_checkin_date_local = estimated_checkin_date_local
        self.reported_by_group = reported_by_group
        self.reported_by_function = reported_by_function
        self.product_release = product_release
        self.product_family = product_family
        self.product_area = product_area
        self.major_area = major_area
        self.release_buildin = release_buildin
        self.classification = classification
        self.num_dup = num_dup
        self.version_found = version_found
        self.owning_ca = ""



    def display(self):
        print self.entry_id+" , "+self.summary+" , "+self.assigned_to+" , "+self.direct_manager+" , "+ \
            self.reported_by+" , "+self.create_date_local+" , "+self.status+" , "+self.status_details+" , "+ \
            self.blocking+" , "+self.priority+" , "+self.type+" , "+self.estimated_checkin_date_local+" , "+ \
            self.reported_by_group+" , "+self.reported_by_function+" , "+self.product_release+" , "+self.product_family +\
            ", "+self.product_area+" ,"+self.major_area+","+self.release_buildin+","+self.classification+","+\
            str(self.num_dup)+","+self.version_found


def generate_unity_ar_obj(platformUnityAR):
    """
    Generates platform unity AR object from raw database record.
    AR Fields Map:

        Entry-Id: 536870921                string
        Summary: 536870925                 string
        Assigned-to Full Name: 600000701   string
        Direct Manager: 536870929          string
        Reported by: 600000700             string
        Create-date: 3                     int
        Status: 7                          long
        Status Details: 536870941          string
        Blocking: 700000320                long
        Priority: 536870922                string
        Type: 536871084                    string
        Estimated Checkin Date: 536871606  int
        Reported by Group: 536871388       string
        Reported by Function: 536871389    string
        Product Release: 536870940         string
        Product Family: 536871628          string
        Product Area: 8                    string
        Major Area: 536871412              string
        Release Build-in: 536871455        string
        Classification                     string
        Num of Duplicates                  int
        Version Found                      string
        DaysInStatus                       int


    :param platformUnityAR: database record
    :return:
    """
    timer = TimeHelper()
    for key, value in platformUnityAR[1].iteritems():
        if key == 536870921:
            entry_id = strer.str_exclude_pre_zero(value)
        elif key == 536870925:
            summary = value
        elif key == 600000701:
            assigned_to = value
        elif key == 536870929:
            direct_manager = value
        elif key == 600000700:
            reported_by = value
        elif key == 3:
            create_date = value
            create_date_local = timer.mtime_to_local_date(value)
        elif key == 7:
            if value == 0:
                status = "Open"
            elif value == 1:
                status = "Dismissed"
            elif value == 2:
                status = "In-progress"
            elif value == 3:
                status = "Fixed"
            elif value == 4:
                status = "Waiting on Originator"
            else:
                status = "NULL"
        elif key == 536870941:
            status_details = value
        elif key == 700000320:
            if value ==0:
                blocking = "Y"
            #if value == 1:
            else:
                blocking = "N"
        elif key == 536870922:
            priority = value
        elif key == 536871084:
            type = value
        elif key == 536871606:
            estimated_checkin_date = value
            estimated_checkin_date_local = timer.julain_day_to_calendar_date(value)
        elif key == 536871388:
            reported_by_group = value
        elif key == 536871389:
            reported_by_function = value
        elif key == 536870940:
            product_release = value
        elif key == 536871628:
            product_family = value
        elif key == 8:
            product_area = value
        elif key == 536871412:
            major_area = value
        elif key == 536871455:
            release_buildin = value
        elif key == 536870927:
            if value==0:
                classification='Parent'
            elif value==1:
                classification='Child'
            elif value==2:
                classification='Unique'
        elif key == 536870945:
            num_dup = value
        elif key == 536870914:
            version_found = value
        elif key == 'days_in_status':
            days_in_status = value
    return PlatformUnityAR(entry_id,summary,assigned_to,direct_manager,reported_by,create_date,create_date_local, \
                          status,days_in_status,status_details,blocking,priority,type,estimated_checkin_date, \
                          estimated_checkin_date_local,reported_by_group,reported_by_function,product_release,\
                          product_family,product_area,major_area, release_buildin, classification, num_dup,version_found)


def filter_release(ar_obj_list, product_releases):
    """
    Filters the releases as in product_releases
    :param ar_obj_list: list of AR objects
    :param product_releases: list of product releases
    :return: list of qualified AR objects
    """
    res = []
    try:
        for obj in ar_obj_list:
            if obj.product_release in product_releases:
                res.append(obj)
        return sorted(res)
    except Exception,e:
        logger.error(LOG_FILE,e)
        raise


def filter_product_family(ar_obj_list,product_families,if_positive_filter):
    """
    Filter the product family.
    :param ar_obj_list: list of AR object
    :param product_families: list of product family
    :param if_positive_filter: If True, ARs within the product_families will be returned, else otherwise.
    :return: list of AR object
    """
    res = []
    try:
        for obj in ar_obj_list:
            if if_positive_filter:
                if obj.product_family in product_families:
                    res.append(obj)
            else:
                if obj.product_family not in product_families:
                    res.append(obj)
        return sorted(res)
    except Exception,e:
        logger.error(LOG_FILE,e)
        raise

def get_obj_releases(ar_obj_list):
    """
    Gets the releases of the AR objects
    :param ar_obj_list: list of AR objects
    :return: list of releases
    """
    res = []
    for obj in ar_obj_list:
        if obj.product_release not in res:
            res.append(obj.product_release)
    return sorted(res)


def get_blocking_AR(ar_obj_list):
    """
    Gets the blocking ARs
    :param ar_obj_list: list of AR objects
    :return: list of blocking ARs
    """
    res = []
    for obj in ar_obj_list:
        if obj.blocking == 'Y':
            res.append(obj)
    return sorted(res)