from qgis.core import *
from qgis.gui import QgsMapCanvas, QgsGenericProjectionSelector
from PyQt4.QtGui import *
import urlreader02 as urlreader
import utils
import sys


def show_image(img_data, my_label):
    pixmap = QPixmap()
    pixmap.loadFromData(img_data)
    my_label.setPixmap(pixmap)
    my_label.resize(pixmap.width(), pixmap.height())


def get_data_table(json_data, columns=[]):
    """
    Provide table from json_data, containing data of the provided columns

    :param json_data: JSON data to be parsed
    :param columns: field of data that we want to be returned
    :return: table of parsed data
    """

    table = []
    for st in json_data:
        row = []
        for key in columns:
            row.append(st[key] if key in st.keys() else None)
        table.append(row)
    return table


class PoTimeline(object):

    def __init__(self, i_face, gui, test=False):
        """
        Object  responsible for everything concerning current water level measurements

        :param i_face: used to display messages
        :param gui: used to get currently selected station in the combobox
        :param test: used to tell us if we are are testing or not
        """

        self.i_face = i_face
        self.test = test

        if test:
            self.app = QApplication(sys.argv)
        else:
            self.c_box = gui.cboxTimelineSelect
        self.label = QLabel()

    def down_timeline_pic(self, name=None):
        """
        Download measurement picture for the station currently shown in the combobox
        and display it in a QLabel

        :param name: Optional will only be used when testing
        """

        # Testing: use name instead of the cbox entry
        if not self.test:
            name = self.c_box.currentText()

        # Clear label content
        self.label.clear()

        if name:
            url = 'http://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/%s/W/measurements.png?start=P15D'\
                  % name
            # Download image and show label
            display_data = urlreader.get_data_response(urlreader.mask_url_string(url))
            self.label.setWindowTitle(name + ' Timeline')
            show_image(display_data, self.label)
            self.label.show()
        else:
            # Case nothing was selected
            msg = 'Nothing selected, so no timetable can be shown, ' \
                  'please select a station you want to see the timeline of.'
            self.i_face.messageBar().pushMessage('Noting selected', msg, level=0, duration=3)

        # Testing: Show the image
        if self.test:
            self.app.exec_()

    def down_station_dialog(self, name=None):
        """
        Export timestamp and value data for the currently selected station
        in the combobox to a csv file using a file dialog

        :param name: optional will only be used when testing
        """

        # Testing: use name instead of the cbox entry
        if not self.test:
            name = unicode(self.c_box.currentText())

        if name:
            url = 'http://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/%s/W/measurements.json' % name

            # File-Dialog: User supplies directory
            file_name = QFileDialog.getSaveFileName(None, 'CSV export', name + ".csv", '*.csv')

            # Download from Pegel-Online
            fields = ["timestamp", "value"]
            json_data = urlreader.get_json_response(urlreader.mask_url_string(url))
            table = get_data_table(json_data, fields)

            if file_name:
                f = open(file_name, 'w+')
                csv_header = ";".join(fields)
                f.write(csv_header + '\n')

                for row in table:
                    csv_row = ";".join(str(e) for e in row)
                    f.write(csv_row + '\n')
                f.close()
        else:
            # Case nothing was selected
            msg = 'Nothing selected, please select a station you want to see save the data of.'
            self.i_face.messageBar().pushMessage('Noting selected', msg, level=0, duration=3)

    def zoom_to_station(self):
        """
        Zooms to the currently selected station in the combobox,
        bounding box of the station will transformed to project CRS,
        so that we do not zoom to some random place
        """

        station = self.c_box.currentText()

        if station:
            layer = utils.get_layer("CurrentW", self.i_face)
            if layer:
                expr = """"shortname" ILIKE '%s'""" % station
                expr = QgsExpression(expr)

                sel = layer.getFeatures(QgsFeatureRequest(expr))
                ids = [i.id() for i in sel]
                layer.setSelectedFeatures(ids)

                # Our coordinates are WGS84 to make sure that if the current project is changes
                # the coordinate system  and everything our bounding box still works, we need to
                # convert our coordinates to whatever the project uses:

                crs_src = QgsCoordinateReferenceSystem(4326)
                crs_des = self.i_face.mapCanvas().mapSettings().destinationCrs()
                xform = QgsCoordinateTransform(crs_src, crs_des)

                box = layer.boundingBoxOfSelected()
                box = xform.transform(box)
                self.i_face.mapCanvas().setExtent(box)
                self.i_face.mapCanvas().refresh()
        else:
            # Case nothing was selected
            msg = 'Nothing selected, please select a station you want to zoom to.'
            self.i_face.messageBar().pushMessage('Noting selected', msg, level=0, duration=3)


if __name__ == '__main__':
    # Tests
    timeline = PoTimeline(None, None, True)

    # Test displaying TimeLine picture
    timeline.down_timeline_pic('BONN')
    # Test downloading Timeline values
    timeline.down_station_dialog('BONN')
