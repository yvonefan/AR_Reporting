#!/usr/bin/python

# Copyright 2015 by Platform Product Integration Team.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, not be used in advertising or publicity
# pertaining to distribution

import argparse
import json
import pprint
#import os

from UtilDatabase import *
from PlatformUnityDailyAR import *
from UtilGraph import *
from UtilArrayMap import *
from UtilExcel import *
from UtilEmail import *
from ARAuditTrail import *

from RadarCrawler import *
import ar_radar_report
import xlwt
import warnings
from jira import JIRA


__author__ = "Winnie.Fan@emc.com"

reload(sys)
sys.setdefaultencoding('utf8')

__filename__ = os.path.basename(__file__)
fpath = os.path.dirname(os.path.realpath(__file__))
dataprefix = fpath + '\\data\\'
data_csvprefix = dataprefix + '\\csv\\'
data_daily_openar_prefix = dataprefix + '\\daily_open\\'
data_weekly_inoutar_prefix = dataprefix + '\\weekly_inout\\'
pngprefix = fpath + '\\png\\'
logprefix = fpath + '\\log\\'

logger = LogHelper()
ayer = ArrayMapHelper()
timer = TimeHelper(logger)
crawler = RadarCrawler()
excer = ExcelHelper(logger)
dber = DatabaseHelper(logger)
grapher = GraphHelper(logger)
strer = StringHelper(logger)
jira_session = None

CUR_TIME = int(timer.get_mtime())
CUR_WEEK_START_TIME = timer.get_week_start(CUR_TIME)
PRE_DATE_RADAR = timer.mtime_to_radar_date(CUR_TIME - 24*60*60)
PRE_DATE_LOCAL = timer.mtime_to_local_date(CUR_TIME - 24*60*60)
PRE_WEEK_START_DATE =timer.mtime_to_radar_date(CUR_WEEK_START_TIME -7*24*60*60)
PRE_WEEK_END_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME - 60*60)
CUR_WEEK_START_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME)
CUR_WEEK_END_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME + 7*24*60*60 -60*60)
CUR_DATE = timer.mtime_to_radar_date(CUR_TIME)

BASIC_URL = 'http://radar.usd.lab.emc.com/Classes/Misc/sp.asp?t=ArrivalARS&ex=1&p=%s&tab=B%s&' \
            'p2=Bug|&p1=P00|P01|P02|&p13=%s&p10=%s|&wkend=%s&&dt=%s'

COLOR_SETS = [
    [(155/255.0, 0/255.0, 0/255.0),(255/255.0,0/255.0, 0/255.0),\
     (255/255.0, 102/255.0, 102/255.0),(255/255.0, 204/255.0, 204/255.0),\
     (220/255.0, 100/255.0, 60/255.0),(255/255.0, 128/255.0, 0/255.0), \
     (255/255.0, 178/255.0, 102/255.0),(255/255.0, 255/255.0, 204/255.0)],
    [(220/255.0, 100/255.0, 60/255.0),(255/255.0, 128/255.0, 0/255.0), \
     (255/255.0, 178/255.0, 102/255.0),(255/255.0, 255/255.0, 229/255.0), \
     (102/255.0, 204/255.0, 0/255.0),(153/255.0, 255/255.0, 51/255.0),\
     (204/255.0,255/255.0, 153/255.0),(229/255.0, 255/255.0, 204/255.0)],
    [(102/255.0, 204/255.0, 0/255.0),(153/255.0, 255/255.0, 51/255.0),\
     (204/255.0,255/255.0, 153/255.0),(229/255.0, 255/255.0, 229/255.0),\
     (0/255.0, 128/255.0, 255/255.0),(102/255.0, 178/255.0, 255/255.0), \
     (204/255.0, 229/255.0, 255/255.0),(204/255.0, 255/255.0, 255/255.0)]
]

def arg_parser():
    parser = argparse.ArgumentParser(prog=__filename__,usage='%(prog)s [options]')
    parser.add_argument('-u', nargs=1, dest='username', required=True)
    parser.add_argument('-p', nargs=1, dest='password', required=True)
    parser.add_argument('-config','--configuration',help="provide configuration file",nargs=1)
    parser.add_argument('-t','--test',help="turn on test mode",action="store_true")
    return parser.parse_args()

def init_param(args):
    with open(fpath+'\\'+args.configuration[0]) as cfg:
        data = json.load(cfg)
        parammap = dict(data)
        cfg.close()
        if(args.test):
            parammap['to'] = __author__
            parammap['cc'] = __author__
            parammap['bcc'] = __author__

        parammap['user'] = args.username[0]
        parammap['pwd'] = args.password[0]
        return parammap

def get_ar_obj_list(rawars, isTBV=None):
    logger.debug("getting AR obj list ...")
    res = []
    for ar in rawars:
        #The ar is from Remedy if it is a list.
        if isinstance(ar,list) and 536870921 in ar[1]:
            ar_obj = generate_unity_ar_obj(ar)
            if isTBV:
                #tbv ar from remedy has no field days_in_status, so need to calculate it here.
                (items, num) = dber.get_fixed_time_from_audit_trail_with_rules(ar[1][536870921])
                fixed_time_list = [item[1][536870929] for item in items]
                final_fixed_time = max(fixed_time_list)
                days_in_status = (CUR_TIME - final_fixed_time) / (24 * 60 * 60) + 1
                ar_obj.days_in_status = days_in_status
        elif ar.key:
            ar_obj = generate_cyclone_ar_obj(ar)
            if isTBV:
                final_fixed_time = ar_obj.days_in_status
                final_fixed_time_sec = timer.cyc_strtime_to_timestamp(final_fixed_time)
                days_in_status = (CUR_TIME - final_fixed_time_sec) / (24 * 60 * 60) + 1
                ar_obj.days_in_status = days_in_status

        res.append(ar_obj)
    return res

def save_AR_list_to_excel(ar_list, filename, isTBV=None):
    """
    Saves the content in the list of ARs to excel file
    :param ar_list: list of ARs
    :return:
    """
    timer = TimeHelper()
    text = []
    text.append([])
    if isTBV:
        text[0] = ['Entry-Id', 'Summary', 'Assigned-to', 'Owning\nCA', 'Direct\nManager', 'Reported\nby', 'Create-date', \
                   'Status', 'DaysIn\nStatus', 'Status\nDetails', 'Blocking', 'Prio\nrity', 'ETA', 'Report\nGroup', \
                   'Report\nFunction', 'Major\nArea', 'Product\nArea', 'Product\nFamily', 'Product\nRel.',
                   'Releases Build-in','Classification', 'Num of \nDuplicates', 'Version\nFound', 'Age/Days']
    else:
        text[0] = ['Entry-Id', 'Summary', 'Assigned-to', 'Owning\nCA', 'Direct\nManager', 'Reported\nby', 'Create-date', \
                   'Status', 'Status\nDetails', 'Blocking', 'Prio\nrity', 'ETA', 'Report\nGroup', \
                   'Report\nFunction', 'Major\nArea', 'Product\nArea', 'Product\nFamily', 'Product\nRel.',
                   'Releases Build-in','Classification', 'Num of \nDuplicates', 'Version\nFound', 'Age/Days']

    for obj in ar_list:
        text.append([])
        text[len(text)-1].append(obj.entry_id)
        text[len(text)-1].append(obj.summary)
        text[len(text)-1].append(obj.assigned_to)
        text[len(text)-1].append(obj.owning_ca)
        text[len(text)-1].append(obj.direct_manager)
        text[len(text)-1].append(obj.reported_by)
        text[len(text)-1].append(obj.create_date_local)
        text[len(text)-1].append(obj.status)
        if isTBV:
            text[len(text)-1].append(obj.days_in_status)
        text[len(text)-1].append(obj.status_details)
        text[len(text)-1].append(obj.blocking)
        text[len(text)-1].append(obj.priority)
        #text[len(text)-1].append(obj.type)
        text[len(text)-1].append(obj.estimated_checkin_date_local)
        text[len(text)-1].append(obj.reported_by_group)
        text[len(text)-1].append(obj.reported_by_function)
        text[len(text)-1].append(obj.major_area)
        text[len(text)-1].append(obj.product_area)
        text[len(text)-1].append(obj.product_family)
        text[len(text)-1].append(obj.product_release)
        text[len(text)-1].append(obj.release_buildin)
        text[len(text)-1].append(obj.classification)
        text[len(text)-1].append(obj.num_dup)
        text[len(text)-1].append(obj.version_found)
        text[len(text)-1].append(int((timer.get_mtime()-obj.create_date)/(24*60*60)))
    exler = ExcelHelper(logger)
    exler.save_twod_array_to_excel(text,filename,'ARs',[[1,200*20],[8,70*20],[9,70*20]])
    exler.add_filter(filename,'ARs')

def count_bug_total(arObjList, twodkeyset):
    """
    Counts the number of ARs for each program, and for different priority levels
    :param arObjList: AR obj list
    :param twodkeyset: second dimension key set
    :return: map containing the number of ARs for each program, and for different priority levels
    """
    res = {}
    arrayer = ArrayMapHelper(logger)
    for obj in arObjList:
        arrayer.update_twod_map_values(res, obj.product_release, obj.priority, twodkeyset, iftotal=True)
        #if (obj.product_family == "Unified Systems") or (obj.product_family == "Bearcat"):
            #arrayer.update_twod_map_values(res,obj.product_release,obj.priority,twodkeyset, iftotal=True)
            #if obj.blocking is 'Y':
            #   arrayer.update_twod_map_values(res,obj.product_release,'Blockers',twodkeyset, iftotal=False)
        #if obj.product_family == 'USD Test':
        #    arrayer.update_twod_map_values(res,obj.product_release,'Test Total',twodkeyset, iftotal=False)
    return res

def bug_total_report(arObjList, parammap, title, save_to_file):
    """
    Generates unity bug summary report
    :param arObjList: AR obj list
    :param save_to_file: path to save the report chart
    :return: map containing the total bug count data
    """
    grapher = GraphHelper()
    arrayer = ArrayMapHelper(logger)

    bug_count_map = count_bug_total(arObjList, ['P00','P01','P02','Total'])
    logger.debug("bug_count_map :" + str(bug_count_map))

    #product count map(data type: dictionary)
    map_product = {}
    for key in bug_count_map.keys():
        map_product[key] = arrayer.positive_map_filter(bug_count_map[key], ['P00','P01','P02','Total'])

    #product count table(data type: list)
    #1. Convert data from dict to list
    #2. Order releases(AR numbers > 0) from top to bottom in table by Json code(assinged to manager param map -> Product Release)
    table_product = arrayer.twod_map_to_report_table(map_product, 'Program', True)
    logger.debug("table_product :" + str(table_product))
    custom_ordered_releases = [rel.replace('"', '') for rel in parammap['releases for total report']]
    releases_have_ars = [rel for rel in custom_ordered_releases if rel in bug_count_map.keys()]
    ordered_table_data = [line for rel in releases_have_ars for line in table_product[1:-1] if rel == line[0]]
    ordered_table_product = [table_product[0]] + ordered_table_data + [table_product[-1]]
    logger.debug("ordered_table_product :" + str(ordered_table_product))

    #replaces '0' or 0 to blank(char ' ') in the table
    arrayer.replace_twod_array_zero(ordered_table_product,1,len(ordered_table_product)-2,1,len(ordered_table_product[0])-1,' ')

    #draw table
    plt, table= grapher.draw_table_first_last_row_colored(ordered_table_product, 2.0*len(ordered_table_product[0]),
                                                  0.4*len(ordered_table_product), 0.98, False, title, 'left', 10)

    #save figure
    plt.savefig(save_to_file, bbox_inches='tight')
    return bug_count_map

def count_bug_older_than_two_days(ar_obj_list):
    current_time = timer.get_day_start(timer.get_mtime())
    two_day = 2*24*60*60
    count = 0
    for obj in ar_obj_list:
        if ('MDT' not in obj.entry_id ) and (obj.product_family != 'Unified Systems') and (obj.product_family != 'Bearcat'):
            continue
        tlen = current_time - obj.create_date
        if tlen > two_day:
            count += 1
    return count

def count_bug_older_than_one_week(ar_obj_list):
    current_time = timer.get_day_start(timer.get_mtime())
    one_week = 7*24*60*60
    count = 0
    for obj in ar_obj_list:
        if ('MDT' not in obj.entry_id ) and (obj.product_family != 'Unified Systems') and (obj.product_family != 'Bearcat'):
            continue
        tlen = current_time - obj.create_date
        if tlen > one_week:
            count += 1
    return count

def count_bug_age(ar_obj_list):
    """
    Counts the age of ARs for each program and for different priority levels
    :param ar_obj_list:  list of AR object
    :return: map containing ages of ARs in each program with regarding to different priority levels
    """
    res = {}
    current_time = timer.get_day_start(timer.get_mtime())
    one_week = 7*24*60*60
    oned_key_set =['0-1 week','1-2 week','2-3 week','3-4 week','4-5 week','5-6 week','>=6 week']
    twod_key_set = ['P00','P01','P02']
    for obj in ar_obj_list:
        if ('MDT' not in obj.entry_id ) and (obj.product_family != 'Unified Systems') and (obj.product_family != 'Bearcat'):
            continue
        tlen = current_time - obj.create_date
        if tlen < one_week:
            ayer.update_twod_map_values(res,'0-1 week',obj.priority,twod_key_set,iftotal=True)
        elif tlen < 2*one_week:
            ayer.update_twod_map_values(res,'1-2 week',obj.priority,twod_key_set, iftotal=True)
        elif tlen < 3*one_week:
            ayer.update_twod_map_values(res,'2-3 week',obj.priority,twod_key_set, iftotal=True)
        elif tlen < 4*one_week:
            ayer.update_twod_map_values(res,'3-4 week',obj.priority,twod_key_set, iftotal=True)
        elif tlen < 5*one_week:
            ayer.update_twod_map_values(res,'4-5 week',obj.priority,twod_key_set, iftotal=True)
        elif tlen < 6*one_week:
            ayer.update_twod_map_values(res,'5-6 week',obj.priority,twod_key_set, iftotal=True)
        else:
            ayer.update_twod_map_values(res,'>=6 week',obj.priority,twod_key_set, iftotal=True)
    twod_key_set.append('Total')
    for key in oned_key_set:
        if key not in res.keys():
            res[key]={}
            for n in twod_key_set:
                res[key][n]=0
    return res

def total_age_report(arObjList, ttitle,color_set,save_to_file):
    """
    Generates bug age report
    :param arObjList: list of AR objects
    :param ttitle: title of the report chart
    :param color_set: color set used to draw the rows and cols
    :param save_to_file: path to save the chart to
    :return:
    """

    bug_age_map = count_bug_age(arObjList)

    logger.debug("[total_age_report]---bug_age_map:")
    logger.debug(bug_age_map)

    bug_age_table = ayer.twod_map_to_report_table(bug_age_map,'Age',True)
    rownames = timer.get_weekly_interval(len(bug_age_table) -2)
    rownames.append(rownames[len(rownames)-1])
    rownames.append(" ")
    bug_age_table = ayer.insert_col(bug_age_table,rownames,0)
    ratecols = []
    week_duration =[1,2,3,6]
    total_num = bug_age_table[len(bug_age_table)-1][len(bug_age_table[0])-1]
    col_nums = len(bug_age_table[0])
    for i in range(0,len(week_duration)):
        ratecols.append([])
        ratecols[i].append(">"+str(week_duration[i])+" week")
        num = total_num
        for j in range(0,week_duration[i]):
            num = num - bug_age_table[j+1][col_nums-1]
        for m in range(0,len(bug_age_table)-2):
            ratecols[i].append(" ")
        ratecols[i].append(strer.get_rate_string(num,total_num))
        bug_age_table = ayer.insert_col(bug_age_table,ratecols[i],len(bug_age_table[0]))
    ayer.replace_twod_array_zero(bug_age_table, 1,len(bug_age_table)-2,2,len(bug_age_table[0])-1-len(week_duration),' ')
    plt, table = grapher.draw_age_table(bug_age_table,6.1,2.5,0.9,True,col_nums,week_duration,color_set,ttitle,'left',10)
    plt.savefig(save_to_file, bbox_inches='tight')

def count_direct_manager_bug(ar_obj_list):
    """
    Counts the number of ARs for each direct manager, regarding different product releases
    :param ar_obj_list: list of AR objects
    :return: map containing number of ARs for each direct manager with regarding to different product releases
    """
    ayer = ArrayMapHelper()
    res= {}
    releases = get_obj_releases(ar_obj_list)
    for obj in ar_obj_list:
        ayer.update_twod_map_values(res,obj.direct_manager,obj.product_release,releases, iftotal=True)
    return res

def direct_manager_report(ar_obj_list, title, save_to_file):
    """
    Generates bug report for each direct manager of different product release
    :param ar_obj_list: list of AR objects
    :param save_to_file: path to save the chart to
    :return:
    """
    ayer = ArrayMapHelper()
    strer = StringHelper()
    grapher = GraphHelper()
    direct_manager_bug_map = count_direct_manager_bug(ar_obj_list)
    logger.debug("[direct_manager_report]direct_manager_bug_map :")
    logger.debug(str(direct_manager_bug_map))
    map_without_total = {}
    for key in sorted(direct_manager_bug_map.keys()):
        map_without_total[key] = ayer.negative_map_filter(direct_manager_bug_map[key],['Total'])
    direct_manager_bug_table = ayer.twod_map_to_report_table(map_without_total,'Direct Manager',True)
    total = []
    for key in sorted(direct_manager_bug_map.keys()):
        total.append(direct_manager_bug_map[key]['Total'])
    total.append(ayer.sum_array(total))
    total.insert(0,'Total')
    report_with_total = ayer.insert_col(direct_manager_bug_table,total,len(direct_manager_bug_table[0]))

    for j in range(1,len(report_with_total[0])):
        if len(report_with_total[0][j]) > 6:
            report_with_total[0][j] = strer.split_str_by_length(report_with_total[0][j],j+4)
    ayer.replace_twod_array_zero(report_with_total,1,len(report_with_total)-2,1,
                            len(report_with_total[0])-2,' ')
    #c_width = 0.8*len(report_with_total[0])
    plt, table = grapher.draw_table_first_last_row_colored(report_with_total, 0.9*len(report_with_total[0]),
                                                   0.5*len(report_with_total),0.9, True,
                                                   None, 'left', 10)
    celh = 1.0/(len(report_with_total))*1.8
    cell_dict = table.get_celld()
    for j in range(0,len(report_with_total[0])):
        cell_dict[(0,j)].set_height(celh)
    plt.text(-0.0005*len(report_with_total[0]),1 + 0.7/len(report_with_total),
             title,fontsize=14, ha='left')
    plt.savefig(save_to_file, bbox_inches='tight')

def get_cur_ar_list(ar_list, ca):
    pre_date = PRE_DATE_RADAR
    res = list()
    for ar in ar_list:
        if pre_date in ar.ac_date:
            ar.ca = ca
            res.append(ar)
    return res

def analyz_inar_lists(ar_list, ca):
    res = list()
    arrival_movein = 0
    arrival_new = 0
    arrival_other = 0
    arrival_reopen = 0
    for ar in ar_list:
        if ar.ac_method == "Move in":
            arrival_movein += 1
        elif ar.ac_method == "New":
            arrival_new += 1
        elif ar.ac_method == "Reopen":
            arrival_reopen += 1
        elif ar.ac_method == "Other":
            arrival_other += 1
    total = arrival_movein + arrival_new + arrival_other + arrival_reopen
    res.extend([ca, arrival_movein, arrival_new, arrival_reopen, arrival_other, total])
    return res

def convert_AR_objs_to_html_table(ar_list, table_name):
    """
    Coverts the list of ARs into html table
    :param ar_list: list of ARs
    :param table_name: id of the html table
    :return: html formatted table
    """
    timer = TimeHelper()
    ayer = ArrayMapHelper()
    text = []
    text.append([])
    text[0] = ['Entry-Id','Prio\nrity','Type','Product\nRelease','Summary','Status','Status\nDetails', \
               'Assigned-to','Direct\nManager','Create-date','Age']
    for obj in ar_list:
        text.append([])
        text[len(text)-1].append(obj.entry_id)
        text[len(text)-1].append(obj.priority)
        text[len(text)-1].append(obj.type)
        text[len(text)-1].append(obj.product_release)
        text[len(text)-1].append(obj.summary)
        text[len(text)-1].append(obj.status)
        text[len(text)-1].append(obj.status_details)
        text[len(text)-1].append(obj.assigned_to)
        text[len(text)-1].append(obj.direct_manager)
        text[len(text)-1].append(obj.create_date_local)
        text[len(text)-1].append(int((timer.get_mtime()-obj.create_date)/(24*60*60)))
    #text = ayer.sort_twod_array_by_col(text,1,11)
    #now don't need to save it to html since it has already been saved to png.
    return ayer.twod_array_to_html_table(text, table_name, 'Blocking ARs'), text

def refine_twod_array(twod_array):
    """
    Coverts the twod_array to one-dimention
    :param twod_array
    :return:
    """
    strer = StringHelper()
    res = list()
    for i in range(0, len(twod_array)):
        res.append(list())
        for j in range(0, len(twod_array[0])):
            print twod_array[i][j]
            res[i].append(strer.split_str_by_length(str(twod_array[i][j]), 15, 45))
    return res

def update_last_record(file, timestamp, csvstr, header=''):
    """
    write csvstr to file
    :param file:
    :param timestamp:
    :param csvstr:
    :param header:
    :return:
    """
    with open(file, "a+") as myfile:
        if os.path.getsize(file) == 0:
            myfile.write(header)
        else:
            lines = myfile.readlines()
            l = lines[-1]
            if timestamp in l:
                myfile.seek(0,os.SEEK_END)
                pos = myfile.tell() -len(l) -1
                myfile.seek(pos,os.SEEK_SET)
                myfile.truncate()
        myfile.write(csvstr)
        myfile.close()

def update_AR_summary_history_file(bug_map, releases, file):
    """
    Updates the records in AR summary history file. One record per day.
    :param bug_map: map containing AR infomation
    :return:
    """
    total = 0
    timer = TimeHelper()
    timestamp = timer.mtime_to_local_date(timer.get_mtime())
    for key in bug_map.keys():
        total += bug_map[key]['Total']
    csvstr = timestamp
    header = 'Date'
    for rel in releases:
        rel = rel.replace('"', '')
        header += ',' + rel
        if rel in bug_map.keys():
            csvstr += ',' + str(bug_map[rel]['Total'])
        else:
            csvstr += ',0'
    header += ',' + 'Total' + '\n'
    csvstr += ',' + str(total) + '\n'
    update_last_record(file, timestamp, csvstr, header)

def get_file_enteries(file_name):
    with open(file_name,'r') as myfile:
        lines = myfile.readlines()
        items = lines[0].split(',')
        res = []
        for i in items:
            if ('Date' not in i ) and ('Total' not in i):
                res.append(i)
        myfile.close()
        return res

def generate_AR_trends_report_data_file(num, file_origin, file):
    """
    Generates data file for AR trends report
    :return: the AR records count
    """
    with open(file_origin, 'r') as myfile:
        lines = myfile.readlines()
        newfile = open(file,'w')
        newfile.write(lines[0])
        if len(lines) < num + 1:
            for i in range(1, len(lines)):
                newfile.write(lines[i])
        else:
            for i in range( len(lines) - num, len(lines)):
                newfile.write(lines[i])
        newfile.close()
        myfile.close()
        return len(lines)

def get_ca_map_entry(mmap, v):
    v = "\"" + v + "\""
    for k in mmap.keys():
        if v in mmap[k]:
            return k

def process_ar_fixed_dismissed_in_time_range(ar_in_out_obj_dict, parammap, auditEntries):
    ar = ar_in_out_obj_dict
    for entry in auditEntries:
        for key, value in entry[1].iteritems():
            if key == 536870921:
                entry_id = value
            if key == 536870916:
                from_value = value
            elif key == 536870917:
                to_value = value
            elif key == 536870929:
                touch_date =value
            elif key == 536870938:
                touch_man = value
            elif key == 600000701:
                assignee_fname = value
            elif key == 8:
                product_area = value
            elif key == 7:
                status = value
            elif key == 536870941:
                status_details = value
            elif key == 536871535:
                not_a_child = value
            elif key == 536871412:
                major_area = value
            elif key == 536871084:
                ar_type = value
            elif key == 3:
                create_time = value
            elif key == 536870940:
                product_release = value

        if entry_id not in ar.keys():
            #print ("DEBUG %s" % entry_id)
            ar[entry_id]=dict()
            ar[entry_id]["entry_id"]=entry_id
            ar[entry_id]["from_value"]=from_value
            ar[entry_id]["to_value"]=to_value
            ar[entry_id]["touch_date"]=touch_date
            ar[entry_id]["touch_man"]=touch_man
            ar[entry_id]["assignee_fname"]=assignee_fname
            ar[entry_id]["product_area"]=product_area
            ar[entry_id]["status"]=status
            ar[entry_id]["status_details"]=status_details
            ar[entry_id]["not_a_child"]=not_a_child
            ar[entry_id]["major_area"]=major_area
            ar[entry_id]["ar_type"]=ar_type
            ar[entry_id]['create_time']=create_time
            ar[entry_id]['product_release'] = product_release
            if to_value=="Fixed":
                ar[entry_id]['atf_time']=touch_date
                ar[entry_id]['atf_man']=touch_man
            elif to_value=="Dismissed":
                ar[entry_id]['atm_time']=touch_date
                ar[entry_id]['atm_man']=touch_man
            else:
                print "DEBUG: error happened! 4"
        else:
            if to_value=="Fixed":
                ar[entry_id]['atf_time']=touch_date
                ar[entry_id]['atf_man']=touch_man
            elif to_value=="Dismissed":
                ar[entry_id]['atm_time']=touch_date
                ar[entry_id]['atm_man']=touch_man
            else:
                print "DEBUG: error happened! 5"

def process_ar_reopen_in_time_range(ar_in_out_obj_dict, parammap, auditEntries):
    ar = ar_in_out_obj_dict
    for entry in auditEntries:
        for key, value in entry[1].iteritems():
            if key == 536870921:
                entry_id = value
            if key == 536870916:
                from_value = value
            elif key == 536870917:
                to_value = value
            elif key == 536870929:
                touch_date =value
            elif key == 536870938:
                touch_man = value
            elif key == 600000701:
                assignee_fname = value
            elif key == 8:
                product_area = value
            elif key == 7:
                status = value
            elif key == 536870941:
                status_details = value
            elif key == 536871535:
                not_a_child = value
            elif key == 536871412:
                major_area = value
            elif key == 536871084:
                ar_type = value
            elif key == 3:
                create_time = value
            elif key == 536870940:
                product_release = value

        if entry_id not in ar.keys():
            #print ("DEBUG %s" % entry_id)
            ar[entry_id]=dict()
            ar[entry_id]["entry_id"]=entry_id
            ar[entry_id]["from_value"]=from_value
            ar[entry_id]["to_value"]=to_value
            ar[entry_id]["touch_date"]=touch_date
            ar[entry_id]["touch_man"]=touch_man
            ar[entry_id]["assignee_fname"]=assignee_fname
            ar[entry_id]["product_area"]=product_area
            ar[entry_id]["status"]=status
            ar[entry_id]["status_details"]=status_details
            ar[entry_id]["not_a_child"]=not_a_child
            ar[entry_id]["major_area"]=major_area
            ar[entry_id]["ar_type"]=ar_type
            ar[entry_id]['create_time']=create_time
            ar[entry_id]['product_release'] = product_release
            if to_value=="Open":
                ar[entry_id]['ati_time']=touch_date
                ar[entry_id]['atm_man']=touch_man
            else:
                print "DEBUG: error happened! 4"
        else:
            if to_value=="Open":
                ar[entry_id]['ati_time']=touch_date
                ar[entry_id]['atf_man']=touch_man
            else:
                print "DEBUG: error happened! 5"

def process_ar_from_assigned_to_manager_join(ar_in_out_obj_dict, parammap, auditEntries):
    ar = ar_in_out_obj_dict
    for entry in auditEntries:
        for key, value in entry[1].iteritems():
            if key == 536870921:
                entry_id = value
            elif key == 600000701:
                assignee_fname = value
            elif key == 8:
                product_area = value
            elif key == 7:
                status = value
            elif key == 536870941:
                status_details = value
            elif key == 536871535:
                not_a_child = value
            elif key == 536871412:
                major_area = value
            elif key == 536871084:
                ar_type = value
            elif key == 3:
                create_time = value
            elif key == 536870940:
                product_release = value

        if entry_id not in ar.keys():
            #print ("DEBUG %s "% entry_id)
            ar[entry_id]=dict()
            ar[entry_id]["entry_id"]=entry_id
            ar[entry_id]["assignee_fname"]=assignee_fname
            ar[entry_id]["product_area"]=product_area
            ar[entry_id]["status"]=status
            ar[entry_id]["status_details"]=status_details
            ar[entry_id]["not_a_child"]=not_a_child
            ar[entry_id]["major_area"]=major_area
            ar[entry_id]["ar_type"]=ar_type
            ar[entry_id]['create_time']=create_time
            ar[entry_id]['product_release'] = product_release

def process_ar_from_audit_trail(ar_in_out_obj_dict, parammap, auditEntries):
    ar = ar_in_out_obj_dict
    for entry in auditEntries:
        #search ar in manager table with entry_id to get senior manager info to check if this ar belongs to platform.
        entry_id=''
        attribute_field=''
        from_value=''
        to_value=''
        touch_date=''
        touch_man=''
        assignee_fname=''
        product_area=''
        status=''
        status_details=''
        not_a_child=''
        major_area=''
        ar_type=''
        create_time=''
        product_release = ''

        for key, value in entry[1].iteritems():
            if key == 536870921:
                entry_id = value
            elif key == 536870925:
                attribute_field = value
            elif key == 536870916:
                from_value = value
            elif key == 536870917:
                to_value = value
            elif key == 536870929:
                touch_date =value
            elif key == 536870938:
                touch_man = value
            elif key == 600000701:
                assignee_fname = value
            elif key == 8:
                product_area = value
            elif key == 7:
                status = value
            elif key == 536870941:
                status_details = value
            elif key == 536871535:
                not_a_child = value
            elif key == 536871412:
                major_area = value
            elif key == 536871084:
                ar_type = value
            elif key == 3:
                create_time = value
            elif key == 536870940:
                product_release = value

        #print "DEBUG: Parsing AR[" + entry_id + "]"
        target_area = [str(product_area.replace('"', '')) for product_area in parammap['platform product areas']['product area names']]

        if entry_id not in ar.keys():
            ar[entry_id]=dict()
            ar[entry_id]["entry_id"]=entry_id
            ar[entry_id]["from_value"]=from_value
            ar[entry_id]["to_value"]=to_value
            ar[entry_id]["touch_date"]=touch_date
            ar[entry_id]["touch_man"]=touch_man
            ar[entry_id]["assignee_fname"]=assignee_fname
            ar[entry_id]["product_area"]=product_area
            ar[entry_id]["status"]=status
            ar[entry_id]["status_details"]=status_details
            ar[entry_id]["not_a_child"]=not_a_child
            ar[entry_id]["major_area"]=major_area
            ar[entry_id]["ar_type"]=ar_type
            ar[entry_id]['create_time']=create_time
            ar[entry_id]['product_release'] = product_release
            if attribute_field == "Product Area":
                if from_value in target_area:   # This is an outgoing AR.
                    ar[entry_id]['ato_time']=touch_date
                    ar[entry_id]['ato_man']=touch_man
                elif to_value in target_area:   # This is an incoming AR.
                    ar[entry_id]['ati_time']=touch_date
                    ar[entry_id]['ati_man']=touch_man
                else:
                    print "DEBUG: error happened! 0"
            elif attribute_field == "Classification":   # This is a duplicated AR. But attribute_field still equals to "Product Area"
                ar[entry_id]['atd_time']=touch_date
                ar[entry_id]['atd_man']=touch_man
            else:
                print "DEBUG: error happened! 1 [" + attribute_field + "][" + from_value + "][" + to_value + "]"
        else:
            if attribute_field == "Product Area":
                if from_value in target_area:   # This is an outgoing AR.
                    if "ato_time" not in ar[entry_id].keys():
                        ar[entry_id]['ato_time']=touch_date   #touch_date seems like create-date
                        ar[entry_id]['ato_man']=touch_man
                        ar[entry_id]["from_value"]=from_value
                        ar[entry_id]["to_value"]=to_value
                        ar[entry_id]["touch_date"]=touch_date
                        ar[entry_id]["touch_man"]=touch_man
                    else:
                        #
                        if ar[entry_id]['ato_time']<touch_date:
                            ar[entry_id]['ato_time']=touch_date
                            ar[entry_id]['ato_man']=touch_man
                            ar[entry_id]["from_value"]=from_value
                            ar[entry_id]["to_value"]=to_value
                            ar[entry_id]["touch_date"]=touch_date
                            ar[entry_id]["touch_man"]=touch_man
                elif to_value in target_area:   # This is an incoming AR.
                    if "ati_time" not in ar[entry_id].keys():
                        ar[entry_id]['ati_time']=touch_date
                        ar[entry_id]['ati_man']=touch_man
                        ar[entry_id]["from_value"]=from_value
                        ar[entry_id]["to_value"]=to_value
                        ar[entry_id]["touch_date"]=touch_date
                        ar[entry_id]["touch_man"]=touch_man
                    else:
                        #
                        if ar[entry_id]['ati_time']<touch_date:
                            ar[entry_id]['ati_time']=touch_date
                            ar[entry_id]['ati_man']=touch_man
                            ar[entry_id]["from_value"]=from_value
                            ar[entry_id]["to_value"]=to_value
                            ar[entry_id]["touch_date"]=touch_date
                            ar[entry_id]["touch_man"]=touch_man
                else:
                    print "DEBUG: error happened! 2"
            else:
                print "DEBUG: error happened! 3"

def get_ar_created_in_time_range_per_product_area(ar_in_out_obj_dict, parammap, start_date, end_date):
    #schema = 'EMC:Issue Assigned-to Manager Join'
    get_param = dict()
    get_param['Type'] = parammap['assinged to manager param map']['Type']
    get_param['Priority'] = parammap['assinged to manager param map']['Priority']
    get_param['Product Release'] = parammap['assinged to manager param map']['Product Release']
    get_param['Product Family'] = parammap['assinged to manager param map']['Product Family']
    get_param['Status'] = parammap['assinged to manager param map']['Status']
    # get_param['Create-date Low'] = [str(start_date), ]
    # get_param['Create-date High'] = [str(end_date), ]

    get_param['Senior Manager'] = parammap['assinged to manager param map']['Senior Manager']

    dber = DatabaseHelper()
    entries, num = dber.get_AR_from_assigned_to_manager(get_param)
    if entries:
        process_ar_from_assigned_to_manager_join(ar_in_out_obj_dict, parammap, entries)

def get_ar_created_pa_in_time_range_per_product_area(ar_in_out_obj_dict, parammap, start_date, end_date):
    #schema = 'EMC:Issue Assigned-to Manager Join'
    get_param = dict()
    get_param['Type'] = parammap['assinged to manager param map']['Type']
    get_param['Priority'] = parammap['assinged to manager param map']['Priority']
    get_param['Product Release'] = parammap['assinged to manager param map']['Product Release']
    get_param['Product Family'] = parammap['assinged to manager param map']['Product Family']
    get_param['Status'] = parammap['assinged to manager param map']['Status']
    # get_param['Create-date Low'] = [str(start_date), ]
    # get_param['Create-date High'] = [str(end_date), ]
    ca_dict = dict(parammap['platform product areas'])
    for k, v in ca_dict.iteritems():
        if 'Product Area' not in get_param.keys():
            get_param['Product Area'] = list(v)
        else:
            get_param['Product Area'] += list(v)

    dber = DatabaseHelper()
    entries, num = dber.get_AR_from_assigned_to_manager(get_param)
    if entries:
        process_ar_from_assigned_to_manager_join(ar_in_out_obj_dict, parammap, entries)

def get_ar_fixed_dismissed_in_time_range(ar_in_out_obj_dict, parammap, start_date, end_date):
    schema = 'EMC:Issue_Audit_join'
    get_param = dict()
    get_param['Type'] = parammap['audit trail param map']['Type']
    get_param['Priority'] = parammap['audit trail param map']['Priority']
    get_param['Product Release'] = parammap['audit trail param map']['Product Release']
    get_param['Product Family'] = parammap['audit trail param map']['Product Family']
    get_param['To Value'] = ["\"Fixed\"","\"Dismissed\""]
    get_param['From Time'] = [str(start_date), ]
    get_param['To Time'] = [str(end_date), ]
    get_param['Attribute Label'] = ["\"Status\"",]
    ca_dict = dict(parammap['platform product areas'])
    for k, v in ca_dict.iteritems():
        if 'Product Area' not in get_param.keys():
            get_param['Product Area'] = list(v)
        else:
            get_param['Product Area'] += list(v)

    entries, num = dber.get_AR_from_audit_trail(get_param)
    process_ar_fixed_dismissed_in_time_range(ar_in_out_obj_dict, parammap, entries)

def get_ar_reopen_in_time_range(ar_in_out_obj_dict, parammap, start_date, end_date):
    schema = 'EMC:Issue_Audit_join'
    get_param = dict()
    get_param['Type'] = parammap['audit trail param map']['Type']
    get_param['Priority'] = parammap['audit trail param map']['Priority']
    get_param['Product Release'] = parammap['audit trail param map']['Product Release']
    get_param['Product Family'] = parammap['audit trail param map']['Product Family']
    get_param['From Value'] = ["\"Fixed\"","\"Dismissed\""]
    get_param['To Value'] = ["\"Open\""]
    get_param['From Time'] = [str(start_date), ]
    get_param['To Time'] = [str(end_date), ]
    get_param['Attribute Label'] = ["\"Status\"",]
    ca_dict = dict(parammap['platform product areas'])
    for k, v in ca_dict.iteritems():
        if 'Product Area' not in get_param.keys():
            get_param['Product Area'] = list(v)
        else:
            get_param['Product Area'] += list(v)

    entries, num = dber.get_AR_from_audit_trail(get_param)
    process_ar_reopen_in_time_range(ar_in_out_obj_dict, parammap, entries)

def get_in_out_ar_from_audit_trail_with_rules(ar_in_out_obj_dict, parammap, start_date, end_date):
    """
    Get all the ars from audit trail table, the product release are defined in platform_config.json.
    :param parammap:
    :param start_date:
    :param end_date:
    :param ar_direction: True - in, assigned to platform; False - out, assigned to other product areas
    :return:res - the ars from audit trail table
    """
    get_param = dict(parammap["audit trail param map"])
    get_param['From Time'] = [str(start_date), ]
    get_param['To Time'] = [str(end_date), ]

    ca_dict = dict(parammap['platform product areas'])
    for k, v in ca_dict.iteritems():
        if 'From Value' not in get_param.keys():
            get_param['From Value'] = list(v)
        else:
            get_param['From Value'] += list(v)

    dber = DatabaseHelper()
    entries1, num1 = dber.get_AR_from_audit_trail(get_param)
    get_param['To Value'] = get_param['From Value']
    get_param.pop('From Value')
    entries2, num2 = dber.get_AR_from_audit_trail(get_param)
    ar_list = entries1 + entries2
    process_ar_from_audit_trail(ar_in_out_obj_dict, parammap, ar_list)

def filter_ar_with_release(ar_in_out_obj_dict, parammap, start_date,end_date, file):
    """

    :param parammap:
    :param rls_cnt_dict:
    :param ar_list:
    :return:
    """

    ar_weekly_in_out_record = dict()
    ar_in_out_in_time_range = dict()
    ar_weekly_in_out_record['Total_In'] = 0
    ar_weekly_in_out_record['Total_Out'] = 0
    concern_release = []
    for product_release in parammap["audit trail param map"]["Specific Product Release"]:
        product_release = str(product_release.replace('"', ''))
        concern_release.append(product_release)
        ar_weekly_in_out_record[product_release + '_In'] = 0
        ar_weekly_in_out_record[product_release + '_Out'] = 0

    for k, v in ar_in_out_obj_dict.iteritems():
        #For the child ar, in_time should not be dup_time, it should be create_time
        # if 'create_time' in v.keys() and 'in_time' in v.keys():
        #     if v["not_a_child"] != 0:
        #         v['in_time'] = v['create_time']
        #
        #For the child ar, if in_time > out_time, i.e., after duplicated, the in_time is the updated of its parent ar not this child ar.
        if 'in_time' in v.keys() and 'out_time' in v.keys():
            if v["not_a_child"] != 0 and v['in_time'] >= v['out_time']:
                v['in_time'] = 0
                v['out_time'] = 0

        if 'in_time' in v.keys():
            # remove the ar not in search time range, since get_child_ar_from_audit_trail get all child ars in audit table included ars not in search time range.
            if v['in_time'] >= start_date and v['in_time'] <= end_date:
                ar_in_out_in_time_range[k] = v
                ar_weekly_in_out_record['Total_In'] += 1
                if 'product_release' in v.keys() and v['product_release'] in concern_release:
                    ar_weekly_in_out_record[v['product_release'] + '_In'] += 1

        if 'out_time' in v.keys():
            if v['out_time'] >= start_date and v['out_time'] <= end_date:
                ar_in_out_in_time_range[k] = v
                ar_weekly_in_out_record['Total_Out'] += 1
                if 'product_release' in v.keys() and v['product_release'] in concern_release:
                    ar_weekly_in_out_record[v['product_release'] + '_Out'] += 1

    from copy import deepcopy
    ar_in_out_obj_dict.clear()
    ar_in_out_obj_dict.update(ar_in_out_in_time_range)
    header = 'Date'
    csvstr = timer.mtime_to_local_date(end_date)
    for k, v in ar_weekly_in_out_record.iteritems():
        header += ',' + k
        csvstr += ',' + str(v)
    header += '\n'
    csvstr += '\n'
    timestamp = timer.mtime_to_local_date(timer.get_mtime())
    update_last_record(file, timestamp, csvstr, header)
    #return ar_in_out_in_time_range

def update_dup_time_for_child_ar(ar_in_out_obj_dict, entry_id, start_date, end_date):
    ar = ar_in_out_obj_dict
    dber = DatabaseHelper()
    auditEntries, num = dber.get_child_ar_from_audit_trail(entry_id,start_date,end_date)
    for entry in auditEntries:
        for key, value in entry[1].iteritems():
            if key == 536870929:
                #touch_date is the date of this ar changed to child from unique or parent
                touch_date =value
            elif key == 536870938:
                touch_man = value
        if "atd_time" not in ar[entry_id].keys():
            ar[entry_id]['atd_time']=touch_date
            ar[entry_id]['atd_man']=touch_man
        else:
            #when deplicated for several times, atd_time use the latest duplicate time. Since if the parent ar is duplicated again, the last child will also be updated the touch_date.
            if ar[entry_id]['atd_time']<touch_date:
                ar[entry_id]['atd_time']=touch_date
                ar[entry_id]['atd_man']=touch_man

def process_ar_total_weekly_in_out(ar_in_out_obj_dict, parammap, start_date, end_date):
    ar = ar_in_out_obj_dict
    print "DEBUG: Calculate In/Out Time and fill up the rest fields"
    length = str(len(ar))
    print ("DEBUG: AR Number before filter[%s]" % length)
    i = 0
    for x in ar.keys():
        ar[x]['error'] = ""
        ar[x]["hide"] = 0

        pa = ar[x]['product_area']

        product_area = [str(product_area.replace('"', '')) for product_area in
                       parammap['platform product areas']['product area names']]
        # AR X is in target area now.
        if pa in product_area:
            if ar[x]["not_a_child"] != 0:  # AR X is a child AR now.
                res = update_dup_time_for_child_ar(ar_in_out_obj_dict, x, start_date, end_date)
                # Get the In-Time for AR X.
                if "ati_time" in ar[x].keys():  # AR X has been triaged or duped into target_area from other area.
                    ar[x]['in_time'] = ar[x]['ati_time']
                else:  # AR X has been duped into target_area from target_area.
                    if "atd_time" in ar[x].keys() and ar[x]['atd_time'] >= start_date and ar[x]['atd_time'] <= end_date:  # AR X has been duplicated into target area within the time_range.
                        ar[x]['in_time'] = ar[x]['atd_time']  #why in_time = atd_time? e.g., ar 903300 it has create_time, so in_time should be create_time.
                    else:  # AR X has been created before the given time beginning.
                        ar[x]['error'] = ar[x][
                                             'error'] + "No In-Time: Child X in target_area was not triaged/duped in time_range, "
                        ar[x]["hide"] = ar[x]["hide"] + 1
                # Get the Out-Time for AR X.
                if "atd_time" in ar[x].keys() and ar[x]['atd_time'] >= start_date and ar[x]['atd_time'] <= end_date:  # AR X has been duped into target_area within the time_range
                    ar[x]['out_time'] = ar[x]['atd_time']
                    ar[x]['out_man'] = ar[x]['atd_man']
                else:  # AR X has been duped into target_area before the time_range.
                    ar[x]['error'] = ar[x][
                                         'error'] + "No Out-Time: Child X in target_area was not duped in time_range, "
                    ar[x]["hide"] = ar[x]["hide"] + 1
            else:  # AR X is unique or parent AR, we call it as "Adult" AR.
                # Get the In-Time for AR X.
                if "ati_time" in ar[x].keys():  # AR X has been triaged into target_area from other area.
                    ar[x]['in_time'] = ar[x]['ati_time']
                else:  # AR X in target_area was created within the time_range.
                    if ar[x]['create_time'] >= start_date:  # AR X has been created within the time range
                        ar[x]['in_time'] = ar[x]['create_time']
                    else:  # AR X in target_area was created before the time_range.
                        ar[x]['error'] = ar[x][
                                             'error'] + "No In-Time: Adult X in target_area was created before time_range, "
                        ar[x]["hide"] = ar[x]["hide"] + 1
                # Get the Out-Time for AR X.
                if "atf_time" in ar[x].keys() and "atm_time" in ar[x].keys():
                    if ar[x]['atm_time'] > ar[x]['atf_time']:
                        ar[x]['out_time'] = ar[x]['atm_time']
                        ar[x]['out_man'] = ar[x]['atm_man']
                    else:
                        ar[x]['out_time'] = ar[x]['atf_time']
                        ar[x]['out_man'] = ar[x]['atf_man']
                elif "atf_time" in ar[x].keys() and "atm_time" not in ar[x].keys():
                    ar[x]['out_time'] = ar[x]['atf_time']
                    ar[x]['out_man'] = ar[x]['atf_man']
                elif "atf_time" not in ar[x].keys() and "atm_time" in ar[x].keys():
                    ar[x]['out_time'] = ar[x]['atm_time']
                    ar[x]['out_man'] = ar[x]['atm_man']
                else:
                    ar[x]['error'] = ar[x][
                                         'error'] + "No Out-Time: Adult X in target_area was NOT fixed/dismissed in time_range, "
                    ar[x]["hide"] = ar[x]["hide"] + 1
        else:  # AR X is NOT in target_area now.
            if ar[x]["not_a_child"] != 0:  # =None, AR X is a child AR now.
                res = update_dup_time_for_child_ar(ar_in_out_obj_dict, x, start_date, end_date)
                # Get the In-Time for AR X.
                if "ati_time" in ar[x].keys():  # AR X had been triaged or duped into target_area from other area.
                    ar[x]['in_time'] = ar[x]['ati_time']
                else:
                    if ar[x]['create_time'] >= start_date:  # AR X in target_area had been created within the time range
                        ar[x]['in_time'] = ar[x]['create_time']
                    else:  # AR X has been created before the given time beginning
                        ar[x]['error'] = ar[x][
                                             'error'] + "No In-Time: Child X not in target_area was created before time_range, "
                        ar[x]["hide"] = ar[x]["hide"] + 1
                # Get the Out-Time for AR X.
                if "ato_time" in ar[x].keys() and "atd_time" in ar[x].keys():
                    if ar[x]['ato_time'] < ar[x]['atd_time']:
                        ar[x]['out_time'] = ar[x]['ato_time']
                        ar[x]['out_man'] = ar[x]['ato_man']
                    else:
                        ar[x]['out_time'] = ar[x]['atd_time']
                        ar[x]['out_man'] = ar[x]['atd_man']
                elif "ato_time" not in ar[x].keys() and "atd_time" in ar[x].keys():
                    ar[x]['out_time'] = ar[x]['atd_time']
                    ar[x]['out_man'] = ar[x]['atd_man']
                elif "ato_time" in ar[x].keys() and "atd_time" not in ar[x].keys():
                    ar[x]['out_time'] = ar[x]['ato_time']
                    ar[x]['out_man'] = ar[x]['ato_man']
                else:  # "ato_time" not in ar[x].keys() and "atd_time" not in ar[x].keys():
                    ar[x]['error'] = ar[x][
                                         'error'] + "No Out-Time: Child X not in target_area was NOT duped/triaged-out in time_range, "
                    ar[x]["hide"] = ar[x]["hide"] + 1
            else:  # Unique or Parent AR
                # Get the In-Time for AR X.
                if "ati_time" in ar[x].keys():
                    ar[x]['in_time'] = ar[x]['ati_time']
                else:
                    if ar[x]['create_time'] >= start_date:  # AR X has been created within the time range
                        ar[x]['in_time'] = ar[x]['create_time']
                    else:  # X has been created before the given time beginning
                        ar[x]['error'] = ar[x][
                                             'error'] + "No In-Time: Adult X not in target_area was created before time_range, "
                        ar[x]['hide'] = ar[x]['hide'] + 1
                # Get the Out-Time
                if "ato_time" in ar[x].keys():
                    ar[x]['out_time'] = ar[x]['ato_time']
                    ar[x]['out_man'] = ar[x]['ato_man']
                else:
                    ar[x]['error'] = ar[x][
                                         'error'] + "No Out-Time: Adult X not in target_area was NOT triaged-out in time_range, "
                    ar[x]['hide'] = ar[x]['hide'] + 1

def save_weekly_ar(ar_in_out_obj_dict, date):
    ar = ar_in_out_obj_dict
    timer = TimeHelper()
    file_time = timer.mtime_to_local_file_time(date)
    outfile = data_weekly_inoutar_prefix + "ar_weekly_" + file_time + ".xls"
    wb = xlwt.Workbook()
    sht1 = wb.add_sheet("All_In_Out")

    rn = 0

    row1 = sht1.row(rn)

    row1.write(0, 'Entry ID')
    row1.write(1, 'Type')
    row1.write(2, 'Priority')
    row1.write(3, 'Summary')
    row1.write(4, 'Major Area')
    row1.write(5, 'Product Area')
    row1.write(6, 'Assignee')
    row1.write(7, 'Assignee Full Name')
    row1.write(8, 'Status')
    row1.write(9, 'Status Details')
    row1.write(10, 'Not_a_child')
    row1.write(11, 'Product Release')
    row1.write(12, 'Customer Issue')
    row1.write(13, 'Create Time')
    row1.write(14, 'From_value')
    row1.write(15, 'To_value')
    row1.write(16, 'Touched Time')
    row1.write(17, 'Touched man')
    row1.write(18, 'AT_In_date')
    row1.write(19, 'AT_In_man')
    row1.write(20, 'AT_Out_date')
    row1.write(21, 'AT_Out_man')
    row1.write(22, 'AT_Dup_date')
    row1.write(23, 'AT_Dup_man')
    row1.write(24, 'AT_Fix_date')
    row1.write(25, 'AT_Fix_man')
    row1.write(26, 'AT_Dis_date')
    row1.write(27, 'AT_Dis_man')
    row1.write(28, 'In Time')
    row1.write(29, 'Out Time')
    row1.write(30, 'Out Man')
    row1.write(31, 'comments')

    for k in ar.keys():
        # print k
        if ar[k]["hide"] < 2:
            rn = rn + 1
            rown = sht1.row(rn)
            for key, value in ar[k].iteritems():
                if key == "entry_id":
                    rown.write(0, str(value))
                elif key == "type":
                    rown.write(1, str(value))
                elif key == "priority":
                    rown.write(2, str(value))
                elif key == "summary":
                    rown.write(3, str(value))
                elif key == "major_area":
                    rown.write(4, str(value))
                elif key == "product_area":
                    rown.write(5, str(value))
                elif key == "assignee":
                    rown.write(6, str(value))
                elif key == "assignee_fname":
                    rown.write(7, str(value))
                elif key == "status":
                    if value == 0:
                        rown.write(8, "Open")
                    elif value == 1:
                        rown.write(8, "Dismissed")
                    elif value == 2:
                        rown.write(8, "In-progress")
                    elif value == 3:
                        rown.write(8, "Fixed")
                    elif value == 4:
                        rown.write(8, "WOO")
                    else:
                        rown.write(8, "Unknown")
                elif key == "status_details":
                    rown.write(9, value)
                elif key == "not_a_child":
                    if value == 0:
                        rown.write(10, "Y")
                    else:
                        rown.write(10, "N")
                elif key == "product_release":
                    rown.write(11, str(value))
                elif key == "customer_issue":
                    if value == 0:
                        rown.write(12, "Y")
                    else:
                        rown.write(12, "N")
                elif key == "create_time":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(13, date_str)
                elif key == "from_value":
                    rown.write(14, str(value))
                elif key == "to_value":
                    rown.write(15, str(value))
                elif key == "touch_date":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(16, date_str)
                elif key == "touch_man":
                    rown.write(17, str(value))
                elif key == "ati_time":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(18, date_str)
                elif key == "ati_man":
                    rown.write(19, str(value))
                elif key == "ato_time":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(20, date_str)
                elif key == "ato_man":
                    rown.write(21, str(value))
                elif key == "atd_time":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(22, date_str)
                elif key == "atd_man":
                    rown.write(23, str(value))
                elif key == "atf_time":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(24, date_str)
                elif key == "atf_man":
                    rown.write(25, str(value))
                elif key == "atm_time":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(26, date_str)
                elif key == "atm_man":
                    rown.write(27, str(value))
                elif key == "in_time":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(28, date_str)
                elif key == "out_time":
                    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                    rown.write(29, date_str)
                elif key == "out_man":
                    rown.write(30, str(value))
                elif key == "error":
                    rown.write(31, value)

    print "DEBUG write to [" + outfile + "]"
    wb.save(outfile)

def get_one_week_in_out_ar(ar_one_week_in_out_obj_dict, parammap, start_date, end_date, record_file):
    get_in_out_ar_from_audit_trail_with_rules(ar_one_week_in_out_obj_dict, parammap,
                                              start_date, end_date)
    # Get all Open/In-Progress/WOO ARs per product area
    get_ar_created_in_time_range_per_product_area(ar_one_week_in_out_obj_dict, parammap,
                                                  start_date, end_date)
    # get_ar_created_pa_in_time_range_per_product_area(ar_one_week_in_out_obj_dict, parammap,
    #                                               start_date, end_date)
    # # Get all fixed or dismissed after target_time_head ARs per product area;the result is a subset of get_in_out_ar_from_audit_trail_with_rules,just used to update the in/out time.
    get_ar_fixed_dismissed_in_time_range(ar_one_week_in_out_obj_dict, parammap, start_date,
                                         end_date)
    # #
    get_ar_reopen_in_time_range(ar_one_week_in_out_obj_dict, parammap, start_date,end_date)
    # update in/out time or other info.
    process_ar_total_weekly_in_out(ar_one_week_in_out_obj_dict, parammap, start_date,
                                   end_date)
    filter_ar_with_release(ar_one_week_in_out_obj_dict, parammap, start_date,end_date, record_file)

def get_ar_total_weekly_in_out(parammap, record_file, hist_needed = False):
    """
    get ar list from the remedy table 'Issue_Audit_join', these ars are created by other domain and assign to platform domain.
    platform domain =>  other domains
    :param parammap: parameters given by user
    :param hist_needed: if need to get the historical weekly ars before the current week start.
    :return: ar_date_cnt_dict - key is the date, value is a list with sequence [totoal_in, rls1_in, rls2_in, ...].
    """
    timer = TimeHelper()

    cur_time = timer.get_mtime()
    # get historical ARs before this week start(Monday)
    if hist_needed:
        start = "2017-01-02 9:00:00"
        th_ta = time.strptime(start, "%Y-%m-%d %H:%M:%S")
        start_sec = int(time.mktime(th_ta))
        #end = "2017-05-07 11:22:00"
        #th_tb = time.strptime(end, "%Y-%m-%d %H:%M:%S")
        #end_sec = int(time.mktime(th_tb))
        end_sec = cur_time
        internal_sec = 7 * 24 * 60 * 60
        while start_sec < end_sec:
            ar_one_week_in_out_obj_dict = dict()
            get_one_week_in_out_ar(ar_one_week_in_out_obj_dict, parammap, start_sec - internal_sec, start_sec, record_file)
            save_weekly_ar(ar_one_week_in_out_obj_dict, start_sec)
            start_sec += internal_sec

    cur_mondaydate = timer.get_week_start(timer.get_mtime())
    #get inout ar only when the current time is Sunday of this week
    if (cur_time < cur_mondaydate + 24 * 60 * 60):
        ar_one_week_in_out_obj_dict = dict()
        get_one_week_in_out_ar(ar_one_week_in_out_obj_dict, parammap, cur_mondaydate - 7 * 24 * 60 * 60,
                               cur_mondaydate, record_file)
        save_weekly_ar(ar_one_week_in_out_obj_dict, cur_mondaydate - 7 * 24 * 60 * 60)

    return 0

def count_audit_in(llist,parammap):
    res = {}
    ayer = ArrayMapHelper()
    for i in llist:
        k = get_ca_map_entry(parammap['platform domain'],i.to_value)
        #logger.debug("k :" + str(k))
        ayer.update_oned_map_values(res, k + ' In')
    return res

def get_audit_trail_out_list(parammap, time_interval):
    """
    get ar list from the remedy table 'Issue_Audit_join', these ars are created by platform domain and assign to other domains.
    platform domain => other domains
    :param parammap: parameters given by user
    :param time_interval: time interval such as daily, weekly.
    :return: ar list
    """
    timer = TimeHelper()
    if time_interval == 'daily':
        cur_date = timer.get_day_start(timer.get_mtime()) - 24 * 60 * 60
        pre_date = cur_date - 24 * 60 * 60
    elif time_interval == 'weekly':
        cur_date = timer.get_week_start(timer.get_mtime())
        pre_date = cur_date - 7 * 24 * 60 * 60
    res = []
    out_param = dict(parammap["audit trail param map"])
    out_param['From Time']=[str(pre_date),]
    out_param['To Time']=[str(cur_date),]
    ca_dict = dict(parammap['platform product areas'])
    for k, v in ca_dict.iteritems():
        if 'From Value' not in out_param.keys():
            out_param['From Value'] = list(v)
        else:
            out_param['From Value'] += list(v)

    dber = DatabaseHelper()
    #print out_param
    for e in dber.get_AR_from_audit_trail(out_param)[0]:
        # remove the ars whose 'From Value' should not in platform domain
        if e[1][536870917] not in out_param['From Value']:
            res.append(generate_audit_trail_obj(e))
        else:
            logger.debug(
                "This ar's to value is " + e[1][536870917] + " which should not be in platform product areas.")
    return res

def count_audit_out(llist,parammap):
    res = {}
    ayer = ArrayMapHelper()
    for i in llist:
        k = get_ca_map_entry(parammap['platform domain'], i.from_value)
        ayer.update_oned_map_values(res, k + ' Out')
    return res

def update_total_in_out_record_file(cnt_in, cnt_out, file):
    timer = TimeHelper()
    cur_date = timer.get_week_start(timer.get_mtime())
    #pre_date = cur_date - 7*24*60*60
    timestamp = timer.mtime_to_local_date(cur_date)

    logger.debug("[update_total_weekly_in_out_record_file]")
    #logger.debug(str(ddict))

    csvstr = timestamp
    header = 'Date'
    csvstr += ',' + str(cnt_in) + ',' + str(cnt_out) + '\n'
    header += ',' + 'Total In' + ',' + 'Total Out' + '\n'

    logger.debug('headers: '+str(header))
    logger.debug('csvstr: '+str(csvstr))

    update_last_record(file, timestamp, csvstr, header)

def sent_report_email(parammap, files_to_send, bug_releases, additional_body):
    """
    Sends out report via email
    :param bug_releases: release of the bugs
    :param additional_body: additional to append at the end of the email
    :return:
    """
    logger.debug("-" * 40 + "[sent_report_email]" + "-" * 40)
    mailer = EmailHelper()
    att = files_to_send['attachment']
    subj = parammap['report name'] + ' Daily Bug Report'
    ifHtmlBody = True
    embed_images = files_to_send['image']
    body='<h3>This report is generated automatically by Common Platform team.</h3><hr>'
    if len(additional_body) != 0:
        body += '<p><a href="#blockings">Check The Details Of Blocking ARs<a/></p>'
    notice = ''
    #entries = get_file_enteries(dataprefix + '[31]' + parammap['report name'].replace(' ', '') + "_ARs_Product.csv")
    entries = [rel.replace('"', '') for rel in parammap['assinged to manager param map']['Product Release']]
    for key in entries:
        if key not in bug_releases:
            notice += key + ', '
    if len(notice) is not 0:
        notice = '<p style="color:red">' + notice[:-2]
        notice = notice + ' have no AR.\n<p>'
        # notice = notice + '<p style="color:red">Get P00~P03 ARs for Smuttynose, get P00~P02 ARs for other releases.<p>'
    #notice = '<p style="color:red"> Resent to more people..</p>' + notice
    body = body + notice
    style = '<style>table,th,td{border: 1px solid black;border-collapse: collapse;font-family:"Arial";'+\
            'font-size:8.0pt;color:black} table{width:900px;}caption{text-align: left;font-size:14.0pt;}'+\
            'th{text-align:center;font:bold;background-color:#ccff99} td{text-align:center;font:bold;}' +\
            'span{margin-bottom:20px;display:block;font-family:"sans-serif";font-size:14.0pt;}</style>'
    mailer.send_email(parammap['to'], subj, style+body, ifHtmlBody, embed_images, additional_body, parammap['cc'], parammap['bcc'], att)

#get AR related to camap, i.e., classify AR with ca name.
def count_by_ca_manager(arobjlist, cas, camap):
    res = dict()
    for k in cas:
        res[k] = list()
    for o in arobjlist:
        for k in cas:
            if o.direct_manager in camap[k] or o.assigned_to in camap[k]:
                res[k].append(o)
                break
    return res

def add_assigned_to_ca(objlist, ca_manager_map):
    cammap =dict(ca_manager_map)
    ayer = ArrayMapHelper()
    cammap = ayer.remove_map_quote(cammap)
    for ar in objlist:
        for k in cammap.keys():
            if ar.direct_manager in cammap[k] or ar.assigned_to in cammap[k] :
                ar.owning_ca = k
                break

def add_total(llist):
    total = list()
    total.append("Total")
    pprint.pprint(llist)
    for j in range(1, len(llist[0])):
        sum = 0
        for i in range(0, len(llist)):
            sum += llist[i][j]
        total.append(sum)
    llist.append(total)

#******************************************** reports ****************************************#

def get_ars_assigned_in_Remedy(ar_obj_list, parammap):
    logger.debug("[get_ars assigned to common platform team in Remedy]......")
    rawars, numrawars = dber.get_AR_from_assigned_to_manager(parammap['assinged to manager param map'])
    if numrawars == 0:
        logger.debug("No open AR ...")
        return

    ar_obj_list += get_ar_obj_list(rawars)
    #add ARs assigned to ca
    if "major area managers" in parammap.keys():
       add_assigned_to_ca(ar_obj_list,parammap["major area managers"])

def get_ars_assigned_in_Jira(ar_obj_list, parammap):
    logger.debug("[get_ars assigned to common platform team in Jira]......")
    mres_query_string = 'project = MDT AND "MRES Product" = Cyclone AND Release = Smuttynose AND issuetype = Bug AND status in (Open, "In Progress", Reopened, WOO) AND issueFunction not in hasLinks("duplicates(childof)") AND "Major Area" in ("IO Modules and Backend", "Storage Processor") AND priority in (P00,P01,P02) ORDER BY created DESC'
    mres_max_results = 200
    global jira_session
    mres_open_issues = jira_session.search_issues(mres_query_string, startAt=0, maxResults=mres_max_results, expand="changelog")
    if not mres_open_issues:
        logger.debug("No open Jira AR ...")
        return

    ar_obj_list += get_ar_obj_list(mres_open_issues)

def get_ars_assigned_to_common_platform(ar_obj_list, parammap, files_to_send):
    logger.debug("[get_ars assigned to common platform]......")
    get_ars_assigned_in_Remedy(ar_obj_list, parammap)
    get_ars_assigned_in_Jira(ar_obj_list, parammap)

    #save AR list to excel && append excel to sharepoint
    file_date = time.strftime('%Y%m%d_%H%M',time.localtime(time.time()))
    save_to_excel = data_daily_openar_prefix + 'ARs_Daily_Total_List_' + file_date + '.xls'
    save_AR_list_to_excel(ar_obj_list, save_to_excel)
    files_to_send['attachment'].append(save_to_excel)
    #sharepoint_files.append(ar_list_save_to_excel)

def ar_total_report(ar_obj_list, bugmap, parammap, files_to_send):
    logger.debug("-"*40 + "[ar_total_report]" + "-"*40)
    save_to_png = pngprefix + '[01]' + parammap['report name'].replace(' ', '') + '_ARs_Total.png'
    title = parammap['report name'].replace(' ', '') + ' Total ARs'
    bug_count_map = bug_total_report(ar_obj_list, parammap, title, save_to_png)
    bugmap.update(bug_count_map)
    logger.debug("bugmap : "+str(bugmap))
    files_to_send["image"].append(save_to_png)

# def ar_total_in_out_trend_report(parammap, files_to_send):
#     logger.debug("-"*40 + "[ar_total_in_out_trend_report]" + "-"*40)
#
#     ar_date_cnt_dict = get_audit_trail_list(parammap, 'daily')
#     in_map = count_audit_in(audit_in_list,parammap)
#     audit_out_list = get_audit_trail_out_list(parammap, 'daily')
#     out_map = count_audit_out(audit_out_list,parammap)
#     #append out_map to in_map
#     in_map.update(out_map)
#
#     record_file = dataprefix + '[21]' + parammap["report name"].replace(' ', '') + '_ARs_Total_In_Out.csv'
#     trend_record_file = dataprefix + '[22]' + parammap["report name"].replace(' ', '') + '_ARs_Total_In_Out_Trend.csv'
#     entries = sorted([ca+' In' for ca in parammap["major area managers"]] + [ca+' Out' for ca in parammap["major area managers"]])
#     #logger.debug('entries : '+str(entries))
#
#     update_total_in_out_record_file(in_map, entries, record_file)
#     ar_records_cnt = generate_AR_trends_report_data_file(28, record_file, trend_record_file)
#
#     #draw total ar in/out trend chart
#     date_x_unit = calc_date_x_unit(ar_records_cnt)
#     title = parammap['report name'].replace(' ', '') + ' Total ARs In/Out Trend'
#     lines = ['Total In', 'Total Out']
#     save_to_png = pngprefix + '[02]' + parammap["report name"].replace(' ', '') + '_ARs_Total_In_Out_Trend.png'
#     grapher.draw_trent_chart(trend_record_file, lines, title, 14, 4, 5, date_x_unit, save_to_png)
#     files_to_send["image"].append(save_to_png)

def join2dicts(dict_in, dict_out):
    """
    Join two dicts into one dict with all values.
    e.g., {date1, list_in} + {date1, list_out} => {date1, [list_in,list_out]}
    :param dict_in:
    :param dict_out:
    :return: dict_inout
    """
    from collections import Counter
    dict_in, dict_out = Counter(dict_in), Counter(dict_out)
    dict_inout = dict(dict_in + dict_out)
    return dict_inout

def update_weekly_in_out_record_file(parammap, ar_date_cnt_dict, file):
    """
    update all the records from audit table to file which names such as [21]CommonPlatform_ARs_Total_Weekly_In_Out_Trend.csv
    :param parammap:
    :param ar_date_cnt_dict:
    :param file:
    :return: None
    """
    header = 'Date' + ',' + 'Total_In'
    for rls in parammap["audit trail param map"]["Specific Product Release"]:
        rls = rls.replace('"', '')
        header += ',' + rls + '_In'

    header += ',' + 'Total_Out'

    for rls in parammap["audit trail param map"]["Specific Product Release"]:
        rls = rls.replace('"', '')
        header += ',' + rls + '_Out'

    header += '\n'

    timestamp = timer.mtime_to_local_date(timer.get_mtime())

    sorted_date_list = ar_date_cnt_dict.keys()
    sorted_date_list.sort()
    for date in sorted_date_list:
        csvstr = timer.mtime_to_local_date(date)
        for cnt in ar_date_cnt_dict[date]:
            csvstr += ',' + str(cnt)
        csvstr += '\n'
        update_last_record(file, timestamp, csvstr, header)

def draw_weekly_total_inout_trend_chart(parammap, record_file, files_to_send):
    """
    Draw the ARs Total Weekly In/Out Trend chart.
    :param parammap:
    :param record_file:
    :param files_to_send:
    :return:
    """

    title = parammap['report name'].replace(' ', '') + ' ARs Total Weekly In/Out Trend'
    lines = ['Total_In', 'Total_Out']
    save_to_png = pngprefix + '[11]' + parammap["report name"].replace(' ', '') + '_ARs_Total_Weekly_In_Out_Trend.png'
    grapher.draw_trent_chart(record_file, lines, title, 14, 4, 5, save_to_png)
    files_to_send["image"].append(save_to_png)

def draw_weekly_release_inout_trend_chart(parammap, record_file, files_to_send):
    """
    Draw the ARs Weekly In/Out Trend of product release configured in .json file.
    :param parammap:
    :param record_file:
    :param files_to_send:
    :return:
    """

    for rls in parammap["audit trail param map"]["Specific Product Release"]:
        rls = rls.replace('"', '')
        title = parammap['report name'].replace(' ', '') + ' ARs ' + rls + ' Weekly In/Out Trend'
        lines = [rls + '_In', rls + '_Out']
        save_to_png = pngprefix + '[12]' + parammap["report name"].replace(' ', '') + '_ARs_' + rls + '_Weekly_In_Out_Trend.png'
        grapher.draw_trent_chart(record_file, lines, title, 14, 4, 5, save_to_png)
        files_to_send["image"].append(save_to_png)

def ar_total_weekly_in_out_trend_report(parammap, files_to_send):
    """
    Get in/out ar lists from audit table; save the results into a file; draw the trend chart.
    :param parammap:
    :param files_to_send:
    :return: None
    """
    logger.debug("-"*40 + "[ar_total_weekly_in_out_trend_report]" + "-"*40)
    hist_needed = parammap["audit trail param map"]["Get AR from the begining of this year"]
    record_file = data_csvprefix + '[11]' + parammap["report name"].replace(' ', '') + '_ARs_Total_Weekly_In_Out_Trend.csv'
    get_ar_total_weekly_in_out(parammap, record_file, hist_needed)

    if os.path.exists(record_file):
        draw_weekly_total_inout_trend_chart(parammap, record_file, files_to_send)
        draw_weekly_release_inout_trend_chart(parammap, record_file, files_to_send)

def ar_total_age_report(ar_obj_list, parammap, files_to_send):
    logger.debug("-"*40 + "[ar_total_age_report]" + "-"*40)
    save_to_png = pngprefix + '[03]' + parammap["report name"].replace(' ', '') + '_AR_Total_Age.png'
    title = parammap["report name"].replace(' ', '') + ' Total ARs by Age'
    total_age_report(ar_obj_list, title, COLOR_SETS[0], save_to_png)
    files_to_send["image"].append(save_to_png)
    #sharepoint_images.append(bug_age_table)

def ar_total_trend_report(bugmap, parammap, files_to_send):
    logger.debug("-"*40 + "[ar_total_trend_report]" + "-"*40)
    summary_releases = sorted(parammap['releases for total report'])
    record_file = data_csvprefix + '[01]' + parammap['report name'].replace(' ', '') + "_ARs_Total.csv"
    trend_record_file = data_csvprefix + '[04]' + parammap['report name'].replace(' ', '') + "_ARs_Total_Trend.csv"
    update_AR_summary_history_file(bugmap, summary_releases, record_file)
    ar_records_cnt = generate_AR_trends_report_data_file(365, record_file, trend_record_file)

    title = parammap['report name'].replace(' ', '') + ' Total ARs Trend'
    lines = ['Total']
    save_to_png = pngprefix + '[04]' + parammap['report name'].replace(' ', '') + '_ARs_Total_Trend.png'
    grapher.draw_trent_chart(trend_record_file, lines, title, 14, 4, 5, save_to_png)
    files_to_send["image"].append(save_to_png)

def ar_direct_manager_report(ar_obj_list, parammap, files_to_send):
    logger.debug("-"*40 + "[ar_direct_manager_report]" +"-"*40)
    title = parammap['report name'].replace(' ', '') + ' Total ARs for Direct Manager'
    save_to_png = pngprefix + '[05]' + parammap["report name"].replace(' ', '') + '_ARs_DirectManager.png'
    direct_manager_report(ar_obj_list, title , save_to_png)
    files_to_send["image"].append(save_to_png)

def ar_tbv_report(parammap, files_to_send):
    logger.debug("-"*40 + "[ar_tbv_direct_manager_report]" + "-"*40)
    tbv_list_remedy, num_tbv_remedy = dber.get_AR_from_reported_to_manager(parammap['reported by manager param map'])

    tbv_list_jira = []
    logger.debug("[get TBV ars of common platform team in Jira]......")
    mres_query_string = 'project = MDT AND "MRES Product" = Cyclone AND Release = Smuttynose AND issuetype = Bug AND status in (Resolved) AND issueFunction not in hasLinks("duplicates(childof)") AND "Major Area" in ("IO Modules and Backend", "Storage Processor") AND priority in (P00,P01,P02) ORDER BY created DESC'
    mres_max_results = 200
    global jira_session
    tbv_list_jira = jira_session.search_issues(mres_query_string, startAt=0, maxResults=mres_max_results,
                                                  expand="changelog")
    if not tbv_list_jira:
        logger.debug("No TBV Jira AR ...")

    tbv_list = tbv_list_remedy + tbv_list_jira
    num_tbv = len(tbv_list)
    if num_tbv != 0:
        tbvobjlist = get_ar_obj_list(tbv_list, 1)
        if "major area managers" in parammap.keys():
            add_assigned_to_ca(tbvobjlist, parammap["major area managers"])
        save_to_excel = data_daily_openar_prefix + parammap['report name'].replace(' ', '') + '_ARs_TBV_List.xls'
        save_AR_list_to_excel(tbvobjlist, save_to_excel, 1)
        files_to_send['attachment'].append(save_to_excel)
        title = parammap['report name'].replace(' ', '') + ' Total TBV ARs for Direct Manager'
        save_to_png = pngprefix + '[06]' + parammap['report name'].replace(' ', '') + '_ARs_TBV_DirectManager.png'
        direct_manager_report(tbvobjlist, title, save_to_png)
        files_to_send["image"].append(save_to_png)

def releases_report(ar_obj_list, parammap, files_to_send):
    logger.debug("-"*40 + "[releases_report]" + "-"*40)
    unified_systems_ar = filter_product_family(ar_obj_list, ["Unified Systems"], True)
    cas = sorted(parammap['major area managers'])
    logger.debug(cas)
    cammap = ayer.remove_map_quote(parammap['major area managers'])
    for rel in parammap['releases for detail report']:
        #get all the ar with 'report releases' == rel
        ars = filter_release(ar_obj_list, rel)
        ar_count_map = count_by_ca_manager(ars, cas, cammap)
        logger.debug('ar_count_map is :'+str(ar_count_map))

        #release age report
        title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ','') +' ARs by Age'
        color_set = COLOR_SETS[((parammap['releases for detail report'].index(rel))+1)%len(COLOR_SETS)]
        save_to_png = pngprefix + '[07]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ','') + '_ARs_by_Age.png'
        total_age_report(ars, title, color_set, save_to_png)
        files_to_send["image"].append(save_to_png)

        #update trend record file
        timestamp = timer.mtime_to_local_date(timer.get_mtime())
        header = 'Date'
        csvstr = timestamp
        domain_total = len(ars)
        ca_total = 0
        for ca in cas:
            header = header + ',' + ca
            ca_total += len(ar_count_map[ca])
            csvstr = csvstr + ',' + str(len(ar_count_map[ca]))
        header = header + ',CA Total,Domain Total' + '\n'
        csvstr = csvstr + ',' + str(ca_total) + ',' + str(domain_total) + '\n'
        ca_record_file = data_csvprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total.csv'
        trend_ca_record_file = data_csvprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total_Trend.csv'
        update_last_record(ca_record_file, timestamp, csvstr, header)
        ar_records_cnt = generate_AR_trends_report_data_file(365, ca_record_file, trend_ca_record_file)

        #update age record file
        bug_age_map = count_bug_age(ars)
        timestamp = timer.mtime_to_local_date(timer.get_mtime())
        header = 'Date'
        csvstr = timestamp
        num_total = 0
        num_older_than_one_week = count_bug_older_than_one_week(ars)
        num_older_than_twos_days = count_bug_older_than_two_days(ars)
        #num_total = count_bug_total(ar_obj_list)
        for week_duration in sorted(bug_age_map):
            #if week_duration != '0-1 week':
            #    older_than_one_week += bug_age_map[week_duration]['Product Total']
            header = header + ',' + week_duration
            num_total += bug_age_map[week_duration]['Total']
            csvstr = csvstr + ',' + str(bug_age_map[week_duration]['Total'])
        header = header + ',Total,>1 week,>2 days' + '\n'
        csvstr = csvstr + ',' + str(num_total) + ',' + str(num_older_than_one_week) + ',' + str(num_older_than_twos_days) + '\n'
        age_record_file = data_csvprefix + '[07]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total_Age.csv'
        update_last_record(age_record_file, timestamp, csvstr, header)

        #draw release domain total trend chart
        lines = ['Domain Total']
        title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs Total Trend'
        save_to_png = pngprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_ARs_Trend.png'
        grapher.draw_trent_chart(trend_ca_record_file, lines, title, 14, 4, 5, save_to_png)
        files_to_send["image"].append(save_to_png)

        '''
        #draw CAs' actual VS target trend chart
        total_data = read_csv(trend_ca_record_file)
        age_data = read_csv(age_record_file)
        title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs Actual vs Target'
        save_to_png = pngprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_ARs_Actual_VS_Target.png'
        grapher.draw_target_chart(parammap["target dates"], parammap["target"], total_data['Date'].values, total_data['Domain Total'].values,
                                       age_data['Date'].values, age_data['>2 days'].values, title, 14, 4, 5, 'weekly', save_to_png)
        files_to_send["image"].append(save_to_png)
        '''

        #draw CAs' release trend lines all in one chart
        title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs CA Trend'
        lines = cas
        save_to_png = pngprefix + '[09]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_ARs_Trend_by_CA.png'
        grapher.draw_trent_chart(trend_ca_record_file, lines, title, 14, 4, 2, save_to_png)
        files_to_send["image"].append(save_to_png)

        #draw release age report table for per CA
        for ca in cas:
            ca_ar_obj_list = ar_count_map[ca]
            if len(ca_ar_obj_list) != 0:
                title = parammap['report name'].replace(' ', '') + ' ' + ca + ' ' + rel.replace(' ','') +' ARs by Age'
                color_set = COLOR_SETS[((parammap['releases for detail report'].index(rel))+1)%len(COLOR_SETS)]
                save_to_png = pngprefix + '[10]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_' + ca + '_ARs_by_Age.png'
                total_age_report(ca_ar_obj_list, title, color_set, save_to_png)
                files_to_send["image"].append(save_to_png)

def releases_trend_report(ar_obj_list, parammap, files_to_send):
    logger.debug("-"*40 + "[releases_trend_report]" + "-"*40)
    unified_systems_ar = filter_product_family(ar_obj_list, ["Unified Systems"], True)
    cas = sorted(parammap['major area managers'])
    cammap = ayer.remove_map_quote(parammap['major area managers'])
    #cammap = dict(parammap['major area managers'])
    for rel in parammap["trend report releases"]:
        ars = filter_release(unified_systems_ar, rel)
        ar_count_map = count_by_ca_manager(ars, cas, cammap)
        logger.debug('ar_count_map:'+str(ar_count_map))

        #update trend record file
        timestamp = timer.mtime_to_local_date(timer.get_mtime())
        header = 'Date'
        csvstr = timestamp
        #total = 0
        total = len(ars)
        for ca in cas:
            header += ',' + ca
            #total += len(ar_count_map[ca])
            csvstr += ',' + str(len(ar_count_map[ca]))
        header = header + ',' + 'Total' + '\n'
        csvstr = csvstr + ',' + str(total) + '\n'
        record_file = data_csvprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total.csv'
        trend_record_file = data_csvprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total_Trend.csv'
        update_last_record(record_file, timestamp, csvstr, header)
        ar_records_cnt = generate_AR_trends_report_data_file(365, record_file, trend_record_file)

        #draw CAs' target VS total trend chart
        ar_history_data = read_csv(trend_record_file)
        title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs Total vs Target'
        save_to_png = pngprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_ARs_Total_VS_Target.png'
        grapher.draw_target_chart(parammap["target dates"], parammap["target"], ar_history_data.Date.values, ar_history_data['Total'].values,
                                      title, 14, 4, 5, 'weekly', save_to_png)
        files_to_send["image"].append(save_to_png)

        #draw CAs' release trend lines all in one chart
        title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' CA ARs Trend'
        lines = cas
        save_to_png = pngprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_ARs_Trend_by_CA.png'
        grapher.draw_trent_chart(trend_record_file, lines, title, 14, 4, 2, save_to_png)
        files_to_send["image"].append(save_to_png)

        #draw release age report table for per CA
        for ca in cas:
            ca_ar_obj_list = ar_count_map[ca]
            if len(ca_ar_obj_list) != 0:
                title = ca + ' ' + rel.replace(' ','') +' ARs by Age'
                color_set = COLOR_SETS[((parammap['age report releases'].index(rel))+1)%len(COLOR_SETS)]
                save_to_png = pngprefix + '[9]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_' + ca + '_ARs_by_Age.png'
                total_age_report(ca_ar_obj_list, title, color_set, save_to_png)
                files_to_send["image"].append(save_to_png)

def ar_blocking_report(ar_obj_list, parammap, files_to_send):
    logger.debug("-"*40 + "[ar_blocking_report]" + "-"*40)
    blocking_ar_list = get_blocking_AR(ar_obj_list)
    if len(blocking_ar_list) != 0:
        #The additional_body is useless, so now don't need to convert_AR_objs_to_html_table.
        additional_body, blocking_text = convert_AR_objs_to_html_table(blocking_ar_list, 'blockings')
        #just truncate the member of blocking_text
        blocking_text = refine_twod_array(blocking_text)
        title = parammap['report name'].replace(' ', '')+' Blocking ARs'
        plt, table = grapher.draw_table_first_row_colored(blocking_text, 1*len(blocking_text[0]), 0.5*len(blocking_text), 0.98, True, title, 'center', 10)
        save_to_png = pngprefix + '[00]' + parammap['report name'].replace(' ', '') + '_ARs_Blocking.png'
        plt.savefig(save_to_png, bbox_inches='tight')
        files_to_send["image"].append(save_to_png)

def init_dir():
    dir_list = [dataprefix, data_csvprefix, data_daily_openar_prefix, data_weekly_inoutar_prefix, pngprefix, logprefix]
    for dir in dir_list:
        if not os.path.exists(dir):
            os.makedirs(dir)

def create_jira_session(parammap):
    jira_server = 'https://jira.cec.lab.emc.com:8443'
    jira_para = {'server': jira_server, 'verify': False}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        jira_session = JIRA(jira_para, basic_auth=(parammap['user'], parammap['pwd']))
    return jira_session

def main():
    start = time.clock()
    parammap = init_param(arg_parser()) #init parameters
    init_dir()  #make directories: data, png and log
    global jira_session
    jira_session = create_jira_session(parammap)
    files_to_send = {}
    files_to_send['attachment'] = []
    files_to_send["image"] = []
    additional_body = ""
    ar_obj_list = []
    ar_in_out_obj_dict = dict()
    bugmap = dict()
    logger.debug("="*25 + "Start" + "="*25 + "\n" + "-"*25 + "REPORT NAME: " + parammap['report name'] + "-"*25)
    get_ars_assigned_to_common_platform(ar_obj_list, parammap, files_to_send)
    ar_blocking_report(ar_obj_list, parammap, files_to_send)
    ar_total_report(ar_obj_list, bugmap, parammap, files_to_send)
    ar_total_age_report(ar_obj_list, parammap, files_to_send)
    ar_total_trend_report(bugmap, parammap, files_to_send)
    ar_direct_manager_report(ar_obj_list, parammap, files_to_send)
    #need to do some changes for cyclone
    ar_tbv_report(parammap, files_to_send)
    #ar_radar_report.radar_report(parammap, files_to_send)
    releases_report(ar_obj_list, parammap, files_to_send)
    ar_total_weekly_in_out_trend_report( parammap, files_to_send)
    logger.debug(bugmap.keys())
    sent_report_email(parammap, files_to_send, bugmap.keys(), additional_body)
    logger.debug("="*25 + "End" + "="*25)
    total_time = time.clock() - start
    print("total time(mins): ", total_time/60)
    return 0

if __name__ == '__main__':
    main()






