# -*- coding: utf-8 -*-
import requests
import json
from PyQt5.QtCore import *
from UI.ClientWindow import *
from prettytable import PrettyTable
import webbrowser
import os

strHeadtMeterId = ""
strValveId = ""
strHeadtMeterData = ""
strCreateBMUId = ""
dictConfig = None
strBMUId = ""
strDataTaskServerUrl = ""
strGbt26831ServerUrl = ""

# 全局变量
try:
    file = open("config.txt", "r")
    try:
        configcontent = eval(file.read())
    except Exception:
        dictConfig = None
    else:
        if ("BMUId" in configcontent.keys()) and ("DataTaskServerUrl" in configcontent.keys()) and (
                "Gbt26831ServerUrl" in configcontent.keys()):
            dictConfig = configcontent
            strBMUId = dictConfig["BMUId"]
            strDataTaskServerUrl = dictConfig["DataTaskServerUrl"]
            strGbt26831ServerUrl = dictConfig["Gbt26831ServerUrl"]
        else:
            dictConfig = None
    file.close()
except FileNotFoundError:
    dictConfig = None


class MyClientWindow(Ui_widget):
    def __init__(self, widgets):
        super().setupUi(widgets)
        # 创建 清空任务寄存器 的线程和事件
        self.cleanTaskThread = CleanTaskThread()
        self.btnCleanTask.clicked.connect(self.onClickedbtnCleanTask)

        # 创建 定时读取任务寄存器和任务响应寄存器 的线程和事件
        self.readTaskRegisterThread = ReadTaskRegisterThread()  # 读任务寄存器
        self.readTaskRegisterThread.start()
        self.readTaskRegisterThread.trigger.connect(self.setTextEditTaskRegister)

        self.readTaskRespondRegisterThread = ReadTaskRespondRegisterThread()  # 读任务响应寄存器
        self.readTaskRespondRegisterThread.start()
        self.readTaskRespondRegisterThread.trigger.connect(self.setTextEditTaskRespondRegister)

        # 创建 定时器 定时清除状态
        self.timerCleanSatus = QTimer()
        self.timerCleanSatus.timeout.connect(self.cleanLineEditStatus)

        # 创建 读写BMU工作模式按键 的线程及事件
        self.readBMUModeThread = ReadBMUModeThread()  # 读BMU模式
        self.btnReadBMUMode.clicked.connect(self.onClickedbtnReadBMUMode)

        self.setBMUModeA1Thread = SentModeA1ToServerThread()  # 1轮3次整点自动抄收模式
        self.btnSetBMUModeA1.clicked.connect(self.onClickedbtnSetBMUModeA1)

        self.setBMUModeA2Thread = SentModeA2ToServerThread()  # 3轮1次整点自动抄收模式
        self.btnSetBMUModeA2.clicked.connect(self.onClickedbtnSetBMUModeA2)

        self.setBMUMode10Thread = SentMode10ToServerThread()  # 一次抄收模式
        self.btnSetBMUMode10.clicked.connect(self.onClickedbtnSetBMUMode10)

        self.setBMUMode20Thread = SentMode20ToServerThread()  # 自校时模式
        self.btnSetBMUMode20.clicked.connect(self.onClickedbtnSetBMUMode20)

        self.setBMUMode21Thread = SentMode21ToServerThread()  # 广播校时模式
        self.btnSetBMUMode21.clicked.connect(self.onClickedbtnSetBMUMode21)

        self.setBMUMode22Thread = SentMode22ToServerThread()  # 依次校时模式
        self.btnSetBMUMode22.clicked.connect(self.onClickedbtnSetBMUMode22)

        self.setBMUMode00Thread = SentMode00ToServerThread()  # 值守模式
        self.btnSetBMUMode00.clicked.connect(self.onClickedbtnSetBMUMode00)

        self.setBMUMode11Thread = SentMode11ToServerThread()  # 三次抄收模式
        self.btnSetBMUMode11.clicked.connect(self.onClickedbtnSetBMUMode11)

        self.setBMUModeA0Thread = SentModeA0ToServerThread()  # 连续自动抄收模式
        self.btnSetBMUModeA0.clicked.connect(self.onClickedbtnSetBMUModeA0)

        self.setBMUMode30Thread = SentMode30ToServerThread()  # 用户档案下发模式
        self.btnSetBMUMode30.clicked.connect(self.onClickedbtnSetBMUMode30)

        self.setBMUMode40Thread = SentMode40ToServerThread()  # 设备状态下发模式
        self.btnSetBMUMode40.clicked.connect(self.onClickedbtnSetBMUMode40)

        self.setBMUMode50Thread = SentMode50ToServerThread()  # 广播升级模式
        self.btnSetBMUMode50.clicked.connect(self.onClickedbtnSetBMUMode50)

        self.setBMUMode51Thread = SentMode51ToServerThread()  # 依次升级模式
        self.btnSetBMUMode51.clicked.connect(self.onClickedbtnSetBMUMode51)

        self.setBMUMode61Thread = SentMode61ToServerThread()  # 初始化DTU模式
        self.btnSetBMUMode61.clicked.connect(self.onClickedbtnSetBMUMode61)

        self.setBMUModeB0Thread = SentModeB0ToServerThread()  # 自动发现模式
        self.btnSetBMUModeB0.clicked.connect(self.onClickedbtnSetBMUModeB0)

        # 创建 通过ID读热量表数据 的线程及事件
        self.readHeatMeterDataByIdThread = ReadHeatMeterDataByIdThread()
        self.btnReadHeatMeterDataByID.clicked.connect(self.onClickedbtnReadHeatMeterDataByID)

        # 创建 设置阀门开、关按键 的线程及事件
        self.setValveOpenByIdThread = SetValveOpenByIdThread()  # 阀门开
        self.btnSetValveOpenById.clicked.connect(self.onClickedbtnSetValveOpenById)

        self.setValveCloseByIdThread = SetValveCloseByIdThread()  # 阀门关
        self.btnSetValveCloseById.clicked.connect(self.onClickedbtnSetValveCloseById)

        # 创建 解析热量表数据 的线程及事件
        self.parseHeatMeterDataThread = ParseHeatMeterDataThread()
        self.btnParseHeatMeterData.clicked.connect(self.onClickedbtnParseHeatMeterData)

        # 创建 定时器 定时清除解析结果文本框
        self.timerCleanParseResult = QTimer()
        self.timerCleanParseResult.timeout.connect(self.cleanTextEditParseHeatMeterData)

        self.btnCleanParseResult.clicked.connect(self.cleanTextEditParseHeatMeterData)

        # BMU ID
        self.lineEditBMUId.setText(strBMUId)
        self.btnSetBMUId.clicked.connect(self.onClickedbtnSetBMUId)
        self.btnRecoverBMUId.clicked.connect(self.onClickedbtnRecoverBMUId)

        # 建表
        self.btnCreateTable.clicked.connect(self.onClickedbtnCreateTable)
        self.createTableThread = CreateTableThread()
        self.createTableThread.trigger.connect(self.setLineEditStatus)

        # 删表
        self.btnDelTable.clicked.connect(self.onClickedbtnDelTable)
        self.delTableThread = DelTableThread()
        self.delTableThread.trigger.connect(self.setLineEditStatus)

        # 查询服务器热量表历史数据
        self.btnReadHeatMeterData.clicked.connect(self.onClickedbtnReadHeatMeterData)
        self.getHeterMeterDataThread = GetHeterMeterDataThread()

        # 查询服务智能阀历史数据
        self.btnReadValveData.clicked.connect(self.onClickedbtnReadValveData)
        self.getValveDataThread = GetValveDataThread()

        # 查询服务器电能表历史数据
        self.btnElectricMeterData.clicked.connect(self.onClickedbtnElectricMeterData)
        self.getElectricMeterDataThread = GetElectricMeterDataThread()

    def onClickedbtnCleanTask(self):
        """清空 任务寄存器按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.cleanTaskThread.start()
        self.cleanTaskThread.trigger.connect(self.setLineEditStatus)

    def setTextEditTaskRegister(self, strContent):
        """设置 任务寄存器显示 事件"""
        self.textEditTaskRegister.setPlainText(strContent)

    def setTextEditTaskRespondRegister(self, strContent):
        """设置 任务响应寄存器显示 事件"""
        self.textEditTaskRespondRegister.setPlainText(strContent)

    def setLineEditStatus(self, strContent):
        """设置 状态显示 事件"""
        self.lineEditStatus.setText(strContent)
        self.timerCleanSatus.start(3000)

    def cleanLineEditStatus(self):
        """清除 状态显示 事件"""
        self.lineEditStatus.setText("")
        self.timerCleanSatus.stop()

    def onClickedbtnReadBMUMode(self):
        """读 BMU工作模式按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.readBMUModeThread.start()
        self.readBMUModeThread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUModeA1(self):
        """设置 BMU工作模式A1按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUModeA1Thread.start()
        self.setBMUModeA1Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUModeA2(self):
        """设置 BMU工作模式A1按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUModeA2Thread.start()
        self.setBMUModeA2Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode10(self):
        """设置 BMU工作模式A1按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode10Thread.start()
        self.setBMUMode10Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode20(self):
        """设置 BMU工作模式20按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode20Thread.start()
        self.setBMUMode20Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode21(self):
        """设置 BMU工作模式21按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode21Thread.start()
        self.setBMUMode21Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode22(self):
        """设置 BMU工作模式22按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode22Thread.start()
        self.setBMUMode22Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode00(self):
        """设置 BMU工作模式00按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode00Thread.start()
        self.setBMUMode00Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode11(self):
        """设置 BMU工作模式11按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode11Thread.start()
        self.setBMUMode11Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUModeA0(self):
        """设置 BMU工作模式A0按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUModeA0Thread.start()
        self.setBMUModeA0Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode30(self):
        """设置 BMU工作模式30按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode30Thread.start()
        self.setBMUMode30Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode40(self):
        """设置 BMU工作模式40按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode40Thread.start()
        self.setBMUMode40Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode50(self):
        """设置 BMU工作模式50按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode50Thread.start()
        self.setBMUMode50Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode51(self):
        """设置 BMU工作模式51按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode51Thread.start()
        self.setBMUMode51Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUMode61(self):
        """设置 BMU工作模式61按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUMode61Thread.start()
        self.setBMUMode61Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnSetBMUModeB0(self):
        """设置 BMU工作模式B0按键 事件"""
        self.textEditTaskRegister.setPlainText("")
        self.textEditTaskRespondRegister.setPlainText("")
        self.setBMUModeB0Thread.start()
        self.setBMUModeB0Thread.trigger.connect(self.setLineEditStatus)

    def onClickedbtnReadHeatMeterDataByID(self):
        """设置 通过ID读取热量表数据按键 事件"""
        global strHeadtMeterId
        strTmp = self.lineEditHeatMeterId.text()
        if len(strTmp) == 16:
            strHeadtMeterId = strTmp
            self.textEditTaskRegister.setPlainText("")
            self.textEditTaskRespondRegister.setPlainText("")
            self.readHeatMeterDataByIdThread.start()
            self.readHeatMeterDataByIdThread.trigger.connect(self.setLineEditStatus)
        else:
            strHeadtMeterId = ""
            self.setLineEditStatus("热量表ID错误")

    def onClickedbtnSetValveOpenById(self):
        """设置 通过ID打开阀门按键 事件"""
        global strValveId
        strTmp = self.lineEditValveId.text()
        if len(strTmp) == 16:
            strValveId = strTmp
            self.textEditTaskRegister.setPlainText("")
            self.textEditTaskRespondRegister.setPlainText("")
            self.setValveOpenByIdThread.start()
            self.setValveOpenByIdThread.trigger.connect(self.setLineEditStatus)
        else:
            strValveId = ""
            self.setLineEditStatus("智能阀ID错误！")

    def onClickedbtnSetValveCloseById(self):
        """设置 通过ID关闭阀门按键 事件"""
        global strValveId
        strTmp = self.lineEditValveId.text()
        if len(strTmp) == 16:
            strValveId = strTmp
            self.textEditTaskRegister.setPlainText("")
            self.textEditTaskRespondRegister.setPlainText("")
            self.setValveCloseByIdThread.start()
            self.setValveCloseByIdThread.trigger.connect(self.setLineEditStatus)
        else:
            strValveId = ""
            self.setLineEditStatus("智能阀ID错误！")

    def onClickedbtnParseHeatMeterData(self):
        """设置 解析热量表数据按键 事件"""
        global strHeadtMeterData
        strContent = self.textEditParseHeatMeterData.toPlainText()
        if not strContent.startswith("68"):
            try:
                strContent = json.loads(self.textEditTaskRespondRegister.toPlainText())[0]["data"]
            except Exception:
                strContent = ""
        if strContent.startswith("68"):
            strHeadtMeterData = strContent
            self.parseHeatMeterDataThread.start()
            self.parseHeatMeterDataThread.trigger.connect(self.setTextEditParseHeatMeterData)
        else:
            self.setTextEditParseHeatMeterData("没有热量表数据！")
            self.timerCleanParseResult.start(3000)

    def setTextEditParseHeatMeterData(self, strTable):
        """显示解析结果"""
        self.textEditParseHeatMeterData.setPlainText(strTable)

    def cleanTextEditParseHeatMeterData(self):
        """清除错误显示"""
        self.textEditParseHeatMeterData.setPlainText("")
        self.timerCleanParseResult.stop()

    def onClickedbtnSetBMUId(self):
        """修改BMU ID"""
        global dictConfig, strBMUId
        strTemp = self.lineEditBMUId.text()
        if len(strTemp) == 16:
            if dictConfig != None:
                dictConfig["BMUId"] = strTemp
                json_data = json.dumps(dictConfig, indent=4)
                with open("./config.txt", "w") as file:
                    file.write(str(json_data))
                strBMUId = strTemp
                self.textEditTaskRegister.setPlainText("")
                self.textEditTaskRespondRegister.setPlainText("")
                self.setLineEditStatus("修改成功！")
            else:
                self.setLineEditStatus("没有配置文件！")
        else:
            self.setLineEditStatus("BMU ID错误！")

    def onClickedbtnRecoverBMUId(self):
        """显示当前BMU ID"""
        global dictConfig
        if dictConfig != None:
            self.lineEditBMUId.setText(strBMUId)
        else:
            self.lineEditBMUId.setText("没有配置文件！")

    def onClickedbtnCreateTable(self):
        global strCreateBMUId
        strTemp = self.lineEditCreateBMUId.text()
        if len(strTemp) == 16:
            strCreateBMUId = strTemp
            self.createTableThread.start()
        else:
            self.setLineEditStatus("BMU ID错误，建表失败！")

    def onClickedbtnDelTable(self):
        global strCreateBMUId
        strTemp = self.lineEditCreateBMUId.text()
        if len(strTemp) == 16:
            strCreateBMUId = strTemp
            self.delTableThread.start()
        else:
            self.setLineEditStatus("BMU ID错误，删表失败！")

    def onClickedbtnReadHeatMeterData(self):
        self.getHeterMeterDataThread.start()

    def onClickedbtnReadValveData(self):
        self.getValveDataThread.start()

    def onClickedbtnElectricMeterData(self):
        self.getElectricMeterDataThread.start()


class CleanTaskThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(CleanTaskThread, self).__init__()

    def run(self):
        global dictConfig, strBMUId, strDataTaskServerUrl
        if dictConfig != None:
            # 构造发送的指令
            strJsonData = "[" + str({"RA": "65534", "data": "00"}).replace("'", '"') + "]"
            # 发送指令到服务器
            try:
                respond = requests.put(url=strDataTaskServerUrl + strBMUId, data=strJsonData,
                                       headers={'Content-Type': 'application/json;charset=UTF-8'})
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            except Exception:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class ReadTaskRegisterThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(ReadTaskRegisterThread, self).__init__()

    def run(self):
        global dictConfig, strBMUId, strDataTaskServerUrl
        if dictConfig != None:
            while True:
                # 构造发送的指令
                dictData = {"RA": 65534, "RN": 1}
                # 发送指令到服务器
                try:
                    respond = requests.get(url=strDataTaskServerUrl + strBMUId, params=dictData)
                    self.trigger.emit(json.dumps(respond.json(), indent=2))
                except Exception:
                    self.trigger.emit("网络异常！")
                self.sleep(5)
        else:
            self.trigger.emit("配置文件错误！")


class ReadTaskRespondRegisterThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(ReadTaskRespondRegisterThread, self).__init__()

    def run(self):
        global dictConfig, strBMUId, strDataTaskServerUrl
        if dictConfig != None:
            while True:
                # 构造发送的指令
                dictData = {"RA": 65535, "RN": 1}
                # 发送指令到服务器
                try:
                    respond = requests.get(url=strDataTaskServerUrl + strBMUId, params=dictData)
                    self.trigger.emit(json.dumps(respond.json(), indent=2))
                except Exception:
                    self.trigger.emit("网络异常！")
                self.sleep(5)
        else:
            self.trigger.emit("配置文件错误！")


class ReadBMUModeThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(ReadBMUModeThread, self).__init__()

    def run(self):
        global dictConfig, strBMUId, strDataTaskServerUrl
        if dictConfig != None:
            # 构造发送的指令
            strJsonData = "[" + str({"RA": "65534", "data": "FD " + " ".join(
                [strBMUId[i:i + 2] for i in range(0, len(strBMUId), 2)]) + " 43 00 05 01"}).replace("'", '"') + "]"
            # 发送指令到服务器
            try:
                respond = requests.put(url=strDataTaskServerUrl + strBMUId, data=strJsonData,
                                       headers={'Content-Type': 'application/json;charset=UTF-8'})
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            except Exception:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class SentModeToServerThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(SentModeToServerThread, self).__init__()

    def sentModeToServer(self, strMode):
        global strBMUId, strDataTaskServerUrl
        # 构造发送的指令
        strJsonData = "[" + str({"RA": "65534", "data": "FD " + " ".join(
            [strBMUId[i:i + 2] for i in range(0, len(strBMUId), 2)]) + "44 00 05 " + strMode}).replace("'", '"') + "]"
        # 发送指令到服务器
        try:
            respond = requests.put(url=strDataTaskServerUrl + strBMUId, data=strJsonData,
                                   headers={'Content-Type': 'application/json;charset=UTF-8'})
            # 返回访问服务器结果
            return respond
        except Exception:
            return None

    def run(self):
        pass


class SentModeA1ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentModeToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("A1")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class SentModeA2ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentModeA2ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("A2")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class SentMode10ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode10ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("10")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class SentMode20ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode20ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("20")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class SentMode21ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode21ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("21")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class SentMode22ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode22ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("22")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class SentMode00ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode00ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("00")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误！")


class SentMode11ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode11ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("11")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常！")
        else:
            self.trigger.emit("配置文件错误!")


class SentModeA0ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentModeA0ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("A0")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class SentMode30ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode30ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("30")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class SentMode40ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode40ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("40")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class SentMode50ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode50ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("50")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class SentMode51ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode51ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("51")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class SentMode61ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentMode61ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("61")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class SentModeB0ToServerThread(SentModeToServerThread):
    def __int__(self):
        super(SentModeB0ToServerThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentModeToServer("B0")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class ReadHeatMeterDataByIdThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(ReadHeatMeterDataByIdThread, self).__init__()

    def run(self):
        global strHeadtMeterId, strDataTaskServerUrl, strBMUId
        # 构造发送的指令
        strJsonData = "[" + str({"RA": "65534", "data": "FD " + " ".join(
            [strHeadtMeterId[i:i + 2] for i in range(0, len(strHeadtMeterId), 2)]) + " 48"}).replace("'", '"') + "]"
        # 发送指令到服务器
        try:
            respond = requests.put(url=strDataTaskServerUrl + strBMUId, data=strJsonData,
                                   headers={'Content-Type': 'application/json;charset=UTF-8'})
            # 返回访问服务器结果
            self.trigger.emit(respond.text)
        except Exception:
            self.trigger.emit("网络异常!")


class SetValveByIdThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(SetValveByIdThread, self).__init__()

    def sentOnOffToServer(self, strOnOff):
        global strValveId, strBMUId, strDataTaskServerUrl
        # 构造发送的指令
        strJsonData = "[" + str({"RA": "65534", "data": "FD " + " ".join(
            [strValveId[i:i + 2] for i in range(0, len(strValveId), 2)]) + " 44 08 0A " + strOnOff}).replace("'",
                                                                                                             '"') + "]"
        # 发送指令到服务器
        try:
            respond = requests.put(url=strDataTaskServerUrl + strBMUId, data=strJsonData,
                                   headers={'Content-Type': 'application/json;charset=UTF-8'})
            # 返回访问服务器结果
            return respond
        except Exception:
            return None

    def run(self):
        pass


class SetValveOpenByIdThread(SetValveByIdThread):
    def __int__(self):
        super(SetValveOpenByIdThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentOnOffToServer("FF")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class SetValveCloseByIdThread(SetValveByIdThread):
    def __int__(self):
        super(SetValveCloseByIdThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            respond = self.sentOnOffToServer("00")
            if respond != None:
                # 返回访问服务器结果
                self.trigger.emit(respond.text)
            else:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class ParseHeatMeterDataThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(ParseHeatMeterDataThread, self).__init__()

    def run(self):
        global dictConfig, strHeadtMeterData, strGbt26831ServerUrl
        if dictConfig != None:
            dictQueryParams = {"data": strHeadtMeterData}
            try:
                # 获得解析结果
                respond = requests.get(strGbt26831ServerUrl + "parser", dictQueryParams)
                dictParseResult = respond.json()
                # 创建表格
                tb = PrettyTable(["Value", "Unit", "Description"])
                tb.align = "l"
                tb.add_row([dictParseResult["C"], "", "C"])
                tb.add_row([dictParseResult["A"], "", "A"])
                tb.add_row([dictParseResult["CI"], "", "CI"])
                tb.add_row([dictParseResult["header"]["did"] + "; " + dictParseResult["header"]["fid"] + "; " +
                            dictParseResult["header"]["vid"] + "; " + dictParseResult["header"]["pid"], "",
                            "did; fid; vid; pid"])
                tb.add_row([str(dictParseResult["header"]["access-number"]) + "; " + dictParseResult["header"][
                    "status"] + "; " + dictParseResult["header"]["signature"], "", "access-number; status; signature"])
                for dictRecord in dictParseResult["records"]:
                    tb.add_row([dictRecord["value"], dictRecord["unit"], dictRecord["description"]])
                self.trigger.emit(str(tb))
            except Exception:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class CreateTableThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(CreateTableThread, self).__init__()

    def run(self):
        global dictConfig, strDataTaskServerUrl, strCreateBMUId
        if dictConfig != None:
            dictNewTable = {"ID": strCreateBMUId}
            try:
                # 获得解析结果
                respond = requests.post(strDataTaskServerUrl, dictNewTable)
                self.trigger.emit(respond.text)
            except Exception:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class DelTableThread(QThread):
    trigger = pyqtSignal(str)

    def __int__(self):
        super(DelTableThread, self).__init__()

    def run(self):
        global dictConfig, strDataTaskServerUrl, strCreateBMUId
        if dictConfig != None:
            try:
                # 获得解析结果
                respond = requests.delete(strDataTaskServerUrl + strCreateBMUId)
                self.trigger.emit(respond.text)
            except Exception:
                self.trigger.emit("网络异常!")
        else:
            self.trigger.emit("配置文件错误!")


class GetDataThread(QThread):
    def __int__(self):
        super(GetDataThread, self).__init__()

    def getDataFromServer(self, RA, RN):
        global strDataTaskServerUrl, strBMUId
        dictParam = {"RA": RA, "RN": RN}
        try:
            response = requests.get(strDataTaskServerUrl + strBMUId, dictParam)
            return response.json()
        except Exception:
            return None

    def run(self):
        pass


class GetHeterMeterDataThread(GetDataThread):
    def __int__(self):
        super(GetHeterMeterDataThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            listHeaterMeterData = self.getDataFromServer(2048, 512)
            if listHeaterMeterData != None:
                strHtmlBody = ""
                for dictData in listHeaterMeterData:
                    if not dictData["data"].startswith("00"):  # 有效数据
                        strHtmlBody += "\n<div>\n"
                        strHtmlBody += json.dumps(dictData, indent=2).replace("\n", "</br>")
                        strHtmlBody += "\n</div></br></br>"
                with open("./HeterMeterData.html", "w") as f:
                    strHtml = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>HeterMeterData</title>
</head>
<body>""" + strHtmlBody + """
</body>
</html>"""
                    f.write(strHtml)
                    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    webbrowser.open("file://" + dir_path + "/HeterMeterData.html")


class GetValveDataThread(GetDataThread):
    def __int__(self):
        super(GetValveDataThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            listValveData = self.getDataFromServer(2560, 512)
            if listValveData != None:
                strHtmlBody = ""
                for dictData in listValveData:
                    if not dictData["data"].startswith(
                            "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"):  # 有效数据
                        strHtmlBody += "\n<div>\n"
                        strHtmlBody += json.dumps(dictData, indent=2).replace("\n", "</br>")
                        strHtmlBody += "\n</div></br></br>"
                with open("./ValveData.html", "w") as f:
                    strHtml = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>ValveData</title>
</head>
<body>""" + strHtmlBody + """
</body>
</html>"""
                    f.write(strHtml)
                    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    webbrowser.open("file://" + dir_path + "/ValveData.html")


class GetElectricMeterDataThread(GetDataThread):
    def __int__(self):
        super(GetElectricMeterDataThread, self).__init__()

    def run(self):
        global dictConfig
        if dictConfig != None:
            listValveData = self.getDataFromServer(3072, 1)
            strHtmlBody = ""
            strHtmlBody += "\n<div>\n"
            strHtmlBody += json.dumps(listValveData, indent=2).replace("\n", "</br>")
            strHtmlBody += "\n</div></br></br>"
            with open("./ElectricMeterData.html", "w") as f:
                strHtml = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>ElectricMeterData</title>
</head>
<body>""" + strHtmlBody + """
</body>
</html>"""
                f.write(strHtml)
                dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                webbrowser.open("file://" + dir_path + "/ElectricMeterData.html")

# tb = PrettyTable(["Value", "Unit", "Description"])
# tb.align = "l"
# intDataLen = int(dictData["data"][0:2], 16)
# dictParam = {"data": "72" + dictData["data"][2:2 + intDataLen * 3]}
# respond = requests.get(strGbt26831ServerUrl + "parser/link-layer-user-data", dictParam)
# dictParseResult = respond.json()
# tb.add_row([dictParseResult["CI"], "", "CI"])
# tb.add_row([dictParseResult["header"]["did"] + "; " + dictParseResult["header"]["fid"] + "; " +
#             dictParseResult["header"]["vid"] + "; " + dictParseResult["header"]["pid"], "",
#             "did; fid; vid; pid"])
# tb.add_row([str(dictParseResult["header"]["access-number"]) + "; " + dictParseResult["header"][
#     "status"] + "; " + dictParseResult["header"]["signature"], "",
#             "access-number; status; signature"])
# for dictRecord in dictParseResult["records"]:
#     tb.add_row([dictRecord["value"], dictRecord["unit"], dictRecord["description"]])
# print(tb)
