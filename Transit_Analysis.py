from qgis.gui import QgsMapToolIdentify
from PyQt5.QtCore import Qt, QVariant
import math
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
from qgis.core import (
    QgsWkbTypes,
    QgsProject,
    edit,
    QgsVectorLayer,
    QgsField,
    QgsFields,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsMessageLog
    )

#Class for enabling the selection of points
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

#Class for populating our info tab with selected points
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

#Class for creating the tabs for tool
class InfoTabs2(QTabWidget):
    def __init__(self, parent=None):
        super(InfoTabs2, self).__init__(parent)

        #First tab on widget
        tab1 = QWidget()
        self.addTab(tab1, "Controls")
        layout1 = QVBoxLayout()
        
        '''
        Section for buttons and dropdowns
        '''
        
        #Button to clear seleced points
        self.button = QPushButton('Clear Selection')
        self.button.clicked.connect(self.on_button_clicked)
        layout1.addWidget(self.button)
        

        #Dropdown for selecting polygon layer
        self.polygon_dropdown = QComboBox()
        self.polygon_dropdown.addItem("Select Polygon Layer")
        layout1.addWidget(self.polygon_dropdown)
        
        #Dropdown for polygoin join field
        self.poly_join_dropdown = QComboBox()
        self.poly_join_dropdown.addItem("Select Polygon Join Layer")
        layout1.addWidget(self.poly_join_dropdown)
        
        #Dropdown for selecting table layer
        self.table_dropdown = QComboBox()
        self.table_dropdown.addItem("Select Table Layer")
        layout1.addWidget(self.table_dropdown)
        
        #Dropdown for selecting population field
        self.pop_field_dropdown = QComboBox()
        self.pop_field_dropdown.addItem("Select Population Field")
        layout1.addWidget(self.pop_field_dropdown)
        
        #Dropdown for population join field
        self.pop_join_dropdown = QComboBox()
        self.pop_join_dropdown.addItem("Select Table Join Field")
        layout1.addWidget(self.pop_join_dropdown)
        
        #Dropdown for area field
        self.area_dropdown = QComboBox()
        self.area_dropdown.addItem("Select Area Field")
        layout1.addWidget(self.area_dropdown)
        
        #Text box for buffer radius in miles
        self.buffer_radius_input = QLineEdit()
        self.buffer_radius_input.setPlaceholderText("Enter Buffer Radius (Miles)")
        layout1.addWidget(self.buffer_radius_input)

        #Button to calculate coverage
        self.apply_buffer_button = QPushButton("Calculate Coverage")
        self.apply_buffer_button.clicked.connect(self.calculate_coverage)
        layout1.addWidget(self.apply_buffer_button)
        
        # Get all layers in the project
        self.layers = QgsProject.instance().mapLayers().values()

        # Filter layers by geometry type and populate dropdowns
        for layer in self.layers:
            if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.polygon_dropdown.addItem(layer.name(), layer)
            elif layer.geometryType() != QgsWkbTypes.PointGeometry and layer.geometryType() != QgsWkbTypes.PolygonGeometry:
                self.table_dropdown.addItem(layer.name(), layer)
        
        #Update area dropwdown with polygon fields
        self.polygon_dropdown.currentIndexChanged.connect(self.populate_polygon_fields)
        self.table_dropdown.currentIndexChanged.connect(self.populate_table_fields)

        tab1.setLayout(layout1)

        #Second tab on widget
        tab2 = QWidget()
        self.addTab(tab2, "Selection Info")
        layout2 = QVBoxLayout()

        self.toolLabel = QLabel("Selected points")
        layout2.addWidget(self.toolLabel)

        self.toolText = QTextEdit("<b>No points selected</b>")
        layout2.addWidget(self.toolText)

        tab2.setLayout(layout2)

        self.setCurrentIndex(0) #controls show first
    
    '''
    Section for populating empty dropdowns
    '''
    #Gets all the fields of selected polygon layer in dropdown box
    def populate_polygon_fields(self):
        #Clear existing items in the area field dropdown
        self.area_dropdown.clear()
        self.area_dropdown.addItem("Select Area Field")
        #Clear existing items in the polygon join field dropdown
        self.poly_join_dropdown.clear()
        self.poly_join_dropdown.addItem("Select Polygon Join Field")
        
        #Get the selected polygon layer
        selected_polygon_layer = self.polygon_dropdown.currentData()

        #Populate the dropdowns with fields of the selected polygon layer
        if selected_polygon_layer:
            fields = selected_polygon_layer.fields()
            for field in fields:
                self.area_dropdown.addItem(field.name(), field)
                self.poly_join_dropdown.addItem(field.name(), field)

    #Gets all the fields of selected table in table dropdown
    def populate_table_fields(self):
        #Clear existing items in the table join dropdown
        self.pop_join_dropdown.clear()
        self.pop_join_dropdown.addItem("Select Table Join Field")
        #Clear existing items in the population field dropdown
        self.pop_field_dropdown.clear()
        self.pop_field_dropdown.addItem("Select Population Field")
        
        #Get the selected table layer
        selected_table_layer = self.table_dropdown.currentData()
        
        #Populate the dropdowns with fields of the selected table layer
        if selected_table_layer:
            fields = selected_table_layer.fields()
            for field in fields:
                self.pop_join_dropdown.addItem(field.name(), field)
                self.pop_field_dropdown.addItem(field.name(), field)
    
    
    #Clears selected points from map
    def on_button_clicked(self):
        l = iface.activeLayer()
        if l is not None:
            l.selectByIds([])
        self.toolText.setText('all cleared')
        iface.messageBar().pushMessage('Information', 'Selected Points Cleared', level=Qgis.Info)
        
    
    '''
    Geoprocessing section
    '''
    #Function to calculate coverage of seleced points
    def calculate_coverage(self):
        
        #Grabs layers in dropdown boxes
        polygon_data = self.polygon_dropdown.currentData()
        poly_join = self.poly_join_dropdown.currentData()
        population = self.table_dropdown.currentData()
        pop_fld = self.pop_field_dropdown.currentData()
        pop_join = self.pop_join_dropdown.currentData()
        area_fld = self.area_dropdown.currentData()
        
        
        
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
            #Create a new memory layer
            layer = QgsVectorLayer("Point", "Selected Features", "memory")

            #Define attribute fields
            fields = selected_features[0].fields() if selected_features else []

            #Add fields to the new layer
            layer_data_provider = layer.dataProvider()
            layer_data_provider.addAttributes(fields)
            layer.updateFields()

            #If a target CRS is specified, set it for the layer
            if target_crs:
                layer.setCrs(target_crs)

            #Start editing the layer
            layer.startEditing()

            #Add features to the new layer
            for feature in selected_features:
                #Create a new feature
                new_feature = QgsFeature()
                new_feature.setGeometry(feature.geometry())
                new_feature.setAttributes(feature.attributes())

                #Add the new feature to the layer
                layer.addFeature(new_feature)

            #Commit changes
            layer.commitChanges()

            return layer
            
        #Grabs the selected points
        selected_features = iface.activeLayer().selectedFeatures()
        #Creates new layer based on points
        new_layer = selected_features_to_layer(selected_features)

        '''
        Buffer
        '''
        #Apply buffer to the new layer (selected points)
        buffer_output = QgsProcessingUtils.generateTempFilename('/buffer.shp')
        if os.path.exists(buffer_output):
            driver.DeleteDataSource(buffer_output)
        

        buffer = processing.run('native:buffer', {
          'INPUT': new_layer,
          'DISTANCE': buffer_radius * 1609,
          'SEGMENTS': 5,
          'OUTPUT': buffer_output})
        
        buffer_layer = QgsVectorLayer(buffer_output, 'Coverage', 'ogr')
        buffer_layer.setCrs(layer.crs())
        
        QgsProject.instance().addMapLayer(buffer_layer)
        
        '''
        Add areas to buffer
        '''
        buffer_area_output = QgsProcessingUtils.generateTempFilename('/buffer_area.shp')
        if os.path.exists(buffer_area_output):
            driver.DeleteDataSource(buffer_area_output)
            
        buffer_area_out = processing.run('qgis:exportaddgeometrycolumns', {
            'INPUT': buffer_layer,
            'CALC_METHOD': '0',
            'OUTPUT': buffer_area_output})
        
        buffer_area = QgsVectorLayer(buffer_area_output, 'Buffer Area', 'ogr')
        
        
        #Get total buffer area
        total_buffer_area = 0
        for f in buffer_area.getFeatures():
            total_buffer_area += f['area']
        

        '''
        Intersecting buffers on eachother to get overlapping coverage
        '''
        #Finds first occurence of numeric field for self intersect funtion
        layer_id = ''
        for field in buffer_layer.fields():
            #4 represents integer
            if field.type() == 4:
                layer_id = field.name()
                break
        
        buffer_self_intersect_output = QgsProcessingUtils.generateTempFilename('/self_intersect.shp')
        if os.path.exists(buffer_self_intersect_output):
            driver.DeleteDataSource(buffer_self_intersect_output)
        
        self_intersect = processing.run('saga:polygonselfintersection', {
            'POLYGONS': buffer_layer,
            'INTERSECT': buffer_self_intersect_output,
            'ID': layer_id})
        
        self_intersect_layer = QgsVectorLayer(buffer_self_intersect_output, 'Self Intersect', 'ogr')
        self_intersect_layer.setCrs(buffer_layer.crs())
        
        '''
        Filter out the non overlapping geometry
        '''
        provider = self_intersect_layer.dataProvider()
        #All the overlapped geometries have a layer_id of 0
        non_overlap = [f.id() for f in self_intersect_layer.getFeatures() if f[layer_id] > 0]
        res = provider.deleteFeatures(non_overlap)
        layer.updateExtents()
        layer.triggerRepaint()
        
        '''
        Dissolve overlaps
        '''
        dissolve_output = QgsProcessingUtils.generateTempFilename('/dissolve.shp')
        if os.path.exists(dissolve_output):
            driver.DeleteDataSource(dissolve_output)
        
        dissolve_layer = processing.run('qgis:dissolve', {
            'INPUT':self_intersect_layer,
            'FIELD':layer_id,
            'OUTPUT': dissolve_output})
        
        dissolve = QgsVectorLayer(dissolve_output, 'Overlapping Coverage', 'ogr')

        '''
        Intersect Overlaps with tract
        '''
        overlap_intersect_output = QgsProcessingUtils.generateTempFilename('/overlap_intersect.shp')
        if os.path.exists(overlap_intersect_output):
            driver.DeleteDataSource(overlap_intersect_output) 
        
        overlap_intersect = processing.run('qgis:intersection', {
            'INPUT': polygon_data,
            'OVERLAY': dissolve,
            'OUTPUT': overlap_intersect_output})
        
        overlap_intersect_layer = QgsVectorLayer(overlap_intersect_output, 'Overlapping Coverage Intersection', 'ogr')
        overlap_intersect_layer.setCrs(buffer_layer.crs())
        
        '''
        Join population with intersected overlaps
        '''
        joined_layer_output = QgsProcessingUtils.generateTempFilename('/joined_layer.shp')
        if os.path.exists(joined_layer_output):
            driver.DeleteDataSource(joined_layer_output)
        
        joined_layer_out = processing.run('qgis:joinattributestable', {
            'INPUT': overlap_intersect_layer,
            'FIELD': poly_join.name(),
            'INPUT_2': population,
            'FIELD_2': pop_join.name(),
            'OUTPUT': joined_layer_output})
        
        joined_layer = QgsVectorLayer(joined_layer_output, 'joined_layer', 'ogr')
        
        '''
        Get areas of overlapped tracts
        '''
        joined_layer_area_output = QgsProcessingUtils.generateTempFilename('/joined_layer_area.shp')
        if os.path.exists(joined_layer_area_output):
            driver.DeleteDataSource(joined_layer_area_output)
        
        
        joined_layer_area_out = processing.run('qgis:exportaddgeometrycolumns', {
            'INPUT': joined_layer,
            'CALC_METHOD': '0',
            'OUTPUT': joined_layer_area_output})
        
        joined_layer_area = QgsVectorLayer(joined_layer_area_output, 'Overlapping Coverage', 'ogr')
        
        
        '''
        Calculate new population of intersection tracts
        '''
        fieldname_area = 'area_2'
        fldname_pop = 'NewPop'
        total_joined_area = 0
        
        #Enables us to enter the joined layer
        provider = joined_layer_area.dataProvider()
        #Creates new field for proportionaly correct population
        provider.addAttributes([QgsField(fldname_pop, QVariant.Double)])
        joined_layer_area.updateFields()

        #Loops through each feature and calculates the new population
        field_id2 = provider.fieldNameIndex(fldname_pop)
        for f in joined_layer_area.getFeatures():
            newpop = f[pop_fld.name()] * f[fieldname_area] / f[area_fld.name()]
            total_joined_area += f[fieldname_area]
            provider.changeAttributeValues({f.id(): {field_id2:newpop}})
        
        QgsProject.instance().addMapLayer(joined_layer_area)
        
        '''
        Find total population within overlaps
        '''
        total_pop_within_overlaps = 0
        for f in joined_layer_area.getFeatures():
            total_pop_within_overlaps += f[fldname_pop]
        
        '''
        Find total population in tracts
        '''
        total_pop = 0
        for f in population.getFeatures():
            total_pop += f[pop_fld.name()]
        
        
        #Calculates percent of overlapping coverage
        percent_overlap = (total_joined_area/total_buffer_area)*100
        percent_overlap = round(percent_overlap, 2)
        QgsMessageLog.logMessage(f'Percent of coverage that overlaps: \
        {percent_overlap}', "MyPlugin", level=Qgis.Info)
        
        #Message log for total population within overlapping coverage
        QgsMessageLog.logMessage(f'Total population within overlapping coverage: \
        {total_pop_within_overlaps}', "MyPlugin", level=Qgis.Info)
        
        #Calculate the percent of population within overlapping coverage
        pop_prop = total_pop_within_overlaps / total_pop
        pop_prop = round(pop_prop, 5)
        QgsMessageLog.logMessage(f'Percent of total population within overlapping coverage: \
        {pop_prop}', "MyPlugin", level=Qgis.Info)
        
        
        #Popup box with our data
        msg_box = QMessageBox()
        
        msg_box.setWindowTitle("Coverage Analysis")
        msg_box.setText(f"Percent of coverage that overlaps: {percent_overlap}%\
        \nTotal Population within overlapping coverage: {math.floor(total_pop_within_overlaps)}\
        \nPercent of total population within overlapping coverage: {pop_prop}")
        msg_box.setIcon(QMessageBox.Information)
        
        msg_box.exec()
        
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