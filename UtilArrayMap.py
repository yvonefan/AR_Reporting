# HIT @ EMC Corporation
# UtilArrayMap.py
# Purpose: Provides general functions on list, etc..
# Author: Youye Sun
# Version: 1.0 03/12/2015

import math
from UtilLogging import *
logger = LogHelper()

class ArrayMapHelper:
    def __init__(self, log=None):
        self.logger = log

    def positive_map_filter(self,mmap, key_list):
        """
        Filters the map with specified keys
        :param mmap: map of meta data and data
        :param key_list: list of keys
        :return: map containing the data of the specified keys
        """
        res = {}

        for key in mmap.keys():
            if key in key_list:
                res[key] = mmap[key]
        return res

    def negative_map_filter(self,mmap, key_list):
        res = {}
        for key in mmap.keys():
            if key not in key_list:
                res[key] = mmap[key]
        return res

    def twod_map_to_twod_array(self,colname, rowname, mmap):
        """
        Coverts the content in 2D map to 2D array
        :param colname: list of column names
        :param rowname: list of row names
        :param mmap: map of meta data and data
        :return: 2d array containing data of the map
        """
        text = []
        i = 0
        for key in rowname:
            text.append([])

            for t in colname:
                text[i].append(mmap[key][t])
            i +=1
        return text

    def get_sublist_from_twodmap(self,mmap, twodkey, if_total = False, if_title=False, title=None):
        res = []
        for key in sorted(mmap.keys()):
            res.append(mmap[key][twodkey])
        if if_total:
            res.append(self.sum_array(res))
        if if_title:
            res.insert(0,title)
        return res

    def twod_map_to_report_table(self,mmap,tablename,iftotal):
        """
        Converts data map to report table (2D List)
        :param mmap: map containing meta data and data
        :param tablename: name of the report table, can be None
        :param iftotal: if to calculate the total row
        :return: two d list containing the report
        """
        colname = sorted(mmap[mmap.keys()[0]].keys())
        rowname = sorted(mmap.keys())
        text = self.twod_map_to_twod_array(colname,rowname,mmap)
        total =None
        if iftotal:
            total = []
            total.append("Total")
            for i in range(0,len(text[0])):
                total.append(self.sum_col(text,i))
        res = self.combine_report_table(tablename,colname,rowname,text,total)
        return res

    def update_twod_map_values(self, mmap, onedkey, twodkey, twodkeyset, iftotal=False):
        """
        Updates map values according to the keys. If the key exists, add 1 to the value.
        Otherwise, init the value to 1.
        :param mmap: map containing metadata and data
        :param onedkey: first dimension key of the map
        :param twodkey: second dimension key
        :param twodkeyset: expected second dimension keys
        :param iftotal: if to count total
        :return:
        """

        if onedkey in mmap.keys():
            if(iftotal):
                mmap[onedkey]['Total'] += 1
            mmap[onedkey][twodkey] += 1
        else:
            mmap[onedkey]={}
            for key in twodkeyset:
                mmap[onedkey][key] = 0
            if(iftotal):
                mmap[onedkey]['Total'] = 1
            mmap[onedkey][twodkey] = 1

    def update_twod_map_values2(self, mmap, onedkey, twodkey, twodkeyset, iftotal=False):
        """
        Updates map values according to the keys. If the key exists, add 1 to the value.
        Otherwise, init the value to 1.
        :param mmap: map containing metadata and data
        :param onedkey: first dimension key of the map
        :param twodkey: second dimension key
        :param twodkeyset: expected second dimension keys
        :param iftotal: if to count total
        :return:
        """

        if onedkey in mmap.keys():
            if(iftotal):
                mmap[onedkey]['Total'] += 1
            mmap[onedkey][twodkey] += 1
        else:
            mmap[onedkey]={}
            for key in twodkeyset:
                mmap[onedkey][key] = 0
            if(iftotal):
                mmap[onedkey]['Total'] = 1
            mmap[onedkey][twodkey] = 1

    def update_oned_map_values(self,mmap,onedkey):
        if onedkey in mmap.keys():
            mmap[onedkey] += 1
        else:
            mmap[onedkey] = 1

    def get_ca_map_entry(self,mmap, v):
        v = "\"" + v + "\""
        for k in mmap.keys():
            if v in mmap[k]:
                return k

    def combine_report_table(self,tablename,colname,rowname,text,total):
        """
        Combines table name, column names, row names, table text, and total summary
        :param tablename: name of the table to be put in the very left-top corner
        :param colname: names of the columns
        :param rowname: names of the rows
        :param text: text of the table
        :param total: totals of each column, it can be None
        :return: content of the report table
        """
        if colname is None or rowname is None or text is None:
            self.logger.error("colname or rowname or text can not be empty...") if self.logger else ""
            raise
        if (len(colname) != len(text[0])) or (len(rowname) != len(text)):
            self.logger.error("length of colname or rowname doesn't match with text...") if self.logger else ""
            raise
        res = []
        res.append([])
        if tablename is None:
            res[0].append(" ")
        else:
            res[0].append(tablename)
        res[0] = res[0] + colname
        for i in range(0,len(text)):
            res.append([])
            res[i+1].append(rowname[i])
            res[i+1] = res[i+1] + text[i]
        if total is not None:
            res.append([])
            res[len(res)-1] = res[len(res)-1] + total
        return res

    def replace_twod_array_zero(self,ttable,row_start,row_end,col_start,col_end,to_char):
        """
        Replaces '0' or 0 in the table with specified char
        :param ttable: table containing data
        :param row_start: index of the start row
        :param row_end: index of the end row
        :param col_start: index of the start column
        :param col_end: index of the end column
        :param to_char: char to replace '0' / 0  to ''
        :return:
        """
        for i in range(row_start,row_end+1):
            for j in range(col_start,col_end+1):
                if ttable[i][j] == '0' or ttable[i][j] == 0:
                    ttable[i][j] = to_char

    def sort_twod_array_by_col(self,ttable,row_start,target_col_index):
        """
        Sorts two dimesion array by column
        :param ttable: two dimension array
        :param row_start: index of the row to start sorting
        :param target_col_index: index of the column used to compare
        :return: sorted two dimension array
        """
        for i in range(row_start,len(ttable)):
            for j in range(i+1,len(ttable)):
                if ttable[j][target_col_index] < ttable[i][target_col_index]:
                    tmp = ttable[j]
                    ttable[j]=ttable[i]
                    ttable[i] = tmp
        return ttable

    def get_array_min_max_index_value(self,llist):
        """
        Gets the minimum and maximum value and index of the array
        :param llist: array of data
        :return: minimum value and its index, and maximum value and its index
        """
        nonNaNIndex =1
        for i in range(0,len(llist)):
            if not math.isnan(llist[i]):
                nonNaNIndex = i
                break
            else:
                nonNaNIndex +=1
        if nonNaNIndex == len(llist):
            return

        min_v = llist[nonNaNIndex]
        max_v =llist[nonNaNIndex]
        min_p =nonNaNIndex
        max_p =nonNaNIndex
        for i in range(nonNaNIndex,len(llist)):
            if llist[i] <= min_v:
                min_v = llist[i]
                min_p = i
            elif llist[i] >= max_v:
                max_v = llist[i]
                max_p = i
        return (min_v,min_p,max_v,max_p)

    def twod_array_to_html_table(self, twod_array, name, cap=''):
        """
        Converts two dimension array into html table
        :param twod_array: two dimesion array containing the data
        :param name: name of the table (ID)
        :param cap: capital of the table
        :return: html flavored table
        """
        res_html = '<div ><a name=\"' + name + '\"></a>'
        if len(cap) != 0:
            res_html += '<span>' + cap + '</span><table>'
        for i in range(0,len(twod_array)):
            res_html += '<tr>'
            for j in range(0,len(twod_array[0])):
                if i == 0:
                    res_html += '<th>'+str(twod_array[i][j]) + '</th>'
                else:
                    res_html += '<td>'+str(twod_array[i][j]).decode("cp1251").encode("utf8") + '</td>'
            res_html += '</tr>'
        res_html += '</table></div>'
        return res_html

    def sum_col(self,ttable, col_index):
        """
        Gets the sum of data(int) in a column
        :param ttable: 2d data array
        :param col_index: index of the column
        :return: the sum of data of a column
        """
        row_len = len(ttable)
        res = 0
        for i in range(0,row_len):
            res += ttable[i][col_index]
        return res

    def sum_array(self,llist):
        """
        Sums the data in the array
        :param llist: array containing the data
        :return: sum of the data
        """
        res = 0
        for i in range(0,len(llist)):
            res += llist[i]
        return res

    def insert_col(self,ttable, col, index):
        """
        Inserts column into table at the index number.
        :param ttabel: table to insert column into
        :param col: column to be inserted
        :param index: position to insert into
        :return: 2d array containing the column inserted
        """
        text = []
        for i in range(0,len(ttable)):
            text.append([])
            for j in range(0,index):
                text[i].append(ttable[i][j])
            text[i].append(col[i])
            for k in range(index,len(ttable[0])):
                text[i].append(ttable[i][k])
        return text

    def sum_two_arrays(self, array1, array2):
        if len(array1) != len(array2):
            return
        res = [0]*len(array1)
        for i in range(0, len(array1)):
            res[i] = int(array1[i]) + int(array2[i])
        return res

    def array_to_csv_string(self, array):
        res = ''
        for i in array:
            res += str(i) + ','
        return res[:-1]

    def remove_map_quote(self,mmap):
        res = dict()
        for k in mmap.keys():
            llist = list()
            for i in mmap[k]:
                llist.append(i.replace("\"",""))
            res[k] = llist
        return res

    def append_multi_to_array(self, array, *items):
        for i in items:
            array.append(i)

if __name__ == '__main__':
    ayer = ArrayMapHelper()
    res = ayer.sum_two_arrays(['0','1','2','3'],[1,2,3,4])
    for i in res:
        print i
    res = list()
    ayer.append_multi_to_array(res, 1, 2, 3, 4)
    print res