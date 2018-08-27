from qgis.core import *
from qgis.gui import QgsMapCanvas
from osgeo import gdal
import utils


class PoOpenStreetMap(object):

    def __init__(self, i_face, gui):
        """
        PoOpenStreetMap keeps track of Coordinate Reference Systems
        and provides method to download OpenStreetMap layer

        :param i_face: iface needed to get crs data
        :param gui: Plugin GUI needed to change button text
        """

        self.i_face = i_face
        self.crs_button = gui.pbChangeCrs
        self.osm_crs = QgsCoordinateReferenceSystem("EPSG:3857")
        self.default_crs = QgsMapCanvas().mapSettings().destinationCrs()
        self.current_crs = self.default_crs

        # get current crs
        self.i_face.mapCanvas().mapRenderer().setProjectionsEnabled(True)

    def change_to_osm_crs(self):
        """
        Switch between project CRS and OSM layer CRS so that we can look at the
        layer without it being distorted
        """
        canvas = self.i_face.mapCanvas()
        if self.current_crs == self.default_crs:
            canvas.setDestinationCrs(self.osm_crs)
            self.crs_button.setText("Change CRS Back To Default")
            self.current_crs = self.osm_crs
        else:
            canvas.setDestinationCrs(self.default_crs)
            self.crs_button.setText("  Change CRS To OSM CRS   ")
            self.current_crs = self.default_crs

    def load_osm_wsm(self):
        """
        Creates OSM layer using gdal
        """

        # remove OSM layer if already loaded in order to not have duplicates
        utils.remove_layer("OSM", self.i_face)

        # xml for osm gdal, IMPORTANT: right projection
        xml = """<GDAL_WMS>
        <Service name="TMS">
            <ServerUrl>http://tile.openstreetmap.org/${z}/${x}/${y}.png</ServerUrl>
        </Service>
        <DataWindow>
            <UpperLeftX>-20037508.34</UpperLeftX>
            <UpperLeftY>20037508.34</UpperLeftY>
            <LowerRightX>20037508.34</LowerRightX>
            <LowerRightY>-20037508.34</LowerRightY>
            <TileLevel>18</TileLevel>
            <TileCountX>1</TileCountX>
            <TileCountY>1</TileCountY>
            <YOrigin>top</YOrigin>
        </DataWindow>
        <Projection>EPSG:3857</Projection>
        <BlockSizeX>256</BlockSizeX>
        <BlockSizeY>256</BlockSizeY>
        <BandsCount>3</BandsCount>
        <Cache />
        </GDAL_WMS>"""

        vfn = "/vsimem/osm.xml"
        gdal.FileFromMemBuffer(vfn, xml)
        raster_lyr = QgsRasterLayer(vfn, "OSM")

        if raster_lyr.isValid():
            QgsMapLayerRegistry.instance().addMapLayers([raster_lyr])
        else:
            msg = 'Something went wrong, Layer is not valid'
            self.i_face.messageBar().pushMessage('OSM Error', msg, level=2, duration=3)

    def remove_layer(self):
        utils.remove_layer("OSM", self.i_face)