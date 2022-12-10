from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage,flex_message, TextSendMessage,QuickReply,TemplateSendMessage,FlexSendMessage,PostbackAction,QuickReplyButton,MessageAction,LocationMessage,LocationAction,ConfirmTemplate)
import pymongo
import uuid
import random
import datetime
now = datetime.datetime.now()
current_time = now.strftime("%Y-%m-%d %H:%M:%S")
#Line
line_bot_api = LineBotApi('n6IFRxEkUC+Wy2rprCo+MXEOlipi8JPHrvcm7sdHjtYjIOs7a0nAG1s5LDpoh8pbhT1qVzVUD9nsc2J7fihZJuzL6PLcL/bnDjzhgDlmxgU5BNa1TFl+R/ZKFs26zfVzA67jirOtaMuZrZwziKo/SQdB04t89/1O/w1cDnyilFU=') #chnnel access token
handler = WebhookHandler('f48e5452ada9f30180000e6cf4a6ce42') #channel secret
#MongoDB
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["Chatbot"]
mycol = mydb["Repair_List"]


app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World!'

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'Connection'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global repiar_type,repiar,detail,address,phonenumber
    repair_list = ['น้ำประปาไม่ไหล','มีกลิ่น,ขุ่น,มิเตอร์','ระบบไฟฟ้า','ระบบปรับอากาศ','โยธาสถาปัตย์','ประปาและสุขาภิบาล','ตัดหญ้า','ตัดแต่งกิ่ง','กำจัดแมลง']
    fallback = ['ขออภัยค่ะ ฉันไม่เข้าใจ','ขอโทษค่ะ ฉันไม่เข้าใจ','กรุณาตรวจสอบข้อความก่อนส่งค่ะ','คุณต้องการใช้บริการอะไรคะ','หากต้องการใช้บริการกรุณากดเมนูดูได้เลยค่ะ']
    if  'สวัสดี' in event.message.text : 
        line_bot_api.reply_message(event,"สวัสดีค่ะ เราคือแชทบอทแจ้งซ่อม หากต้องการใช้บริการสามารถกดที่ปุ่มเมนูเพื่อเลือกบริการที่ต้องการค่ะ")
    #แจ้งซ่อม
    elif event.message.text == 'แจ้งซ่อม' : 
        quickreply_repairtype(event,"เลือกประเภทงานบริการ")
    elif event.message.text == 'แจ้งซ่อมระบบประปา' :
        repiar_type = 'แจ้งซ่อมระบบประปา'
        plumbing_system(event,"รายละเอียดแจ้งซ่อม")
    elif event.message.text == 'แจ้งซ่อมไฟฟ้า' :
        repiar_type = 'แจ้งซ่อมไฟฟ้า' 
        electrical_system(event,"รายละเอียดแจ้งซ่อม")
    elif event.message.text == 'งานซ่อมบำรุงรักษา' : 
        repiar_type = 'งานซ่อมบำรุงรักษา'
        maintenance(event,"รายละเอียดแจ้งซ่อม")
    elif event.message.text == 'แจ้งงานภูมิทัศน์' : 
        repiar_type = 'แจ้งงานภูมิทัศน์'
        landscape(event,"รายละเอียดแจ้งซ่อม")
    #เช็ครายละเอียดเพิ่มเติม
    elif (event.message.text[0] == '-' and event.message.text[1] == 'd') or (event.message.text[0] == '-' and event.message.text[1] == '*') :
        if event.message.text[1] == '*':
            detail='-'
        else:detail = event.message.text[3:]
        confirmdata(event,"หากตรวจสอบข้อมูลเรียบร้อยแล้ว\nกรุณากดยืนยันค่ะ")
    #ช่องทางการติดต่อ
    elif event.message.text == 'ช่องทางการติดต่อ' : 
        line_bot_api.reply_message(event,"สามารถติดต่อได้ตามช่องทางด้านล่างเลยค่ะ")
    #ปัญหาที่จะแจ้งซ่อม
    elif event.message.text in repair_list:
        repiar=event.message.text
        address=quickreply_asklocation(event,"ขอทราบที่อยู่ค่ะ")
    #เช็คเบอร์โทรศัพท์
    elif event.message.text[0] == '-' and event.message.text[1] == 'p':
        if event.message.text[3:].isdigit() and len(event.message.text[3:])==10:
            phonenumber = event.message.text[3:]
            if phonenumber[0] == "0" and (phonenumber[1]=="6" or phonenumber[1]=="9" or phonenumber[1]=="8"):
                phonenumber = event.message.text[3:]
                sendMessage(event,"หากต้องการแจ้งหมายเหตุ\nพิมพ์-d(เว้นวรรค)ตามด้วยข้อความ\nหากไม่มีให้พิมพ์ \"-*\")")
            else: sendMessage(event,"ตรวจวสอบเบอร์โทรศัพท์อีกครั้งค่ะ")
        else: sendMessage(event,"กรุณาแจ้งเบอร์โทรศัพท์ที่ถูกต้องค่ะ")
    elif event.message.text == 'ตรวจสอบสถานะ':
        checkstatus(event,"ต้องการตรวจสอบแบบไหนดีคะ")
    elif event.message.text == 'ใส่ไอดีแจ้งซ่อม':
        sendMessage(event,"กรุณาใส่ไอดีแจ้งซ่อมค่ะ")
    elif event.message.text[0] == 'S' and  event.message.text[1] == 'U' and  event.message.text[2] == 'T':
        yourid=event.message.text
        if mycol.count_documents({"repair_id": yourid}) > 0:
            for i in mycol.find({"repair_id": yourid}):
                print(i)
                yourstatus=i['status']
                if yourstatus == 'เสร็จสิ้น':
                    StatusSuccess(event,"สถานะการแจ้งซ่อม",yourid)
                elif yourstatus == 'กำลังดำเนินการ':
                    StatusInProgress(event,"สถานะการแจ้งซ่อม",yourid)
                elif yourstatus == 'รอดำเนินการ':
                    StatusPending(event,"สถานะการแจ้งซ่อม",yourid)
                else: sendMessage(event,"ไอดีแจ้งซ่อมไม่ถูกต้องค่ะ")
        else: sendMessage(event,"กรุณาตรวจสอบไอดีแจ้งซ่อมค่ะ")
    elif event.message.text == '.ยืนยัน':  
        detail_data(event,"ข้อมูลแจ้งซ่อม",repair_id,repiar_type,repiar,location,phonenumber,status,detail)
        yes()
        insertdb()
    elif event.message.text == 'สถิติการแจ้งซ่อม':
        pending = mycol.count_documents({"status": "รอดำเนินการ"})
        in_progress = mycol.count_documents({"status": "กำลังดำเนินการ"})
        success = mycol.count_documents({"status": "เสร็จสิ้น"})
        Showstatus(event,"สถิติการแจ้งซ่อม",pending,in_progress,success)
    else: sendMessage(event,random.choice(fallback))    
            
@handler.add(MessageEvent, message=LocationMessage)
def location_message(event):
    global location
    address=event.message.address #ที่อยู่ที่userแชร์มา
    lst_location = ['Suranaree','Suranari','SUT']
    for i in lst_location:
        if i in address:
            location = address
            sendMessage(event,"รบกวนแจ้งเบอร์โทรศัพท์ค่ะ\nพิมพ์ -p(เว้นวรรค)ตามด้วยเบอร์\n(เช่น -p 0999999999)")
        else: quickreply_asklocation(event,"กรุณากรอกที่อยู่ภายในมหาวิทยาลัยค่ะ")

def sendMessage(event,message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message),
        print(message))
    
def quickreply_repairtype(event,message):
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="แจ้งซ่อมไฟฟ้า", text="แจ้งซ่อมไฟฟ้า")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="แจ้งซ่อมระบบประปา", text="แจ้งซ่อมระบบประปา")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="งานซ่อมบำรุงรักษา", text="งานซ่อมบำรุงรักษา")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="แจ้งงานภูมิทัศน์", text="แจ้งงานภูมิทัศน์")
                        ),
                    ])))
    
def quickreply_asklocation(event,message):
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=LocationAction(label="แชร์ที่อยู่")
                        )
                    ])))

def plumbing_system(event,message):
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="น้ำประปาไม่ไหล", text="น้ำประปาไม่ไหล")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="มีกลิ่น,ขุ่น,มิเตอร์", text="มีกลิ่น,ขุ่น,มิเตอร์")
                        )
                    ])))

def electrical_system(event,message):
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="ระบบปรับอากาศ", text="ระบบปรับอากาศ")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="ระบบไฟฟ้า", text="ระบบไฟฟ้า")
                        )
                    ])))
    
def maintenance(event,message):
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="โยธาสถาปัตย์", text="โยธาสถาปัตย์")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="ประปาและสุขาภิบาล", text="ประปาและสุขาภิบาล")
                        )
                    ])))
    
def landscape(event,message):
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="ตัดหญ้า", text="ตัดหญ้า")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="ตัดแต่งกิ่ง", text="ตัดแต่งกิ่ง")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="กำจัดแมลง", text="กำจัดแมลง")
                        )
                    ])))


status = 'รอดำเนินการ'
def confirmdata(event,message):
    line_bot_api.reply_message(
        event.reply_token,
        TemplateSendMessage(
        alt_text='Confirm template',
        template=ConfirmTemplate(
            text=message,
            actions=[
                {
                    "type": "message",
                    "label": "ยืนยัน",
                    "text": ".ยืนยัน"
                },
                {
                    "type": "message",
                    "label": "ยกเลิก",
                    "text": "ยกเลิก"
                }
            ]
        ))
) 
    
def checkstatus(event,message):
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="ใส่ไอดีแจ้งซ่อม", text="ใส่ไอดีแจ้งซ่อม")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="สถิติการแจ้งซ่อม", text="สถิติการแจ้งซ่อม")
                        )
                    ])))
    
def generate_id():
    id = uuid.uuid1().hex
    id = str(id[:5])
    id = "SUT"+id
    return id
repair_id = generate_id()

def detail_data(event,message,repair_id,repiar_type,repiar,location,phonenumber,status,detail):
        flex_message = FlexSendMessage(
            alt_text= message,
            contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {
                "type": "uri",
                "uri": "http://linecorp.com/"
                }
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": "แจ้งซ่อม",
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "spacing": "sm",
                        "contents": [
                        {
                            "type": "text",
                            "text": "ไอดีแจ้งซ่อม",
                            "color": "#666666",
                            "size": "sm",
                            "margin": "none",
                            "flex": 5
                        },
                        {
                            "type": "text",
                            "text": repair_id,
                            "color": "#666666",
                            "size": "sm",
                            "flex": 8
                        },
                        {
                            "type": "text",
                            "text": "hello, world"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "spacing": "sm",
                        "contents": [
                        {
                            "type": "text",
                            "text": "ประเภทบริการ",
                            "color": "#666666",
                            "size": "sm",
                            "flex": 5
                        },
                        {
                            "type": "text",
                            "text": repiar_type,
                            "size": "sm",
                            "flex": 8,
                            "color": "#666666"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                        {
                            "type": "text",
                            "text": "รายละเอียด",
                            "flex": 5,
                            "size": "sm",
                            "color": "#666666"
                        },
                        {
                            "type": "text",
                            "text": repiar,
                            "flex": 8,
                            "size": "sm",
                            "color": "#666666"
                        }
                        ],
                        "spacing": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                        {
                            "type": "text",
                            "text": "ที่อยู่",
                            "color": "#666666",
                            "flex": 5,
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": location,
                            "size": "sm",
                            "color": "#666666",
                            "flex": 8
                        }
                        ],
                        "spacing": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                        {
                            "type": "text",
                            "text": "เบอร์",
                            "flex": 5,
                            "size": "sm",
                            "color": "#666666"
                        },
                        {
                            "type": "text",
                            "text": phonenumber,
                            "flex": 8,
                            "size": "sm",
                            "color": "#666666"
                        }
                        ],
                        "spacing": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                        {
                            "type": "text",
                            "text": "สถานะ",
                            "size": "sm",
                            "color": "#666666",
                            "flex": 5
                        },
                        {
                            "type": "text",
                            "text": status,
                            "flex": 8,
                            "size": "sm",
                            "color": "#666666"
                        }
                        ],
                        "spacing": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                        {
                            "type": "text",
                            "text": "หมายเหตุ",
                            "flex": 5,
                            "size": "sm",
                            "color": "#666666"
                        },
                        {
                            "type": "text",
                            "text": detail,
                            "flex": 8,
                            "size": "sm"
                        }
                        ],
                        "spacing": "sm"
                    }
                    ]
                }
                ]
            },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "แจ้งซ่อมเสร็จสิ้น ขอบคุณที่ใช้บริการค่ะ",
                        "margin": "none",
                        "align": "center"
                    }
                    ]
                }
            }
        )
        line_bot_api.reply_message(event.reply_token, flex_message)
  
def Showstatus(event,message,pending,in_progress,success):
    flex_message = FlexSendMessage(
            alt_text= message,
            contents={
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "สถิติการแจ้งซ่อม",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": "SUT ChatBot",
                        "weight": "bold",
                        "size": "xxl",
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xxl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "รอดำเนินการ",
                                "size": "sm",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": "{}".format(pending),
                                "size": "sm",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "กำลังดำเนินการ",
                                "size": "sm",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": "{}".format(in_progress),
                                "size": "sm",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "เสร็จสิ้น",
                                "size": "sm",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": "{}".format(success),
                                "size": "sm",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "xxl"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "md",
                        "contents": [
                        {
                            "type": "text",
                            "text": "Update",
                            "size": "xs",
                            "color": "#aaaaaa",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "{}".format(current_time),
                            "color": "#aaaaaa",
                            "size": "xs",
                            "align": "end"
                        }
                        ]
                    }
                    ]
                },
                "styles": {
                    "footer": {
                    "separator": True
                    }
                }
                }
        )
    line_bot_api.reply_message(event.reply_token, flex_message)
    
def StatusPending(event,message,yourid):
    flex_message = FlexSendMessage(
        alt_text= message,
            contents={
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "ID",
                        "color": "#ffffff66",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": "{}".format(yourid),
                        "color": "#ffffff",
                        "size": "xl",
                        "flex": 4,
                        "weight": "bold"
                    }
                    ]
                }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#0367D3",
                "spacing": "md",
                "height": "90px",
                "paddingTop": "22px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": "Updtae: {}".format(current_time),
                    "color": "#b7b7b7",
                    "size": "xs"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "filler"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [],
                            "cornerRadius": "30px",
                            "height": "12px",
                            "width": "12px",
                            "borderColor": "#EF454D",
                            "borderWidth": "2px"
                        },
                        {
                            "type": "filler"
                        }
                        ],
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "รอดำเนินการ",
                        "gravity": "center",
                        "flex": 4,
                        "size": "sm"
                    }
                    ],
                    "spacing": "lg",
                    "cornerRadius": "30px",
                    "margin": "xl"
                }
                ]
            }
            }
        )
    line_bot_api.reply_message(event.reply_token, flex_message)

def StatusInProgress(event,message,yourid):
    flex_message = FlexSendMessage(
        alt_text= message,
            contents={
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "ID",
                        "color": "#ffffff66",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": "{}".format(yourid),
                        "color": "#ffffff",
                        "size": "xl",
                        "flex": 4,
                        "weight": "bold"
                    }
                    ]
                }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#0367D3",
                "spacing": "md",
                "height": "90px",
                "paddingTop": "22px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": "Updtae: {}".format(current_time),
                    "color": "#b7b7b7",
                    "size": "xs"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "filler"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [],
                            "cornerRadius": "30px",
                            "height": "12px",
                            "width": "12px",
                            "borderColor": "#EF454D",
                            "borderWidth": "2px"
                        },
                        {
                            "type": "filler"
                        }
                        ],
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "รอดำเนินการ",
                        "gravity": "center",
                        "flex": 4,
                        "size": "sm"
                    }
                    ],
                    "spacing": "lg",
                    "cornerRadius": "30px",
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "filler"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "width": "2px",
                                "backgroundColor": "#6486E3"
                            },
                            {
                                "type": "filler"
                            }
                            ],
                            "flex": 1
                        }
                        ],
                        "width": "12px"
                    }
                    ],
                    "spacing": "lg",
                    "height": "64px"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "filler"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [],
                            "cornerRadius": "30px",
                            "width": "12px",
                            "height": "12px",
                            "borderWidth": "2px",
                            "borderColor": "#FFD700"
                        },
                        {
                            "type": "filler"
                        }
                        ],
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "กำลังดำเนินการ",
                        "gravity": "center",
                        "flex": 4,
                        "size": "sm"
                    }
                    ],
                    "spacing": "lg",
                    "cornerRadius": "30px"
                }
                ]
            }
            }
        )
    line_bot_api.reply_message(event.reply_token, flex_message)
    
def StatusSuccess(event,message,yourid):
    flex_message = FlexSendMessage(
        alt_text= message,
            contents={
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "ID",
                            "color": "#ffffff66",
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": "{}".format(yourid),
                            "color": "#ffffff",
                            "size": "xl",
                            "flex": 4,
                            "weight": "bold"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "20px",
                    "backgroundColor": "#0367D3",
                    "spacing": "md",
                    "height": "90px",
                    "paddingTop": "22px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "Updtae:{}".format(current_time),
                        "color": "#b7b7b7",
                        "size": "xs"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "filler"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "cornerRadius": "30px",
                                "height": "12px",
                                "width": "12px",
                                "borderColor": "#EF454D",
                                "borderWidth": "2px"
                            },
                            {
                                "type": "filler"
                            }
                            ],
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "รอดำเนินการ",
                            "gravity": "center",
                            "flex": 4,
                            "size": "sm"
                        }
                        ],
                        "spacing": "lg",
                        "cornerRadius": "30px",
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "filler"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [],
                                    "width": "2px",
                                    "backgroundColor": "#B7B7B7"
                                },
                                {
                                    "type": "filler"
                                }
                                ],
                                "flex": 1
                            }
                            ],
                            "width": "12px"
                        }
                        ],
                        "spacing": "lg",
                        "height": "64px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "filler"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "cornerRadius": "30px",
                                "width": "12px",
                                "height": "12px",
                                "borderWidth": "2px",
                                "borderColor": "#FFD700"
                            },
                            {
                                "type": "filler"
                            }
                            ],
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "กำลังดำเนินการ",
                            "gravity": "center",
                            "flex": 4,
                            "size": "sm"
                        }
                        ],
                        "spacing": "lg",
                        "cornerRadius": "30px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "filler"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [],
                                    "width": "2px",
                                    "backgroundColor": "#6486E3"
                                },
                                {
                                    "type": "filler"
                                }
                                ],
                                "flex": 1
                            }
                            ],
                            "width": "12px"
                        }
                        ],
                        "spacing": "lg",
                        "height": "64px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "filler"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "cornerRadius": "30px",
                                "width": "12px",
                                "height": "12px",
                                "borderColor": "#008000",
                                "borderWidth": "2px"
                            },
                            {
                                "type": "filler"
                            }
                            ],
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "เสร็จสิ้น",
                            "gravity": "center",
                            "flex": 4,
                            "size": "sm"
                        }
                        ],
                        "spacing": "lg",
                        "cornerRadius": "30px"
                    }
                    ]
                }
                }
        )
    line_bot_api.reply_message(event.reply_token, flex_message)
       
def yes():
    print("ประเภทงานบริการ: {}\n แจ้งซ่อม: {}\n สถานที่: {}\n หมายเลขโทรศัพท์: {}\n สถานะ: {}\n รายละเอียดเพิ่มเติม: {}".format(repiar_type,repiar,location,phonenumber,status,detail))

def insertdb():
    global repair_id
    mydict = { "repair_id": repair_id,"repair_type": repiar_type,"repiar": repiar , "address": location, "tel": phonenumber,"status": status, "note": detail}
    x = mycol.insert_one(mydict)
    print(x)

if __name__ == '__main__':
    app.run(debug=True)