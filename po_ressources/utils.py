from PyQt4.QtGui import QProgressBar
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry


def remove_layer(layer_name, i_face):
    """
    Remove a layer if it is currently loaded

    :param layer_name: Name of the layer to be removed
    :param i_face: Name of iface from which the layer should be removed
    """

    for layer in i_face.mapCanvas().layers():
        if type(layer) == QgsVectorLayer and layer.name() == layer_name:
            QgsMapLayerRegistry.instance().removeMapLayer(layer.id())


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
