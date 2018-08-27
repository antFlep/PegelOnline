# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PegelOnline
                                 A QGIS plugin
 Plugin lädt Daten zu Stationen und Wasserständen über die REST-Schnittstelle von Pegelonline
                              -------------------
        begin                : 2018-06-27
        git sha              : $Format:%H$
        copyright            : (C) 2018 by amr, Universität Trier
        email                : amr@nirvana.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from pegel_online_dockwidget import PegelOnlineDockWidget
import os.path

# import po-modules
from po_ressources.database import PoDB
from po_ressources.stations import PoStations
from po_ressources.currentw import PoCurrentW
from po_ressources.timeline import PoTimeline
from po_ressources.openstreet import PoOpenStreetMap


class PegelOnline:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """

        # Save reference to the QGIS interface
        self.iface = iface

        self.db = None
        self.stations = None
        self.currentw = None
        self.timeline = None
        self.os_map = None

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # DB-Name with path
        self.dbname = os.path.join(self.plugin_dir, "po_spatialite_db/stations.sqlite")

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PegelOnline_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Pegel Online Reader')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'PegelOnline')
        self.toolbar.setObjectName(u'PegelOnline')

        # print "** INITIALIZING PegelOnline"

        self.pluginIsActive = False
        self.dockwidget = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PegelOnline', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/PegelOnline/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Open Pegel Online Reader'),
            callback=self.run,
            parent=self.iface.mainWindow())

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING PegelOnline"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD PegelOnline"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Pegel Online Reader'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING PegelOnline"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = PegelOnlineDockWidget()
                # connect Signals and Slots
                self.makeEvents()

                self.db = PoDB(self.dbname)
                self.stations = PoStations(self.db, self.iface)
                self.currentw = PoCurrentW(self.db, self.iface, self.dockwidget)
                self.timeline = PoTimeline(self.iface, self.dockwidget)
                self.os_map = PoOpenStreetMap(self.iface, self.dockwidget)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()


    def makeEvents(self):
        self.dockwidget.pbStationsLoad.clicked.connect(self.doStationsLoad)
        self.dockwidget.pbStationsMap.clicked.connect(self.doStationsMap)
        self.dockwidget.pbStationsTable.clicked.connect(self.doStationsTable)
        self.dockwidget.pbCurrentLoad.clicked.connect(self.doCurrentLoadLevels)
        self.dockwidget.pbCurrentMap.clicked.connect(self.doCurrentMap)
        self.dockwidget.pbCurrentTable.clicked.connect(self.doCurrentTable)
        self.dockwidget.pbTimelinePNG.clicked.connect(self.doTimelinePNG)
        self.dockwidget.pbTimelineExport.clicked.connect(self.doTimelineExport)
        self.dockwidget.pbCleanDb.clicked.connect(self.doCleanDb)
        self.dockwidget.pbRemoveLayers.clicked.connect(self.doRemoveLayers)
        self.dockwidget.pbOsmLoad.clicked.connect(self.doOsmLoad)
        self.dockwidget.pbTimelineZoom.clicked.connect(self.doTimelineZoom)
        self.dockwidget.pbChangeCrs.clicked.connect(self.doChangeCrs)


    def doStationsLoad(self):
        """Download stations data from Pegel Online"""
        print "Info: Calling doStationLoad"
        self.stations.download_stations()

    def doStationsMap(self):
        print "Info: Calling doStationsMap"
        self.stations.show_stations()

    def doStationsTable(self):
        print "Info: Calling doStationsTable"
        self.stations.show_stations_table()

    def doCurrentLoadLevels(self):
        print"Info: Calling doCurrentLoadLevels"
        self.currentw.download_current_w()

    def doCurrentMap(self):
        print "Info: Calling docCurrentMap"
        self.currentw.show_current_w()

    def doCurrentTable(self):
        print "Info: Calling doCurrentTable"
        self.currentw.show_current_w_table()

    def doTimelinePNG(self):
        print "Info: Calling doTimelinePNG"
        self.timeline.down_time_pic()

    def doTimelineExport(self):
        print "Info: Calling doTimelineExport"
        self.timeline.down_station()

    def doTimelineZoom(self):
        print "Info: Calling doTimelineZoom"
        self.timeline.zoom_to_station()

    def doCleanDb(self):
        print "Info: Calling doCleanDb"
        self.db.clean_table('poStation')
        self.db.clean_table('poCurrentW')

    def doRemoveLayers(self):
        print "Info: Calling doRemoveLayers"
        self.stations.remove_layer()
        self.currentw.remove_layer()
        self.os_map.remove_layer()

    def doOsmLoad(self):
        print "Info: Calling doOsmLoad"
        self.os_map.load_osm_wsm()

    def doChangeCrs(self):
        print "Info: Calling doChangeCrs"
        self.os_map.change_to_osm_crs()


