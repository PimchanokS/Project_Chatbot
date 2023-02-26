from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, StickerMessage,ImageSendMessage, CameraAction,VideoMessage, CameraRollAction, TextMessage, ImageMessage, TextSendMessage, QuickReply, TemplateSendMessage, FlexSendMessage, PostbackAction, QuickReplyButton, MessageAction, LocationMessage, LocationAction, ConfirmTemplate)
import pymongo
import uuid
import random
import tempfile
import os
import imgbbpy
import datetime
now = datetime.datetime.now()
current_time = now.strftime("%Y-%m-%d %H:%M:%S")
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Line
line_bot_api = LineBotApi('n6IFRxEkUC+Wy2rprCo+MXEOlipi8JPHrvcm7sdHjtYjIOs7a0nAG1s5LDpoh8pbhT1qVzVUD9nsc2J7fihZJuzL6PLcL/bnDjzhgDlmxgU5BNa1TFl+R/ZKFs26zfVzA67jirOtaMuZrZwziKo/SQdB04t89/1O/w1cDnyilFU=')  # chnnel access token
handler = WebhookHandler('f48e5452ada9f30180000e6cf4a6ce42')  # channel secret
# MongoDB
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["Chatbot"]
mycol = mydb["Repair_List"]

app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello World!'


@app.route('/webhook', methods=['GET', 'POST'])
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


@handler.add(MessageEvent, message=(TextMessage, LocationMessage, ImageMessage,StickerMessage,VideoMessage))
def handle_message(event):
    global repair_id
    global repair_type
    global repair
    global detail
    global latitude
    global longitude
    global phonenumber
    global location
    global status
    global message_content
    global url
    repair_list = ['น้ำประปาไม่ไหล', 'มีกลิ่น,ขุ่น,มิเตอร์', 'ระบบไฟฟ้า', 'ระบบปรับอากาศ',
                   'โยธาสถาปัตย์', 'ประปาและสุขาภิบาล', 'ตัดหญ้า', 'ตัดแต่งกิ่ง', 'กำจัดแมลง']
    fallback = ['ขออภัยค่ะ ฉันไม่เข้าใจ', 'ขอโทษค่ะ ฉันไม่เข้าใจ', 'กรุณาตรวจสอบข้อความก่อนส่งค่ะ',
                'คุณต้องการใช้บริการอะไรคะ', 'หากต้องการใช้บริการกรุณากดเมนูดูได้เลยค่ะ']
    if isinstance(event.message, TextMessage):
        if 'สวัสดี' in event.message.text:
            sendMessage(
                event, "สวัสดีค่ะ เราคือแชทบอทแจ้งซ่อม หากต้องการใช้บริการสามารถกดที่ปุ่มเมนูเพื่อเลือกบริการที่ต้องการค่ะ")
        # แจ้งซ่อม
        elif event.message.text == 'แจ้งซ่อม':
            quickreply_repairtype(event, "เลือกประเภทงานบริการ")
        elif event.message.text == 'แจ้งซ่อมระบบประปา':
            repair_type = 'แจ้งซ่อมระบบประปา'
            plumbing_system(event, "รายละเอียดแจ้งซ่อม")
        elif event.message.text == 'แจ้งซ่อมไฟฟ้า':
            repair_type = 'แจ้งซ่อมไฟฟ้า'
            electrical_system(event, "รายละเอียดแจ้งซ่อม")
        elif event.message.text == 'งานซ่อมบำรุงรักษา':
            repair_type = 'งานซ่อมบำรุงรักษา'
            maintenance(event, "รายละเอียดแจ้งซ่อม")
        elif event.message.text == 'แจ้งงานภูมิทัศน์':
            repair_type = 'แจ้งงานภูมิทัศน์'
            landscape(event, "รายละเอียดแจ้งซ่อม")
        elif event.message.text == 'อื่นๆ':
            repair_type = 'อื่นๆ'
            sendMessage(
                event, "กรุณาระบุเพิ่มเติมค่ะ \nพิมพ์(เว้นวรรค)ตามด้วยสิ่งที่ต้องการแจ้งซ่อม")
        # เช็ครายละเอียดเพิ่มเติม
        elif event.message.text[0] == '-' or (event.message.text[0] == '-' and event.message.text[1] == '*'):
            if event.message.text[1] == '*':
                detail = '-'
            else:
                detail = event.message.text[1:]
            confirmdata(
                event, "หากตรวจสอบข้อมูลเรียบร้อยแล้ว\nกรุณากดยืนยันค่ะ")
        # ช่องทางการติดต่อ(ยังไม่เสร็จ)
        elif event.message.text == 'ตรวจสอบการแจ้งซ่อม':
            userid = event.source.user_id
            yourdata = ""
            if mycol.count_documents({"user_id": userid}) > 0:
                n = mycol.count_documents({"user_id": userid})
                for i in mycol.find({"user_id": userid}):
                    yourdata += ("\nไอดีแจ้งซ่อม: %s\nแจ้งซ่อม: %s\nรายละเอียดการแจ้งซ่อม: %s\nสถานที่: %s\nวันที่: %s\nสถานะ: %s\nหมายเหตุ: %s\n\n˚ ༘♡ ⋆｡˚ ❀˚ ༘♡ ⋆｡˚ ❀˚ ༘♡ ⋆｡˚ ❀\n" %
                                 (i['repair_id'], i['repair'], i['repair_type'], i['address'], i['timestamp'], i['status'], i['note']))
                letter = "สถานะของคุณมีทั้งหมด %d รายการ\n\n｡☆✼★━━━━━━━━★✼☆｡\n" % n
                sendMessage(event, letter+yourdata)
            else:
                sendMessage(
                    event, "ไม่มีรายการแจ้งซ่อมของคุณ กรุณาแจ้งซ่อมก่อนค่ะ")
        # ปัญหาที่จะแจ้งซ่อม
        elif event.message.text[0] == ' ':
            repair = event.message.text[1:]
            askforimage(event, "มีรูปภาพประกอบหรือไม่")
        elif event.message.text in repair_list:
            repair = event.message.text
            askforimage(event, "มีรูปภาพประกอบหรือไม่")
        elif event.message.text == '.มี':
            url = 'Yes'
            imageaction(event, "รูปภาพประกอบค่ะ")
        elif event.message.text == '.ไม่มี':
            url = 'No'
            quickreply_asklocation(event, "ขอทราบที่อยู่ค่ะ")
        # ตรวจสอบสถานะ
        elif event.message.text == 'ตรวจสอบสถานะ':
            checkstatus(event, "ต้องการตรวจสอบแบบไหนดีคะ")
        elif event.message.text == 'ใส่ไอดีแจ้งซ่อม':
            sendMessage(event, "กรุณาใส่ไอดีแจ้งซ่อมค่ะ")
        #คู่มือ
        elif event.message.text == 'คู่มือการใช้งาน':
            quickreply_guid(event, "ต้องการทราบอะไรคะ")
        elif event.message.text == '.การแจ้งซ่อม':
            url=urlimage2('6.PNG')
            sendImage(event, url,"คู่มือการแจ้งซ่อม")
        elif event.message.text == '.การตรวจสอบการแจ้งซ่อม':
            url=urlimage2('7.PNG')
            sendImage(event, url,"คู่มือการตรวจสอบการแจ้งซ่อม")
        elif event.message.text == '.การตรวจสอบสถานะ':
            url=urlimage2('8.PNG')
            sendImage(event, url,"คู่มือการตรวจสอบสถานะ")
        
        # เช็คไอดีแจ้งซ่อม
        elif event.message.text[0] == 'S' and event.message.text[1] == 'U' and event.message.text[2] == 'T':
            yourid = event.message.text
            if mycol.count_documents({"repair_id": yourid}) > 0:
                for i in mycol.find({"repair_id": yourid}):
                    yourstatus = i['status']
                    if yourstatus == 'เสร็จสิ้น':
                        StatusSuccess(event, "สถานะการแจ้งซ่อม", yourid)
                    elif yourstatus == 'กำลังดำเนินการ':
                        StatusInProgress(event, "สถานะการแจ้งซ่อม", yourid)
                    elif yourstatus == 'รอดำเนินการ':
                        StatusPending(event, "สถานะการแจ้งซ่อม", yourid)
                    else:
                        sendMessage(event, "ไอดีแจ้งซ่อมไม่ถูกต้องค่ะ")
            else:
                sendMessage(event, "กรุณาตรวจสอบไอดีแจ้งซ่อมค่ะ")
        # cf
        elif event.message.text == '.ยืนยัน':
            try: repair_type
            except NameError: repair_type = None
            try: repair
            except NameError: repair = None
            try: location
            except NameError: location = None
            try: phonenumber
            except NameError: phonenumber = None
            try: detail
            except NameError: detail = None
            try: url
            except NameError: url = None
            if repair_type is None : sendMessage(event, "คุณไม่ได้ประเภทบริการ กรุณาแจ้งซ่อมอีกครั้งค่ะ")
            if repair is None: sendMessage(event, "คุณไม่ได้แจ้งแจ้งรายละเอียด กรุณาแจ้งซ่อมอีกครั้งค่ะ")
            if location is None: sendMessage(event, "คุณไม่ได้แจ้งสถานที่ซ่อม กรุณาแจ้งซ่อมอีกครั้งค่ะ")
            if phonenumber is None: sendMessage(event, "คุณไม่ได้แจ้งเบอร์โทรศัพท์ กรุณาแจ้งซ่อมอีกครั้งค่ะ")
            if detail is None: sendMessage(event, "คุณไม่ได้แจ้งหมายเหตุ กรุณาแจ้งซ่อมอีกครั้งค่ะ")
            if url is None: sendMessage(event, "คุณไม่ได้แจ้งรูปภาพประกอบ กรุณาแจ้งซ่อมอีกครั้งค่ะ")
            status = 'รอดำเนินการ'
            repair_id = generate_id()
            user_id = event.source.user_id
            time = event.timestamp
            date = datetime.datetime.fromtimestamp(
                time//1000).strftime("%m/%d/%Y %H:%M:%S")
            insertdb(repair_id, repair_type, repair, location,phonenumber, status, detail, date, user_id, url)
            if mycol.count_documents({"repair_id": repair_id}) > 0:
                for i in mycol.find({"repair_id": repair_id}):
                    id_db = i['repair_id']
                    type_db = i['repair_type']
                    img_url = i['image']
                    repair_db = i['repair']
                    location_db = i['address']
                    tel_db = i['tel']
                    status_db = i['status']
                    note_db = i['note']
                    time_db = i['timestamp']
            detail_data(event, "ข้อมูลแจ้งซ่อม", id_db, type_db, repair_db,
                        location_db, tel_db, status_db, note_db, time_db, img_url)
        # cc
        elif event.message.text == 'ยกเลิก':
            repair_id = None
            repair_type = None
            repair = None
            location = None
            phonenumber = None
            status = None
            detail = None
            sendMessage(event, "ทำการยกเลิกเรียบร้อยค่ะ")
        # เช็คสถิติ
        elif event.message.text == 'สถิติการแจ้งซ่อม':
            pending = mycol.count_documents({"status": "รอดำเนินการ"})
            in_progress = mycol.count_documents({"status": "กำลังดำเนินการ"})
            success = mycol.count_documents({"status": "เสร็จสิ้น"})
            all_status = mycol.count_documents({})
            Showstatus(event, "สถิติการแจ้งซ่อม",
                       pending, in_progress, success, all_status)

        # เช็คเบอร์โทรศัพท์
        elif event.message.text.isdigit() and event.message.text[0] == '0':
            phonenumber = event.message.text
            if len(phonenumber) == 10:
                if phonenumber[1] == "6" or phonenumber[1] == "9" or phonenumber[1] == "8":
                    phonenumber = event.message.text[0:]
                    sendMessage(
                        event, "หากต้องการแจ้งหมายเหตุ\nพิมพ์-ตามด้วยข้อความ\nหากไม่มีให้พิมพ์ \"-*\")")
                else:
                    sendMessage(event, "ตรวจสอบเบอร์โทรศัพท์อีกครั้งค่ะ")
            else:
                sendMessage(event, "กรุณาพิมพ์เบอร์โทรศัพท์ให้ครบ10ตัวค่ะ")
        else:
            sendMessage(event, random.choice(fallback))
            
    elif isinstance(event.message, LocationMessage):
        address = event.message.address  # ที่อยู่ที่userแชร์มา
        location = address
        latitude = event.message.latitude
        longitude = event.message.longitude
        sendMessage(event, "รบกวนแจ้งเบอร์โทรศัพท์ค่ะ")

    elif isinstance(event.message, ImageMessage):
        message_content = line_bot_api.get_message_content(event.message.id)
        quickreply_asklocation(event, "ขอทราบที่อยู่ค่ะ")
        
    else: sendMessage(event, random.choice(fallback))
    
def urlimage(dist_name):
    client = imgbbpy.SyncClient('e010a1c870aa4da729494ac9378741c2')
    image = client.upload(
        file=r'C:\Users\ASUS\Documents\B6236182\Line_Chatbot\lineproject\static\tmp\{}'.format(dist_name))
    return image.url

def urlimage2(name):
    client = imgbbpy.SyncClient('e010a1c870aa4da729494ac9378741c2')
    image = client.upload(
        file=r'C:\Users\ASUS\Pictures\คู่มือ\{}'.format(name))
    return image.url

def sendMessage(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message),
        print(message))

def sendImage(event,url,message):
    image_message = ImageSendMessage(
        alt_text=message,
        original_content_url='{}'.format(url),
        preview_image_url='{}'.format(url)
    )
    line_bot_api.reply_message(event.reply_token, image_message)

    
def quickreply_repairtype(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(
                            label="แจ้งซ่อมไฟฟ้า", text="แจ้งซ่อมไฟฟ้า")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="แจ้งซ่อมระบบประปา", text="แจ้งซ่อมระบบประปา")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="งานซ่อมบำรุงรักษา", text="งานซ่อมบำรุงรักษา")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="แจ้งงานภูมิทัศน์", text="แจ้งงานภูมิทัศน์")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="อื่นๆ(โปรดระบุ)", text="อื่นๆ")
                    ),
                ])))
    
def quickreply_guid(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(
                            label="การแจ้งซ่อม", text=".การแจ้งซ่อม")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="การตรวจสอบการแจ้งซ่อม", text=".การตรวจสอบการแจ้งซ่อม")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="การตรวจสอบสถานะ", text=".การตรวจสอบสถานะ")
                    ),
                ])))


def quickreply_asklocation(event, message):
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


def imageaction(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=CameraAction(label="ถ่ายภาพ")
                    ),
                    QuickReplyButton(
                        action=CameraRollAction(label="เลือกภาพถ่าย")
                    )
                ])))


def askforimage(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="มี", text=".มี")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="ไม่มี", text=".ไม่มี")
                    )
                ])))


def plumbing_system(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(
                            label="น้ำประปาไม่ไหล", text="น้ำประปาไม่ไหล")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="มีกลิ่น,ขุ่น,มิเตอร์", text="มีกลิ่น,ขุ่น,มิเตอร์")
                    )
                ])))


def electrical_system(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(
                            label="ระบบปรับอากาศ", text="ระบบปรับอากาศ")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="ระบบไฟฟ้า", text="ระบบไฟฟ้า")
                    )
                ])))


def maintenance(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(
                            label="โยธาสถาปัตย์", text="โยธาสถาปัตย์")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="ประปาและสุขาภิบาล", text="ประปาและสุขาภิบาล")
                    )
                ])))


def landscape(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(
                            label="ตัดหญ้า", text="ตัดหญ้า")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="ตัดแต่งกิ่ง", text="ตัดแต่งกิ่ง")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="กำจัดแมลง", text="กำจัดแมลง")
                    )
                ])))


def confirmdata(event, message):
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


def checkstatus(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(
                            label="ใส่ไอดีแจ้งซ่อม", text="ใส่ไอดีแจ้งซ่อม")
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="สถิติการแจ้งซ่อม", text="สถิติการแจ้งซ่อม")
                    )
                ])))


def generate_id():
    id = uuid.uuid1().hex
    id = str(id[:5])
    id = "SUT"+id
    return id


def all(event, message, n):
    flex_message = FlexSendMessage(
        alt_text=message,
        contents={
            "type": "carousel",
            "contents": [
                {
                    "type": "bubble",
                    "size": "kilo",
                    "hero": {
                        "type": "image",
                        "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip10.jpg",
                        "size": "full",
                        "aspectMode": "cover",
                        "aspectRatio": "320:213"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "การแจ้งซ่อม",
                                "weight": "bold",
                                "size": "sm",

                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "spacing": "sm",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "รหัสแจ้งซ่อม",

                                                "color": "#8c8c8c",
                                                "size": "xs",
                                                "flex": 1
                                            },
                                            {
                                                "type": "text",
                                                "text": "hello, world",
                                                "flex": 1
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents": []
                                    }
                                ]
                            }
                        ],
                        "spacing": "sm",
                        "paddingAll": "13px"
                    }
                }
            ]
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)


def detail_data(event, message, id_db, type_db, repair_db, location_db, tel_db, status_db, note_db, time_db, img_url):
    flex_message = FlexSendMessage(
        alt_text=message,
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "{}".format(img_url),
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
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": id_db,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 8
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
                                        "text": type_db,
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
                                        "text": repair_db,
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
                                        "text": location_db,
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
                                        "text": tel_db,
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
                                        "text": status_db,
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
                                        "text": note_db,
                                        "flex": 8,
                                        "size": "sm"
                                    }
                                ],
                                "spacing": "sm"
                            }, {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "วันที่",
                                        "color": "#666666",
                                        "flex": 5,
                                        "size": "sm"
                                    },
                                    {
                                        "type": "text",
                                        "text": time_db,
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 8
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


def Showstatus(event, message, pending, in_progress, success, all_status):
    flex_message = FlexSendMessage(
        alt_text=message,
        contents={
            "type": "carousel",
            "contents": [
                {
                    "type": "bubble",
                    "size": "micro",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "รอดำเนินการ",
                                "color": "#ffffff",
                                "align": "start",
                                "size": "md",
                                "gravity": "center",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "{} ({:.2f}%)".format(pending,(pending/all_status)*100),
                                "color": "#ffffff",
                                "align": "start",
                                "size": "xs",
                                "gravity": "center",
                                "margin": "lg"
                            }
                        ],
                        "backgroundColor": "#FF6B6E",
                        "paddingTop": "19px",
                        "paddingAll": "12px",
                        "paddingBottom": "16px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "แจ้งซ่อมสำเร็จ",
                                        "color": "#8C8C8C",
                                        "size": "sm",
                                        "align": "center"
                                    },
                                    {
                                        "type": "text",
                                        "text": "รอดำเนินการซ่อม",
                                        "color": "#8C8C8C",
                                        "size": "sm",
                                        "align": "center"
                                    }
                                ],
                                "flex": 1
                            }
                        ],
                        "spacing": "md",
                        "paddingAll": "12px"
                    },
                    "styles": {
                        "footer": {
                        }
                    }
                },
                {
                    "type": "bubble",
                    "size": "micro",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "กำลังดำเนินการ",
                                "color": "#ffffff",
                                "align": "start",
                                "size": "md",
                                "gravity": "center",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "{} ({:.2f}%)".format(in_progress,(in_progress/all_status)*100),
                                "color": "#ffffff",
                                "align": "start",
                                "size": "xs",
                                "gravity": "center",
                                "margin": "lg"
                            }
                        ],
                        "backgroundColor": "#FDA50E",
                        "paddingTop": "19px",
                        "paddingAll": "12px",
                        "paddingBottom": "16px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "กำลังดำเนินการซ่อม",
                                        "color": "#8C8C8C",
                                        "size": "sm",
                                        "align": "center"
                                    },
                                    {
                                        "type": "text",
                                        "text": "ภายใน1-3วัน",
                                        "color": "#8C8C8C",
                                        "size": "sm",
                                        "align": "center"
                                    }
                                ],
                                "flex": 1
                            }
                        ],
                        "spacing": "md",
                        "paddingAll": "12px"
                    },
                    "styles": {
                        "footer": {
                        }
                    }
                },
                {
                    "type": "bubble",
                    "size": "micro",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "เสร็จสิ้น",
                                "color": "#ffffff",
                                "align": "start",
                                "size": "md",
                                "gravity": "center",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "{} ({:.2f}%)".format(success,((success/all_status)*100)),
                                "color": "#ffffff",
                                "align": "start",
                                "size": "xs",
                                "gravity": "center",
                                "margin": "lg"
                            }
                        ],
                        "backgroundColor": "#27ACB2",
                        "paddingTop": "19px",
                        "paddingAll": "12px",
                        "paddingBottom": "16px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "ดำเนินการซ่อมเสร็จสิ้น",
                                        "color": "#8C8C8C",
                                        "size": "sm",
                                        "align": "center"
                                    }
                                ],
                                "flex": 1
                            }
                        ],
                        "spacing": "md",
                        "paddingAll": "12px"
                    },
                    "styles": {
                        "footer": {
                        }
                    }
                }
            ]
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)


def StatusPending(event, message, yourid):
    flex_message = FlexSendMessage(
        alt_text=message,
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


def StatusInProgress(event, message, yourid):
    flex_message = FlexSendMessage(
        alt_text=message,
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


def StatusSuccess(event, message, yourid):
    flex_message = FlexSendMessage(
        alt_text=message,
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


def insertdb(repair_id, repair_type, repair, location, phonenumber, status, detail, timestamp, user_id, url):
    if url == 'Yes':
        ext = 'jpg'
        with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name
            dist_path = tempfile_path + '.' + ext
            dist_name = os.path.basename(dist_path)
            tf.close()
            os.rename(tempfile_path, dist_path)
            os.chdir(
                r'C:\Users\ASUS\Documents\B6236182\Line_Chatbot\lineproject\static\tmp')
            url_img = urlimage(dist_name)
    elif url == 'No':
        url_img = 'https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png'
    mydict = {"user_id": user_id, "repair_id": repair_id, "repair_type": repair_type, "repair": repair, "image": url_img,
              "address": location, "tel": phonenumber, "status": status, "note": detail, "timestamp": timestamp}
    x = mycol.insert_one(mydict)


if __name__ == '__main__':
    app.run(debug=True)
