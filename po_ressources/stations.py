from qgis.core import *
from database import PoDB
from pyspatialite import dbapi2 as db
import urlreader02 as url_reader
import utils


def get_data_table(json_data, columns=[]):
    """
    Create table form JSON data that will be saved in the database,
    columns define which data will be saved and which won't.
    Additionally the water column in the JSON Data will be replaced with its longname sub-entry
    and an additional column containing WTK point data will be added.
    Entries without point coordinates (longitude and latitude) will be ignored.

    :param json_data: JSON data from which we create our table
    :param columns: Data fields we want to save
    :return: Table containing the data of the column fields supplied and WTK points.
    """

    table = []
    for st in json_data:
        row = []
        # accept only rows with point coordinates
        try:
            # replace 'water' dict with 'longname' sub-entry
            if 'water' in st:
                st['water'] = st['water']['longname']

            for key in columns:
                row.append(st[key] if key in st else None)

            # WKT-Point-String as last column
            str_geom = 'POINT(%f %f)' % (st['longitude'], st['latitude'])
            row.append(str_geom)
            table.append(row)
        except KeyError as e:
            print """INFO: Ignoring entry %s because attribute %s is missing""" % (st['shortname'], e)
    return table


class PoStations(object):

    def __init__(self, database, i_face, test=False):
        """
        Responsible for downloading and displaying station Information

        :param database: Database where our data is/will be stored
        :param i_face: Used to display messages to user
        :param test: Boolean used for local testing
        """
        self.po_db = database
        self.i_face = i_face
        self.test = test

        self.connection = db.connect(database.db_name)
        self.layer = None

    def download_stations(self):
        """
        Downloads station data from Pegel-Online and saves it to our database
        """

        url = "http://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json"

        if not self.test:
            # Progress bar (without progress)
            # utils.show_progress(self.i_face, 'Downloading station data')
            msg = 'Downloading Stations Data'
            self.i_face.messageBar().pushMessage('Download', msg, level=0, duration=3)

        # Download data
        json_data = url_reader.get_json_response(url)
        # self.i_face.messageBar().pushMessage('Download', 'Download finished successfully', level=0, duration=5)
        fields = ["uuid", "number", "shortname", "longname", "km", "agency", "longitude", "latitude", "water"]
        table = get_data_table(json_data, fields)

        cur = self.connection.cursor()
        for row in table:
            # Generate question mark string for sql query
            str_fgz = ",".join(['?'] * (len(row)-1))
            # Functions are always part of this
            str_fgz += ", GeomFromText(?, 4326)"
            # Build the whole sql string
            sql = "INSERT OR REPLACE INTO poStation VALUES (%s)" % str_fgz
            cur.execute(sql, row)
        # Complete changes
        self.connection.commit()

        # if not self.test:
        #     self.i_face.messageBar().clearWidgets()

    def show_stations(self):
        """
        Load poStation data and display the stations as a separate Layer
        If a poStation layer is already loaded it will be removed and a new layer will be loaded,
        which is useful if the data in the database has changed
        """

        # check if layer is already loaded, if it is remove it
        utils.remove_layer('Stations', self.i_face)

        # check if table is empty
        if self.po_db.is_empty('poStation'):
            msg = "Empty Table poStation Nothing to Show"
            self.i_face.messageBar().pushMessage('Empty Table', msg, level=0, duration=3)
            return

        # URI for access
        uri = QgsDataSourceURI()
        uri.setDatabase(self.po_db.db_name)
        uri.setDataSource('', 'poStation', 'geom')

        # Add layer to QGis
        self.layer = QgsVectorLayer(uri.uri(), 'Stations', 'spatialite')
        QgsMapLayerRegistry.instance().addMapLayer(self.layer)

    def show_stations_table(self):
        """
        Show poStation database table
        """

        if self.layer is None:
            msg = 'poStation data has not been loaded, thus nothing can be shown'
            self.i_face.messageBar().pushMessage('Data unavailable', msg, level=0, duration=3)
        else:
            self.i_face.showAttributeTable(self.layer)

    def remove_layer(self):
        """
        Remove Stations Layer
        :return:
        """

        utils.remove_layer('Stations', self.i_face)
        self.layer = None


if __name__ == '__main__':
    # Download Test

    db_name = '../po_spatialite_db/stations.sqlite'
    my_po_db = PoDB(db_name)
    myStat = PoStations(my_po_db, None, True)
    myStat.download_stations()
    print "Downloaded Stations"

    # See table entries
    sql = """SELECT * FROM poStation LIMIT 10"""
    print '\nTEST:', sql
    result_table = my_po_db.fetch_query(sql)
    for row in result_table:
        print row

    # See geom values
    sql = """SELECT longname, AsText(geom) FROM poStation LIMIT 10"""
    result_table = my_po_db.fetch_query(sql)
    print '\nTEST:', sql
    for row in result_table:
        print row
