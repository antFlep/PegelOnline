import urlreader02 as urlreader
import sys
from PyQt4.QtGui import *


def show_image(img_data, my_label):
    pixmap = QPixmap()
    pixmap.loadFromData(img_data)
    my_label.setPixmap(pixmap)
    my_label.resize(pixmap.width(), pixmap.height())


def get_data_table(json_data, columns=[]):
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
        self.gui = gui
        self.test = test
        if test:
            self.app = QApplication(sys.argv)
        self.label = QLabel()

    def down_time_pic(self, name=None):
        """
        Download measurement picture for the station currently shown in the combobox
        and display it in a QLabel

        :param name: Optional will only be used when testing
        """

        # Testing: use name instead of the cbox entry
        if not self.test:
            name = self.gui.cboxTimelineSelect.currentText()

        # Clear label content
        self.label.clear()

        if name:
            url = 'http://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/%s/W/measurements.png?start=P15D' % name
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

    def down_station(self, name=None):
        """
        Export timestamp and value data for the currently selected station
        in the combobox to a csv file using a file dialog

        :param name: optional will only be used when testing
        :return:
        """

        # Testing: use name instead of the cbox entry
        if not self.test:
            name = unicode(self.gui.cboxTimelineSelect.currentText())

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


if __name__ == '__main__':
    # Tests
    timeline = PoTimeline(None, None, True)

    # Test displaying TimeLine picture
    timeline.down_time_pic('BONN')
    # Test downloading Timeline values
    timeline.down_station('BONN')
