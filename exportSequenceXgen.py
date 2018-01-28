import maya.cmds as cmds
import maya.mel as mel
import xgenm as xg
import xgenm.xgGlobal as xgg
import xgenm.xgUtil as xgu
import os
import itertools
import sys
import os
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
de = xgg.DescriptionEditor
currentDescription = de.currentDescription()
currentCollection = de.currentPalette()
palette = de.currentPalette()
description = de.currentDescription()
minTime = int(cmds.playbackOptions(minTime=True, q=True))
maxTime = int(cmds.playbackOptions(maxTime=True, q=True))
step = cmds.playbackOptions(q=True, by=True)
class mainWindow(QTabWidget):
    def __init__(self):
        super(mainWindow, self).__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        # define tabs count and type
        self.tab1 = QWidget()

        # add tabs to main widget
        self.addTab(self.tab1, "Tab 1")
        self.tab1UI()
        self.setWindowTitle("Crocoraffe's xGen to alembic exporter")

        # set initial position and size
        self.setGeometry(500, 400, 600, 90)
        # set minimum size
        self.setMinimumSize(600, 90)
        self.setMaximumSize(600, 90)

    def tab1UI(self):
        # define main layout
        layout = QVBoxLayout()
        gbox = QGroupBox()
        layout.addWidget(gbox)

        # define first row of groupbox
        self.b1 = QLabel('Frame range:', gbox)
        self.f1 = QLineEdit(gbox)
        self.t1 = QLabel(' - ', gbox)
        self.f2 = QLineEdit(gbox)
        self.b2 = QLabel('Step:', gbox)
        self.f3 = QComboBox(gbox)
        self.b3 = QPushButton('Export xGen', gbox)

        # set validators for text fields only to be able to accept numbers
        l2 = QVBoxLayout()
        intValidator = QIntValidator()
        fValidator = QDoubleValidator()
        self.f1.setValidator(intValidator)
        self.f2.setValidator(intValidator)

        # connect events
        self.f1.returnPressed.connect(self.setMinRange)
        self.f2.returnPressed.connect(self.setMaxRange)
        self.b3.clicked.connect(self.exportMehses)

        # set initial data
        self.f1.setText(str(minTime))
        self.f2.setText(str(maxTime))

        #add step variants to step combobox
        self.f3.addItem('1')
        self.f3.addItem('0.5')
        self.f3.addItem('0.25')
        self.f3.addItem('0.2')
        self.f3.addItem('0.1')

        # add all widgets to main window
        gbl = QHBoxLayout()

        gbl.addWidget(self.b1)
        gbl.addWidget(self.f1)
        gbl.addWidget(self.t1)
        gbl.addWidget(self.f2)
        gbl.addWidget(self.b2)
        gbl.addWidget(self.f3)
        gbl.addWidget(self.b3)
        gbox.setLayout(gbl)
        spacerItem1 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacerItem1)

        # set name of first tab
        self.setTabText(0, "Export xGen")
        self.tab1.setLayout(layout)

    ###defs for button functional
    def exportMehses(self):
        minTime=int(self.f1.text())
        maxTime=int(self.f2.text())
        step=float(self.f3.currentText())
        exportXgenMeshes(minTime, maxTime, step)

    def getNewText(self):
        sender = self.sender()
        stepText = sender.text()
        cmds.playbackOptions(by=float(stepText))
        print stepText

    def setMinRange(self):
        sender = self.sender()
        minTime = sender.text()

    def setMaxRange(self):
        sender = self.sender()
        maxTime = sender.text()

def seq(minTime, maxTime, step):
    assert (step != 0)
    sample = abs(maxTime - minTime) / step
    return itertools.islice(itertools.count(minTime, step), sample)

selectGroupName = str(currentDescription) + "_convert"

def makePath():
    sceneName = os.path.normpath(cmds.file(sn=True, q=True))
    splittedSceneName = sceneName.rsplit(os.sep, 2)
    exportPath = os.path.join(splittedSceneName[0]) + os.sep + 'cache' + os.sep + 'xgenExport' + os.sep
    if os.name == 'nt':
        return (exportPath.replace("\\", '/'))
    else:
        return (exportPath)

exportPath = makePath()

percentage = xg.getAttr('percent', palette, description, 'GLRenderer')

exportName = str('_percentage') + '_' + str(percentage.split('.')[0])


def makeExport(i):
    cmds.currentTime(i, update=True, edit=True)
    mel.eval('xgmGeoRender -pb  -convertSelected 0 -combineMesh 1 -useWidthRamp 1 -insertWidthSpan 0 -uvInTiles 1 -uvLayoutType 0 -uvTileSeparation 0.0 -createStripJoints 0 -createGuideJoints 0 "%s"' % currentDescription)
    object = cmds.select(cmds.ls(selectGroupName, dag=1)[1])
    cmds.rename(str(selectGroupName) + '_' + str(i))
    command = 'AbcExport -j "'
    command += '-frameRange '
    command += str(i) + ' ' + str(i)
    command += ' -uvWrite -wholeFrameGeo -worldSpace -writeVisibility -eulerFilter -dataFormat hdf -root |'
    command += str(cmds.ls(selectGroupName, dag=1)[0]) + '|' + str(cmds.ls(selectGroupName, dag=1)[1])
    command += ' -file '
    command += str(exportPath + os.sep + currentCollection.replace(':', '_')) + '_' + i + '.abc' + '"'
    last = str(exportPath + currentCollection.replace(':', '_')) + '_' + i + '.abc' + '"'
    print last
    mel.eval(command)
    cmds.delete(cmds.ls(selectGroupName, dag=1)[0])

def exportXgenMeshes(minTime, maxTime, step):
    cmds.undoInfo(state=False)
    cmds.autoSave(enable=False)
    cmds.saveToolSettings
    cmds.saveViewportSettings
    for i in seq(minTime, maxTime+step+step, step):
        if not i >= maxTime+step:
            print i
            eqValue = round(float(i)-int(i), 1)
            if str(eqValue) == '0.0':
                if os.path.isdir(exportPath):
                    print str("value: ") + str(eqValue)
                    print 'frame, folder exists'
                    makeExport(str(int(i)))
                else:
                    os.makedirs(str(exportPath))
                    print str("value: ") + str(eqValue)
                    print 'frame, folder created'
                    makeExport(str(int(i)))
            elif str(eqValue) == '1.0':
                if os.path.isdir(exportPath):
                    print str("value: ") + str(eqValue)
                    print 'frame, folder exists'
                    makeExport(str(int(i+1)))
                else:
                    os.makedirs(str(exportPath))
                    print str("value: ") + str(eqValue)
                    print 'frame, folder created'
                    makeExport(str(int(i+1)))
            else:
                if os.path.isdir(exportPath):
                    print str("value: ") + str(eqValue)
                    print 'subframe, folder exists'
                    makeExport(str(i))
                else:
                    os.makedirs(str(exportPath))
                    print str("value: ") + str(eqValue)
                    print 'subframe, folder created'
                    makeExport(str(i))
        else:
            pass
ex = mainWindow()
ex.show()