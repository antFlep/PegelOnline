from qgis.core import *
from PyQt4.QtGui import QProgressBar

def remove_layer(layer_name, i_face):
    """
    Remove a layer if it is currently loaded

    :param layer_name: Name of the layer to be removed
    :param i_face: Name of iface from which the layer should be removed
    """

    for layer in i_face.mapCanvas().layers():
        if (type(layer) == QgsVectorLayer or type(layer) == QgsRasterLayer) and layer.name() == layer_name:
            QgsMapLayerRegistry.instance().removeMapLayer(layer.id())


def get_layer(layer_name, i_face):
    """
    Searches a layer with the proviced name and returns the first one found

    :param layer_name: name of layer we are searching for
    :param i_face: Name of iface that will be searched
    :return: First layer with the provided name
    """

    for layer in i_face.mapCanvas().layers():
        if (type(layer) == QgsVectorLayer or type(layer) == QgsRasterLayer) and layer.name() == layer_name:
            return layer
    return None


def show_progress(i_face, msg):
    """
    Creates and shows a progress bar for some event.
    Does not have any progress information.
    Used to show user that something should be happening in the background

    :param i_face: iface where the progressbar will be shown
    :param msg: Message to be displayed in front of the progress bar
    """

    # Progress bar (without progress)
    bar = QProgressBar()
    bar.setRange(0, 0)
    progress_msg = i_face.messageBar().createMessage(msg)
    progress_msg.layout().addWidget(bar)
    i_face.messageBar().pushWidget(progress_msg, level=0)
