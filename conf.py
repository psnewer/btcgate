# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import json
import gate_api
import sympy
from scipy.optimize import fsolve
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
	    sender = '969941416@qq.com'  # 发件人邮箱账号
	    receive = ['969941416@qq.com']  # 收件人邮箱账号
	    passwd = 'vrjcijjtujcrbfff'
	    mailserver = 'smtp.qq.com'
	    port = '465'
	    sub = 'Gateio Surveil'

	    try:
		msg = MIMEMultipart('related')
		msg['From'] = formataddr(["sender", sender])  # 发件人邮箱昵称、发件人邮箱账号
		msg['To'] = formataddr(["receiver", receive])  # 收件人邮箱昵称、收件人邮箱账号
		msg['Subject'] = sub
		body = """
		<b>This is HJGT statement items:</b>
		<div>{e_html}</div>
		""".format(e_html = e_html)
	        text = MIMEText(body, 'html', 'utf-8')
		msg.attach(text)
		smtpobj=smtplib.SMTP_SSL(mailserver,465) #本地如果有本地服务器，则用localhost ,默认端口２５,腾讯的（端口465或587）
		smtpobj.set_debuglevel(1)
		smtpobj.login(sender,passwd)#登陆QQ邮箱服务器
		smtpobj.sendmail(sender, receive, msg.as_string())  # 发件人邮箱账号、收件人邮箱账号、发送邮件
		smtpobj.quit()
		print('send mail success')
	    except Exception as e:
	        print(e)
		

def send_weixin(msg):
    global N_message
    if N_message < 500:
	N_message = N_message + 1
	requests.get("https://sc.ftqq.com/SCU60300T026729377fffbccacceb5c62ab430d7f5d78a7743d03a.send?text={}&desp={}".format('告警', str(N_message)+' '+str(msg)))
	time.sleep(3)

def regression_1(Pf,Pb,Sf,Sb,P,T_tr,T_rt):
    def func(x):
        return (T_tr-T_rt*(P-(P*x+Pf*Sf)/(x+Sf))/(P-Pb))**0.5 - (Sf+x)/Sb
#    x = symbols('x')
#    P_t = (Pf*Sf + P*x)/(x+Sf)
#    a = float(P - Pb)
#    b = float(P - Pf)
#    s = solve(a*(x**3) - a*T_tr*Sb*Sb*x + b*Sb*Sb*Sf)
    s = fsolve(func,1.0)
    print (s)
    res = 0
    for _s in s:
        if _s > 0 and _s + Sf <= Sb:
            res = _s
            break
    return res

def regression_2(Pf,Pb,Sf,Sb,P,T_tr,T_rt):
    def func(x):
        return (T_tr-T_rt*(P-Pf)/(P-(Pb*Sb+P*x)/(x+Sb)))**0.5 - Sf/(Sb+x)
#    x = symbols('x')
#    P_t = (Pb*Sb + P*x)/(x+Sb)
#    a = float(P - Pb)
#    b = float(P - Pf)
#    s = solve(b*(x**3) - a*T_tr*Sb*(x**2) + a*Sb*Sf*Sf)
    s = fsolve(func,1.0)
    print (s)
    res = 0
    for _s in s:
        if _s > 0 and _s + Sb >= Sf:
            res = _s
            break
    return res 

forward_configuration = gate_api.Forward_Configuration()
backward_configuration = gate_api.Backward_Configuration()
forward_api_instance = gate_api.FuturesApi(gate_api.ApiClient(forward_configuration))
backward_api_instance = gate_api.FuturesApi(gate_api.ApiClient(backward_configuration))

