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

__author__ = "Ming.Yao@emc.com"

reload(sys)
sys.setdefaultencoding('utf8')

__filename__ = os.path.basename(__file__)
fpath = os.path.dirname(os.path.realpath(__file__))
dataprefix = fpath + '\\data\\'
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
        return parammap

def get_ar_obj_list(rawars, isTBV=None):
    logger.debug("getting AR obj list ...")
    res = []
    for ar in rawars:
        if isTBV:
            (items, num) = dber.get_fixed_time_from_audit_trail_with_rules(ar[1][536870921])
            #logger.debug("items :" + "\n" + str(items))
            fixed_time_list = [item[1][536870929] for item in items]
            final_fixed_time = max(fixed_time_list)
            days_in_status = (CUR_TIME - final_fixed_time) / (24 * 60 * 60) + 1
            logger.debug("AR Status: " + str(items[0][1][536870917]) + ", DaysInStatus: " + str(days_in_status))
            ar[1]['days_in_status'] = days_in_status
            #logger.debug("ar:" + "\n" + str(ar))
        else:
            ar[1]['days_in_status'] = None
        ar_obj = generate_unity_ar_obj(ar)
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
        #print obj.product_release
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
        map_product[key] = arrayer.positive_map_filter(bug_count_map[key], ['P00','P01','P02', 'Total'])

    #product count table(data type: list)
    #1. Convert data from dict to list
    #2. Order releases(AR numbers > 0) from top to bottom in table by Json code(assinged to manager param map -> Product Release)
    table_product = arrayer.twod_map_to_report_table(map_product, 'Program', True)
    logger.debug("table_product :" + str(table_product))
    custom_ordered_releases = [rel.replace('"', '') for rel in parammap['assinged to manager param map']['Product Release']]
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
        if (obj.product_family != 'Unified Systems') and (obj.product_family != 'Bearcat'):
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
        if (obj.product_family != 'Unified Systems') and (obj.product_family != 'Bearcat'):
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
        if (obj.product_family != 'Unified Systems') and (obj.product_family != 'Bearcat'):
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

def get_audit_trail_in_list(parammap):
    timer = TimeHelper()
    cur_date = timer.get_day_start(timer.get_mtime())- 24*60*60
    pre_date = cur_date - 24*60*60
    res = []
    in_param = dict(parammap["audit trail param map"])
    in_param['From Time']=[str(pre_date),]
    in_param['To Time']=[str(cur_date),]
    ca_dict = dict(parammap['major areas'])
    for k,v in ca_dict.iteritems():
        if 'To Value' not in in_param.keys():
            in_param['To Value'] = list(v)
        else:
            in_param['To Value'] += list(v)
    dber = DatabaseHelper()
    print in_param
    for e in dber.get_AR_from_audit_trail(in_param)[0]:
        res.append(generate_audit_trail_obj(e))
    return res

def count_audit_in(llist,parammap):
    res = {}
    ayer = ArrayMapHelper()
    for i in llist:
        k = get_ca_map_entry(parammap['major areas'],i.to_value)
        #logger.debug("k :" + str(k))
        ayer.update_oned_map_values(res, k + ' [In]')
    return res

def get_audit_trail_out_list(parammap):
    timer = TimeHelper()
    cur_date = timer.get_day_start(timer.get_mtime())- 24*60*60
    pre_date = cur_date - 24*60*60
    res = []
    out_param = dict(parammap["audit trail param map"])
    out_param['From Time']=[str(pre_date),]
    out_param['To Time']=[str(cur_date),]
    ca_dict = dict(parammap['major areas'])
    for k, v in ca_dict.iteritems():
        if 'From Value' not in out_param.keys():
            out_param['From Value'] = list(v)
        else:
            out_param['From Value'] += list(v)
    dber = DatabaseHelper()
    print out_param
    for e in dber.get_AR_from_audit_trail(out_param)[0]:
        res.append(generate_audit_trail_obj(e))
    return res

def count_audit_out(llist,parammap):
    res = {}
    ayer = ArrayMapHelper()
    for i in llist:
        k = get_ca_map_entry(parammap['major areas'], i.from_value)
        ayer.update_oned_map_values(res, k + ' [Out]')
    return res

def update_total_in_out_record_file(ddict, entries, file):
    timer = TimeHelper()
    cur_date = timer.get_day_start(timer.get_mtime())
    pre_date = cur_date - 24*60*60
    timestamp = timer.mtime_to_local_date(pre_date)

    logger.debug("[update_total_in_out_record_file]ddict :")
    logger.debug(str(ddict))

    in_total = 0
    out_total = 0
    for key in sorted(ddict.keys()):

        if key.find('In') != -1:
            in_total += ddict[key]
        elif key.find('Out') != -1:
            out_total += ddict[key]

    csvstr = timestamp
    header = 'Date'
    for k in entries:
        header += ',' + k
        if k in ddict.keys():
            csvstr += ',' + str(int(ddict[k]))
        else:
            csvstr += ',0'
    csvstr += ',' + str(in_total) + ',' + str(out_total) + '\n'
    header += ',' + 'Total In' + ',' + 'Total Out' + '\n'


    logger.debug("in_total : "+str(in_total))
    logger.debug("out_total : "+str(out_total))
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
        notice = notice + ' have no AR.<p>'
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

def get_ars_assigned_to_manager(ar_obj_list, parammap, files_to_send):
    logger.debug("[get_ars assigned to manager]......")
    rawars, numrawars = dber.get_AR_from_assigned_to_manager(parammap['assinged to manager param map'])
    if numrawars == 0:
        logger.debug("No open AR ...")
        return

    ar_obj_list += get_ar_obj_list(rawars)
    #dd ARs assigned to ca
    if "major area managers" in parammap.keys():
       add_assigned_to_ca(ar_obj_list,parammap["major area managers"])

    #save AR list to excel && append excel to sharepoint
    save_to_excel = dataprefix + parammap['report name'].replace(' ', '') + '_ARs_Total_List.xls'
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

def ar_total_in_out_trend_report(parammap, files_to_send):
    logger.debug("-"*40 + "[ar_total_in_out_trend_report]" + "-"*40)

    audit_in_list = get_audit_trail_in_list(parammap)
    in_map = count_audit_in(audit_in_list,parammap)
    audit_out_list = get_audit_trail_out_list(parammap)
    out_map = count_audit_out(audit_out_list,parammap)
    in_map.update(out_map)

    record_file = dataprefix + '[21]' + parammap["report name"].replace(' ', '') + '_ARs_Total_In_Out.csv'
    trend_record_file = dataprefix + '[22]' + parammap["report name"].replace(' ', '') + '_ARs_Total_In_Out_Trend.csv'
    entries = sorted([ca+' In' for ca in parammap["major area managers"]] + [ca+' Out' for ca in parammap["major area managers"]])
    #logger.debug('entries : '+str(entries))

    update_total_in_out_record_file(in_map, entries, record_file)
    ar_records_cnt = generate_AR_trends_report_data_file(28, record_file, trend_record_file)

    #draw total ar in/out trend chart
    date_x_unit = calc_date_x_unit(ar_records_cnt)
    title = parammap['report name'].replace(' ', '') + ' Total ARs In/Out Trend'
    lines = ['Total In', 'Total Out']
    save_to_png = pngprefix + '[02]' + parammap["report name"].replace(' ', '') + '_ARs_Total_In_Out_Trend.png'
    grapher.draw_trent_chart(trend_record_file, lines, title, 14, 4, 5, date_x_unit, save_to_png)
    files_to_send["image"].append(save_to_png)

def ar_total_age_report(ar_obj_list, parammap, files_to_send):
    logger.debug("-"*40 + "[ar_total_age_report]" + "-"*40)
    save_to_png = pngprefix + '[03]' + parammap["report name"].replace(' ', '') + '_AR_Total_Age.png'
    title = parammap["report name"].replace(' ', '') + ' Total ARs by Age'
    total_age_report(ar_obj_list, title, COLOR_SETS[0], save_to_png)
    files_to_send["image"].append(save_to_png)
    #sharepoint_images.append(bug_age_table)

def ar_total_trend_report(bugmap, parammap, files_to_send):
    logger.debug("-"*40 + "[ar_total_trend_report]" + "-"*40)
    summary_releases = sorted(parammap['assinged to manager param map']["Product Release"])
    record_file = dataprefix + '[31]' + parammap['report name'].replace(' ', '') + "_ARs_Total.csv"
    trend_record_file = dataprefix + '[32]' + parammap['report name'].replace(' ', '') + "_ARs_Total_Trend.csv"
    update_AR_summary_history_file(bugmap, summary_releases, record_file)
    ar_records_cnt = generate_AR_trends_report_data_file(128, record_file, trend_record_file)

    date_x_unit = calc_date_x_unit(ar_records_cnt)
    title = parammap['report name'].replace(' ', '') + ' Total ARs Trend'
    lines = ['Total']
    save_to_png = pngprefix + '[04]' + parammap['report name'].replace(' ', '') + '_ARs_Total_Trend.png'
    grapher.draw_trent_chart(trend_record_file, lines, title, 14, 4, 20, date_x_unit, save_to_png)
    files_to_send["image"].append(save_to_png)

def ar_direct_manager_report(ar_obj_list, parammap, files_to_send):
    logger.debug("-"*40 + "[ar_direct_manager_report]" +"-"*40)
    title = parammap['report name'].replace(' ', '') + ' Total ARs for Direct Manager'
    save_to_png = pngprefix + '[05]' + parammap["report name"].replace(' ', '') + '_ARs_DirectManager.png'
    direct_manager_report(ar_obj_list, title , save_to_png)
    files_to_send["image"].append(save_to_png)

def ar_tbv_report(parammap, files_to_send):
    logger.debug("-"*40 + "[ar_tbv_direct_manager_report]" + "-"*40)
    tbv_list, num_tbv = dber.get_AR_from_reported_to_manager(parammap['reported by manager param map'])
    if num_tbv != 0:
        tbvobjlist = get_ar_obj_list(tbv_list, 1)
        if "major area managers" in parammap.keys():
            add_assigned_to_ca(tbvobjlist, parammap["major area managers"])
        save_to_excel = dataprefix + parammap['report name'].replace(' ', '') + '_ARs_TBV_List.xls'
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
    for rel in parammap['report releases']:
        #get all the ar with 'report releases' == rel
        ars = filter_release(ar_obj_list, rel)
        ar_count_map = count_by_ca_manager(ars, cas, cammap)
        logger.debug('ar_count_map is :'+str(ar_count_map))

        #release age report
        title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ','') +' ARs by Age'
        color_set = COLOR_SETS[((parammap['report releases'].index(rel))+1)%len(COLOR_SETS)]
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
        ca_record_file = dataprefix + '[50]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total.csv'
        trend_ca_record_file = dataprefix + '[50]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total_Trend.csv'
        update_last_record(ca_record_file, timestamp, csvstr, header)
        ar_records_cnt = generate_AR_trends_report_data_file(28, ca_record_file, trend_ca_record_file)

        #calculate the x_unit
        date_x_unit = calc_date_x_unit(ar_records_cnt)
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
        age_record_file = dataprefix + '[50]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total_Age.csv'
        update_last_record(age_record_file, timestamp, csvstr, header)

        #draw release domain total trend chart
        lines = ['Domain Total']
        title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs Total Trend'
        save_to_png = pngprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_ARs_Trend.png'
        grapher.draw_trent_chart(trend_ca_record_file, lines, title, 14, 4, 20, date_x_unit, save_to_png)
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
        save_to_png = pngprefix + '[08]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_ARs_Trend_by_CA.png'
        grapher.draw_trent_chart(trend_ca_record_file, lines, title, 14, 4, 2, date_x_unit, save_to_png)
        files_to_send["image"].append(save_to_png)

        #draw release age report table for per CA
        for ca in cas:
            ca_ar_obj_list = ar_count_map[ca]
            if len(ca_ar_obj_list) != 0:
                title = parammap['report name'].replace(' ', '') + ' ' + ca + ' ' + rel.replace(' ','') +' ARs by Age'
                color_set = COLOR_SETS[((parammap['report releases'].index(rel))+1)%len(COLOR_SETS)]
                save_to_png = pngprefix + '[12]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_' + ca + '_ARs_by_Age.png'
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
        record_file = dataprefix + '[50]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total.csv'
        trend_record_file = dataprefix + '[50]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Total_Trend.csv'
        update_last_record(record_file, timestamp, csvstr, header)
        ar_records_cnt = generate_AR_trends_report_data_file(28, record_file, trend_record_file)

        date_x_unit = calc_date_x_unit(ar_records_cnt)

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
        grapher.draw_trent_chart(trend_record_file, lines, title, 14, 4, 2, date_x_unit, save_to_png)
        files_to_send["image"].append(save_to_png)

        #draw release age report table for per CA
        for ca in cas:
            ca_ar_obj_list = ar_count_map[ca]
            if len(ca_ar_obj_list) != 0:
                title = ca + ' ' + rel.replace(' ','') +' ARs by Age'
                color_set = COLOR_SETS[((parammap['age report releases'].index(rel))+1)%len(COLOR_SETS)]
                save_to_png = pngprefix + '[12]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_' + ca + '_ARs_by_Age.png'
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
    dir_list = [dataprefix, pngprefix, logprefix]
    for dir in dir_list:
        if not os.path.exists(dir):
            os.makedirs(dir)


def calc_date_x_unit(ar_records_cnt):
    """
    Calculate the x_unit when x aixs is date.
    :param ar_records_cnt: the count of AR records
    :return date_x_unit: daily/weekly/monthly
    """
    if (ar_records_cnt <= 7):
        date_x_unit = "daily"
    elif (ar_records_cnt > 7 and ar_records_cnt <= 70):
        date_x_unit = "weekly"
    else:
        date_x_unit = "monthly"

    return date_x_unit

def main():
    parammap = init_param(arg_parser()) #init parameters
    init_dir()  #make directories: data, png and log
    files_to_send = {}
    files_to_send['attachment'] = []
    files_to_send["image"] = []
    additional_body = ""
    ar_obj_list = []
    bugmap = dict()
    logger.debug("="*25 + "Start" + "="*25 + "\n" + "-"*25 + "REPORT NAME: " + parammap['report name'] + "-"*25)

    get_ars_assigned_to_manager(ar_obj_list, parammap, files_to_send)
    ar_blocking_report(ar_obj_list, parammap, files_to_send)
    ar_total_report(ar_obj_list, bugmap, parammap, files_to_send)
    #ar_total_in_out_trend_report(parammap, files_to_send)
    ar_total_age_report(ar_obj_list, parammap, files_to_send)
    ar_total_trend_report(bugmap, parammap, files_to_send)
    ar_direct_manager_report(ar_obj_list, parammap, files_to_send)
    ar_tbv_report(parammap, files_to_send)
    #ar_radar_report.radar_report(parammap, files_to_send)
    releases_report(ar_obj_list, parammap, files_to_send)
    logger.debug(bugmap.keys())
    sent_report_email(parammap, files_to_send, bugmap.keys(), additional_body)
    logger.debug("="*25 + "End" + "="*25)
    return 0

if __name__ == '__main__':
    main()






