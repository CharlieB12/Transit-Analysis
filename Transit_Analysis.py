from qgis.gui import QgsMapToolIdentify
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QTabWidget,
    QWidget,
    QDockWidget,
    QMessageBox,
    QLineEdit
)
from qgis.core import QgsWkbTypes, QgsProject, edit


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
                feature = r.mFeature
                if feature.geometry().type() == QgsWkbTypes.PointGeometry:
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

class SelectTool2(SelectTool):
    def __init__(self, canvas, labelwidget, textwidget, cursor=Qt.ArrowCursor):
        SelectTool.__init__(self, canvas)
        self.labelwidget = labelwidget
        self.textwidget = textwidget
        self.setCursor(cursor)
    def printFeatures(self, layer):
        selection = layer.selectedFeatures()
        textmsg = 'Attributes: \n'
        for f in selection:
            textmsg += str(f.attributes()) + '\n'
        self.labelwidget.setText(layer.name())
        self.textwidget.setTextColor(QColor('blue'))
        self.textwidget.setText(textmsg)

class InfoTabs2(QTabWidget):
    def __init__(self, parent=None):
        super(InfoTabs2, self).__init__(parent)

        #First tab on widget
        tab1 = QWidget()
        self.addTab(tab1, "Controls")
        layout1 = QVBoxLayout()

        #Button to clear seleced points
        self.button = QPushButton('Clear Selection')
        self.button.clicked.connect(self.on_button_clicked)
        layout1.addWidget(self.button)
        
        #Text box for buffer radius in miles
        self.buffer_radius_input = QLineEdit()
        self.buffer_radius_input.setPlaceholderText("Enter Buffer Radius (Miles)")
        layout1.addWidget(self.buffer_radius_input)

        #Button to apply buffer
        self.apply_buffer_button = QPushButton("Apply Buffer")
        self.apply_buffer_button.clicked.connect(self.apply_buffer)
        layout1.addWidget(self.apply_buffer_button)


        tab1.setLayout(layout1)

        #Second tab on widget
        tab2 = QWidget()
        self.addTab(tab2, "Information")
        layout2 = QVBoxLayout()

        self.toolLabel = QLabel("Label text example")
        layout2.addWidget(self.toolLabel)

        self.toolText = QTextEdit("<b>Useful info goes here</b>")
        layout2.addWidget(self.toolText)

        tab2.setLayout(layout2)

        self.setCurrentIndex(0) #controls show first

    def on_button_clicked(self):
        l = iface.activeLayer()
        if l is not None:
            l.selectByIds([])
        self.toolText.setText('all cleared')
        iface.messageBar().pushMessage('Information', 'All should be gone by now!', level=Qgis.Info)
    
    # Function to apply buffer to selected points
    def apply_buffer(self):
        #Checks if radius is numeric
        buffer_radius_text = self.buffer_radius_input.text()
        try:
            buffer_radius = float(buffer_radius_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric value for the buffer radius.")
            return

        #Gets the active layer
        layer = iface.activeLayer()

        #Checks for valid layer and selections
        if layer is None:
            QMessageBox.warning(self, "No Layer Selected", "Please select a layer.")
            return
        if layer.geometryType() != QgsWkbTypes.PointGeometry:
            QMessageBox.warning(self, "Invalid Layer Type", "Please select a point layer.")
            return
        if not layer.selectedFeatures():
            QMessageBox.warning(self, "No Points Selected", "Please click on points to select them.")
            return
        
        #Create a driver to make new shapefiles
        from osgeo import ogr
        driver = ogr.GetDriverByName('ESRI Shapefile')
        
        #Function to convert selected points into a new layer
        def selected_features_to_layer(selected_features, target_crs=None):
            # Create a new memory layer
            layer = QgsVectorLayer("Point", "Selected Features", "memory")

            # Define attribute fields
            fields = selected_features[0].fields() if selected_features else []

            # Add fields to the new layer
            layer_data_provider = layer.dataProvider()
            layer_data_provider.addAttributes(fields)
            layer.updateFields()

            # If a target CRS is specified, set it for the layer
            if target_crs:
                layer.setCrs(target_crs)

            # Start editing the layer
            layer.startEditing()

            # Add features to the new layer
            for feature in selected_features:
                # Create a new feature
                new_feature = QgsFeature()
                new_feature.setGeometry(feature.geometry())
                new_feature.setAttributes(feature.attributes())

                # Add the new feature to the layer
                layer.addFeature(new_feature)

            # Commit changes
            layer.commitChanges()

            return layer
            
    
        selected_features = iface.activeLayer().selectedFeatures()
        new_layer = selected_features_to_layer(selected_features)
        
        #Apply buffer to the new layer (selected points)
        buffer_output = QgsProcessingUtils.generateTempFilename('/buffer.shp')
        if os.path.exists(buffer_output):
            driver.DeleteDataSource(buffer_output)
        
        buffer = processing.run('native:buffer', {
          'INPUT': new_layer,
          'DISTANCE': buffer_radius * 1609,
          'SEGMENTS': 5,
          'OUTPUT': buffer_output})
        
        buffer_layer = QgsVectorLayer(buffer_output, 'Buffer', 'ogr')
        # Checks if buffer layer is correct crs
        if not buffer_layer.isValid():
            print("Buffer layer is not valid. Check if the output file was created correctly.")
        else:
            # Set a valid CRS for the buffer layer
            buffer_layer.setCrs(layer.crs())
        
        #add buffer layer to map
        QgsProject.instance().addMapLayer(buffer_layer)
        
        
    def getToolLabel(self):
        return self.toolLabel
    def getToolText(self):
        return self.toolText
        
        
dwtooltab = QDockWidget("Select Tool Info Board")
dwtooltab.setWidget(InfoTabs2())

toolText = dwtooltab.widget().getToolText()
toolLabel = dwtooltab.widget().getToolLabel()

seltool2 = SelectTool2(iface.mapCanvas(), toolLabel, toolText)
iface.mapCanvas().setMapTool(seltool2)

iface.addDockWidget(Qt.RightDockWidgetArea, dwtooltab)