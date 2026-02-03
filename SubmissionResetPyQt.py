#
# https://www.pythonguis.com/pyqt6-tutorial/
# https://zetcode.com/pyqt6/
#
from PyQt6.QtCore import QSize, Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import(
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QComboBox,
    QWidget,
    QHBoxLayout,
    QTableView
)

import requests
import os
import sys
import pandas as pd


class PandasModel(QAbstractTableModel):
    # https://www.pythonguis.com/tutorials/pyqt6-qtableview-modelviews-numpy-pandas/
    # https://doc.qt.io/qtforpython-6/examples/example_external_pandas.html

    def __init__(self, dataframe:pd.DataFrame, parent=None):
        #super().__init__()
        QAbstractTableModel.__init__(self, parent)
        self._dataframe = dataframe
    
    #def data(self, index, role):
    def data(self, index:QModelIndex, role=Qt.ItemDataRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])
        return None
        #if role == Qt.ItemDataRole.DisplayRole:
        #    value =  self.data[index.row()][index.column()]
        #    return str(value)


    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._dataframe.index[section])
        return None
        
    def rowCount(self, parent=QModelIndex()) -> int:
        if parent == QModelIndex():
            return self._dataframe.shape[0]
            # return len(self._dataframe)
        #return len(self._data)
        #return self._data.shape[0]
        return 0
    
    def columnCount(self, parent=QModelIndex()) -> int:
        if parent == QModelIndex():
            return self._dataframe.shape[1]
            # return len(self._dataframe.columns)
        #return len(self._data[0])
        #return self._data.shape[1]
        return 0
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRDC Data Hub Submission Reset")
        self.resize(400,200)

        self.subtable = QTableView()
        

        #self._createMenuBar()

        tier_layout = QHBoxLayout()
        table_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        tier_label = QLabel("Select a tier: ")
        table_label = QLabel("Submissions")

        tier_combobox = QComboBox()
        tier_combobox.addItems(["","Production", "Stage", "QA", "Dev"])
        tier_combobox.currentIndexChanged.connect(self.tier_index_changed)
        tier_combobox.currentTextChanged.connect(self.tier_text_changed)
        tier_combobox.currentTextChanged.connect(self.getSubmissionData)

        tier_layout.addWidget(tier_label)
        tier_layout.addWidget(tier_combobox)

        subtable = QTableView()
        subtable.horizontalHeader().setStretchLastSection(True)
        subtable.setAlternatingRowColors(True)
        subtable.setSelectionBehavior(QTableView.selectRow)

        widget = QWidget()
        widget.setLayout(tier_layout)
        self.setCentralWidget(widget)
        


    def tier_index_changed(self, index):
        print(index)

    def tier_text_changed(self, text):
        print(text)





    def dhAPICreds(self,tier):
        url = None
        token = None
        if tier == 'production':
            url = 'https://hub.datacommons.cancer.gov/api/graphql'
            token = os.getenv('PRODAPI')
        elif tier == 'stage':
            url = 'https://hub-stage.datacommons.cancer.gov/api/graphql'
            token = os.getenv('STAGEAPI')
        elif tier == 'qa':
            url = 'https://hub-qa.datacommons.cancer.gov/api/graphql'
            token = os.getenv('QAAPI')
        elif tier == 'qa2':
            url = 'https://hub-qa2.datacommons.cancer.gov/api/graphql'
            token = os.getenv('QA2API')
        elif tier == 'dev':
            url = 'https://hub-dev.datacommons.cancer.gov/api/graphql'
            token = os.getenv('DEVAPI')
        elif tier == 'dev2':
            url = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
            token = os.getenv('DEV2API')
        elif tier == 'localtest':
            url = 'https://this.is.a.test/url/graphql'
            token = os.getenv('LOCALTESTAPI')
        return {'url': url, 'token': token}



    def dhApiQuery(self, url, apitoken, query, variables=None):
        headers = {"Authorization": f"Bearer {apitoken}"}
        try:
            if variables is None:
                result = requests.post(url=url, headers=headers, json={"query": query})
            else:
                result = requests.post(url=url, headers=headers, json={"query": query, "variables": variables})
            if result.status_code == 200:
                return result.json()
            else:
                return (f"Status Code: {result.status_code}\n{result.content}")
        except requests.exceptions.HTTPError as e:
            return (f"HTTPError: {e}")
        

    def getSubmissionData(self, tier):
        tier = tier.lower()
        print(f"Getting submission data for {tier}")
        creds = self.dhAPICreds(tier)
        list_sub_query = """
            query ListSubmissions($status: [String]!){
            listSubmissions(status: $status){
                submissions{
                _id
                name
                submitterID
                submitterName
                studyAbbreviation
                studyID
                dbGaPID
                createdAt
                updatedAt
                metadataValidationStatus
                fileValidationStatus
                status
                }
            }
            }
            """
        subvariables = {"status": ["New", "In Progress"]}
        subres = self.dhApiQuery(url=creds['url'], apitoken=creds['token'], query=list_sub_query, variables=subvariables)
        #print(subres)
        sub_df = pd.DataFrame(subres['data']['listSubmissions']['submissions'])
        print(sub_df.head())
        


    
    

app = QApplication([])

mainWindow = MainWindow()
mainWindow.show()

app.exec()