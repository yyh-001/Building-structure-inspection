from PySide6 import QtWidgets,QtGui,QtCore
from PySide6.QtCore import Qt, Signal, QObject, QRectF, QTimer, QPoint
import qtawesome as qta
import pyqtgraph as pg
import shiboken6
import json

from share import gstore

from connector import connector

PIC_LIST = [
    'gas-meter', 'temp-meter',
    'wind-meter', 'water-meter',
    'water-valve', 'water-tank',
    'air-pump', 'camera',
    'hydrant', 'pipeline'
]

class Item:
    def keyPressEvent(self, e):

        if window.mode == 'view':
            QtWidgets.QMessageBox.warning(
                window,
                '禁止',
                '查看模式不能使用键盘修改界面')
            return

        if e.key() == Qt.Key_Up:
            self.setPos(self.x(), self.y() - 1)
        elif e.key() == Qt.Key_Down:
            self.setPos(self.x(), self.y() + 1)
        elif e.key() == Qt.Key_Left:
            self.setPos(self.x() - 1, self.y())
        elif e.key() == Qt.Key_Right:
            self.setPos(self.x() + 1, self.y())
        elif e.key() == Qt.Key_Delete:
            window.delItem()

    def itemChange(self, change, value, ):
        # 被选中
        if change == QtWidgets.QGraphicsItem.ItemSelectedChange and value == True:
            # 设置属性框内容
            window.setPropTable(self.props)


        return super().itemChange(change, value)

    def toSaveData(self):
        pos = self.pos()
        return {
            'type': self.__class__.__name__,
            'pos':  [pos.x(),pos.y()],
            'props': self.props
        }


# 自定义信号源对象类型，一定要继承自 QObject
class DeviceSignalObject(QObject):
    mdata_change = Signal(dict)


class WaterTankItem(Item, QtWidgets.QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.waterPercent = 0.9


        self.props = {
            'zValue' : '0.0',
            '设备编号' : ''
        }

        self.dso = DeviceSignalObject()
        self.dso.mdata_change.connect(self.handleNotify)


    def loadData(self,data):
        # 设置props
        self.props = data["props"]
        props = self.props
        self.setZValue(float(props["zValue"]))

        self.setPos(*data["pos"])

        # 有 设备编号 属性的子item， 额外处理
        deviceSn = self.props.get('设备编号')
        if deviceSn:
            gstore.deviceSn_to_item[deviceSn] = self

    def itemPropChanged(self,cfgName,newValue:str):
        oldValue = self.props[cfgName]
        self.props[cfgName] = newValue


        if cfgName == 'zValue':
            self.setZValue(float(newValue))

        elif cfgName == '设备编号':
            if newValue in gstore.deviceSn_to_item:
                QtWidgets.QMessageBox.warning(
                    window,
                    '警告',
                    '已经存在同名设备，请输入别的sn')
                return

            gstore.deviceSn_to_item.pop(oldValue, None)
            gstore.deviceSn_to_item[newValue] = self

        else :
            return


    def handleNotify(self, msg):
        self.waterPercent = msg['water-amount']
        self.update()

    # 设定控件显示内容
    def paint(self, painter, option, widget):
        # 选中状态，画选中方框
        if self.isSelected():
            painter.drawRect(1, 1, 78, 93)

        # 画上下椭圆截面
        painter.drawEllipse(5, 5, 70, 22)
        painter.drawEllipse(5, 63, 70, 22)

        # 画水箱正面矩形体
        painter.setBrush(QtGui.QBrush(Qt.white))
        painter.drawRect(5, 15, 70, 60)

        # 画水
        painter.setPen(QtGui.QPen(QtGui.QColor('#d0ffff')))
        painter.setBrush(QtGui.QBrush(QtGui.QColor('#d0ffff')))
        height = int(self.waterPercent * (60-2))
        y = 75-1-height
        painter.drawRect(6, y, 68, height)

        # 显示百分比数字
        painter.setPen(QtGui.QPen(QtGui.QColor('black')))
        percent = f'{self.waterPercent*100:.1f}%'
        painter.drawText(20, 50, percent)


    # 设定控件显示区域大小
    def boundingRect(self):
        return QRectF(0, 0, 85, 95)




class WindPumpItem(Item, QtWidgets.QGraphicsItem):
    def __init__(self):
        super().__init__()

        self.btn1_x_range = [10,10+12]
        self.btn2_x_range = [35,35+12]
        self.btn3_x_range = [60,60+12]
        self.btn_y_up = 40 + 35 + 4   # cy + r + 4
        self.btn_y_bottom = 40 + 35 + 4 + 12  # cy + r + 6 + width

        self.selectedBtn = None

        self.startAngle = 360
        self.timer = QTimer()
        self.timer.timeout.connect(self.timerEvent)


        self.props = {
            'zValue' : '0.0',
            '设备编号' : ''
        }


    def loadData(self,data):
        # 设置props
        self.props = data["props"]
        props = self.props
        self.setZValue(float(props["zValue"]))

        self.setPos(*data["pos"])


    def itemPropChanged(self,cfgName,newValue:str):
        oldValue = self.props[cfgName]
        self.props[cfgName] = newValue

        if cfgName == 'zValue':
            self.setZValue(float(newValue))

        elif cfgName == '设备编号':
            if newValue in gstore.deviceSn_to_item:
                QtWidgets.QMessageBox.warning(
                    window,
                    '警告',
                    '已经存在同名设备，请输入别的sn')
                return

            gstore.deviceSn_to_item.pop(oldValue, None)
            gstore.deviceSn_to_item[newValue] = self

        else :
            return

    def timerEvent(self):
        self.startAngle -= 20
        if self.startAngle < 0:
            self.startAngle += 360
        self.update()

    # 设定控件显示内容
    def paint(self, painter, option, widget):

        # 画笔
        painter.setPen(QtGui.QPen(QtGui.QColor('#4c8bbe'), 1))
        painter.setBrush(QtGui.QBrush(QtGui.QColor('#fff')))

        # 选中状态，画选中方框
        if self.isSelected():
            painter.drawRect(1, 1, 88, 98)

        # 圆心坐标
        cx, cy = 40, 40
        # 圆半径
        r = 35

        # 底座
        painter.drawPolygon(
            [
                QPoint(cx-30,cy+20),
                QPoint(cx-39,cy+55 ),
                QPoint(cx+39,cy+55 ),
                QPoint(cx+30,cy+20),
            ]
        )

        # 风箱体
        painter.drawEllipse(QPoint(cx, cy), r, r)
        # 喷嘴
        painter.drawRect(cx, cy-r, r+10, r-10)
        # 遮挡多余线条
        painter.setPen(QtGui.QPen(QtGui.QColor('white'), 2))
        painter.drawLine(cx, cy-r+2, cx, cy-10)
        painter.drawLine(cx, cy-10, cx+r-3, cy-10)

        # 风扇
        painter.setPen(QtGui.QPen(QtGui.QColor('gray'), 1))
        painter.drawPie(cx-25,cy-25, 50, 50, self.startAngle*16, 50*16)
        painter.drawPie(cx-25,cy-25, 50, 50, (self.startAngle+120)*16, 50*16)
        painter.drawPie(cx-25,cy-25, 50, 50, (self.startAngle+240)*16, 50*16)

        # 控制按钮
        btn1x, btn2x, btn3x = 10, 35, 60
        btnY = cy + r + 4
        width = 12

        colorWhite = QtGui.QColor('white')
        colorBlue  = QtGui.QColor('#6DCDDC')

        painter.setPen(QtGui.QPen(QtGui.QColor('#4c8bbe'), 1))

        if self.selectedBtn == 1:
            painter.setBrush(QtGui.QBrush(colorBlue))
        else:
            painter.setBrush(QtGui.QBrush(colorWhite))
        painter.drawRect(btn1x, btnY, width, width)


        if self.selectedBtn == 2:
            painter.setBrush(QtGui.QBrush(colorBlue))
        else:
            painter.setBrush(QtGui.QBrush(colorWhite))
        painter.drawRect(btn2x, btnY, width, width)

        if self.selectedBtn == 3:
            painter.setBrush(QtGui.QBrush(colorBlue))
        else:
            painter.setBrush(QtGui.QBrush(colorWhite))
        painter.drawRect(btn3x, btnY, width, width)

    def mouseDoubleClickEvent(self, e):
        # print(e.pos())

        x, y = e.pos().x(), e.pos().y()

        if not (self.btn_y_up <= y <= self.btn_y_bottom):
            return

        if self.btn1_x_range[0] <= x <= self.btn1_x_range[1]:
            if self.selectedBtn == 1: # 已经选中，双击停止
                self.selectedBtn = None
                self.timer.stop()
            else:
                self.selectedBtn = 1
                self.timer.stop()
                self.timer.start(200)
        elif self.btn2_x_range[0] <= x <= self.btn2_x_range[1]:
            if self.selectedBtn == 2: # 已经选中，双击停止
                self.selectedBtn = None
                self.timer.stop()
            else:
                self.selectedBtn = 2
                self.timer.stop()
                self.timer.start(70)
        elif self.btn3_x_range[0] <= x <= self.btn3_x_range[1]:
            if self.selectedBtn == 3: # 已经选中，双击停止
                self.selectedBtn = None
                self.timer.stop()
            else:
                self.selectedBtn = 3
                self.timer.stop()
                self.timer.start(30)
        else:
            return

        self.update()

        fanSpeed = self.selectedBtn if self.selectedBtn else 0
        connector.sendMsg('device_control', {
            "device-sn" : self.props['设备编号'],
            "operation" : "set-wind-pump-speed",
            "fan-speed" : fanSpeed
        })

    # 设定控件显示区域大小
    def boundingRect(self):
        return QRectF(0, 0, 90, 100)





class PictureItem(Item, QtWidgets.QGraphicsItemGroup):
    def __init__(self, pic=None, text=None):
        super().__init__()

        self.props = {
            '图标位置' : '0,0',
            '图标宽度' : '40',
            '文字内容' : text,
            '文字位置' : '10,50',
            '文字宽度' : '70',
            'zValue' : '0.0',
        }

        self.dso = DeviceSignalObject()
        self.dso.mdata_change.connect(self.handleNotify)

        # 从文件加载
        if pic is None:
            return

        self.pic = pic
        self.oriPixmap = QtGui.QPixmap(f'./images/{pic}.png')
        pixmap = self.oriPixmap.scaledToWidth(40, Qt.SmoothTransformation)

        self.picItem = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.picItem.setPos(0, 0)  # 设置其在parent的显示位置

        self.textItem = QtWidgets.QGraphicsTextItem()
        self.textItem.setDefaultTextColor(QtGui.QColor('#3687b8'))
        self.textItem.setFont(QtGui.QFont('微软雅黑', pointSize=9))
        self.textItem.setTextWidth(70)
        self.textItem.setPlainText(text)
        self.textItem.setPos(40, 10)  # 设置其在parent的显示位置

        # 添加子item到组item中
        self.addToGroup(self.picItem)
        self.addToGroup(self.textItem)

    def handleNotify(self):
        pass

    def loadData(self,data):
        # 设置props
        self.props = data["props"]
        props = self.props
        self.setZValue(float(props["zValue"]))

        # 其他设置
        self.pic = data["pic"]
        self.oriPixmap = QtGui.QPixmap(f'./images/{self.pic}.png')
        pixmap = self.oriPixmap.scaledToWidth(int(props['图标宽度']), Qt.SmoothTransformation)

        self.picItem = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.picItem.setPos(*[int(p) for p in props['图标位置'].split(',')])

        self.textItem = QtWidgets.QGraphicsTextItem()
        self.textItem.setDefaultTextColor(QtGui.QColor('#3687b8'))
        self.textItem.setFont(QtGui.QFont('微软雅黑', pointSize=9))
        self.textItem.setTextWidth(float(props['文字宽度']))
        self.textItem.setPlainText(props['文字内容'])
        self.textItem.setPos(*[int(p) for p in props['文字位置'].split(',')])  # 设置其在parent的显示位置

        # 添加子item到组item中
        self.addToGroup(self.picItem)
        self.addToGroup(self.textItem)

        self.setPos(*data["pos"])

        # 有 设备编号 属性的子item， 额外处理
        deviceSn = self.props.get('设备编号')
        if deviceSn:
            gstore.deviceSn_to_item[deviceSn] = self

    def itemPropChanged(self,cfgName,newValue:str):
        oldValue = self.props[cfgName]
        self.props[cfgName] = newValue


        if cfgName == '图标位置':
            self.picItem.setPos(*[int(p) for p in newValue.split(',')])
            self.removeFromGroup(self.picItem)
            self.addToGroup(self.picItem)

        elif cfgName == '图标宽度':
            pixmap = self.oriPixmap.scaledToWidth(int(newValue), Qt.SmoothTransformation)
            self.picItem.setPixmap(pixmap)

            self.removeFromGroup(self.picItem)
            self.addToGroup(self.picItem)

        elif cfgName == '文字内容':
            self.textItem.setPlainText(newValue)

            self.removeFromGroup(self.picItem)
            self.addToGroup(self.picItem)


        elif cfgName == '文字位置':
            self.textItem.setPos(*[int(p) for p in newValue.split(',')])

            self.removeFromGroup(self.picItem)
            self.addToGroup(self.picItem)


        elif cfgName == '文字宽度':
            self.textItem.setTextWidth(float(newValue))

            self.removeFromGroup(self.picItem)
            self.addToGroup(self.picItem)

        elif cfgName == 'zValue':
            self.setZValue(float(newValue))

        elif cfgName == '设备编号':
            if newValue in gstore.deviceSn_to_item:
                QtWidgets.QMessageBox.warning(
                    window,
                    '警告',
                    '已经存在同名设备，请输入别的sn')
                return

            gstore.deviceSn_to_item.pop(oldValue, None)
            gstore.deviceSn_to_item[newValue] = self

        else :
            return


    def toSaveData(self):

        data = super().toSaveData()
        data['pic'] = self.pic

        return data


class PictureItem_GasMeter(PictureItem):
    def __init__(self, pic=None, text=None):
        super().__init__(pic,text)

        self.props['设备编号'] = ''

    def handleNotify(self, msg):
        txt = f'''CO : {msg['CO']}
SO2 : {msg['SO2']}
HCL : {msg['HCl']}
        '''

        self.textItem.setPlainText(txt)


class PictureItem_TempMeter(PictureItem):
    def __init__(self, pic=None, text=None):
        super().__init__(pic,text)

        self.props['设备编号'] = ''


    def handleNotify(self, msg):
        txt = f'''温度 : {msg['temperature']}
湿度 : {msg['humidity']}
        '''

        self.textItem.setPlainText(txt)

class PictureItem_WindMeter(PictureItem):
    def __init__(self, pic=None, text=None):
        super().__init__(pic,text)

        self.props['设备编号'] = ''

    def handleNotify(self, msg):
        txt = f'''风速 : {msg['flow-rate']}
        '''

        self.textItem.setPlainText(txt)

class PictureItem_WaterMeter(PictureItem):
    def __init__(self, pic=None, text=None):
        super().__init__(pic,text)

        self.props['设备编号'] = ''

    def handleNotify(self, msg):
        txt = f'''流速 : {msg['flow-rate']}
水压 : {msg['water-pressure']}
        '''

        self.textItem.setPlainText(txt)

class PictureItem_WaterTank(PictureItem):
    def __init__(self, pic=None, text=None):
        super().__init__(pic,text)

        self.props['设备编号'] = ''

    def handleNotify(self, msg):
        txt = f'''水量 : {msg['water-amount']*100:.1f}%'''
        self.textItem.setPlainText(txt)


class PictureItem_Camera(PictureItem):
    def __init__(self, pic=None, text=None):
        super().__init__(pic,text)

        self.props['设备编号'] = ''
        self.props['视频流地址'] = 'rtmp://127.0.0.1/mytv/room01'

    def mouseDoubleClickEvent(self, e):
        rtmpUrl = self.props['视频流地址']
        cmd = f'{gstore.rtmpPlayer} {rtmpUrl}'
        import subprocess
        subprocess.Popen(args=cmd, shell=True)


class RectItem(Item, QtWidgets.QGraphicsRectItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '矩形宽度'     : '200',
            '矩形高度'     : '100',
            '填充颜色'     : '222, 241, 255, 0',
            '线条宽度'     : '1',
            '线条颜色'     : '0, 0, 0',
            'zValue'      : '0.0',
        }

    def loadData(self,data):
        # 设置props
        self.props = data["props"]
        props = self.props
        self.setPos(*data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置
        qrf = self.rect()
        qrf.setWidth(float(props["矩形宽度"]))
        qrf.setHeight(float(props["矩形高度"]))
        self.setRect(qrf)

        color = QtGui.QColor(*[int(v) for v in props["填充颜色"].replace(' ', '').split(',')])
        self.setBrush(QtGui.QBrush(color))

        pen = self.pen()
        pen.setWidth(int(props["线条宽度"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["线条颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

    def itemPropChanged(self,cfgName,cfgValue:str):
        self.props[cfgName] = cfgValue

        if cfgName == '矩形宽度':
            qrf = self.rect()
            qrf.setWidth(float(cfgValue))
            self.setRect(qrf)  # 重新设定

        elif cfgName == '矩形高度':
            qrf = self.rect()
            qrf.setHeight(float(cfgValue))
            self.setRect(qrf)  # 重新设定

        elif cfgName == '填充颜色':
            color = QtGui.QColor(  *[int(v) for v in cfgValue.replace(' ','').split(',')])
            self.setBrush(QtGui.QBrush(color))


        elif cfgName == '线条颜色':
            pen = self.pen()
            color = QtGui.QColor(  *[int(v) for v in cfgValue.replace(' ','').split(',')])
            pen.setColor(color)
            self.setPen(pen)


        elif cfgName == '线条宽度':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else :
            return


class EllipseItem(Item, QtWidgets.QGraphicsEllipseItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '椭圆宽度'     : '200',
            '椭圆高度'     : '100',
            '填充颜色'     : '222, 241, 255, 0',
            '线条宽度'     : '1',
            '线条颜色'     : '0, 0, 0',
            'zValue'      : '0.0',
        }

    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        self.setPos(*data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置
        qrf = self.rect()
        qrf.setWidth(float(props["椭圆宽度"]))
        qrf.setHeight(float(props["椭圆高度"]))
        self.setRect(qrf)

        color = QtGui.QColor(*[int(v) for v in props["填充颜色"].replace(' ', '').split(',')])
        self.setBrush(QtGui.QBrush(color))

        pen = self.pen()
        pen.setWidth(int(props["线条宽度"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["线条颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

    def itemPropChanged(self,cfgName,cfgValue:str):
        self.props[cfgName] = cfgValue

        if cfgName == '椭圆宽度':
            qrf = self.rect()
            qrf.setWidth(float(cfgValue))
            self.setRect(qrf)  # 重新设定

        elif cfgName == '椭圆高度':
            qrf = self.rect()
            qrf.setHeight(float(cfgValue))
            self.setRect(qrf)  # 重新设定

        elif cfgName == '填充颜色':
            color = QtGui.QColor(  *[int(v) for v in cfgValue.replace(' ','').split(',')])
            self.setBrush(QtGui.QBrush(color))


        elif cfgName == '线条颜色':
            pen = self.pen()
            color = QtGui.QColor(  *[int(v) for v in cfgValue.replace(' ','').split(',')])
            pen.setColor(color)
            self.setPen(pen)


        elif cfgName == '线条宽度':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else :
            return


class LineItem(Item, QtWidgets.QGraphicsLineItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '线宽' : '1',
            '颜色' : '0, 0, 0',
            '线长' : '200',
            '旋转角度' : '0',
            'zValue' : '0.0',
        }


    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        self.setPos(*data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置

        pen = self.pen()
        pen.setWidth(int(props["线宽"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

        line = QtCore.QLineF(0,0, 200, 0)
        line.setLength(float(props["线长"]))
        line.setAngle(float(props["旋转角度"]))
        self.setLine(line)


    def itemPropChanged(self,cfgName,cfgValue:str):
        self.props[cfgName] = cfgValue


        if cfgName == '线宽':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == '颜色':
            pen = self.pen()
            color = QtGui.QColor(  *[int(v) for v in cfgValue.replace(' ','').split(',')])
            pen.setColor(color)
            self.setPen(pen)


        elif cfgName == '线长':
            line = self.line()
            line.setLength(float(cfgValue))
            self.setLine(line)


        elif cfgName == '旋转角度':
            line = self.line()
            line.setAngle(float(cfgValue))
            self.setLine(line)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else :
            return

class TextItem(Item, QtWidgets.QGraphicsTextItem):
    html_templt = '''<div style='color:$color$;
                font-size:$size$px;
                font-weight:$weight$;
                font-family:$font$;
                '>$content$</div>'''

    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '内容' : '文字内容',
            '颜色' : 'black',
            '大小' : '18',
            '字体' : 'fangsong',
            '字粗' : '200',
            'zValue' : '0.0',
        }


    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        self.setPos(*data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置

        html = self.html_templt.replace('$content$', self.props['内容'])
        html = html.replace('$color$', self.props['颜色'])
        html = html.replace('$size$', self.props['大小'])
        html = html.replace('$font$', self.props['字体'])
        html = html.replace('$weight$', self.props['字粗'])

        self.setHtml(html)


    def itemPropChanged(self,cfgName,cfgValue:str):
        self.props[cfgName] = cfgValue


        if cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else :

            html = self.html_templt.replace('$content$', self.props['内容'])
            html = html.replace('$color$', self.props['颜色'])
            html = html.replace('$size$', self.props['大小'])
            html = html.replace('$font$', self.props['字体'])
            html = html.replace('$weight$', self.props['字粗'])

            self.setHtml(html)



class DragLabel(QtWidgets.QLabel):

    def mouseMoveEvent(self, e):

        if e.buttons() != Qt.LeftButton:
            return

        mimeData = QtCore.QMimeData()

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        drag.exec(Qt.DropActions.MoveAction)





class DnDGraphicView(QtWidgets.QGraphicsView):

    def __init__(self, *args):
        super().__init__(*args)
        self.lastDropItem = None

    def dragMoveEvent(self, e):
        pass


    def dragEnterEvent(self, e):
        src = e.source()
        if hasattr(src, 'dndinfo') :
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):

        if window.mode == 'view':
            QtWidgets.QMessageBox.warning(
                self,
                '禁止',
                '查看模式不能添加Item')
            return


        name = e.source().dndinfo['name']
        # print(name)
        if name == '矩形':
            item = RectItem(0,0, 200, 100)
        elif name == '椭圆':
            item = EllipseItem(0,0, 200, 100)
        elif name == '线条':
            item = LineItem(0,0, 200, 0)
        elif name == '文字':
            item = TextItem("文字内容")
        elif name == '水箱':
            item = WaterTankItem()
        elif name == '风泵':
            item = WindPumpItem()

        else:
            if name == 'gas-meter':
                item = PictureItem_GasMeter(name, name)
            elif name == 'temp-meter':
                item = PictureItem_TempMeter(name, name)
            elif name == 'wind-meter':
                item = PictureItem_WindMeter(name, name)
            elif name == 'water-meter':
                item = PictureItem_WaterMeter(name, name)
            elif name == 'water-tank':
                item = PictureItem_WaterTank(name, name)
            elif name == 'camera':
                item = PictureItem_Camera(name, name)
            else:
                item = PictureItem(name, name)



        self.scene().addItem(item)

        # 设置一些属性
        item.setPos(e.position())

        # 设置item可以移动
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        # 设置item可以选中
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        # 设置item可以聚焦，这样才会有键盘按键回调keyPressEvent
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)

        # 设置为选中
        if self.lastDropItem:
            try:
                self.lastDropItem.setSelected(False)
            except:
                pass
        item.setSelected(True)
        self.lastDropItem = item

    # 该方法使得view 改变大小时（比如拖拽主窗口resize）， scene大小跟着变化
    # 否则，view和secen大小不一致， 拖放item 时，位置就不对了。
    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = event.size()
        self.setSceneRect(0, 0, size.width(), size.height())


class MWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.resize(1800, 1000)

        gstore.main_window = self

        self.brush_edit = QtGui.QBrush(QtGui.QColor(0xfaf3f3 ), bs=Qt.CrossPattern)
        self.brush_view   = QtGui.QBrush(QtGui.QColor(0xfafafa ), bs=Qt.SolidPattern)

        # 设置标题栏
        self.setWindowTitle('白月黑羽 - 矿采监控系统')

        # central Widget
        centralWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(centralWidget)

        # central Widget 里面的 主 layout
        self.mainLayout = QtWidgets.QHBoxLayout(centralWidget)

        # 左边区
        self.setupLeftPane()


        # 参数 Qt.Vertical 是垂直分裂， Qt.Horizontal是水平分裂
        self.splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.mainLayout.addWidget(self.splitter)

        # 中间绘制区
        self.setupCanvas()
        self.splitter.insertWidget(0, self.view)

        self.setupRightPane()
        self.splitter.insertWidget(1, self.propTable)

        #  设置每个部分的宽度，单位是像素
        self.splitter.setSizes([400, 150])

        self.setupToolBar()

        self.dso = DeviceSignalObject()
        self.dso.mdata_change.connect(self.handle_stats)

    def setupToolBar(self):

        # 创建 工具栏 对象 并添加
        toolbar = QtWidgets.QToolBar(self)
        self.addToolBar(toolbar)

        # 添加 工具栏 条目Action
        actionSave = toolbar.addAction(qta.icon("ph.download-light",color='green'),"保存")
        actionSave.triggered.connect(self.save)

        actionLoad = toolbar.addAction(qta.icon("ph.upload-light",color='green'),"加载")
        actionLoad.triggered.connect(self.load)

        actionDelItem = toolbar.addAction(qta.icon("ph.x-square-light",color='green'),"删除")
        actionDelItem.triggered.connect(self.delItem)

        actionDelAllItem = toolbar.addAction(qta.icon("ph.trash-light",color='green'),"清空")
        actionDelAllItem.triggered.connect(self.delAllItems)

        self.icon_view = qta.icon("ph.eye-light",color='green')
        self.icon_edit = qta.icon("ph.tree-structure-light",color='green')


        self.actionSwitchMode = toolbar.addAction(self.icon_view,"操作模式切换")
        self.actionSwitchMode.triggered.connect(self.switchMode)
        # 当前操作模式
        self.mode = 'view'  # view or edit

    def switchMode(self):
        if self.mode == 'edit':
            self.mode = 'view'
            self.actionSwitchMode.setIcon(self.icon_view)
            self.view.setBackgroundBrush(self.brush_view)

            for item in self.scene.items():
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)

        else:
            self.mode = 'edit'
            self.actionSwitchMode.setIcon(self.icon_edit)
            self.view.setBackgroundBrush(self.brush_edit)

            for item in self.scene.items():
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)

    def load(self):
        with open('cfg.json', 'r', encoding='utf8') as f:
            content = f.read()

        data : list = json.loads(content)
        data.reverse()

        for itemData in data:
            typeName = itemData["type"]

            theClass = globals()[typeName]
            item = theClass()
            item.loadData(itemData)
            self.scene.addItem(item)

            # 设置item可以移动
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True if self.mode == 'edit' else False)
            # 设置item可以选中
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            # 设置item可以聚焦，这样才会有键盘按键回调keyPressEvent
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)


    def save(self):

        choice = QtWidgets.QMessageBox.question(
            self,
            '确认',
            '确定替换原来的元件图吗？')

        if choice != QtWidgets.QMessageBox.Yes:
            return

        itemSaveDataList = []
        for item in self.scene.items():
            if hasattr(item, 'toSaveData'):
                saveData = item.toSaveData()
                itemSaveDataList.append(saveData)

        # print(itemSaveDataList)


        content = json.dumps(itemSaveDataList, indent=2, ensure_ascii=False)
        with open('cfg.json', 'w', encoding='utf8') as f:
            f.write(content)

    def delItem(self):
        if self.mode == 'view':
            QtWidgets.QMessageBox.warning(
                self,
                '禁止',
                '查看模式不能删除Item')
            return

        items = self.scene.selectedItems()
        for item in items:
            # self.scene.removeItem(item)
            shiboken6.delete(item)

            deviceSn = item.props.get('设备编号')
            if deviceSn:
                gstore.deviceSn_to_item.pop(deviceSn, None)


    def delAllItems(self):
        if self.mode == 'view':
            QtWidgets.QMessageBox.warning(
                self,
                '禁止',
                '查看模式不能清空')
            return
        # self.scene.clear()
        for item in self.scene.items():
            if hasattr(item, 'toSaveData'):
                shiboken6.delete(item)

        gstore.deviceSn_to_item.clear()

    def setupLeftPane(self):
        leftLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(leftLayout)

        # 位图item
        pixmapLayout = QtWidgets.QGridLayout()
        leftLayout.addLayout(pixmapLayout)

        row, col = 0, 0
        for picName in PIC_LIST:

            # 初始参数就是图片路径名
            pixmap = QtGui.QPixmap(f'./images/{picName}.png')
            # 设定图片缩放大小，这里是50个像素的宽度，高度也会等比例缩放
            pixmap = pixmap.scaledToWidth(40, Qt.SmoothTransformation)

            label = DragLabel()
            label.setToolTip(picName)
            label.dndinfo = {'name': picName}

            # 设置label显示的pixmap
            label.setPixmap(pixmap)

            pixmapLayout.addWidget(label, row, col)  # 添加到第1行，第1列

            if col == 1:
                row += 1
                col = 0
            else:
                col += 1



        # 基本形状 item
        basicItemLayout = QtWidgets.QGridLayout()
        leftLayout.addLayout(basicItemLayout)

        row, col = 0, 0
        BASICITEM_LIST = ['矩形', '线条', '椭圆', '文字', '水箱', '风泵']
        for name in BASICITEM_LIST:

            label = DragLabel(name)
            label.setToolTip(name)
            label.setStyleSheet("background-color:#fff;color:#798699;font-weight: bold;")
            label.setFixedSize(40,40)
            label.setAlignment(Qt.AlignCenter)
            label.dndinfo = {'name': name}

            basicItemLayout.addWidget(label, row, col)  # 添加到第1行，第1列

            if col == 1:
                row += 1
                col = 0
            else:
                col += 1

        leftLayout.addStretch()

    def setupCanvas(self):
        self.scene = QtWidgets.QGraphicsScene(0, 0, 800, 600)

        self.view = DnDGraphicView(self.scene)
        # 设定去锯齿，否则椭圆边线会有明显的锯齿
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setBackgroundBrush(self.brush_view)

        # 统计表

        my_font = QtGui.QFont()
        my_font.setPointSize(11)

        self.pw1 = pg.PlotWidget(background='#fafafa')
        self.pw1.resize(350, 250)
        # 设置图表标题
        self.pw1.setTitle("产量: 红-煤1 | 绿-煤2", color='#008080', size='12pt')
        # 设置上下左右的label
        self.pw1.setLabel("left", "单位 : 吨")
        self.pw1.setLabel("bottom", "时间")
        self.pw1.getAxis("left").label.setFont(my_font)
        self.pw1.getAxis("bottom").label.setFont(my_font)
        self.pw1.showGrid(True,True)
        self.curve1_1 = self.pw1.plot(pen=pg.mkPen('r', width=1))
        self.curve1_2 = self.pw1.plot(pen=pg.mkPen('#3D7D4A', width=1))
        figure1 = self.scene.addWidget(self.pw1)
        figure1.setPos(20,680)

        self.pw2 = pg.PlotWidget(background='#fafafa')
        self.pw2.resize(350, 250)
        # 设置图表标题
        self.pw2.setTitle("水消耗图", color='#008080', size='12pt')
        # 设置上下左右的label
        self.pw2.setLabel("left", "单位 : 吨")
        self.pw2.setLabel("bottom", "时间")
        self.pw2.getAxis("left").label.setFont(my_font)
        self.pw2.getAxis("bottom").label.setFont(my_font)
        self.pw2.showGrid(True,True)
        self.curve2 = self.pw2.plot(pen=pg.mkPen('#4B7696', width=1))
        figure2 = self.scene.addWidget(self.pw2)
        figure2.setPos(420,680)


        self.pw3 = pg.PlotWidget(background='#fafafa')
        self.pw3.resize(350, 250)
        # 设置图表标题
        self.pw3.setTitle("电消耗图", color='#008080', size='12pt')
        # 设置上下左右的label
        self.pw3.setLabel("left", "单位 : 千瓦时")
        self.pw3.setLabel("bottom", "时间")
        self.pw3.getAxis("left").label.setFont(my_font)
        self.pw3.getAxis("bottom").label.setFont(my_font)
        self.pw3.showGrid(True,True)
        self.curve3 = self.pw3.plot(pen=pg.mkPen('#964B4B', width=1))
        figure3 = self.scene.addWidget(self.pw3)
        figure3.setPos(820,680)



    def setupRightPane(self):
        table = QtWidgets.QTableWidget(0,2,self)

        table.verticalHeader().hide() # 隐藏垂直表头
        table.setHorizontalHeaderLabels(["属性", "值"])
        # 设定第1列的宽度为 180像素
        table.setColumnWidth(0, 180)
        tableHeader = table.horizontalHeader()
        tableHeader.setStretchLastSection(True)

        tableStyle = '''
        QTableWidget {
            gridline-color: #e0e0e0;
        }

        QHeaderView::section {     
            background-color: #f8f8f8;
            border-top: 0px solid #e0e0e0;
            border-left: 0px solid #e0e0e0;
            border-right: 1px solid #e0e0e0;
            border-bottom: 1px solid #e0e0e0;
        }
        '''

        table.setStyleSheet(tableStyle)

        self.propTable = table


    def setPropTable(self, props):
        table = self.propTable

        # 先解除 单元格改动信号处理函数
        try:
            table.cellChanged.disconnect(self.itemPropChanged)
        except:
            pass

        table.setRowCount(0) # 删除原来的内容

        row = 0
        for name,value in props.items():
            table.insertRow(row)
            item = QtWidgets.QTableWidgetItem(name)
            item.setFlags(Qt.ItemIsEnabled)
            table.setItem(row, 0, item)
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(value))
            row += 1

        # 再指定单元格改动信号处理函数
        table.cellChanged.connect(self.itemPropChanged)

    def itemPropChanged(self, row, column):
        # 获取更改内容
        cfgName = self.propTable.item(row, 0).text()  # 首列为配置名称
        cfgValue = self.propTable.item(row, column).text()

        items = self.scene.selectedItems()
        if len(items) != 1:
            print('item未选中状态 或 多选')
            return

        selected = items[0]
        selected.itemPropChanged(cfgName,cfgValue)


    def handle_stats(self,msg):
        self.curve1_1.setData(msg['coal-1'])
        self.curve1_2.setData(msg['coal-2'])
        self.curve2.setData(msg['w-used'])
        self.curve3.setData(msg['e-used'])

# 启动通信进程
from connector import startCommunicationThread
startCommunicationThread()


app = QtWidgets.QApplication()
app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Round)

window = MWindow()
window.show()


app.exec()
