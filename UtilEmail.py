# HIT @ EMC Corporation
# UtilEmail.py
# Purpose: Provides functions to send email
# Author: Youye Sun
# Version: 1.0 03/12/2015
import win32com.client
from win32com.client import *

class EmailHelper:
    def __init__(self, log=None):
        self.logger = log

    def send_email(self,to,subj=None,body=None,ifHtmlNody=False,embed_images=False,additional_body=None,cc=None,bcc=None,att=None):
        """
        Sends Email
        :param to: recipients of the email
        :param subj: subject of the email
        :param body: body of the email
        :param ifHtmlNody: if the body is presented as html
        :param embed_images: list of images to be embedded
        :param additional_body: additional body of the email
        :param cc: carbon copy of the email
        :param att: attachment of the email
        :return:
        """
        o = win32com.client.gencache.EnsureDispatch("Outlook.Application")
        mapi = o.GetNamespace('MAPI')
        mapi.Logon('Outlook')  # MAPI profile name
        newMail = o.CreateItem(0)
        if subj is not None:
            newMail.Subject = subj
        if(ifHtmlNody):
            newMail.HTMLBody='<a name="top"></a>'
            if body is not None:
                newMail.HTMLBody +=body
            if embed_images is not None:
                for i in range(0,len(embed_images)):
                    attachment = newMail.Attachments.Add(embed_images[i],\
                                                         win32com.client.constants.olEmbeddeditem,\
                                                         0,'image-'+str(i))
                    imageCid ='image-'+str(i)+'@youyesun'
                    attachment.PropertyAccessor.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x3712001E",\
                                                            imageCid)
                    newMail.HTMLBody +='<p><img src="cid:{0}"></p>'.format(imageCid)

            if additional_body is not None:
                print additional_body
                newMail.HTMLBody +=additional_body

            newMail.HTMLBody +='<p><a href="#top">Back To Top</a></p>'
        else:
            if body is not None:
                newMail.Body = body
        newMail.To = to
        if cc is not None:
            newMail.CC=cc
        if bcc is not None:
            newMail.BCC=bcc
        if att is not None:
            for a in att:
                newMail.Attachments.Add(a)
        newMail.Send()