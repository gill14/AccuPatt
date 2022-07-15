# The following missing module prevents import of skimage.feature
# with skimage 0.18.x.
hiddenimports = [
    'pyqtgraph.GraphicsScene.exportDialogTemplate_pyqt6.'
    'pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt6',
    'pyqtgraph.canvas.CanvasTemplate_pyqt6',
    'pyqtgraph.canvas.TransformGuiTemplate_pyqt6',
    'pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt6',
    'pyqtgraph.imageview.ImageViewTemplate_pyqt6',
]
    