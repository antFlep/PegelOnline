from qgis.core import *
from pyspatialite import dbapi2 as db
from database import PoDB
from PyQt4.QtGui import QColor
import urlreader02 as urlreader
import utils


def get_data_table(json_data, columns=[]):
    """
    Create table form JSON data that will be saved in the database,
    columns define which data will be saved and which won't.
    Specifically generates poCurrentW table.

    :param json_data: JSON data from which we create our table
    :param columns: Data fields we want to save
    :return: Table containing the data of the column fields supplied
    """

    table = []
    for st in json_data:
        row = [st[columns[0]]]
        # There should be only one currentMeasurement entry in timeseries
        current_measurement = st['timeseries'][0]['currentMeasurement']

        for key in columns[1:len(columns)]:
            row.append(current_measurement[key] if key in current_measurement else None)
        table.append(row)

    return table


class PoCurrentW(object):

    def __init__(self, database, i_face, gui, test=False):
        """
        Responsible for downloading and displaying current water measurements data

        :param database: Database where our data is/will be stored
        :param i_face: Used to display messages to user
        :param gui: Widget from which we need the cbox to display names of selected stations
        """

        self.i_face = i_face
        self.po_db = database
        self.connection = db.connect(database.db_name)
        self.layer = None

        self.test = test
        if not self.test:
            self.c_box = gui.cboxTimelineSelect

    def do_layer_selection_changed(self):
        """
        Takes the  names of currently selected stations with water measurements
        and display them in the combobox
        """

        # Can't use activeLayer() cause if I have stations selected,
        # and select another layer it creates an error, when zooming to the stations
        lay = utils.get_layer("CurrentW", self.i_face)
        self.c_box.clear()

        for feat in lay.selectedFeatures():
            self.c_box.addItem(feat['shortname'])

    def download_current_w(self):
        """
        Downloads station data from Pegel-Online and saves it to our database
        """

        if not self.test:
            # show progress bar
            # utils.show_progress(self.i_face, 'Download measurement data')
            msg = 'Downloading Measurement Data'
            self.i_face.messageBar().pushMessage('Download', msg, level=0, duration=3)

        url = 'http://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json?timeseries='\
              'W&includeTimeseries=true&includeCurrentMeasurement=true '

        json_data = urlreader.get_json_response(url)
        fields = ["uuid", "timestamp", "value", "trend", "stateMnwMhw", "stateNswHsw"]
        table = get_data_table(json_data, fields)

        cur = self.connection.cursor()
        for row in table:
            # Generate question mark string for sql query
            str_fgz = ",".join(['?'] * len(row))
            # build the whole sql string
            sql = "INSERT OR REPLACE INTO poCurrentW VALUES (%s)" % str_fgz
            cur.execute(sql, row)

        self.connection.commit()

        # if not self.test:
        #     self.i_face.messageBar().clearWidgets()

    def show_current_w(self):
        """
        Load poCurrentW data and display the stations as a separate Layer
        If a CurrentW layer is already loaded it, will be removed and a new layer will be loaded,
        which is useful if the data in the database has changed.
        Additionally every station will be color coded depending on its trend:
        rising = red,
        falling = green,
        constant = blue
        """

        # check if layer is already loaded, if it is remove it
        utils.remove_layer('CurrentW', self.i_face)

        # check if table is empty
        if self.po_db.is_empty('poCurrentW'):
            msg = "Empty Table poCurrentW Nothing to Show"
            self.i_face.messageBar().pushMessage('Empty Table', msg, level=0, duration=3)
            return

        s_connect = "dbname='" + self.po_db.db_name + "'"

        table = "SELECT poStation.number, poStation.shortname, poCurrentW.uuid, poStation.geom, " + \
                "poCurrentW.timestamp, poCurrentW.value, poCurrentW.trend " + \
                "FROM poCurrentW, poStation " + "WHERE poCurrentW.uuid == poStation.uuid"

        uri = s_connect + " key='number'" + "table=\"(%s)\" (geom) sql=" % table
        display_name = 'CurrentW'
        self.layer = QgsVectorLayer(uri, display_name, 'spatialite')

        if self.layer.isValid():
            self.color_layer()
            # Load Layer
            lay = self.i_face.activeLayer()

            # Change c-box entries depending on what is selected
            lay.selectionChanged.connect(self.do_layer_selection_changed)
        else:
            # Set layer back to None otherwise show table will display empty table
            self.layer = None
            if not self.test:
                msg = "to create this layer you need to download the station data before"
                self.i_face.messageBar().pushMessage('Station Data Missing', msg, level=0, duration=3)

    def color_layer(self):
        """
        Color code every station depending on its trend:
        rising = red,
        falling = green,
        constant = blue
        """

        QgsMapLayerRegistry.instance().addMapLayer(self.layer)

        pegel = {-1: ('green', 'falling'),
                 0: ('blue', 'constant'),
                 1: ('red', 'rising')}

        # Set graphic properties
        cat = []
        for value, (color, label) in pegel.items():
            sym = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
            sym.setColor(QColor(color))
            category = QgsRendererCategoryV2(value, sym, label)
            cat.append(category)

        # Apply to layer
        renderer = QgsCategorizedSymbolRendererV2('trend', cat)
        self.layer.setRendererV2(renderer)
        self.i_face.mapCanvas().refresh()
        self.i_face.legendInterface().refreshLayerSymbology(self.layer)

    def show_current_w_table(self):
        """
        Displays the table of the CurrentW layer
        """

        if self.layer is None:
            msg = 'poCurrentW data has not been loaded, thus nothing can be shown'
            self.i_face.messageBar().pushMessage('Data unavailable', msg, level=0, duration=3)
        else:
            self.i_face.showAttributeTable(self.layer)

    def remove_layer(self):
        """
        Remove CurrentW Layer
        """
        utils.remove_layer('CurrentW', self.i_face)
        self.layer = None


if __name__ == '__main__':
    # Download tests

    db_name = "../po_spatialite_db/stations.sqlite"
    my_po_db = PoDB(db_name)
    my_curr_w = PoCurrentW(my_po_db, None, None, True)

    my_curr_w.download_current_w()

    # See table entries
    sql = """SELECT * FROM poCurrentW LIMIT 10"""
    print '\nTEST:', sql
    result_table = my_po_db.fetch_query(sql)
    for row in result_table:
        print row
