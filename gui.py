import sys
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot,QWaitCondition,QMutexLocker,QMutex
from PyQt5.QtWidgets import QLineEdit,QScrollArea,QMessageBox,QGroupBox,QApplication, QWidget, QVBoxLayout, QSizePolicy,QTextBrowser,QSpacerItem,QPushButton,QFileDialog,QLabel,QComboBox,QRadioButton,QHBoxLayout,QGridLayout
from PyQt5.QtGui import QFont
import pymysql
import socket
import os
import pandas as pd
import threading
import codecs
import re
import uuid
import yaml
from queue import Queue

import logging
from pythonping import ping

import ping3
###############Logging Variables#################
logger = logging.getLogger(__name__)
# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('rfid_reader_error.log')
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)
#Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)
logger.addHandler(f_handler)
###############End Logging Variables##############
df_employee=pd.DataFrame()
df_operations=pd.DataFrame()
db=""
df_bundles=pd.DataFrame()

blue_light="55AA24010008D2" #For Blue Light
mac_recv_id="55AA020000FD"
button_style_sheet="background-color: #4C1CEE; color: white; font-weight: bold;"
title_style_sheet="background-color: #CC4B2F; color: white;"
########GUI############################
app = QApplication(sys.argv)
window = QWidget()
window.setStyleSheet("background-color: #9DF1FB;")
main_layout=QHBoxLayout(window)
#####File Uploading#####
uploaded_data_df=pd.DataFrame()
file_name=""
upload_button=QPushButton("Upload File")
upload_button.setStyleSheet(button_style_sheet)
selectComboLabelFileUpload=QLabel("Select ")
file_save_button = QPushButton("Save to Database")
comb_box=QComboBox()
file_name_label=QLabel()
data_save_label=QLabel()
fileUploadLayouTitle=QLabel()
fileUploadLayouTitle.setStyleSheet(title_style_sheet)
file_upload_layout = QGridLayout()
file_upload_comb_box=QComboBox()
#file_upload_comb_box.lineEdit.setAlignment(Qt.AlignCenter)
file_upload_comb_box.setFixedHeight(50)
file_upload_comb_box.setStyleSheet("color: white; alignment: center; text-align: center")
#file_upload_comb_box.setStyleSheet("background-color: lightblue;")
selectedFileUploadComboxItem="Operator"
##############End File Upload##########
layout = QVBoxLayout()
right_layout = QGridLayout()

device_status_label=QLabel("Device Status:")
device_status=QLabel("")
main_layout.addLayout(layout)
main_layout.addLayout(right_layout)
main_layout.addLayout(file_upload_layout)
main_layout.setStretchFactor(layout,3)
main_layout.setStretchFactor(right_layout,2)

main_layout.setStretchFactor(file_upload_layout,1)
text_browser = QTextBrowser()

# Create a QTextBrowser widget to display the received text
selectedComboxItem="Operator"

text_browser = QTextBrowser()
save_button = QPushButton("Save to Database")
save_button.setStyleSheet(button_style_sheet)
comb_box=QComboBox()
right_label=QLabel("Select Operator")


scroll_area = QScrollArea()
scroll_widget = QWidget()
scroll_layout = QVBoxLayout(scroll_widget)
scroll_layout.setSpacing(0)
scroll_area.setWidgetResizable(True)
scroll_area.setWidget(scroll_widget)
group_box = QGroupBox("Radio Buttons")
no_info="NoInfo"
cardGUID=no_info

radio_buttons=[]
status_queue = Queue()
########################

def on_fileUpload_combobox_changed(index):
    try:
        global file_upload_comb_box,selectedFileUploadComboxItem
        selectedFileUploadComboxItem = file_upload_comb_box.currentText()
        #right_label.setText("Select "+selectedFileUploadComboxItem)
        #fillUpRadioButtons()
        print('Selected: '+selectedFileUploadComboxItem)
    except Exception as e:
        print('Exception at <on_fileUpload_combobox_changed> '+str(e))
        logger.exception('Exception at <on_fileUpload_combobox_changed> '+str(e))
def init_ui():
    try:
        global window,app,layout,comb_box,right_layout,selectedComboxItem,right_label,df_employee
        
        file_upload_comb_box.addItem("Operator")
        
        file_upload_comb_box.addItem("Operation")
        file_upload_comb_box.addItem("Bundle")
        file_upload_comb_box.currentIndexChanged.connect(on_fileUpload_combobox_changed)
        file_upload_layout.addWidget(file_name_label,4,0)
        file_upload_layout.addWidget(data_save_label,6,0)
        fileUploadLayouTitle.setText(generateCSS("Add Style Bulletin, Operator and Bundle Details",20))
        file_upload_layout.addWidget(fileUploadLayouTitle,0,0)
        file_upload_layout.addWidget(QLabel(),1,0)
        file_upload_layout.addWidget(file_upload_comb_box,2,0)
        file_upload_layout.addWidget(upload_button,3,0)
        file_upload_layout.addWidget(file_save_button,5,0)
        file_upload_layout.addWidget(device_status_label)
        file_upload_layout.addWidget(device_status)
        upload_button.clicked.connect(uploadFileFromLocal)
        file_save_button.clicked.connect(save_uploaded_to_database)
        file_save_button.setEnabled(False)
        comb_box.addItem("Operator")
        comb_box.addItem("Operation")
        comb_box.addItem("Bundle")
        comb_box.currentIndexChanged.connect(on_combobox_changed)
        layout.addWidget(text_browser)
        layout.addWidget(comb_box)

        save_button.clicked.connect(save_to_database)
        layout.addWidget(save_button)
        window.setGeometry(200, 100, 1500, 800)
        window.setWindowTitle('Card Assigning')
        font=QFont()
        font.setPointSize(10)
        spacer_item = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_label=QLabel("Select Operator")
#        right_label.setFont(font)
        right_label.setStyleSheet(title_style_sheet)
        right_layout.addWidget(right_label,0,0)
        radio_buttons = []
        #fillA(df_employee['Operator_name'].values)
        fillUpRadioButtons()
        right_layout.setVerticalSpacing(5)
        file_upload_layout.setAlignment(Qt.AlignTop)
        window.setLayout(main_layout)
        window.show()
    except Exception as e:
        print('Exception at <init_ui> '+str(e))
        logger.exception('Exception at <init_ui> '+str(e))

worker_thread1 = None
worker1 = None
mutex = QMutex()
class Worker(QObject):
    append_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.wait_condition = QWaitCondition()
        self.message_queue = []

    @pyqtSlot()
    def do_work(self):
        while True:
            with QMutexLocker(mutex):
                if len(self.message_queue) == 0:
                    self.wait_condition.wait(mutex)

                message = self.message_queue.pop(0)

            self.append_text.emit(message)
def save_uploaded_to_database():
    global file_name,db,uploaded_data_df,data_save_label,file_save_button, selectedFileUploadComboxItem
    try:
#        print(uploaded_data_df.head(5))
        cursor=db.cursor()
        print('#############While Saving Data#######')
        print(uploaded_data_df)
        uploaded_data_df['id'] = [str(uuid.uuid4()) for _ in range(len(uploaded_data_df))]
 #       cols = "`,`".join([str(i) for i in uploaded_data_df.columns.tolist()])#column list
 
        if selectedFileUploadComboxItem=="Operator":
            cursor.execute("DELETE FROM cardLink WHERE linkid IN (SELECT id FROM employee)")
            #truncate_query = f"DELETE FROM employee"
            update_query="UPDATE employee set is_active=0"
            cursor.execute('SET FOREIGN_KEY_CHECKS=0;')
            cursor.execute(update_query)
            #cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
            for i,row in uploaded_data_df.iterrows():
                sql = "INSERT INTO employee (operator_code,Operator_name,Operation_name,Machine_Code,id) VALUES (" + "%s,"*(len(row)-1) + "%s)"#inserting anomlies in table
                cursor.execute(sql, tuple(row))

            db.commit()
        elif selectedFileUploadComboxItem=="Operation":
            
            cursor.execute("DELETE FROM cardLink WHERE linkid IN (SELECT id FROM operation_v2)")
            #truncate_query = f"delete from  operation"
            update_query="UPDATE operation_v2 set is_active=0 where is_active=1"
            cursor.execute('SET FOREIGN_KEY_CHECKS=0;')
            cursor.execute(update_query)
            cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
            # index_to_ignore = uploaded_data_df[uploaded_data_df.iloc[:, 0]==0].index[0]
            # new_df = uploaded_data_df.iloc[:index_to_ignore]

            print('$$$$$$New DF$$$$')
            print(uploaded_data_df)

            for i,row in uploaded_data_df.iterrows():
                
                sql = "INSERT INTO operation_v2 (Operation,R1, R2, R3, avg, mins, pr, alw,SAM,id) VALUES (" + "%s,"*(len(row)-1) + "%s)"  # Inserting anomalies in table
                cursor.execute(sql, tuple(row))

            db.commit()
        elif selectedFileUploadComboxItem=="Bundle":  
            cursor.execute("DELETE FROM cardLink WHERE linkid IN (SELECT id FROM bundles)")
            #truncate_query = f"delete from  bundles"
            update_query="UPDATE bundles set is_active=0 where is_active=1"
            cursor.execute('SET FOREIGN_KEY_CHECKS=0;')
            cursor.execute(update_query)
            cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
            for i,row in uploaded_data_df.iterrows():
                sql = "INSERT INTO bundles (OrderNo,Style,Category,Size,Qty,Cut_Number,Bundle,Shade,Number,id)  VALUES (" + "%s,"*(len(row)-1) + "%s)"#inserting anomlies in table
                cursor.execute(sql, tuple(row))
            db.commit()            
            
        
        data_save_label.setText('<span style="color: green;">Data Saved Successfully</span>')
        loadPreReqData()
        fillUpRadioButtons()            
    except Exception as e:
        print('Exception at <save_to_database> '+str(e))
        cursor.execute('ROLLBACK')
        data_save_label.setText('<span style="color: red;">Data Not Saved: Reason:'+str(e)+'</span>')
    finally:
        cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
        file_save_button.setEnabled(False)
def uploadFileFromLocal():
    global file_name,uploaded_data_df
    try:
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(None, "Select Excel File", "", "Excel Files (*.xlsx *.xlsb);;CSV Files (*.csv)")
        if file_path:
            print("Selected File:", file_path)
            file_extension = file_path.split(".")[-1].lower()
            valid_file_names = ["employee", "machine", "bundles", "operator", "operation"]
            file_name=os.path.splitext(os.path.basename(file_path))[0]
            
            if file_extension == "xlsx" or file_extension=="xlsb":
                uploaded_data_df = pd.read_excel(file_path,keep_default_na=True,skiprows=1)
                file_save_button.setEnabled(True)
                file_name_label.setText('<span style="color: green;">Selected File: '+file_name+'</span>')
                
                print(uploaded_data_df)
            elif file_extension == "csv":
                uploaded_data_df = pd.read_csv(file_path,keep_default_na=False,header=None,skiprows=1)
                #print(uploaded_data_df)
                file_name_label.setText('<span style="color: green;">Selected File: '+file_name+'</span>')
                file_save_button.setEnabled(True)
            
            else:
                print("Invalid File")
                file_name_label.setText('<span style="color: red;">Invalid File Selected! i,e (Operator,Operation,Bundle,Machine)</span>')
                
        else:
            print('Invalid Path')
            file_name_label.setText("No File Selected File")
        uploaded_data_df=uploaded_data_df.fillna(0)
    except Exception as e:
        logger.exception('Exception at <uploadFileFromLocal> '+str(e))
        print('Exception at <uploadFileFromLocal> '+str(e))        

config=""
def getName(id):
    try:
        name=""
        if selectedComboxItem=="Operator":
            
            filtered_df = df_employee[df_employee['id'] == id]
            name = 'Code: '+ str(filtered_df.iloc[0]['operator_code'])+' Name: '+ filtered_df.iloc[0]['Operator_name']
        elif selectedComboxItem=="Operation":
            filtered_df = df_operations[df_operations['id'] == id]
#            name = 'Code: '+ str(filtered_df.iloc[0]['Operation'])+' Operation:'+ filtered_df.iloc[0]['Operation']
            name = str(' Operation:'+ filtered_df.iloc[0]['Operation'])
        elif selectedComboxItem=="Bundle":
            filtered_df = df_bundles[df_bundles['id'] == id]
            name = 'Cut-No: '+ str(filtered_df.iloc[0]['Cut_Number'])+',' +' Bundle-No: '+str(filtered_df.iloc[0]['Bundle'])
            
        return name             
    except Exception as e:
        print('Exception at <getName> '+str(e))
        logger.error('Exception at <getName> '+str(e))
        
def initiateWorkerThread():
    try:
        global worker_thread1,worker1,mutex
        worker_thread1 = QThread()
        worker1 = Worker()
        worker1.append_text.connect(text_browser.append)
        worker1.moveToThread(worker_thread1)

        worker_thread1.started.connect(worker1.do_work)

        # Connect the thread's finished signal to the thread's deleteLater slot
        worker_thread1.finished.connect(worker_thread1.deleteLater)

        # Connect the application's aboutToQuit signal to stop the worker thread
        app.aboutToQuit.connect(worker_thread1.quit)

        # Start the thread
        worker_thread1.start()
    except Exception as e:
        logger.exception('Exception at <initiateWorkerThread> '+str(e))
        print('Exception at <initiateWorkerThread> '+str(e))
def read_config():
    global config
    try:
        config=None
        # https://stackoverflow.com/questions/1773805/how-can-i-parse-a-yaml-file-in-python
        stream=open("rfid_config.yaml", "r") 
        config = yaml.safe_load(stream)
        return config
    except Exception as e:
        logging.exception('Cannot Read Config=> '+str(e))
        return None

def loadPreReqData():
    try:
        global df_employee,df_operations,db,df_bundles,config
        db=DBConnection(config['db_host'],config['db_user'],config['db_password'],config['db_name'])
        if db==None:
            return
        df_employee=fetchData(db,"employee")
        #df_machines=fetchData(db,"machine")
        df_operations=fetchData(db,"operation_v2")
        df_bundles=fetchData(db,"bundles_view")
    except Exception as e:
        print('Exception at <loadPreReqData>'+str(e))
        logger.error('Exception at <loadPreReqData>'+str(e))

def DBConnection(host_, user_, password_, database_):
    mydb = None
    try:
        mydb = pymysql.connect(host=host_, user=user_, password=password_,  db=database_)
    except Exception as e:
        #logger.error('Exception in DBConnection => ' + str(e))
        print('Exception at <DBConnection> '+str(e))
        logger.error('Exception at <DBConnection> '+str(e))
        return None
    return mydb



def selectedRadioItem():
    try:
        global radio_buttons
        for radio_button in radio_buttons:
            if radio_button.isChecked():
                selected_item = radio_button.text()
                return selected_item
    except Exception as e:
        print('Exception at <selectedRadioItem> '+str(e))
        logger.error('Exception at <selectedRadioItem> '+str(e))
def fetchData(db,table,all_data=True):
    df = pd.DataFrame()
    try:
        if all_data:
            sql="select * FROM "+ table+ " where is_active=1;"
        else:
            sql="select * FROM "+ table+ " order by id desc;"
        df=pd.read_sql(sql,db)
    except Exception as e:
        print('Exception at <fetchTempDetails>' +str(e))
        logger.error('Exception at <fetchTempDetails>' +str(e))
        return None
    return df
def fill(values):
    global right_label
    
    while right_layout.count():
        ite = right_layout.takeAt(0)
        widget = ite.widget()
        widget.deleteLater()
        

    right_label=QLabel("Select "+selectedComboxItem)
    radio_buttons=[]
    #label=QLabel("Select "+selectedComboxItem)
    #right_layout.addWidget(label)
    right_layout.addWidget(right_label, 0, 0, 1, right_layout.columnCount())
    for i, item in enumerate(values):
#        label = QLabel(item)
        radio_button = QRadioButton(item)
        #hbox.addWidget(radio_button)
        i=i+1
        right_layout.addWidget(radio_button, i, 0)
        radio_buttons.append(radio_button)
def filterRadioButtons(text):
    global radio_buttons
    for radio_button in radio_buttons:
        if text.lower() in radio_button.text().lower():
            radio_button.setVisible(True)
        else:
            radio_button.setVisible(False)
def fillA(values):
    try:
        global right_label,group_box,scroll_layout,scroll_area,scroll_widget,radio_buttons
        while scroll_layout.count():
            item = scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        right_label.setText("Select "+selectedComboxItem)
        radio_buttons=[]
        # Add a QLineEdit for search
        search_box = QLineEdit()
        if selectedComboxItem=="Operator":
            search_box.setPlaceholderText("Search Operator..")
        elif selectedComboxItem=="Operation":
            search_box.setPlaceholderText("Search Operation..")
        elif selectedComboxItem=="Bundle":
            search_box.setPlaceholderText("Search (CutNumber,Bundle)")
        search_box.textChanged.connect(lambda text: filterRadioButtons(text))

        #label=QLabel("Select "+selectedComboxItem)
        #right_layout.addWidget(label)
        right_layout.addWidget(right_label, 0, 0, 1, right_layout.columnCount())
        right_layout.addWidget(search_box, 1, 0, 1, right_layout.columnCount())

        for i, item in enumerate(values):
    #        label = QLabel(item)
            radio_button = QRadioButton(item)
            #hbox.addWidget(radio_button)
            i=i+1
            scroll_layout.addWidget(radio_button)
            radio_buttons.append(radio_button)
        scroll_layout.setAlignment(Qt.AlignTop)
        scroll_layout.setSpacing(10)
        group_box.setLayout(scroll_layout)
        scroll_widget.setLayout(scroll_layout)
        right_layout.addWidget(scroll_area)
    except Exception as e:
        print('Exception at <fillA> '+str(e))
        logger.error('Exception at <fillA> '+str(e))
def fillUpRadioButtons():
    try:
        
        global df_employee,df_bundles,df_operations,selectedComboxItem,right_label
        if len(df_bundles):
            Style=df_bundles['Style'].values
            
            Category=df_bundles['Category'].values
            Size=df_bundles['Size'].values
            Qty=df_bundles['Qty'].values
            Cut_Number=df_bundles['Cut_Number'].values
            Bundle=df_bundles['Bundle'].values
            Shade=df_bundles['Shade'].values
                        #bundels = [ a + ',' + b+',Size: '+c+',Qty: '+str(d)+',Cut-Number: '+str(e)+', Bundle: '+str(f)+','+g for a, b,c,d,e,f,g in zip(Style, Category,Size,Qty,Cut_Number,Bundle,Shade)]
            bundels = [ a + ',' + b+','+c+','+str(d)+','+str(e)+','+str(f)+','+g for a, b,c,d,e,f,g in zip(Style, Category,Size,Qty,Cut_Number,Bundle,Shade)]        
        if len(df_employee):
            empName_values=df_employee['Operator_name'].values
            oper_codes=df_employee['operator_code'].values
            opr_values = [str(x) + ',' + y  for x, y in zip(oper_codes, empName_values)]

        if len(df_operations)>0:
            
            
#            oprationName_values=df_operations['Opeation_Name'].values
            oprationName_values=df_operations['Operation'].values

#            operationCode_values=df_operations['Opr'].values
            operationCode_values=df_operations['sam'].values

            operation_values = [x + ',' + str(y)  for x, y in zip( oprationName_values,operationCode_values)]
        radio_buttons = []
        if selectedComboxItem=="Operator":
            fillA(opr_values)
        elif selectedComboxItem=="Operation":
            fillA(operation_values)
        elif selectedComboxItem=="Bundle":
            fillA(bundels)

    except Exception as e:
        print('Exception at <fillUpRadioButtons> '+str(e))
        logger.exception('Exception at <fillUpRadioButtons> '+str(e))
            
def checkIfDuplicateID(): 
    try:
        global cardGUID
        df=fetchData(db,"cardlink")
        exists = (df['cardID'] == cardGUID)
        if exists.any():
            return True
        return False
    except Exception as e:
        logger.exception('Exception at <checkIfDuplicateID> '+str(e))
        print('Exception at <checkIfDuplicateID> '+str(e))

      
def saveInfo(id,cardType):
    global cardGUID,db
    try:
        assigned_details=""
        if cardGUID!="55c2aa24000000c39b" and cardGUID!="00" and cardGUID!="XYZ" and cardGUID!="NoInfo":
            cursor=db.cursor()
            if checkIfDuplicateID(): #Operator cannot scaned double bundle at once
                query = f'''
                                UPDATE cardlink
                                SET cardType = '{cardType}',
                                    linkID = '{id}', added_time= now()
                                WHERE cardID = '{cardGUID}'
                            '''
                cursor.execute(query)
            else:
                query = "INSERT INTO cardlink (cardType, cardID, linkID) VALUES (%s, %s, %s)"
                cursor.execute(query, (cardType, cardGUID, id))
            db.commit()
            #QMessageBox.information(window, "Success", "Saved Successfully")
            #showText('<span style="color: green;">'+selectedComboxItem+' Card Assigned Successfully</span>',"green")
            #value=getName(df_employee if selectedComboxItem=="Operator" else df_bundles if selectedComboxItem=="Operation" else df_operations,)
            showText(generateCSS(selectedComboxItem+" Card Assigned: "+getName(id),20,"green"))
        else:
            QMessageBox.warning(window, "Error", "Card is not Scaned")
            showText(generateCSS("Card is Not Scaned",20,"red"),"red")
            
        cardGUID="55c2aa24000000c39b"
    except Exception as e:
        print('Exception at <saveInfo> '+str(e))
        QMessageBox.critical(window,"Error","Error while Adding Details")
        logger.exception('Exception at <saveInfo> '+str(e))
        cardGUID="55c2aa24000000c39b"

def checkDuplicateOperatorBundles(id):
    try:
        df=fetchData(db,"cardlink")
        exists = (df['linkID'] == id)
        if exists.any():
            return True
        return False
    except Exception as e:
        logger.exception('Exception at <checkDuplicateOperatorBundles> '+str(e))
        print('Exception at <checkDuplicateOperatorBundles> '+str(e))   
def save_to_database():
    global window,cardGUID
    try:
        selectedItem=selectedRadioItem()
        
        if selectedItem is None:
            QMessageBox.warning(window,"Warning","Please Select " +selectedComboxItem )
        else:
            values = selectedItem.split(',')
            print(values)
            if selectedComboxItem=="Operator":                
                #column_names = df_employee.columns[:-1]
                #print(column_names)
                #matches = df_employee[df_employee[column_names].apply(lambda row: all(row == values), axis=1)]
                print(values[0])
                matches = df_employee[(df_employee['operator_code'] == int(values[0])) & (df_employee['Operator_name'] == values[1]) ]
                if len(matches)>0:
                    matched_id = matches['id'].iloc[0]
                    print("Operator ID: " +str(matched_id))
                    if checkDuplicateOperatorBundles(matched_id):
                        #showText('<span style="color: red;">'+selectedComboxItem+' Already Assigned</span>',"red")
                        showText(generateCSS(selectedComboxItem+" " +str(values[0])+"-"+values[1]+ " Already Assigned",20,"red"))
                        #text2speech(selectedComboxItem+" " +str(values[0])+"-"+values[1]+ " Already Assigned")
                    else:                    
                        saveInfo(matched_id,'E')
                     
            elif selectedComboxItem=="Operation":
                matches = df_operations[(df_operations['Operation'] == (values[0]))]
                if len(matches)>0:
                    matched_id = matches['id'].iloc[0]
                    print("Operation ID: " +str(matched_id))
                    saveInfo(matched_id,'O')
            elif selectedComboxItem=="Bundle":
                matches = df_bundles[(df_bundles['Style'] == values[0]) & (df_bundles['Category'] == values[1]) & (df_bundles['Size'] == values[2]) & (df_bundles['Qty'] == int(values[3]))& (df_bundles['Cut_Number'] == int(values[4]))& (df_bundles['Bundle'] == int(values[5]))& (df_bundles['Shade'] == (values[6]))]
                if len(matches)>0:
                    matched_id = matches['id'].iloc[0]
                    print("Bundle ID: " +str(matched_id))
                    if checkDuplicateOperatorBundles(matched_id):
                        #showText('<span style="color: red;">'+selectedComboxItem+' Already Assigned</span>',"red")
                        showText(generateCSS(selectedComboxItem+"Already Assigned",20,"red"))
                        
                    else:                    
                        saveInfo(matched_id,'B')
    except Exception as e:
        print('Exception at <save_to_database> '+str(e))
        logger.exception('Exception at <save_to_database> '+str(e))

def specialDecode(ecnodedString):
    try:
        pattern = rb'\x00\x0f\x00([\w\d]+)'

        matches = re.findall(pattern, ecnodedString)
        if len(matches) > 0:
            extracted_value = matches[0].decode()
            print('Extracted Data:'+str(extracted_value))
            return extracted_value
        else:
            print("No match found.")
            return "XYZ"
            
    except Exception as e:
        print('Exception at <specialDecode> '+str(e))
        return None
    
def econding_data(ecnodedString):
    try:
    
        decoded_data = ecnodedString.decode('iso-8859-1')
        bytes_text = decoded_data.encode("utf-8")
        byte_array = bytes_text.hex()
    
        return str(byte_array)     
    
    except Exception as e:
        logger.exception('Exception at <econding_data> '+str(e))
        print('Exception at <econding_data> '+str(e))
def showText(text,color="black"):
    try:
        global window,text_browser
        with QMutexLocker(mutex):
            worker1.message_queue.append(text)
            worker1.wait_condition.wakeAll()

    except Exception as e:
        logger.exception('Exception at <showText>' +str(e))
        print('Exception at <showText>' +str(e))


def removeCharacter(byteString):
        character_to_remove = b'$'
        r_to_remove = b'r'
        string=str(byteString)
        dollarRem=string.replace(character_to_remove.decode(), '')
        rRemoved=dollarRem.replace(r_to_remove.decode(), '')
        return rRemoved
def specialDecode1(ecnodedString):
    try:
        pattern = rb'(?:x[^x]*){3}x([^x]*)'
        rmChar=removeCharacter(ecnodedString)
        cleanString= str(rmChar.replace('\\', ''))
        cleanString=cleanString.encode('utf-8') 
        matches = re.findall(pattern, cleanString)
        if len(matches) > 0:
            extracted_value = matches[0].decode()
            print('Extracted Data:'+str(extracted_value))
            return extracted_value
        else:
            print("No match found.")
            return "XYZ"
            
    except Exception as e:
        print('Exception at <specialDecode> '+str(e))
        return None

def generateCSS(text,font_size=15,color="black"):
    return f'<span style="color: {color}; font-size: {font_size}px;">{text}</span>'
def initialStart(cardID):
    global cardGUID
    try:
        print(cardID)
        cardGUID=cardID
##        if cardGUID !="55c2aa24000000c39b":
        if cardGUID !="00":                  
            #showText("Card Scaned: "+selectedComboxItem)
            showText(generateCSS("Card Scaned: "+selectedComboxItem,17,"green"))
            #showText("Card ID: "+cardID)
            showText(generateCSS("Card ID: "+cardID))
            cardGUID=cardID
        else:
            showText(generateCSS("Please Scan Card",20,"blue"),"green")
            #showText("Please Scan Card!","blue")
        
    except Exception as e:
        logger.exception('Exception at <initialStart> '+str(e))
        print('Exception at <initialStart> '+str(e))

def on_combobox_changed(index):
    try:
        global comb_box,selectedComboxItem,right_label
        selectedComboxItem = comb_box.currentText()
        right_label.setText("Select "+selectedComboxItem)
        fillUpRadioButtons()
    except Exception as e:
        print('Exception at <on_combobox_changed> '+str(e))
        logger.exception('Exception at <on_combobox_changed> '+str(e))
def run_server(host, port):
    # Create a TCP socket
    global blue_light,mac_recv_id,root
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))    
    server_socket.listen(1)
    print(f"Server listening on {host}:{port}")
    #showText(f"Server listening on {host}:{port}","green")
    showText(generateCSS(f"Server listening on {host}:{port}",16,"green"))
    first_time=0
    while not exit_event.is_set():
        try:
            threading.Event().wait(1)    
            client_socket, client_address = server_socket.accept()
            
            response=""
            if(first_time<2):
                if first_time==0:
                    blue_light_hex=blue_light.encode('utf-8').hex()
                    blue_light_ascii = codecs.decode(blue_light_hex, 'hex').decode('ascii')
                    client_socket.send(bytes.fromhex(blue_light_ascii))
                elif first_time==1:
                    mac_id_hex=mac_recv_id.encode('utf-8').hex()
                    mac_ascii_data = codecs.decode(mac_id_hex, 'hex').decode('ascii')
                    client_socket.send(bytes.fromhex(mac_ascii_data))
                first_time+=1
                print(client_address)     
                # client_thread = threading.Thread(target=ping_ip_address, args=(client_address[0], client_address[1]))
                # client_thread.start()    

            if first_time==2:
                dt = client_socket.recv(1024)
                dec_dt = specialDecode(dt)
                first_time=4
                client_socket.close()                
            else:    
                data = client_socket.recv(1024)
                print('Data From Device: '+str(data))
                #data = econding_data(data)
                data=specialDecode1(data)
                print('Data After Encoding! '+ data)
            
                if data is not None:
                    # mainLogic(getCardType(),data)
                    initialStart(data)
                    response_hex = response.encode('utf-8').hex()
                    ascii_data = codecs.decode(response_hex, 'hex').decode('ascii')                    
                #hexa=codecs.encode(response.encode(), 'hex').decode()
                    client_socket.send(bytes.fromhex(ascii_data))
                client_socket.close()
                  
        except Exception as e:
            print('Exception at <ServerRun> '+str(e))
            logger.exception('Exception at <ServerRun> '+str(e))
            client_socket.close()


    server_socket.close()
status_signal = pyqtSignal(str)
class StatusUpdater(QObject):
    status_signal = pyqtSignal(str)  # Define the status_signal as an instance attribute

    @pyqtSlot()
    def update_text_view(self):
        while not exit_event.is_set():
            status = status_queue.get()  # Get the status from the queue
            self.status_signal.emit(status)  # Emit the signal with the status

# Create an instance of the StatusUpdater
status_updater = StatusUpdater()
@pyqtSlot(str)
def handle_status_updates(status):
    device_status.setText(status)
status_updater.status_signal.connect(handle_status_updates)
def ping_ip_address(ip,port):
    try:
        def ping():
            response=os.system("ping "+str(ip))
#            response = ping(ip, count=1)  # Perform a single ping request to the IP
            print('IP Address:', str(ip))
            if response==0:
                print('Ping successful. Response time:')
                txt = '<span style="color: green; font-size: 20px;">Connected</span>'
                status_queue.put(txt)
            else:
                print('Ping failed.')
                txt = '<span style="color: red; font-size: 20px;">Disconnected</span>'
                status_queue.put(txt)
            # Schedule the next ping after 10 seconds
            if not exit_event.is_set():
                timer = threading.Timer(3, ping)
                timer.start()

        # Start the initial ping
        ping()
    except Exception as e:
        print('Exception at <PingIP>'+str(e))
def close_application():
    # Function to handle application termination
    try:
        exit_event.set()
        app.quit()
    except Exception as e:
        print('Exception at <CloseApplication> '+str(e))
if __name__ == '__main__':
    config=read_config()
    loadPreReqData()
    init_ui()
    initiateWorkerThread()
    exit_event = threading.Event()
    worker_thread =threading.Thread(target=run_server, args=(config['ip'],config['port']), daemon=True)
    
    worker_thread.start()
    # status_thread = threading.Thread(target=status_updater.update_text_view)
    # status_thread.start()
    app.aboutToQuit.connect(lambda: exit_event.set())


    sys.exit(app.exec_())

    worker_thread.join()

