# HIT @ EMC Corporation
# UtilDatabase.py
# Purpose: Provides database access functions
# Author: Youye Sun
# Version: 2.0 03/12/2015

import time
from pyars import erars,cars
from UtilString import *
#from UtilLogging import *

class DatabaseHelper:
    def __init__(self,log=None):
        self.logger = log
        self.strer = StringHelper(log)

    def _db_login(self,handler):
        """
        Logs in database
        :param handler: the db connection object
        :return:
        """
        try:
            #TODO:
            # handler.Login('arsystem.isus.emc.com', 'dimsreport', 'report')
            handler.Login('arsappprd01.isus.emc.com', 'dimsreport', 'report')
            self.logger.debug("log in RemedyAR successfully ...") if self.logger else "No"
        except Exception, e:
            self.logger.debug(e) if self.logger else "No"
            raise

    def _db_logoff(self,handler):
        """
        Logs off database
        :param handler: the db connection object
        :return:
        """
        try:
            handler.Logoff()
            self.logger.debug("logs off RemedyAR successfully...") if self.logger else "No"
        except Exception, e:
            self.logger.debug(e) if self.logger else "No"
            raise

    def _generate_manager_query_string(self,mmap):
        """
        Generates the query string for assigned to manager table
        :param mmap: map containing the query params
        :return:
        """
        res = ""
        try:
            self.logger.debug("generating query string for assigned to manager table ...") if self.logger else ""
            if 'Senior Manager' in mmap.keys():
                res = "( " + self.strer.list_to_xsv_str(mmap['Senior Manager'],'\'Senior Manager\'',
                                                      " = "," OR ") + " )"
            if 'Direct Manager' in mmap.keys():
                if len(res) != 0:
                    res = res[:len(res)-1]
                    res += " OR " + self.strer.list_to_xsv_str(mmap['Direct Manager'],
                                                             '\'Direct Manager\''," = "," OR ") + " )"
                else:
                    res += "( " + self.strer.list_to_xsv_str(mmap['Direct Manager'],\
                                                                      '\'Direct Manager\''," = "," OR ") + " )"
            if 'Assigned-to' in mmap.keys():
                if len(res) != 0:
                    res = res[:len(res)-1]
                    res += " OR " + self.strer.list_to_xsv_str(mmap['Assigned-to'],'\'Assigned-to\'',\
                                                                      " = "," OR ") + " )"
                else:
                    res += " ( " + self.strer.list_to_xsv_str(mmap['Assigned-to'],'\'Assigned-to\'',\
                                                                      " = "," OR ") + " )"
            if 'Status' in mmap.keys():
                res += " AND (" + self.strer.list_to_xsv_str(mmap['Status'],'\'Status\''," = ",\
                                                                        " OR ") + " )"
            if 'Major Area' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['Major Area'],'\'Major Area\''\
                                                                         ," = "," OR ") + " )"
            if 'Status Details' in mmap.keys():
                res += " AND (" + self.strer.list_to_xsv_str(mmap['Status Details'],'\'Status Details\''," = ",\
                                                                    " OR ") + " )"
            if 'Parent Bug #' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['Parent Bug #'],'\'Parent Bug #\''\
                                                                         ," = "," OR ") + " )"
            if 'Type' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['Type'],'\'Type\'', " = ",\
                                                                         " OR ") + " )"
            if 'Priority' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['Priority'],'\'Priority\'',\
                                                                         " = "," OR ") + " )"
            if 'Product Release' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['Product Release'],\
                                                                         '\'Product Release\''," = "," OR ") + " )"
            if 'Product Area' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['Product Area'],\
                                                                         '\'Product Area\''," = "," OR ") + " )"
            if "Product Family" in mmap.keys():
                res+= " AND ( " + self.strer.list_to_xsv_str(mmap['Product Family'],\
                                                                         '\'Product Family\''," = "," OR ") + " )"
            if "Product" in mmap.keys():
                res+= " AND ( " + self.strer.list_to_xsv_str(mmap['Product'], '\'Product\''," = "," OR ") + " )"
            if 'No Product' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['No Product'],'\'Product\'',\
                                                                         " != "," AND ") + " )"
            if 'No Direct Manager' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['No Direct Manager'],\
                                                                         '\'Direct Manager\'', " != "," AND ") + " )"
            if 'No Assigned-to' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['No Assigned-to'],\
                                                                         '\'Assigned-to\''," != ", " AND ") + " )"
            if 'No Product Family' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['No Product Family'],\
                                                                         '\'Product Family\'', " != "," AND ") +" )"
            if "Create-date Low" in mmap.keys():
                res += " AND ( " +self.strer.list_to_xsv_str(mmap['Create-date Low'],'\'3\''," >= "," OR ") + " )"
            if 'Create-date High' in mmap.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(mmap['Create-date High'], '\'3\''," < "," OR ") + " )"
            self.logger.debug("query string is %s ..." % res) if self.logger else ""
            return str(res)
        except Exception, e:
            self.logger.error(e) if self.logger else ""
            raise

    def get_AR_from_assigned_to_manager(self,mmap):
        """
        Gets the platform unity ars from Assigned to Manager table
        :param mmap: map containing the query params
        :return:
        """
        self.logger.debug("getting ARs from assigned to manage table ...") if self.logger else ""
        ars = erars.erARS()
        self._db_login(ars)
        schema = 'EMC:Issue Assigned-to Manager Join'
        '''
        query = """
                ('Product Family' = "Unified Systems") AND ('Senior Manager' = "Yan, Sam")
                AND  ('Status' =  "Open" OR 'Status'  =  "Waiting on Originator")
                AND 'Parent Bug #' = $NULL$  AND 'Type' =  "Bug" AND 'Priority' <  "P03"
                AND 'Product Release' = "Merlin"
                """
        '''
        query = self._generate_manager_query_string(mmap)
        #remove 'AND' before ()
        import re
        query = re.sub("^(\s+\w+\s+)\(", "(", query, 1)
        #self.logger.debug("query : " + query)
        """
        fields = ('Entry-Id','Summary','Assigned-to','Direct Manager','Reported by','Create-date','Status','Status Details',
                'Blocking','Priority','Type','Estimated Checkin Date','Reported by Group','Reported by Function',
                'Product Release', 'Product Family','Product Area','Major Area', 'Releases Built-in', 'Claassification',
                '# of Dup', 'Version Found')
        """
        fields = (536870921, 536870925, 600000701,       536870929,   600000700,           3,        7,     536870941,
                  700000320,536870922,536871084,    536871606,            536871388,         536871389,
                  536870940,     536871628,        8,             536871412,            536871455,     536870927,
                  536870945, 536870914, 536871535)
        try:
            self.logger.debug("getting list entry with fields ...") if self.logger else ""
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields,None)
            self.logger.debug("got %s of entries"%(str(num))) if self.logger else ""
        except Exception,e:
            self.logger.error(e) if self.logger else ""
            time.sleep(5)
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields, None)
        self._db_logoff(ars)
        return (entries, num)

    def get_child_ar_from_audit_trail(self,entry_id,start_date,end_date):
        ars = erars.erARS()
        self._db_login(ars)
        schema = 'EMC:Issue_Audit_join'
        query = ""
        query = query + "'536870921'=\"" + str(entry_id) + "\" AND "  # Entry_ID
        query = query + "'536870925'=\"Classification\" AND "  # "attribute change part"="Product Area"
        query = query + "'536870917'=\"Child\""  # "To Value"="CS Linux"
        # Rules for change time of the "Attribute"
        #query = query + "('536870929'>=" + str(start_date) + ") AND ('536870929'<=" + str(end_date) + ")"
        #print "get child query:",query
        fields = (536870921, 536870916, 536870917, 536870929, 536870938)
        try:
            self.logger.debug("getting list entry with fields ...") if self.logger else ""
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields,None)
            self.logger.debug("got %s of entries"%(str(num))) if self.logger else ""
        except Exception,e:
            self.logger.error(e) if self.logger else ""
            time.sleep(5)
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields, None)
        self._db_logoff(ars)
        return (entries, num)

    def get_fixed_time_from_audit_trail_with_rules(self, entry_id):
        """
        use ar's entry_id to search ar info in the table 'EMC:Issue_Audit_join'.
        :param entry_id: ar's id
        :return: (entries, num) the result is only one ar's info.
        """
        self.logger.debug("getting AR field from audi trial table by AR id...") if self.logger else ""
        ars = erars.erARS()
        self._db_login(ars)
        schema = 'EMC:Issue_Audit_join'

        query = ""
        # Rules for "EntryId"
        #query = query + "('536870921'=\"" + entry_id + "\" AND "
        query = query + "('536870921'=\"" + entry_id + "\" AND "
        # Rules for Change of the "Attribute"
        query = query + "'536870926'=\"Field Change\" AND '536870925'=\"Status\""
        # Rules for change time of the "Attribute"
        query = query + " AND '536870917'=\"Fixed\")"

        #print "DEBUG query=[[" + query + "]]"
        # To retrieve following fields in schema: 'EMC:Issue_Audit_join'
        #    Entry-Id:                536870921
        #    Comment:                 536870926
        #    Attribute Label:         536870925
        #    To Value:                536870917
        #    Audit Create Date:       536870929
        #use fields to select which info should be shown in the search results, all the fileds are defined in the related table in library.
        fields = (536870921, 536870926, 536870925, 536870917, 536870929)
        try:
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields)
        except erars.ARError as err:
            print "ARError: wait 5 seconds and try again"
            time.sleep(5)
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields)
        self._db_logoff(ars)
        return (entries, num)

    def get_AR_from_reported_to_manager(self,mmap):
        """
        Gets the platform unity ars from Reported to Manager table
        :param mmap: map containing the query params
        :return:
        """
        self.logger.debug("getting ARs from reported to manage table ...") if self.logger else ""
        ars = erars.erARS()
        self._db_login(ars)
        schema = 'EMC:Issue Reported by Manager Join'
        query = self._generate_manager_query_string(mmap)
        """
        fields = ('Entry-Id','Summary','Assigned-to','Direct Manager','Reported by','Create-date','Status','Status Details',
            'Blocking','Priority','Type','Estimated Checkin Date','Reported by Group','Reported by Function',
            'Product Release', 'Product Family','Product Area','Major Area','Releases Built-in','Claassification',
            '# of Dup', 'Version Found')
        """
        fields = (536870921, 536870925, 600000701,       536870929,   600000700,           3,        7,     536870941,
                 700000320,536870922,536871084,    536871606,            536871388,         536871389,
                 536870940,     536871628,        8,             536871412,     536871455,        536870927,
                 536870945, 536870914)
        try:
            self.logger.debug("getting list entry with fields ...") if self.logger else ""
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields, None)
            self.logger.debug("got %s of entries"%(str(num))) if self.logger else ""
        except Exception,e:
            self.logger.error( e) if self.logger else ""
            time.sleep(5)
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields, None)
        self._db_logoff(ars)
        return (entries, num)

    def _get_audit_trail_query_string(self,dict):
        res = ""
        try:
            self.logger.debug("generating query string for assigned to manager table ...") if self.logger else ""
            if 'Type' in dict.keys():
                if len(res) != 0:
                    res += " AND ( " + self.strer.list_to_xsv_str(dict['Type'],'\'Type\'', " = ", " OR ") + " )"
                else:
                    res += "( " + self.strer.list_to_xsv_str(dict['Type'],'\'Type\'', " = ", " OR ") + " )"
            if 'Attribute Label' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Attribute Label'],'\'536870925\'', " = ", " OR ") + " )"
            if 'No To' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['No To'],'\'536870917\'', " != "," AND ") + " )"
            if 'To Value' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['To Value'], '\'536870917\''," = "," OR ") + " )"
            if 'No From' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['No From'],'\'536870916\'', " != "," AND ") + " )"
            if 'From Value' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['From Value'], '\'536870916\''," = "," OR ") + " )"
            if 'From Time' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['From Time'], '\'536870929\''," >= "," OR ") + " )"
            if 'To Time' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['To Time'],'\'536870929\''," < ","OR") + " )"
            if 'Priority' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Priority'],'\'Priority\'', " = "," OR ") + " )"
            if 'Product Release' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Product Release'], '\'Product Release\''," = ",
                                                         " OR ") + " )"
            if 'Product' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Product'], '\'Product\''," = ", " OR ") + " )"
            if 'Product Family' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Product Family'], '\'Product Family\''," = ",
                                                         " OR ") + " )"
            if 'Product Area' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Product Area'], '\'Product Area\''," = ",
                                                         " OR ") + " )"
            if 'Prime Bug #' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Prime Bug #'],'\'Parent Bug #\''\
                                                                         ," = "," OR ") + " )"
            if 'Major Area' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Major Area'],'\'Major Area\''\
                                                                         ," = "," OR ") + " )"
            if 'Create-date Low' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Create-date Low'], '\'3\''," >= "," OR ") + " )"
            if 'Create-date High' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Create-date High'], '\'3\''," < "," OR ") + " )"
            if 'No Product' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['No Product'],'\'536871386\'', " != "," AND ") + " )"
            if 'No Product Family' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['No Product Family'],'\'536871628\'', " != "," AND ") + " )"
            if 'Assigned-to' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['Assigned-to'],'\'Assigned-to\''," = "," OR ") + " )"
            if 'No Assigned-to' in dict.keys():
                res += " AND ( " + self.strer.list_to_xsv_str(dict['No Assigned-to'],\
                                                                         '\'Assigned-to\''," != ", " AND ") + " )"
            self.logger.debug("query string is %s ..." % res) if self.logger else ""
            #print res
            return str(res)
        except Exception, e:
            self.logger.error(e) if self.logger else ""
            raise

    def get_AR_from_audit_trail(self,dict):
        ars = erars.erARS()
        self._db_login(ars)
        schema = 'EMC:Issue_Audit_join'
        query = self._get_audit_trail_query_string(dict)
        #fields =(536870929,536870917,536870916,536870921,536870925,536870927,536871628,536870940)
        # To retrieve following fields in schema: 'EMC:Issue_Audit_join'
        #    Entry-Id:                536870921
        #    From Value:              536870916
        #    To Value:                536870917
        #    Create Date(touch date): 536870929
        #    Submitter2(touch_man):   536870938
        #    Assigned-to Full Name:   600000701
        #    Product Area:            8
        #    Status:                  7
        #    Status Details:          536870941
        #    ckbx_Not A Child:        536871535
        #    Assigned-to:             4
        #    Major Area:              536871412
        #    Type:                    536871084
        #    Create-date:             3
        #    Attribute:               536870925
        #    Product Release :        536870940
        fields = (536870921, 536870916, 536870917, 536870929, 536870938, 600000701, 8, 7, 536870941, 536871535, 4, 536871412,
        536871084, 3, 536870925, 536870940)
        try:
            self.logger.debug("getting list entry with fields ...") if self.logger else ""
            (entries, num) = ars.GetListEntryWithFields(schema,query,fields,None)
            self.logger.debug("got %s of entries"%(str(num))) if self.logger else ""
        except Exception,e:
            self._db_logoff(ars)
            self.logger.error(e) if self.logger else ""
            time.sleep(5)
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields, None)
        self._db_logoff(ars)
        return (entries, num)

    def _get_employee_query_string(self,ddict):
        res = ""
        try:
            self.logger.debug("generating query string for employee table ...") if self.logger else ""
            if 'Direct Manager' in ddict.keys():
                res += "( " + self.strer.list_to_xsv_str(ddict['Direct Manager'],'\'Direct Manager\'', " = ", " OR ") + " )"
            if 'Senior Manager' in ddict.keys():
                res += " OR ( " + self.strer.list_to_xsv_str(ddict['Senior Manager'],'\'Senior Manager\'', " = ", " OR ") + " )"
            self.logger.debug("query string is %s ..." % res) if self.logger else ""
            #print res
            return str(res)
        except Exception, e:
            self.logger.error(e) if self.logger else ""
            raise

    def get_employee(self, ddict):
        ars = erars.erARS()
        self._db_login(ars)
        schema = 'EMC:SHARE:Employee'
        query = self._get_employee_query_string(ddict)
        fields = (536870929, 536870917, 536870930)
        try:
            self.logger.debug("getting list entry with fields ...") if self.logger else ""
            (entries, num) = ars.GetListEntryWithFields(schema,query,fields,None)
            self.logger.debug("got %s of entries"%(str(num))) if self.logger else ""
        except Exception,e:
            self._db_logoff(ars)
            self.logger.error(e) if self.logger else ""
            time.sleep(5)
            (entries, num) = ars.GetListEntryWithFields(schema, query, fields, None)
        self._db_logoff(ars)
        return (entries, num)
