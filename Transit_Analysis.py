class SelectTool(QgsMapToolIdentify):
    def __init__(self, canvas):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        self.setCursor(Qt.ArrowCursor)
    def canvasReleaseEvent(self, event): # mouse release
        l = iface.activeLayer()
        if l is None:
            return
        results = self.identify(event.x(), event.y(), [l], QgsMapToolIdentify.TopDownStopAtFirst)
        selected = [f.id() for f in l.selectedFeatures()]
        if len(results) > 0:
            for r in results:
                id = r.mFeature.id()
                if not id in selected:
                    selected.append(id)
                else:
                    selected.remove(id)
        else:
            selected = []
        l.selectByIds(selected)
        self.printFeatures(l)
    def printFeatures(self, layer):
        selection = layer.selectedFeatures()
        for f in selection:
            print(f.attributes())
            

class InfoTabs(QTabWidget):
    def __init__(self, parent=None):
        super(InfoTabs, self).__init__(parent)
        tab1 = QWidget()
        tab2 = QWidget()
        self.addTab(tab1, "Layers")
        self.addTab(tab2, "Features")
        #
        self.toolLabel = QLabel("Label text example")
        layout1 = QVBoxLayout()
        layout1.addWidget(self.toolLabel)
        tab1.setLayout(layout1)
        #
        self.toolText = QTextEdit("<b>Useful info goes here</b>")
        layout2 = QVBoxLayout()
        layout2.addWidget(self.toolText)
        tab2.setLayout(layout2)
    def getToolLabel(self):
        return self.toolLabel
    def getToolText(self):
        return self.toolText