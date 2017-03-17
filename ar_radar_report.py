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
import threading
import os

from UtilGraph import *
from UtilArrayMap import *
from UtilExcel import *
from UtilEmail import *
from ARAuditTrail import *
from RadarCrawler import *

__author__ = "Ming.Yao@emc.com"

reload(sys)
sys.setdefaultencoding('utf8')

__filename__ = os.path.basename(__file__)
fpath = os.path.dirname(os.path.realpath(__file__))
logger = LogHelper(fpath+'\\' + 'ca_daily_in_out_log.txt')

grapher = GraphHelper(logger)
ayer = ArrayMapHelper(logger)
excer = ExcelHelper(logger)
crawler = RadarCrawler()

timer = TimeHelper(logger)

CUR_TIME = int(timer.get_mtime())
CUR_DATE = timer.mtime_to_radar_date(CUR_TIME)
PRE_DATE_RADAR = timer.mtime_to_radar_date(CUR_TIME - 24*60*60)
PRE_DATE_LOCAL = timer.mtime_to_local_date(CUR_TIME - 24*60*60)
CUR_WEEK_START_TIME = timer.get_week_start(CUR_TIME)
CUR_WEEK_START_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME)
CUR_WEEK_END_DATE_RADAR = timer.mtime_to_radar_date(CUR_WEEK_START_TIME + 7*24*60*60 - 60*60)
PRE_WEEK_START_DATE_RADAR = timer.mtime_to_radar_date(CUR_WEEK_START_TIME - 7*24*60*60)
PRE_WEEK_END_DATE_RADAR = timer.mtime_to_radar_date(CUR_WEEK_START_TIME - 60*60)

BASIC_URL_WEEKLY = 'http://radar.usd.lab.emc.com/Classes/Misc/sp.asp?t=ArrivalARS&p=%s&tab=B%s&' \
            'p2=Bug|&p1=P00|P01|P02|&p13=%s&p10=%s|&wkend=%s&dt=%s'
BASIC_URL_DAILY = 'http://radar.usd.lab.emc.com/Classes/Misc/sp.asp?t=ArrivalARS&p=%s&tab=B%s&' \
            'p2=Bug|&p1=P00|P01|P02|&p13=%s&p10=%s|&p100=dd&wkend=%s&dt=%s'

lightgrn = (192/255.0, 192/255.0, 192/255.0)
red = (153/255.0, 0/255.0, 0/255.0)

dataprefix = fpath+'\\data\\'
pngprefix = fpath+'\\png\\'

count_day = 0
count_week = 0


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
        return parammap

def get_urls(release, manager, CWEEK):
    manager = manager.replace(' ', '%20')
    manager = manager.replace('"', '')
    release = release.replace(' ', '%20')
    if CWEEK == 0:
        BASIC_URL = BASIC_URL_WEEKLY
        END_DATE = PRE_WEEK_END_DATE_RADAR
        dt = int(CUR_WEEK_START_TIME)-1
    elif CWEEK == 1:
        BASIC_URL = BASIC_URL_WEEKLY
        END_DATE = CUR_DATE
        dt = CUR_TIME
    else:
        BASIC_URL = BASIC_URL_DAILY
        END_DATE = PRE_DATE_RADAR
        dt = int(timer.get_day_start(timer.get_mtime()))-1
    logger.debug("END_DATE: "+str(END_DATE))
    res1 = BASIC_URL % (release, "I", "Movein|New|Reopen|Other|", manager, END_DATE, dt)
    res2 = BASIC_URL % (release, "O", "Duplicate|Fixed|DeferDismissal|ProgramChangeDeferral|NondeferDismissal|Other|",
                        manager, END_DATE, dt)
    return res1, res2

def sent_report_email(parammap,files_to_send):
    """
    Sends out report via email
    :param bug_releases: release of the bugs
    :param additional_body: additional to append at the end of the email
    :return:
    """
    mailer = EmailHelper()
    att = None
    try:
        att = files_to_send['attachment']
    except KeyError:
        print "no attachment"
    subj = parammap['report name'] + ' Weekly Bug Report (Week-ending Date: '+PRE_WEEK_END_DATE_RADAR+')'
    ifHtmlNody = True
    embed_images = files_to_send['image']
    body='<h3>This Report Is Generated Automatically By Platform Product Integration Team.</h3><hr>'
    additional_body = ""

    notice = '<p style="color:red"> Liberty-BrooksHill, KittyHawk+ SP2, and Bearcat SP1 have not been enabled on Radar yet. They' \
             ' will be tracked once they are enabled..</p>'
    body = body + notice
    style = '<style>table,th,td{border: 1px solid black;border-collapse: collapse;font-family:"Arial";'+\
            'font-size:8.0pt;color:black} table{width:900px;}caption{text-align: left;font-size:14.0pt;}'+\
            'th{text-align:center;font:bold;background-color:#ccff99} td{text-align:center;font:bold;}' +\
            'span{margin-bottom:20px;display:block;font-family:"sans-serif";font-size:14.0pt;}</style>'
    mailer.send_email(parammap['to'],subj,style+body,ifHtmlNody,embed_images,additional_body,parammap['cc'],att)

def analyz_in_ar_lists(ar_list):
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
    res.extend([arrival_movein, arrival_new, arrival_reopen, arrival_other, total])
    return res

def analyz_out_ar_lists(ar_list):
    res = list()
    closure_dup = 0
    closure_fix = 0
    closure_deferdis = 0
    closure_prog = 0
    closure_nodeferdis = 0
    closure_other = 0
    for ar in ar_list:
        if ar.ac_method == "Duplicate":
            closure_dup += 1
        elif ar.ac_method == "Fixed":
            closure_fix += 1
        elif ar.ac_method == "Defer Dismissal":
            closure_deferdis += 1
        elif ar.ac_method == "Program Change Deferral":
            closure_prog += 1
        elif ar.ac_method == "Non-defer Dismissal":
            closure_nodeferdis += 1
        elif ar.ac_method == "Other":
            closure_other += 1
    total = closure_dup + closure_fix + closure_deferdis + closure_prog + closure_nodeferdis + closure_other
    res.extend([closure_dup, closure_fix, closure_deferdis, closure_prog, closure_nodeferdis,
                closure_other, total])
    return res

def get_ars_detail(ar_list):
    res = list()
    for ar in ar_list:
        res.append(ar.to_list())
    return res

#**********************************************************    AR IN/Out Report By Week  ********************************************#
def ar_in_out_report_by_week(parammap, files_to_send):
    logger.debug("-"*40 + "[ar_in_out_report_by_week]" + "-"*40)
    for rel in sorted(parammap['report releases']):
        map_ca=parammap["ca managers"]
        map_domain=parammap["director"]
        map_others=parammap["other ca managers"]

        pre_week_data=[['Previous week ('+PRE_WEEK_START_DATE_RADAR+' ~ '+PRE_WEEK_END_DATE_RADAR+')'],['In'],['Out'],['Change'],['Fixed']]
        cur_week_data=[['This week ('+CUR_WEEK_START_DATE+' ~ '+CUR_DATE+')'],['In'],['Out'],['Change'],['Fixed']]

        threads = []
        t11 = threading.Thread(target=ar_in_out_summary_by_week, args=(pre_week_data, map_ca, map_others, map_domain, rel, 0))
        t12 = threading.Thread(target=ar_in_out_summary_by_week, args=(cur_week_data, map_ca, map_others, map_domain, rel, 1))
        threads.extend([t11, t12])
        for i in range(0, len(threads)):
            threads[i].start()
        for i in range(0, len(threads)):
            threads[i].join()

        #merge data list
        data = pre_week_data + cur_week_data
        logger.debug("data: "+str(data))

        #set value '0' to ' '
        for i in range(0, len(data)):
            for j in range(0, len(data[0])):
                if data[i][j] == '0' or data[i][j] == 0:
                    data[i][j] = ' '

        title=parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs Weekly In/Out'
        plt, table= grapher.draw_table_first_row_colored(data, 1.1*len(data[0]),
                                                  0.5*len(data), 0.98, True, title, 'left', 10)
        #draw row 6 Black
        cell_dict = table.get_celld()
        for i in range(0,len(data[0])):
            cell_dict[(5,i)].set_color(lightgrn)
            cell_dict[(5,i)].set_edgecolor('Black')
        #draw clown 8,9 text Red
        for i in range(1, 5) + range(6, len(data)):
            for j in range(len(data[0])-2, len(data[0])):
                cell_dict[i, j].get_text().set_color(red)

        save_to_file = pngprefix + '[09]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ','') + '_Weekly_In_Out_Summary.png'
        plt.savefig(save_to_file, bbox_inches='tight')

        files_to_send["image"].append(save_to_file)

def ar_in_out_summary_by_week(data,  map_ca, map_others, map_domain, release, CWEEK=1):
    logger.debug("ar_in_out_summary_by_week")
    ca_io = {}
    others_io = {'In':0,'Out':0,'Change':0,'Fixed':0}
    domain_io = {'In':0,'Out':0,'Change':0,'Fixed':0}

    threads = []
    # Get the In/Out data for each CA.
    for ca in sorted(map_ca.keys()):
        ca_io[ca] = {'In':0,'Out':0,'Change':0,'Fixed':0}
        t111 = threading.Thread(target=get_statistic_from_name_weekly, args=(release, ca, map_ca[ca], ca_io[ca], CWEEK))
        threads.append(t111)
    #Get the In/Out data of other CA managers
    t112 = threading.Thread(target=get_statistic_from_name_weekly, args=(release, 'others', map_others, others_io, CWEEK))
    #Get the In/Out data of domain
    t113 = threading.Thread(target=get_statistic_from_name_weekly, args=(release, 'domain', map_domain, domain_io, CWEEK))
    threads.extend([t112, t113])

    for i in range(0, len(threads)):
        threads[i].start()
    for i in range(0, len(threads)):
        threads[i].join()

    #logger.debug("ca_io: "+str(ca_io))
    #logger.debug("others_io: "+str(others_io))
    #logger.debug("domain_io: "+str(domain_io))

    for ca in sorted(ca_io.keys()):
        data[0].append(ca)
        data[1].append(ca_io[ca]['In'])
        data[2].append(ca_io[ca]['Out'])
        data[3].append(ca_io[ca]['Change'])
        data[4].append(ca_io[ca]['Fixed'])
    #add headers
    data[0].extend(['Others','CA Total','Domain Total'])
    #add others_io data
    data[1].append(others_io['In'])
    data[2].append(others_io['Out'])
    data[3].append(others_io['Change'])
    data[4].append(others_io['Fixed'])
    #add ca total data
    for i in range(1,5):
        ca_total=0
        for j in range(1,6):
            ca_total+=data[i][j]
        data[i].append(ca_total)
    #add domain_io data
    data[1].append(domain_io['In'])
    data[2].append(domain_io['Out'])
    data[3].append(domain_io['Change'])
    data[4].append(domain_io['Fixed'])
    #logger.debug("data: "+str(data))

def get_statistic_from_name_weekly(rel, ca, name_list, data, CWEEK):
    logger.debug("get_statistic_from_name_weekly[ca] : "+str(ca))
    data['In'] = 0
    data['Out'] = 0
    data['Change'] = 0
    data['Fixed'] = 0
    for name in name_list:
        #logger.debug("name: "+str(name))
        url_in, url_out = get_urls(rel, name, CWEEK)

        logger.debug("url_in: "+str(url_in))
        logger.debug("url_out: "+str(url_out))

        #get week's in ars
        arin = crawler.get_url_response(url_in)
        in_ar_obj = crawler.parse_ar_html_table(arin)
        week_in_ar_obj = get_weekly_ar_list(in_ar_obj, ca, CWEEK)
        in_count = analyz_in_ar_lists(week_in_ar_obj)

        #get week's out ars
        arout = crawler.get_url_response(url_out)
        out_ar_obj = crawler.parse_ar_html_table(arout)
        week_out_ar_obj = get_weekly_ar_list(out_ar_obj, ca, CWEEK)
        out_count = analyz_out_ar_lists(week_out_ar_obj)

        data['In'] += in_count[-1]
        data['Out'] += out_count[-1]
        data['Change'] = in_count[-1] - out_count[-1]
        data['Fixed'] += out_count[1]

    return data

def get_weekly_ar_list(ar_list, ca, CWEEK):
    if CWEEK==0:
        START_TIME = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(CUR_WEEK_START_TIME)-7*24*60*60))
        END_TIME = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(CUR_WEEK_START_TIME)-1))
    else:
        START_TIME = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(CUR_WEEK_START_TIME)))
        END_TIME = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    res = list()
    date = list()
    for ar in ar_list:
        if ar.ac_date >= START_TIME and ar.ac_date <= END_TIME:
            ar.ca = ca
            res.append(ar)
    return res

#**********************************************************    AR IN/Out Report By Day   *******************************************#
def ar_in_out_report_by_day(parammap, files_to_send):
    logger.debug("-"*40 + "ar_in_out_report_by_day" + "-"*40)
    ca_map = dict()
    others_map = dict()
    domain_map = dict()
    for rel in sorted(parammap['report releases']):
        ca_map[rel] = dict()
        others_map[rel] = dict()
        domain_map[rel] = dict()

        #get daily in/out AR count list and detail info list
        record_file = dataprefix  + '[61]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_In_Out.csv'
        trend_record_file = dataprefix + '[62]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_In_Out_Trend.csv'
        threads = []
        for ca in sorted(parammap['ca managers'].keys()):
            ca_map[rel][ca] = dict()
            t1=threading.Thread(target=get_statistic_from_name_daily, args=(rel, ca_map[rel][ca], parammap["ca managers"][ca]))
            threads.append(t1)
        t2=threading.Thread(target=get_statistic_from_name_daily, args=(rel, others_map[rel], parammap["other ca managers"]))
        t3=threading.Thread(target=get_statistic_from_name_daily, args=(rel, domain_map[rel], parammap["director"]))
        threads.extend([t2, t3])

        for i in range(0, len(threads)):
            threads[i].start()
        for i in range(0, len(threads)):
            threads[i].join()

        #update ca in/out record file and ca in/out trend record file
        csvstr = PRE_DATE_LOCAL
        header = 'Date'
        for ca in sorted(parammap['ca managers'].keys()):
            csvstr += ',' + str(ca_map[rel][ca]["in_count"][-1]) + ',' + str(ca_map[rel][ca]["out_count"][-1])
            header += ',' + ca.replace(' ', '') + ' In,' + ca.replace(' ', '') + ' Out'
        header += ',' + 'Total In' + ',' + 'Total Out' + '\n'
        csvstr += ',' + str(domain_map[rel]['in_count'][-1]) + ',' + str(domain_map[rel]['out_count'][-1]) + '\n'
        #logger.debug("csvstr : "+str(csvstr))
        update_last_record(record_file, PRE_DATE_LOCAL, csvstr, header)
        generate_AR_trends_report_data_file(28, record_file, trend_record_file)

        #draw daily in/out summary table
        ar_in_out_summary_report_daily(rel, ca_map, others_map, domain_map, parammap, files_to_send)
        #save daily in/out ar detail to excel file
        ar_in_out_save_to_excel_daily(rel, ca_map, parammap, files_to_send)

        #dorw daily in/out total trend chart of domain
        title =  parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs In/Out Trend'
        lines = ['Total In', 'Total Out']
        save_to_png = pngprefix + '[10]' + parammap['report name'].replace(' ', '') + '' + rel.replace(' ', '') + '_Total_ARs_In_Out_Trend.png'
        grapher.draw_trent_chart(trend_record_file, lines, title, 14, 4, 5, 'weekly', save_to_png)
        files_to_send["image"].append(save_to_png)

        #dorw daily in/out trend chart by ca
        for ca in sorted(parammap['ca managers'].keys()):
                title = parammap['report name'].replace(' ', '') + ' ' + ca.replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs In/Out Trend'
                save_to_png = pngprefix + '[13]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_' + ca.replace(' ', '') + "_In_Out_Trend.png"
                lines = [ca.replace(' ', '')+' In', ca.replace(' ', '')+' Out']
                grapher.draw_trent_chart(trend_record_file, lines, title, 14, 4, 2, "weekly", save_to_png)
                files_to_send["image"].append(save_to_png)

    logger.debug("[daily]ca_map : "+ str(ca_map))
    logger.debug("[daily]others_map : "+ str(others_map))
    logger.debug("[daily]domain_map : "+ str(domain_map))

def get_statistic_from_name_daily(rel, data_map, namelist):

    """
    in_ar_obj_list:  AR objects list     [<RadarCrawler.AR instance at 0x05543260>, <RadarCrawler.AR instance at 0x055432B0>, ......]
    inres:      AR statistic list([ca, arrival_movein, arrival_new, arrival_reopen, arrival_other, total])
    in_ar_obj_list_yesterday:       [<RadarCrawler.AR instance at 0x05543260>, <RadarCrawler.AR instance at 0x055432B0>, ......]
    in_ar_detail_list_yesterday:
    """

    logger.debug("get_statistic_from_name_daily[namelist]: "+str(namelist))
    in_ar_obj_total = []
    out_ar_obj_total = []

    for name in namelist:
        #logger.debug("name: "+str(name))
        url_in, url_out = get_urls(rel, name, 2)
        logger.debug("[yesterday]url_in: "+str(url_in))
        logger.debug("[yesterday]url_out: "+str(url_out))

        #get yesterday's in ars
        arin = crawler.get_url_response(url_in)
        logger.debug("arin[" + str(name) + "]: " + str(arin))
        in_ar_obj = crawler.parse_ar_html_table(arin)
        logger.debug("in_ar_obj[" + str(name) + "]: " + str(in_ar_obj))
        in_ar_obj_total += in_ar_obj
        in_count_with_total = analyz_in_ar_lists(in_ar_obj)
        logger.debug("in_count_with_total[" + str(name) + "]: " + str(in_count_with_total))

        #get yesterday's out ars
        arout = crawler.get_url_response(url_out)
        out_ar_obj = crawler.parse_ar_html_table(arout)
        logger.debug("out_ar_obj[" + str(name) + "]: " + str(out_ar_obj))
        out_ar_obj_total += out_ar_obj
        out_count_with_total = analyz_out_ar_lists(out_ar_obj)
        logger.debug("out_count_with_total[" + str(name) + "]: " + str(out_count_with_total))

    in_detail_total = get_ars_detail(in_ar_obj_total)
    out_detail_total = get_ars_detail(out_ar_obj_total)

    logger.debug("in_count_with_total[total]: " + str(in_count_with_total))
    logger.debug("out_count_with_total[total]: " + str(out_count_with_total))
    data_map["in_count"] =  in_count_with_total
    data_map["in_list"] = in_detail_total
    data_map["out_count"] = out_count_with_total
    data_map["out_list"] = out_detail_total

def ar_in_out_summary_report_daily(rel, ca_map, others_map, domain_map, parammap, files_to_send):
    ca_list = parammap['ca managers'].keys()
    In_Out_Count_Header = [PRE_DATE_RADAR] + sorted(ca_list) + ['Others', 'CA Total', 'Domain Total']

    In_Count_List = [["Move in"] ,["New"] ,["Reopen"],["Other"],["In Total"]]
    for i in range(0, 5):
        others = others_map[rel]["in_count"][i]
        ca_total = 0
        domain_total = domain_map[rel]["in_count"][i]
        for ca in sorted(ca_list):
            value = ca_map[rel][ca]["in_count"][i]
            ca_total += value
            In_Count_List[i].append(value)
        In_Count_List[i].extend([others, ca_total, domain_total])

    Out_Count_List=[["Duplicate"], ["Fixed"], ["Defer Dismissal"], ["Program Change Deferral"], ["Non-defer Dismissal"],["Other"], ["Out Total"]]
    for i in range(0, 7):
        others = others_map[rel]["out_count"][i]
        ca_total = 0
        domain_total = domain_map[rel]["out_count"][i]
        for ca in sorted(ca_list):
            value = ca_map[rel][ca]["out_count"][i]
            ca_total += value
            Out_Count_List[i].append(ca_map[rel][ca]["out_count"][i])
        Out_Count_List[i].extend([others, ca_total, domain_total])

    #logger.debug("In_Count_List : "+str(In_Count_List))
    #logger.debug("Out_Count_List : "+str(Out_Count_List))
    data = [In_Out_Count_Header] + In_Count_List + Out_Count_List

    logger.debug("[daily]data: "+str(data))

    #set value '0' to ' '
    for i in range(1, len(data)):
        for j in range(1, len(data[0])):
            if data[i][j] == '0' or data[i][j] == 0:
                    data[i][j] = ' '

    title = parammap['report name'].replace(' ', '') + ' ' + rel.replace(' ', '') + ' ARs Daily In/Out'
    plt, table = grapher.draw_table_first_last_row_colored(data, 1.1*len(data[0]), 0.5*len(data), 0.98, True, title, 'left', 10)

    #draw row 6 Black
    cell_dict = table.get_celld()
    row = 6
    for col in range(0,len(data[0])):
            cell_dict[(row-1, col)].set_color(lightgrn)
            cell_dict[(row-1, col)].set_edgecolor('Black')

    ar_in_out_report_daily_table = pngprefix + '[11]' + parammap['report name'].replace(' ', '') + '_' +  rel.replace(' ', '') + '_Daily_In_Out_Summary.png'
    plt.savefig(ar_in_out_report_daily_table, bbox_inches='tight')
    files_to_send["image"].append(ar_in_out_report_daily_table)

def update_last_record(file, timestamp, csvstr, header=''):
    with open(file, "a+") as myfile:
        if(os.path.getsize(file) == 0):
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

def generate_AR_trends_report_data_file(num,file_origin,file):
    """
    Generates data file for AR trends report
    :return:
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

def ar_in_out_save_to_excel_daily(rel, domain_map, parammap, files_to_send):
    AR_Detail_Header = ["Issue ID", "AC Date", "AC", "AC Method", "Status",
             "Status Details", "Priority", "Type", "Major Area", "Product Area",
             "Assigned-to", "Assigned-to Sr Mgr", "Reported-by", "Reported-by Sr Mgr"]
    cas = parammap['ca managers'].keys()
    In_AR_Detail_List = list()
    Out_AR_Detail_List = list()
    for ca in sorted(cas):
        In_AR_Detail_List.extend(domain_map[rel][ca]["in_list"])
        Out_AR_Detail_List.extend(domain_map[rel][ca]["out_list"])
    In_AR_Detail_List.insert(0, AR_Detail_Header)
    Out_AR_Detail_List.insert(0, AR_Detail_Header)

    #save In AR to excel
    Daily_In_Excel = dataprefix + '[71]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Daily_In_list.xls'
    excer.save_twod_array_to_excel(In_AR_Detail_List,Daily_In_Excel,'ARs')
    excer.add_filter(Daily_In_Excel,'ARs')
    files_to_send["attachment"].append(Daily_In_Excel)

    #save Out AR to excel
    Daily_Out_Excel = dataprefix + '[72]' + parammap['report name'].replace(' ', '') + '_' + rel.replace(' ', '') + '_Daily_Out_List.xls'
    excer.save_twod_array_to_excel(Out_AR_Detail_List,Daily_Out_Excel,'ARs')
    excer.add_filter(Daily_Out_Excel,'ARs')
    files_to_send["attachment"].append(Daily_Out_Excel)

#**********************************************************    AR IN/Out Report By Day Begin   *******************************************#
def radar_report(parammap, files_to_send):
    ar_in_out_report_by_week(parammap, files_to_send)
    ar_in_out_report_by_day(parammap, files_to_send)

if __name__ == '__main__':
    from time import clock
    start=clock()
    parammap = init_param(arg_parser())
    logger.debug("="*25 + "Start" + "="*25 + "\n" + "-"*25 + "REPORT NAME: " + parammap['report name'] + "-"*25)
    files_to_send = dict()
    files_to_send["image"] = list()
    files_to_send["attachment"]=list()
    radar_report(parammap, files_to_send)
















