# HIT @ EMC Corporation
# UtilString.py
# Purpose: Provides database access functions
# Author: Youye Sun
# Version: 1.0 04/17/2015

class StringHelper:
    def __init__(self,log=None):
        self.logger = log

    def list_to_xsv_str(self,llist, tag, tag_value_combine_mark, value_pair_combine_mark):
        #print tag, tag_value_combine_mark, llist
        """
        Converts the values in the list to string containing the tag value pairs
        :param llist: list containing the values
        :param tag: name of the tag
        :param tag_value_combine_mark: mark combining the tag and the value
        :param value_pair_combine_mark: mark combining the value pairs
        :return: sting containing the value pairs
        """
        s = ""
        try:
            for value in llist:
                s += tag + tag_value_combine_mark + value
                if llist.index(value) != len(llist)-1:
                    s += value_pair_combine_mark
                print s
            return s
        except Exception, e:
            self.logger.error(e) if self.logger else ""
            raise

    def str_exclude_pre_zero(self,sstr):
        """
        Excludes prefix zeros ahead of string
        :param sstr: string to remove zeros from
        :return: string being removed prefix zeros
        """
        i = 0
        try:
            while sstr[i] == '0':
                i += 1
            return sstr[i:]
        except Exception, e:
            self.logger.error(e) if self.logger else ""
            raise

    def get_rate_string(self,num,total_num):
        """
        Calculates the rate then returns it as string
        :param num: numerator
        :param total_num: denominator
        :return: percentage
        """
        try:
            if total_num == 0:
                return str(0) + '%'
            r = round(100*num/float(total_num),1)
            return str(r) + '%'
        except Exception, e:
            self.logger.error(e)
            raise

    def split_str_by_length(self,sstr,length,max_length=None):
        """
        Split string into lines with specified length. Truncates if the result exceed the maximum length
        :param sstr: string to be handled
        :param length: length of each line
        :param max_length: maximum length of the result string
        :return: string with each line having specified length and total length smaller than maximum length
        example:
            sstr = '[MRQE/SYS][Vitality][Baseline][OB-D1142] VNX_VNXe_CIFS_STRESS failed with syswrite failed for writing file'
            res = '[MRQE/SYS][Vita-
            lity][Baseline]-
            [OB-D11...'
        """
        l = len(sstr)
        if l <= length:
            return sstr
        start = 0
        res=''
        offset =0
        while((start+1)*(length)+offset< l):
            if (start+1)*(length)+offset == l-1:
                res+=sstr[start*(length)+offset:l]
                start +=1
            elif sstr[(start+1)*(length)+offset -1] ==' ':
                res +=sstr[start*(length)+offset:(start+1)*(length)+offset-1] +'\n'
            elif sstr[(start+1)*(length)+offset] ==' ':
                res +=sstr[start*(length)+offset:(start+1)*(length)+offset] +'\n'
                offset+=1
            elif sstr[(start+1)*(length)] ==',':
                res +=sstr[start*(length)+offset:(start+1)*(length)+1+offset] +'\n'
                offset+=1
            else:
                res+=sstr[start*(length)+offset:(start+1)*(length)+offset] + '-\n'
            start +=1
        if start*(length) +offset <l:
            res+=sstr[start*(length)+offset:l]
        if max_length is not None:
            if len(res) > max_length:
                res =res[:max_length-4] + '...'
        return res

    def split_string_by_first_comma(slef,sstr):
        """
        Splits the string into two lines by the first comma
        :param fullname:
        :return:
        """
        res = sstr
        for i in range(len(sstr)):
            if sstr[i] == ',':
                res = sstr[:i+1]
                res +='\n'+sstr[i+2:]
                break
        return res




if __name__ == '__main__':
    stringer = StringHelper()
    print "convert_list_to_tag_value_pair_string: " + stringer.list_to_xsv_str(["1","2","3"],'tag','=','or')

