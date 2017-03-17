# HIT @ EMC Corporation
# UtilGraph.py
# Purpose: Provides functions to generate graphics and charts
# Author: Youye Sun
# Version: 1.0 03/16/2015
import datetime, random

from matplotlib import pyplot as plt
from pandas import read_csv
import matplotlib.dates as mdates

from UtilArrayMap import *
from UtilMath import *

class GraphHelper:
    def __init__(self,log=None):
        self.logger=log

    def draw_table_first_row_colored(self,text,canvas_width, canvas_height,top, if_tight, title=None, title_loc='left',
                                          font_size=10):
        logger.debug("draw_table_first_row_colored")
        lightgrn = (192/255.0, 192/255.0, 192/255.0)
        fig = plt.figure(figsize=(canvas_width,canvas_height))
        ax = fig.add_subplot(111, frameon=True, xticks=[], yticks=[])
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        the_table=plt.table(cellText=text[1:],colLabels=text[0],loc='center', cellLoc='center',
                            colColours=[lightgrn]*len(text[0]) )
        plt.subplots_adjust(left=0.01, bottom=0.01,right=0.99,top=top)
        table_props=the_table.properties()
        table_cells=sorted(table_props['child_artists'])
        celw = 1.0/(len(text[0]))
        celh = 1.0/(len(text))
        for cell in table_cells:
            cell.set_width(celw)
            cell.set_height(celh)
            cell.set_fontsize(font_size)
            cell.set_text_props(multialignment='left')
        if if_tight:
            for i in range(0,len(text[0])):
                the_table.auto_set_column_width(i)
        the_table.set_fontsize(font_size)
        if title is not None:
            plt.title(title,loc=title_loc)
        return (plt,the_table)

    def draw_table_first_last_row_colored(self,text, canvas_width, canvas_height,top, if_tight, title=None, title_loc='left',
                                          font_size=10):
        """
        Draw the table with first and last row colored
        :param text: data of the table
        :param canvas_width: width of the canvas
        :param canvas_height: height of the canvas
        :param col_widths: list of width percentage of each column
        :param top: top position of the table
        :param if_tight: if to set the image as tight
        :param title_loc: the location of the title
        :param title: content of the title
        :param font_size: font size
        :return: plt and the table handler
        """

        lightgrn = (192/255.0, 192/255.0, 192/255.0)
        fig = plt.figure(figsize=(canvas_width,canvas_height))
        ax = fig.add_subplot(111, frameon=True, xticks=[], yticks=[])
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        the_table=plt.table(cellText=text[1:],colLabels=text[0],loc='center', cellLoc='center',
                            colColours=[lightgrn]*len(text[0]))
        plt.subplots_adjust(left=0.01, bottom=0.01,right=0.99,top=top)
        cell_dict=the_table.get_celld()
        for i in range(0,len(text[0])):
            cell_dict[(len(text)-1,i)].set_color(lightgrn)
            cell_dict[(len(text)-1,i)].set_edgecolor('Black')
        table_props=the_table.properties()
        table_cells=sorted(table_props['child_artists'])
        celw = 1.0/(len(text[0]))
        celh = 1.0/(len(text))
        for cell in table_cells:
            cell.set_width(celw)
            cell.set_height(celh)
            cell.set_fontsize(font_size)
            cell.set_text_props(multialignment='left')
        if if_tight:
            for i in range(0,len(text[0])):
                the_table.auto_set_column_width(i)
        the_table.set_fontsize(font_size)
        if title is not None:
            plt.title(title,loc=title_loc)
        return (plt,the_table)

    def draw_age_table(self,text,canvas_height,canvas_width,top,if_tight,original_col_nums, week_set,color_set,title=None,
                       title_loc='left',font_size=10):
        """
        Draws the age report chart
        :param text: data of the bug age report chart
        :param canvas_height: height of the canvas
        :param canvas_width: width of the canvas
        :param top: position of the top of the table
        :param if_tight: if to tight the cell width and height
        :param original_col_nums: original number of column in bug age table
        :param week_set: weeks duration we care (right half of the chart)
        :param color_set: color set for ros and columns
        :param title: title of the report chart
        :param title_loc: location of the title
        :param font_size: font size of the chars in the chart
        :return: plt and table handler
        """
        plt, the_table= self.draw_table_first_last_row_colored(text, canvas_height, canvas_width, top, if_tight, title,title_loc,
                                                      font_size)
        cell_dict=the_table.get_celld()
        for j in range(0,4):
            for i in range(0,original_col_nums):
                cell_dict[(j+4,i)].set_color(color_set[len(week_set)-1-j])
                cell_dict[(j+4,i)].set_edgecolor('Black')
        for j in range(original_col_nums,len(text[0])):
            for k in range(week_set[j-original_col_nums]+1,len(text)-1):
                cell_dict[(k,j)].set_color(color_set[len(color_set)-1-j+original_col_nums])
                cell_dict[(k,j)].set_edgecolor('Black')
        return (plt,the_table)

    def gap_y_position(self,llist,gap):
        """
        Gaps the y positions of the text, so that they don't overlap with each other
        :param llist: two dimesion array. For each row it has the row name and the position value
        :param gap:
        :return:
        """
        for i in range(0,len(llist)-1):
            pre = llist[i][1]
            for j in range(i+1,len(llist)):
                if abs(llist[j][1] - pre) < gap:
                    llist[j][1] += gap - abs(llist[j][1] - pre)

    def draw_trent_chart(self,file,field_list,title_str,plt_width,plt_height,y_unit,x_unit,save_to_file):
        """
        Draws trent chart
        :param field_list: releases to de drawn
        :param title_str: title of the chart
        :param plt_width: width of the canvas
        :param plt_height: height of the canvas
        :param y_unit: unit of the y ax
        :param save_to_file: path to save chart to
        :return:
        """
        ayer = ArrayMapHelper()
        mather = MathHelper()
        ar_history_data = read_csv(file)
        #logger.debug("ar_history_data : " +str(ar_history_data))
        colors = [(31, 119, 180),  (255, 127, 14), (174, 199, 232),(255, 187, 120),
                 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
                 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
                (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
                (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
        # Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
        for i in range(len(colors)):
            r, g, b = colors[i]
            colors[i] = (r / 255., g / 255., b / 255.)
        plt.figure(figsize=(plt_width,plt_height))
        ax = plt.subplot(111)
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        datemin = time.strptime(ar_history_data['Date'].values[0],'%m/%d/%Y')
        datemin = datetime.date(datemin.tm_year,datemin.tm_mon,datemin.tm_mday)
        #datemin_fix = datemin+ datetime.timedelta(7- datemin.weekday())
        datemax = time.strptime(ar_history_data['Date'].values[len(ar_history_data['Date'].values)-1],'%m/%d/%Y')
        datemax =datetime.date(datemax.tm_year,datemax.tm_mon,datemax.tm_mday)
        #datemax_fix = datemax + datetime.timedelta(7 - datemax.weekday() )
        #ax.set_xlim(datemin, datemax_fix)
        ax.set_xlim(datemin, datemax)
        if x_unit == "monthly":
            xus  = mdates.MonthLocator()
            xusFmt = mdates.DateFormatter('%m/%Y')
            ax.xaxis.set_major_locator(xus)
            ax.xaxis.set_major_formatter(xusFmt)
            plt.xticks(fontsize=8)
        elif x_unit == "weekly":
            x_p = []
            x_l = []
            tmp = datemin
            while tmp <= datemax:
                x_p.append(tmp)
                x_l.append(tmp.strftime('%m/%d/%Y'))
                tmp += datetime.timedelta(7)
            ax.set_xlim(datemin, datemax)
            plt.xticks(x_p,x_l,fontsize=8)
        elif x_unit == "daily":
            x_p = []
            x_l = []
            tmp = datemin
            while tmp <= datemax:
                x_p.append(tmp)
                x_l.append(tmp.strftime('%m/%d/%Y'))
                tmp += datetime.timedelta(1)
            ax.set_xlim(datemin, datemax)
            plt.xticks(x_p,x_l,fontsize=8)
        days = mdates.DayLocator()
        ax.xaxis.set_minor_locator(days)
        ax.grid(True)

        plt.tick_params(axis="both", which="both", bottom="on", top="off",
                    labelbottom="on", left="off", right="off", labelleft="on")

        y_pos_list =[]
        for rank, column in enumerate(field_list):
            y_pos_list.append([])
            y_pos_list[rank].append(column)
            #logger.debug("ar_history_data[column] :"+str(ar_history_data[column]))
            y_pos_list[rank].append(ar_history_data[column.replace("\n", " ")].values[-1])
        self.gap_y_position(y_pos_list,1)

        mins=[]
        maxs=[]
        for rank, column in enumerate(field_list):
            #logger.debug("column : "+str(column))
            plt.plot(ar_history_data.Date.values,ar_history_data[column].values, lw=2.5, color=colors[rank])
            plt.text(datemax, y_pos_list[rank][1], int(ar_history_data[column].values[-1]), fontsize=8, color=colors[rank])
            min_v,min_p,max_v,max_p = ayer.get_array_min_max_index_value(ar_history_data[column].values)
            mins.append(min_v)
            maxs.append(max_v)
            if(min_p!=(len(ar_history_data[column].values)-1)):
                plt.text(ar_history_data['Date'].values[min_p],min_v-1,'min '+str(int(min_v)),fontsize=8,color=colors[rank])
            if(max_p!=(len(ar_history_data[column].values)-1)):
                plt.text(ar_history_data['Date'].values[max_p],max_v+1,'max '+str(int(max_v)),fontsize=8,color=colors[rank])
        y_min,yminminp,yminmax,yminmaxp = ayer.get_array_min_max_index_value(mins)
        y_max_min,y_maxminp,y_max,y_maxmaxp = ayer.get_array_min_max_index_value(maxs)
        y_floor = mather.ffloor(int(y_min),y_unit)
        y_roof = mather.rroof(int(y_max),y_unit)

        if(len(field_list)>= 1):
            y_roof += y_unit*len(field_list)
            for rank, column in enumerate(field_list):
                y_pos = y_roof - y_unit*rank
                plt.text(datemax - datetime.timedelta(len(ar_history_data[column].values)/5), y_pos, column,
                         fontsize=8, color=colors[rank])

        plt.ylim(y_floor,y_roof + y_unit/2)
        plt.yticks(range(y_floor, y_roof + y_unit/2, y_unit), [str(x) for x in range(y_floor, y_roof + y_unit/2, y_unit)],
                   fontsize=8)
        plt.title(title_str,loc='left')
        plt.savefig(save_to_file, bbox_inches='tight')

    def _draw_line(self,xdata,ydata,xmax,color,ifshowdata=False):
        #logger.debug(xdata)
        #logger.debug(ydata)
        #logger.debug(xmax)
        ayer = ArrayMapHelper()
        plt.plot(xdata,ydata,lw=2.5,color=color)
        plt.text(xmax,ydata[-1],int(ydata[-1]),fontsize=8,color=color)
        min_v,min_p,max_v,max_p = ayer.get_array_min_max_index_value(ydata)
        if ifshowdata:
            for y in ydata:
                plt.text(xdata[ydata.index(y)],y + 1,str(int(y)),fontsize=8,color=color)
        else:
            if(min_p!=(len(ydata)-1)):
                plt.text(xdata[min_p],min_v-1,'min '+str(int(min_v)),fontsize=8,color=color)
            if(max_p!=(len(ydata)-1)):
                plt.text(xdata[max_p],max_v+1,'max '+str(int(max_v)),fontsize=8,color=color)
        return min_v, max_v

    def draw_target_chart(self,targets_dates,targets_data,total_dates,total_data,age_dates,age_data,title_str,plt_width,plt_height,y_unit,x_unit,save_to_file):
        """
        Draws trent chart
        :param title_str: title of the chart
        :param plt_width: width of the canvas
        :param plt_height: height of the canvas
        :param y_unit: unit of the y ax
        :param save_to_file: path to save chart to
        :return:
        """
        ayer = ArrayMapHelper()
        mather = MathHelper()
        colors = [(31, 119, 180),  (255, 127, 14), (174, 199, 232)]
        for i in range(len(colors)):
            r, g, b = colors[i]
            colors[i] = (r / 255., g / 255., b / 255.)
        plt.figure(figsize=(plt_width,plt_height))
        ax = plt.subplot(111)
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        datemin = time.strptime(targets_dates[0],'%m/%d/%Y')
        datemin = datetime.date(datemin.tm_year,datemin.tm_mon,datemin.tm_mday)
        datemax = time.strptime(targets_dates[-1],'%m/%d/%Y')
        datemax =datetime.date(datemax.tm_year,datemax.tm_mon,datemax.tm_mday)
        ax.set_xlim(datemin, datemax)
        if x_unit == "monthly":
            xus  = mdates.MonthLocator()
            xusFmt = mdates.DateFormatter('%m/%Y')
            ax.xaxis.set_major_locator(xus)
            ax.xaxis.set_major_formatter(xusFmt)
            plt.xticks(fontsize=8)
        elif x_unit == "weekly":
            x_p = []
            x_l = []
            tmp = datemin
            while tmp <= datemax:
                x_p.append(tmp)
                x_l.append(tmp.strftime('%m/%d/%Y'))
                tmp += datetime.timedelta(7)
            ax.set_xlim(datemin, datemax)
            plt.xticks(x_p,x_l,fontsize=8)
        elif x_unit == "daily":
            x_p = []
            x_l = []
            tmp = datemin
            while tmp <= datemax:
                x_p.append(tmp)
                x_l.append(tmp.strftime('%m/%d/%Y'))
                tmp += datetime.timedelta(1)
            ax.set_xlim(datemin, datemax)
            plt.xticks(x_p,x_l,fontsize=8)
        days = mdates.DayLocator()
        ax.xaxis.set_minor_locator(days)
        ax.grid(True)
        #xus  = mdates.MonthLocator()
        #xusFmt = mdates.DateFormatter('%m/%Y')
        #ax.xaxis.set_major_locator(xus)
        #ax.xaxis.set_major_formatter(xusFmt)
        #plt.xticks(fontsize=8)
        days = mdates.WeekdayLocator()
        ax.xaxis.set_minor_locator(days)
        ax.grid(True)

        plt.tick_params(axis="both", which="both", bottom="on", top="off",
                    labelbottom="on", left="off", right="off", labelleft="on")

        mins = []
        maxs = []
        min_v, max_v = self._draw_line(targets_dates,targets_data,datemax,colors[0],True)
        mins.append(min_v)
        maxs.append(max_v)

        #total_datemax = time.strptime(total_dates[-1],'%m/%d/%Y')
        #total_datemax =datetime.date(total_datemax.tm_year,total_datemax.tm_mon,total_datemax.tm_mday)
        #min_v,max_v = self._draw_line(total_dates,total_data,total_datemax,colors[1])
        #mins.append(min_v)
        #maxs.append(max_v)

        age_datemax = time.strptime(age_dates[-1],'%m/%d/%Y')
        age_datemax =datetime.date(age_datemax.tm_year,age_datemax.tm_mon,age_datemax.tm_mday)
        min_v,max_v = self._draw_line(age_dates,age_data,age_datemax,colors[1])
        mins.append(min_v)
        maxs.append(max_v)

        y_min,yminminp,yminmax,yminmaxp = ayer.get_array_min_max_index_value(mins)
        y_max_min,y_maxminp,y_max,y_maxmaxp = ayer.get_array_min_max_index_value(maxs)
        y_floor = mather.ffloor(int(y_min),y_unit)
        y_roof = mather.rroof(int(y_max),y_unit) + y_unit
        plt.text(datemax - datetime.timedelta(len(targets_dates)*7/5), y_roof, "Target", fontsize=8, color=colors[0])
        #plt.text(datemax - datetime.timedelta(len(targets_dates)*7/5), y_roof - y_unit, "Domain Total", fontsize=8, color=colors[1])
        plt.text(datemax - datetime.timedelta(len(targets_dates)*7/5), y_roof - y_unit, "Actual", fontsize=8, color=colors[1])

        plt.ylim(y_floor,y_roof + y_unit/2)
        plt.yticks(range(y_floor, y_roof + y_unit/2, y_unit), [str(x) for x in range(y_floor, y_roof + y_unit/2, y_unit)],
                   fontsize=8)
        plt.title(title_str,loc='left')
        plt.savefig(save_to_file, bbox_inches='tight')

    def draw_weekly_chart(self,file,field_list,title_str,plt_width,plt_height,y_unit,save_to_file):
        """
        Draws trent chart
        :param title_str: title of the chart
        :param plt_width: width of the canvas
        :param plt_height: height of the canvas
        :param y_unit: unit of the y ax
        :param save_to_file: path to save chart to
        :return:
        """
        ayer = ArrayMapHelper()
        mather = MathHelper()
        ar_history_data = read_csv(file)
        colors = [(31, 119, 180),  (255, 127, 14), (174, 199, 232),(255, 187, 120),
                 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
                 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
                (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
                (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
        # Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
        for i in range(len(colors)):
            r, g, b = colors[i]
            colors[i] = (r / 255., g / 255., b / 255.)
        plt.figure(figsize=(plt_width,plt_height))
        ax = plt.subplot(111)
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        datemin = time.strptime(ar_history_data['Date'].values[0],'%m/%d/%Y')
        datemin = datetime.date(datemin.tm_year,datemin.tm_mon,datemin.tm_mday)
        datemin_fix = datemin - datetime.timedelta(3)
        datemax = time.strptime(ar_history_data['Date'].values[len(ar_history_data['Date'].values)-1],'%m/%d/%Y')
        datemax =datetime.date(datemax.tm_year,datemax.tm_mon,datemax.tm_mday)
        datemax_fix = datemax + datetime.timedelta(7 - datemax.weekday() )
        ax.set_xlim(datemin_fix, datemax_fix)
        xus = mdates.MonthLocator()
        xusFmt = mdates.DateFormatter('%m/%Y')
        ax.xaxis.set_major_locator(xus)
        ax.xaxis.set_major_formatter(xusFmt)
        plt.xticks(fontsize=8)
        days = mdates.WeekdayLocator()
        ax.xaxis.set_minor_locator(days)
        ax.grid(True)

        plt.tick_params(axis="both", which="both", bottom="on", top="off",
                    labelbottom="on", left="off", right="off", labelleft="on")

        y_pos_list =[]
        for rank, column in enumerate(field_list):
            y_pos_list.append([])
            y_pos_list[rank].append(column)
            y_pos_list[rank].append(ar_history_data[column.replace("\n", " ")].values[-1])
        self.gap_y_position(y_pos_list,1)

        mins=[]
        maxs=[]
        for rank, column in enumerate(field_list):
            plt.plot(ar_history_data.Date.values,ar_history_data[column].values, lw=2.5, color=colors[rank])
            plt.text(datemax, y_pos_list[rank][1], int(ar_history_data[column].values[-1]), fontsize=8, color=colors[rank])
            min_v,min_p,max_v,max_p = ayer.get_array_min_max_index_value(ar_history_data[column].values)
            mins.append(min_v)
            maxs.append(max_v)
            if(min_p!=(len(ar_history_data[column].values)-1)):
                plt.text(ar_history_data['Date'].values[min_p],min_v-1,'min '+str(int(min_v)),fontsize=8,color=colors[rank])
            if(max_p!=(len(ar_history_data[column].values)-1)):
                plt.text(ar_history_data['Date'].values[max_p],max_v+1,'max '+str(int(max_v)),fontsize=8,color=colors[rank])
        y_min,yminminp,yminmax,yminmaxp = ayer.get_array_min_max_index_value(mins)
        y_max_min,y_maxminp,y_max,y_maxmaxp = ayer.get_array_min_max_index_value(maxs)
        y_floor = mather.ffloor(int(y_min),y_unit)
        y_roof = mather.rroof(int(y_max),y_unit)

        if(len(field_list)> 1):
            y_roof += y_unit*len(field_list)
            for rank, column in enumerate(field_list):
                y_pos = y_roof - y_unit*rank
                plt.text(datemax_fix - datetime.timedelta(len(ar_history_data[column].values)/5), y_pos, column,
                         fontsize=8, color=colors[rank])

        plt.ylim(y_floor,y_roof + y_unit/2)
        plt.yticks(range(y_floor, y_roof + y_unit/2, y_unit), [str(x) for x in range(y_floor, y_roof + y_unit/2, y_unit)],
                   fontsize=8)
        plt.title(title_str,loc='left')
        plt.savefig(save_to_file, bbox_inches='tight')

    def draw_pie(self, data, label, explode, figwidth, figheight, title, save_to):
        colors = [(31, 119, 180),  (255, 127, 14), (174, 199, 232),(255, 187, 120),
                 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
                 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
                (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
                (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
        # Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
        for i in range(len(colors)):
            r, g, b = colors[i]
            colors[i] = (r / 255., g / 255., b / 255.)
        plt.figure(figsize=(figwidth,figheight))
        plt.rcParams['font.size'] = 10.0
        plt.rcParams['xtick.labelsize'] = 10.0
        plt.rcParams['axes.titlesize'] = 14.0
        plt.axes([0.09,0.09,0.7,0.7])
        l = len(data)
        labels = list()
        for la in label:
            labels.append(la + " " + str(data[label.index(la)]))
        rd = random.randint(0,5)
        plt.pie(data,labels=labels,colors=colors[rd:rd+l],explode=explode,autopct='%1.1f%%', shadow=True, startangle=90)
        plt.axis('equal')
        plt.title(title,y=1.08)
        plt.savefig(save_to, bbox_inches='tight')


if __name__ == '__main__':
    mmap = [["Program","Blocker","P0", "P1","P2","Total"],["Bearcat",1,2,3,4,5],["Bald eagle",6,7,8,9,10]]
    grapher = GraphHelper()
    #grapher.draw_table_first_last_row_colored(mmap, 'left'),
    dates=["6/14/2015","6/21/2015","6/28/2015","7/5/2015","7/12/2015","7/19/2015","7/26/2015","8/2/2015","8/9/2015","8/16/2015",
           "8/23/2015","8/30/2015","9/6/2015","9/13/2015","9/20/2015","9/27/2015","10/4/2015","10/11/2015","10/18/2015","10/25/2015",
           "11/1/2015","11/8/2015","11/15/2015"]
    targets = [59,56,53,51,48,45,42,39,36,33,
               30,28,25,22,19,16,13,10,8,5,
               2,0,0]
    actualdates = ["6/14/2015","6/15/2015","6/16/2015","6/17/2015","6/18/2015","6/19/2015","6/20/2015","6/21/2015",
                   "6/22/2015","6/23/2015"]
    actuals=[54,56,76,23,44,55,66,44,33,66]
    grapher.draw_target_chart(dates,targets,actualdates,actuals,"Platform Core",7,4,20,"targettest.png")
