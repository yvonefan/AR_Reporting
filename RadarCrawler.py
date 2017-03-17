import urllib2, base64
from ntlm import HTTPNtlmAuthHandler
from bs4 import BeautifulSoup
from UtilLogging import *

ARGS = ['eWFvbTE=', 'QEVtYzIwMTdA']

class AR:
    def __init__(self, issue_id, ac_date, ac, ac_method, status, status_details, priority, type, major_area, product_area,
                 asgn_to, asgn_to_sr_mgr, rpt_by, rpt_by_sr_mgr):
        self.issue_id = issue_id
        self.ac_date = ac_date
        self.ac = ac
        self.ac_method = ac_method
        self.status = status
        self.status_details = status_details
        self.priority = priority
        self.type = type
        self.major_area = major_area
        self.product_area = product_area
        self.asgn_to = asgn_to
        self.asgn_to_sr_mgr = asgn_to_sr_mgr
        self.rpt_by = rpt_by
        self.rpt_by_sr_mgr = rpt_by_sr_mgr
        self.ca = ""

    def to_string(self):
        return "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (self.issue_id, self.ac_date, self.ac,
                                                                 self.ac_method, self.status, self.status_details,
                                                                 self.priority, self.type, self.major_area,
                                                                 self.product_area, self.asgn_to, self.asgn_to_sr_mgr,
                                                                 self.rpt_by, self.rpt_by_sr_mgr, self.ca)

    def to_list(self):
        res = list([self.issue_id, self.ac_date, self.ac, self.ac_method, self.status, self.status_details,
                    self.priority, self.type, self.major_area, self.product_area, self.asgn_to, self.asgn_to_sr_mgr,
                    self.rpt_by, self.rpt_by_sr_mgr, self.ca])
        return res


class RadarCrawler:
    def __init__(self):
        pass

    def get_url_response(self, url):
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, base64.b64decode(ARGS[0]), base64.b64decode(ARGS[1]))
        auth_NTLM = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(passman)
        opener = urllib2.build_opener(auth_NTLM)
        urllib2.install_opener(opener)
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        header = {'Connection':'Keep-alive', 'User-Agent':user_agent}
        return urllib2.urlopen(urllib2.Request(url, None, header))
    
    def count_tbv(self, response):
        data = response.read()
        soup = BeautifulSoup(data)
        tbv = 0
        rows = soup.find_all("tr")
        for row in rows:
            row =str(row)
            if "<td>Test-ready</td>" in row:     
                tbv += 1
        return tbv
    
    def count_arrivals(self, response):
        data = response.read()
        print data
        soup = BeautifulSoup(data)
        arrival_new = 0
        arrival_other = 0
        arrival_reopen = 0
        arrival_movein = 0
        text = list()
        rows = soup.find_all("tr")
        for row in rows:
            tmp = list()
            if rows.index(row) == 0:
                for th in row.find_all('th'):
                    tmp.append(th.contents[0])
            else:
                for td in row.find_all('td'):
                    if len(td.find_all('a')) == 0:
                        tmp.append(td.contents[0])
                    else:
                        tmp.append(td.find_all('a')[0].contents[0])
            text.append(tmp)
            row =str(row)
            if "<td>Arrival</td><td>Move in</td>" in row:
                arrival_movein += 1
            elif "<td>Arrival</td><td>New</td>" in row:
                arrival_new += 1
            elif "<td>Arrival</td><td>Other</td>" in row:
                arrival_other += 1
            elif "<td>Arrival</td><td>Reopen</td>" in row:
                arrival_reopen += 1
        total = arrival_new + arrival_other + arrival_reopen + arrival_movein
        return arrival_movein, arrival_new, arrival_other, arrival_reopen, total, text

    def count_closures(self, response):
        data = response.read()
        print data
        soup = BeautifulSoup(data)
        closure_dup = 0
        closure_fix = 0
        closure_deferdis = 0
        closure_prog = 0
        closure_nodeferdis = 0
        closure_other = 0
        text = list()
        rows = soup.find_all("tr")
        for row in rows:
            tmp = list()
            if rows.index(row) == 0:
                for th in row.find_all('th'):
                    tmp.append(th.contents[0])
            else:
                for td in row.find_all('td'):
                    if len(td.find_all('a')) == 0:
                        tmp.append(td.contents[0])
                    else:
                        tmp.append(td.find_all('a')[0].contents[0])
            text.append(tmp)
            row = str(row)
            if "<td>Closure</td><td>Duplicate</td>" in row:
                closure_dup += 1
            elif "<td>Closure</td><td>Fixed</td>" in row:
                closure_fix += 1
            elif "<td>Closure</td><td>Defer Dismissal</td>" in row:
                closure_deferdis += 1
            elif "<td>Closure</td><td>Program Change Deferral</td>" in row:
                closure_prog += 1
            elif "<td>Closure</td><td>Non-defer Dismissal</td>" in row:
                closure_nodeferdis += 1
            elif "<td>Closure</td><td>Other</td>" in row:
                closure_other += 1
        total = closure_dup + closure_fix + closure_deferdis + closure_prog + closure_nodeferdis + closure_other
        return closure_dup, closure_fix, closure_deferdis, closure_prog, closure_nodeferdis, closure_other, total, text

    def parse_ar_html_table(self, response):
        data = response.read()
        soup = BeautifulSoup(data)
        ars = list()
        rows = soup.find_all("tr")
        for row in rows:
            tmp = list()
            if rows.index(row) == 0:
                pass
            else:
                for td in row.find_all('td'):
                    if len(td.find_all('a')) == 0:
                        tmp.append(td.contents[0])
                    else:
                        tmp.append(td.find_all('a')[0].contents[0])
                ar=AR(*tmp[1:])
                ars.append(ar)
        return ars

if __name__ == '__main__':
    crawer = RadarCrawler()
    url = 'http://usd-qmr-dev//dashboard#defects?p=Thunderbird&tab=OBLT&p1=P00|P01|P02|&p2=Bug|'
    print crawer.get_url_response(url).read()