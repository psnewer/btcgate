# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import json
import gate_api
from gate_api.rest import ApiException

# smtplib模块负责连接服务器和发送邮件
# MIMEText：定义邮件的文字数据
# MIMEImage：定义邮件的图片数据
# MIMEMultipart：负责将文字图片音频组装在一起添加附件
import smtplib  # 加载smtplib模块
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

N_message = 100

def send_email(e_html):
    global N_message
    if N_message < 500:
        N_message = N_message + 1
        time.sleep(3)
        sender = '969941416@qq.com'
        receive = '969941416@qq.com'
        passwd = 'vrjcijjtujcrbfff'
        mailserver = 'smtp.qq.com'
        port = '465'
        sub = 'Gateio Surveil'

        try:
            msg = MIMEMultipart('related')
            msg['From'] = formataddr(["sender", sender])  # �����������ǳơ������������˺�
            msg['To'] = formataddr(["receiver", receive])  # �ռ��������ǳơ��ռ��������˺�
            msg['Subject'] = sub
            body = """
            <b>This is GateIO items:</b>
            <div>{e_html}</div>
            """.format(e_html = e_html)
            text = MIMEText(body, 'html', 'utf-8')
            msg.attach(text)
            smtpobj=smtplib.SMTP_SSL(mailserver,465) #��������б��ط�����������localhost ,Ĭ�϶˿ڣ���,��Ѷ�ģ��˿�465��587��
            smtpobj.set_debuglevel(1)
            smtpobj.login(sender,passwd)#��½QQ���������
            smtpobj.sendmail(sender, receive, msg.as_string())  # �����������˺š��ռ��������˺š������ʼ�
            smtpobj.quit()
            print('send mail success')
        except Exception as e:
            print(e)
		

forward_configuration = gate_api.Forward_Configuration()
backward_configuration = gate_api.Backward_Configuration()
forward_api_instance = gate_api.FuturesApi(gate_api.ApiClient(forward_configuration))
backward_api_instance = gate_api.FuturesApi(gate_api.ApiClient(backward_configuration))

