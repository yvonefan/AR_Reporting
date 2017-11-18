import os
from UtilEmail import *
from UtilLogging import *


__filename__ = os.path.basename(__file__)
fpath = os.path.dirname(os.path.realpath(__file__))

Python = 'C:\Python27\python.exe'
JsonFile = 'platform_config.json'
cmd_log = fpath + '\\log\\' + 'cmd.log'

#cmd = Python + ' ' + "ar_report_daily.py" + ' ' + '-config' + ' ' + JsonFile + ' ' + '-t' + ' 2>' + cmd_log
cmd = Python + ' ' + "ar_report_daily.py" + ' -u fanw4 -p ImiSDo08189' + ' -config' + ' ' + JsonFile + ' 2>' + cmd_log
os.chdir(fpath)

num = 0
while num < 5:
    flag = os.system(cmd)
    if flag == 0:
        print "Run daily report succeed\n"
        break
    else:
        num += 1
        continue
else:
    mailer = EmailHelper()
    logger = LogHelper()
    subject = "Errors occurred with daily AR report."
    body = ""
    error_to = 'Winnie.Fan@emc.com'
    error_cc = 'Winnie.Fan@emc.com'
    attachement = [cmd_log,]
    mailer.send_email(error_to, subj=subject, body=body, att=attachement)