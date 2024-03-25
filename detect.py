from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt


PIC_LIST = [
    "gas-meter",
    "temp-meter",
    "wind-meter",
    "water-meter",
    "water-valve",
    "water-tank",
    "air-pump",
    "camera",
    "hydrant",
    "pipeline",
]


class DragLabel(QtWidgets.QLabel):

    def mouseMoveEvent(self, e):

        if e.buttons() != Qt.LeftButton:
            return

        mimeData = QtCore.QMimeData()

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        drag.exec(Qt.DropActions.MoveAction)


class DnDGraphicView(QtWidgets.QGraphicsView):
    def dragMoveEvent(self, e):
        pass

    def dragEnterEvent(self, e):

        if True:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):

        picName = e.source().dndinfo["name"]
        

        pixmap = QtGui.QPixmap(f"./images/{picName}.png")

        pixmap = pixmap.scaledToWidth(40, Qt.SmoothTransformation)

        item = QtWidgets.QGraphicsPixmapItem(pixmap)

        self.scene().addItem(item)

        item.setPos(e.position())

        # 设置item可以移动
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        # 设置item可以选中
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        # 设置item可以聚焦，这样才会有键盘按键回调keyPressEvent
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)

    # 该方法使得view 改变大小时（比如拖拽主窗口resize）， scene大小跟着变化
    # 否则，view和secen大小不一致， 拖放item 时，位置就不对了。
    def resizeEvent(self, event):
      
        super().resizeEvent(event)
        size = event.size()
        self.setSceneRect(0, 0, size.width(), size.height())


class MWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.resize(1000, 800)

        # central Widget
        centralWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(centralWidget)

        # central Widget 里面的 主 layout
        self.mainLayout = QtWidgets.QHBoxLayout(centralWidget)

        # 左边区
        self.setupLeftPane()

        # 中间绘制区
        self.setupCanvas()

    def setupLeftPane(self):
        leftLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(leftLayout)

        pixmapLayout = QtWidgets.QGridLayout()
        leftLayout.addLayout(pixmapLayout)
        leftLayout.addStretch()

        row, col = 0, 0
        for picName in PIC_LIST:

            # 初始参数就是图片路径名
            pixmap = QtGui.QPixmap(f"./images/{picName}.png")
            # 设定图片缩放大小，这里是50个像素的宽度，高度也会等比例缩放
            pixmap = pixmap.scaledToWidth(40, Qt.SmoothTransformation)

            label = DragLabel()
            label.dndinfo = {"name": picName}

            # 设置label显示的pixmap
            label.setPixmap(pixmap)

            pixmapLayout.addWidget(label, row, col)

            if col == 1:
                row += 1
                col = 0
            else:
                col += 1

    def setupCanvas(self):
        self.scene = QtWidgets.QGraphicsScene(0, 0, 800, 600)
        self.view = DnDGraphicView(self.scene)
        self.mainLayout.addWidget(self.view)


app = QtWidgets.QApplication()
app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Round)

window = MWindow()
window.show()
app.exec()
