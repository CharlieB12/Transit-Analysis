from qgis.gui import QgsMapToolIdentify
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapToolIdentify
from qgis.utils import iface
import os
import math
import processing
from PyQt5.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QTabWidget,
    QWidget,
    QDockWidget,
    QMessageBox,
    QLineEdit,
    QComboBox
)
from qgis.core import (
    Qgis,
    QgsWkbTypes,
    QgsProject,
    edit,
    QgsVectorLayer,
    QgsField,
    QgsFields,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsMessageLog,
    QgsProcessingUtils
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
        

        #Finds first occurence of numeric field for buffer dissolve and self intersect funtion later on
        layer_id = ''
        for field in buffer_layer.fields():
            #4 represents integer
            if field.type() == 4:
                layer_id = field.name()
                break

    
        '''
        Dissolve buffers (for percent overlap calculation)
        '''
        buffer_dissolve_out = QgsProcessingUtils.generateTempFilename('/buffer_dissolve.shp')
        if os.path.exists(buffer_dissolve_out):
            driver.DeleteDataSource(buffer_dissolve_out)
        
        buffer_dissolve = processing.run('qgis:dissolve', {
            'INPUT':buffer_layer,
            'OUTPUT': buffer_dissolve_out})
        
        buffer_dissolve_layer = QgsVectorLayer(buffer_dissolve_out, 'Total Buffer Area', 'ogr')
        #QgsProject.instance().addMapLayer(dissolve)


        '''
        Add area to dissolved buffers (for percent overlap calculation)
        '''
        buffer_dissolve_area_out = QgsProcessingUtils.generateTempFilename('/buffer_area.shp')
        if os.path.exists(buffer_dissolve_area_out):
            driver.DeleteDataSource(buffer_dissolve_area_out)
            
        buffer_dissolve_area = processing.run('qgis:exportaddgeometrycolumns', {
            'INPUT': buffer_dissolve_layer,
            'CALC_METHOD': '0',
            'OUTPUT': buffer_dissolve_area_out})
    
        buffer_disolve_area_layer = QgsVectorLayer(buffer_dissolve_area_out, 'Buffer_Area', 'ogr')

        #Assign buffer dissolve area to variable
        total_buffer_area = 0
        for f in buffer_disolve_area_layer.getFeatures():
            total_buffer_area+=f['area']

        
        '''
        Add Area to Buffer
        '''
        buffer_add_area_out = QgsProcessingUtils.generateTempFilename('/buffer_area.shp')
        if os.path.exists(buffer_add_area_out):
            driver.DeleteDataSource(buffer_add_area_out)
            
        buffer_add_area = processing.run('qgis:exportaddgeometrycolumns', {
            'INPUT': buffer_layer,
            'CALC_METHOD': '0',
            'OUTPUT': buffer_add_area_out})
    
        buffer_area_layer = QgsVectorLayer(buffer_add_area_out, 'Buffer_Area', 'ogr')


        '''
        Union the buffer
        '''
        buffer_union_out = QgsProcessingUtils.generateTempFilename('/buffer_union.shp')
        if os.path.exists(buffer_union_out):
            driver.DeleteDataSource(buffer_union_out)

        buffer_union = processing.run('qgis:union', {
            'INPUT': buffer_area_layer,
            'OUTPUT': buffer_union_out})

        buffer_union_layer = QgsVectorLayer(buffer_union_out, 'Coverage', 'ogr')
        QgsProject.instance().addMapLayer(buffer_union_layer)

        '''
        Get new area of unions
        '''

        union_area_out = QgsProcessingUtils.generateTempFilename('/union_area.shp')
        if os.path.exists(union_area_out):
            driver.DeleteDataSource(union_area_out)

        union_area = processing.run('qgis:exportaddgeometrycolumns', {
            'INPUT': buffer_union_layer,
            'CALC_METHOD': '0',
            'OUTPUT': union_area_out})
    
        union_area_layer = QgsVectorLayer(union_area_out, 'Union_Area', 'ogr')

        '''
        Filter out the non overlapping geometry
        '''
        provider = union_area_layer.dataProvider()
        features_to_delete = []
        
        for feature in union_area_layer.getFeatures():
            dupeFound = False
            if(feature.id() not in features_to_delete):
                for other_feature in union_area_layer.getFeatures():
                    if feature != other_feature and feature['area_2'] == other_feature['area_2']:
                        features_to_delete.append(other_feature.id())
                        dupeFound = True
                if dupeFound == False:
                    features_to_delete.append(feature.id())

        res = provider.deleteFeatures(features_to_delete)
        union_area_layer.updateExtents()
        union_area_layer.triggerRepaint()
        #QgsProject.instance().addMapLayer(union_area_layer)
        
        '''
        Dissolve overlaps
        '''
        dissolve_output = QgsProcessingUtils.generateTempFilename('/dissolve.shp')
        if os.path.exists(dissolve_output):
            driver.DeleteDataSource(dissolve_output)
        
        dissolve_layer = processing.run('qgis:dissolve', {
            'INPUT':union_area_layer,
            'OUTPUT': dissolve_output})
        
        dissolve = QgsVectorLayer(dissolve_output, 'Overlapping Coverage', 'ogr')
        #QgsProject.instance().addMapLayer(dissolve)
        
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
        #QgsProject.instance().addMapLayer(overlap_intersect_layer)
        
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
        #QgsProject.instance().addMapLayer(joined_layer)
        
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
        #QgsProject.instance().addMapLayer(joined_layer_area)
        
        '''
        Calculate new population of overlapped tracts
        '''
        fieldname_area = 'area_4'
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
        {percent_overlap}%', "MyPlugin", level=Qgis.Info)
        
        #Message log for total population within overlapping coverage
        QgsMessageLog.logMessage(f'Total population within overlapping coverage: \
        {math.floor(total_pop_within_overlaps)}', "MyPlugin", level=Qgis.Info)
        
        #Calculate the percent of population within overlapping coverage
        pop_prop = (total_pop_within_overlaps / total_pop) * 100
        pop_prop = round(pop_prop, 3)
        QgsMessageLog.logMessage(f'Percent of total population within overlapping coverage: \
        {pop_prop}%', "MyPlugin", level=Qgis.Info)
        
        
        #Popup box with our data
        msg_box = QMessageBox()
        
        msg_box.setWindowTitle("Coverage Analysis")
        msg_box.setText(f"-Percent of coverage that overlaps: {percent_overlap}%\
        \n-Total Population within overlapping coverage: {math.floor(total_pop_within_overlaps)}\
        \n-Percent of total population within overlapping coverage: {pop_prop}% \
        \n-Walking {buffer_radius} miles will take roughly {buffer_radius*20} minutes.")
        msg_box.setIcon(QMessageBox.Information)
        
        msg_box.exec()
        
    def getToolLabel(self):
        return self.toolLabel
    def getToolText(self):
        return self.toolText
        
        
