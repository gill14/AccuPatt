from PyInstaller.utils.hooks import collect_data_files

# include all .ui and image files
datas = collect_data_files("pyqtgraph",
                           includes=["**/*.ui", "**/*.png", "**/*.svg"])

hiddenimports = [
    'pyqtgraph.GraphicsScene.exportDialogTemplate_pyqt6',
    'pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt6',
    'pyqtgraph.canvas.CanvasTemplate_pyqt6',
    'pyqtgraph.canvas.TransformGuiTemplate_pyqt6',
    'pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt6',
    'pyqtgraph.imageview.ImageViewTemplate_pyqt6',
]
    