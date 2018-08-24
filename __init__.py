# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PegelOnline
                                 A QGIS plugin
 Plugin lädt Daten zu Stationen und Wasserständen über die REST-Schnittstelle von Pegelonline
                             -------------------
        begin                : 2018-06-27
        copyright            : (C) 2018 by amr, Universität Trier
        email                : amr@nirvana.org
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PegelOnline class from file PegelOnline.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """

    from .pegel_online import PegelOnline
    return PegelOnline(iface)
