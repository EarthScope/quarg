#!/usr/bin/env python

"""
:copyright:
    IRIS Data Management Center
:license:
    This file is part of QuARG.

    QuARG is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    QuARG is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with QuARG.  If not, see <https://www.gnu.org/licenses/>.
"""


version='1.1.0'
print("QuARG version %s" % version)

#TODO: Need to include MS Gothic.ttf when packaging the scripts 

import kivy

kivy.require("1.11.0")

from kivy.config import Config
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'resizable', 0)


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout 
from kivy.uix.gridlayout import GridLayout 
from kivy.uix.stacklayout import StackLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty#, StringProperty
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, NoTransition
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.views import _cached_views, _view_base_cache  # supresses Original exception was:/Error in sys.excepthook: recycleview messages
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.clock import Clock
from kivy.uix.dropdown import DropDown
from kivy.graphics import Color, Rectangle


import os
import datetime
import time
import shutil   # used to remove directories
import webbrowser
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import sqlite3
from sqlite3 import Error
import subprocess

import urllib.request
import urllib.error
import requests     # used for getting empty transfer_function returns

import reportUtils

Config.set('input', 'mouse', 'mouse,disable_multitouch')


# PREFERENCE FILE TODOS #

# OVERALL PROGRAM TODOS #
# TODO: status bar at bottom of gui for output that's normally displayed on the command line?
# TODO: add a targets list as an option?
# TODO: If I call on the ObjectProperty version of the properties, do I even need the get_*_inputs() function at all? Or will those update as soon as the field updates in the gui?


# THRESHOLDS #
# TODO: Change the thresholds list popup (all defined thresholds) in the Thresholds Page to be text input so that user can select them, just like in the Examine Issues page)


# FIND ISSUES TODOS#

# EXAMINE TAB TO-DOS #
# TODO: have the 'metrics' populate as the ones involved with the selected threshold(s)? 
# TODO: put a "See Tickets" button to pull up all tickets related to the specified target
# TODO: add link to Mustangular in the resources column 
# TODO: hold onto polarity_check's snql2 and display in the examine issues screen?


# TICKETING TODOS #
# TODO: put button on the "create ticket" screen that looks for existing tickets related to the selected target 
    # Seeing the list of related tickets would be available from both the Examine screen and the Create Ticket screen 
# TODO: popup to select which description to import, if multiple

# GENERATE TAB TO-DOS #

# REPORT UTILS TODOS #



#### POP UPS and DROP DOWNS #### 
class ExitDialog(FloatLayout):
    exit = ObjectProperty(None)
    cancel = ObjectProperty(None)    

    def do_exit(self):
        # first, remove any figures that may be in quarg_plots/, as they are temporary
        try:
            for filename in os.listdir(masterDict['imageDir']):
                if filename.startswith("tmp."):
                    file_path = os.path.join(masterDict['imageDir'], filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))
        except:
            pass
        # Then exit the application
        App.get_running_app().stop()
 
class DeleteDialog(FloatLayout):
    deleteit = ObjectProperty(None)
    cancel = ObjectProperty(None)    

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class LoadDialog2(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    
class OverwriteDialog(FloatLayout):
    dontDoIt = ObjectProperty(None)
    doIt = ObjectProperty(None)

class ReportDialog(FloatLayout):

    a = ObjectProperty(None)
    b = ObjectProperty(None)  

class notifyPopup(FloatLayout):
    closePopup = ObjectProperty(None)
      
class TrackerDropDown(DropDown):
    pass




#####################
### SCREEN CLASSES ###



class MainScreen(Screen):
    
    startDate = ObjectProperty()
    endDate = ObjectProperty()
    find_pref = ObjectProperty()
    find_directory = ObjectProperty()
    find_file = ObjectProperty()
    find_net = ObjectProperty()
    find_sta = ObjectProperty()
    find_loc = ObjectProperty()
    find_cha = ObjectProperty()
    
    examine_pref = ObjectProperty()
    examine_directory = ObjectProperty()
    examine_file = ObjectProperty()
    
    query_pref = ObjectProperty()
    query_net = ObjectProperty()
    query_sta = ObjectProperty()
    query_loc = ObjectProperty()
    query_cha = ObjectProperty()
    query_updated = ObjectProperty()
    query_start = ObjectProperty()
    query_end = ObjectProperty() 
    query_start_before = ObjectProperty()
    query_end_before = ObjectProperty()
    query_status_btn2 = ObjectProperty()
    query_tracker_btn2 = ObjectProperty()
    query_category_btn2 = ObjectProperty()
    query_updated_before = ObjectProperty()
    
    generate_pref = ObjectProperty()
    generate_directory = ObjectProperty()
    generate_file = ObjectProperty() 
    generate_net = ObjectProperty()
    generate_sta = ObjectProperty()
    generate_loc = ObjectProperty()
    generate_cha = ObjectProperty() 
    generate_startDay = ObjectProperty()
    generate_endDay = ObjectProperty() 
        
    start = ""
    end = ""
    query_options = list()
    fileType = ""


    def warning_popup(self, txt):
                
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=txt, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_warning_popup)

        
        popupContent.add_widget(Label(size_hint_y=1.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=1.5))
        popupContent.add_widget(returnButton)
              
        masterDict["warning_popup"] = Popup(title="Warning", content=popupContent, size_hint=(.66, .66))
        masterDict["warning_popup"].open()

    def get_default_dates(self):
        today = datetime.date.today()       
        first= today.replace(day=1)
        lastMonthEnd = first - datetime.timedelta(days=1)
        lastMonthStart = lastMonthEnd.replace(day=1)
        
        if not MainScreen.start:
            self.start = str(lastMonthStart)
        if not MainLScreen.end:
            self.end = str(first)
 
    def set_default_start(self):
        self.get_default_dates()
        return self.start
        
    def set_default_end(self):
        self.get_default_dates()
        return self.end
    
    def get_dates(self): 
        ExamineIssuesScreen.start = self.start
        ExamineIssuesScreen.end = self.end

    def set_directory(self, whichToUse):
        if whichToUse == 'Find':
            self.examine_directory.text = self.find_directory.text
            self.generate_directory.text = self.find_directory.text
            
        if whichToUse == 'Examine':
            self.find_directory.text = self.examine_directory.text
            self.generate_directory.text = self.examine_directory.text
        
        if whichToUse == 'Generate':
            self.find_directory.text = self.generate_directory.text
            self.find_directory.text = self.generate_directory.text
            
    def get_find_inputs(self):
        self.start = self.startDate.text
        self.end =  self.endDate.text
        self.preference =  self.find_pref.text
        masterDict['preference_file'] = self.preference

        self.network =  self.find_net.text
        self.stations =  self.find_sta.text
        self.channels =  self.find_cha.text
        self.locations =  self.find_loc.text
        self.directory = self.find_directory.text
        self.filename =  self.find_file.text
        self.csv =  self.generate_file.text
    
    def go_to_examine(self):    
        ExamineIssuesScreen.issueFile = self.examine_directory.text + '/' + self.examine_file.text
        ExamineIssuesScreen.start = self.start
        ExamineIssuesScreen.end = self.end
            
        ExamineIssuesScreen.initiate_screen(ExamineIssuesScreen)
        
    def get_examine_inputs(self):
        main_screen = screen_manager.get_screen('mainScreen')
        ExamineIssuesScreen.directory = main_screen.examine_directory.text
        ExamineIssuesScreen.issueFile = main_screen.examine_file.text
        ExamineIssuesScreen.start = self.start
        ExamineIssuesScreen.end = self.end
    
    def get_generate_inputs(self):
        main_screen = screen_manager.get_screen('mainScreen')
        self.preference = main_screen.generate_pref.text
        masterDict['preference_file'] = self.preference
        self.directory = main_screen.generate_directory.text
        self.csv = main_screen.generate_file.text

        # These are the dates at the top of the screen
        self.start = main_screen.startDate.text
        self.end = main_screen.endDate.text
        
        # These are the dates for creating a csv file internally 
        self.generate_start = main_screen.generate_startDay.text
        self.generate_end = main_screen.generate_endDay.text
        self.generate_start_after = self.ids.generate_start_after_id.state
        self.generate_end_before = self.ids.generate_end_before_id.state
        
        # These are the target constraings for creating a csv internally
        self.generate_network = ','.join([x.strip() for x in main_screen.generate_net.text.split(',')])
        self.generate_station = main_screen.generate_sta.text
        self.generate_location = main_screen.generate_loc.text
        self.generate_channel = main_screen.generate_cha.text
        
        # Do we need to generate a CSV file first? Yes if using internal ticketing system:
        self.generate_csv_state = self.ids.generate_internal_id.active
        
    def go_to_thresholds(self):
        ThresholdsScreen.go_to_thresholdsLayout(ThresholdsScreen)
    
    def go_to_preferences(self):   
        PreferencesScreen.go_to_preferencesLayout(PreferencesScreen)
        
    def autofill_pref(self,preferenceFile):
        if os.path.isfile(preferenceFile):
            try:
                
                with open(preferenceFile) as f:
                    local_dict = locals()
                    exec(compile(f.read(), preferenceFile, "exec"),globals(), local_dict)
                
                self.startDate.text = local_dict["startday"]
                self.endDate.text = local_dict["endday"]
                  
                self.find_file.text = os.path.basename(local_dict["outfile"])
                self.examine_file.text = os.path.basename(local_dict["outfile"])
                
                file_directory = os.path.dirname(local_dict["outfile"]).replace(os.getcwd(),'./')
                self.find_directory.text = file_directory
                self.examine_directory.text = file_directory
                self.generate_directory.text = file_directory
                
#                 self.examine_file.text = local_dict["outfile"]
                self.find_net.text = local_dict["network"]
                self.query_net.text = local_dict["network"]
                self.find_sta.text = local_dict["station"]
                self.query_sta.text = local_dict["station"]
                self.find_loc.text = local_dict["location"]
                self.query_loc.text = local_dict["location"]
                self.find_cha.text = local_dict["channels"]
                self.query_cha.text = local_dict["channels"]
                
#                 full_csv = os.path.basename(local_dict["csvfile"])
                
                self.generate_file.text = os.path.basename(local_dict["csvfile"])
            except:
                self.warning_popup("WARNING: Could not read selected Preference File")
        else:
            self.warning_popup("WARNING: Preference File not found")

    def dismiss_popup(self,*kwargs):
        masterDict["_popup"].dismiss()
    
    def dismiss_warning_popup(self,*kwargs):
        masterDict["warning_popup"].dismiss()
           
    def dismiss_csv_popup(self,*kwargs):
        masterDict["_popup"].dismiss()
        self.generate_report_pt2()
        
    def dismiss_html_popup(self,*kwargs):
        masterDict["_html_popup"].dismiss()  
        
    def pref_load(self):
        content = LoadDialog(load=self.load_pref, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
        
    def file_load(self):
        content = LoadDialog(load=self.load_file, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def load_pref(self, path, filename):
        try:
            
            filename = filename[0].replace(os.getcwd(),'.')
            self.find_pref.text = filename
            self.examine_pref.text = filename
            self.query_pref.text = filename
            self.generate_pref.text = filename
            masterDict['preference_file'] = filename

        except:
            self.warning_popup("WARNING: No file selected")
        self.dismiss_popup()
        
    def load_file(self, path, filename):
        try:
            file_directory = os.path.dirname(filename[0].replace(os.getcwd(),'.'))
            self.find_directory.text = file_directory
            self.examine_directory.text = file_directory
            self.generate_directory.text = file_directory
            
            self.find_file.text = os.path.basename(filename[0])
            self.examine_file.text = os.path.basename(filename[0])
#             self.find_file.text = filename[0]
#             self.examine_file.text = filename[0]
            ExamineIssuesScreen.issueFile = self.examine_file.text
        except Exception as e:
            self.warning_popup("WARNING: %s"  % e)

        self.dismiss_popup()
    
    def csv_load(self):
        content = LoadDialog(load=self.load_csv, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
    
    def load_csv(self,path, filename):
        try:
            file_directory = os.path.dirname(filename[0].replace(os.getcwd(),'.'))
            self.find_directory.text = file_directory
            self.examine_directory.text = file_directory
            self.generate_directory.text = file_directory
            
            self.ids.csv_id.text = os.path.basename(filename[0])
#             self.ids.csv_id.text = filename[0]
        except Exception as e:
            self.warning_popup("WARNING: %s" % e)
        self.dismiss_popup()
    
    def find_issues(self):
        self.get_find_inputs()
        if self.start == "" or self.end == "":
            self.warning_popup("WARNING: Start and End times required")
            
        elif self.preference == "":
            self.warning_popup("WARNING: Preference File required")
        
        elif self.directory == "":
            self.warning_popup("WARNING: Directory required")
        
        elif self.filename == "":
            self.warning_popup("WARNING: Issue File required")

        elif self.network == "":
            self.warning_popup("WARNING: Network required")
            
        else:
            if os.path.isfile(self.directory + '/' + self.filename):
                self.fileType = self.directory + '/' + self.filename
                content = OverwriteDialog(dontDoIt=self.dismiss_popup, doIt=self.remove_file)
                masterDict["_popup"] = Popup(title=self.filename, content=content,
                                size_hint=(0.9, 0.9))
                masterDict["_popup"].open()
            else:
                self.do_find()
       
    def remove_file(self):
        masterDict["_popup"].dismiss()
        file = self.fileType
        os.remove(file)
        try:
            if file == self.directory + '/' + self.filename:
                self.do_find()
        except:
            pass
        try:
            if file == self.directory + '/' + self.csv:
                doGenerate = self.generate_csv()
                if doGenerate == 1:
                    self.generate_report_pt2()
        except Exception as e:
            self.warning_popup("Warning: could not generate final report")
        
    def do_find(self):
        self.get_find_inputs()
        
        if not os.path.isfile(masterDict['metrics_file']):
            self.warning_popup("WARNING: Could not find file of IRIS metrics: %s\nIf connected to the internet, this file can be generated by entering the Thresholds Editor" % masterDict['metrics_file'])
            return 
        
        if not os.path.isfile(masterDict['metadata_file']):
            self.warning_popup("WARNING: Could not find file of IRIS metadata fields: %s\nIf connected to the internet, this file can be generated by entering the Thresholds Editor" % masterDict['metadata_file'])
            return 
        
        
        
        command = 'python findIssues.py --start=' + self.start + ' --end=' + self.end
        
        if self.preference:
            command = command + ' --preference_file=' + self.preference 
        if self.network:
            command = command + ' --network=' + self.network
        if self.stations:
            command = command + ' --stations=' + self.stations
        if self.channels:
            command = command + ' --channels=' + self.channels
        if self.locations:
            command = command + ' --locations=' + self.locations
        if self.filename:
            command = command + ' --outfile=' +  self.directory + '/' + self.filename
        
        # pass along the metric files so that they don't have to be hardcoded elsewhere
        command = command + ' --thresholds_file=' + masterDict['thresholds_file']
        command = command + ' --metrics_file=' + masterDict['metrics_file']
        command = command + " --metadata_file=" + masterDict['metadata_file']
        print(command)
        os.system(command)
 
        # Check file for any failed metrics
        try:
            with open('failedMetrics.txt','r') as f:
                self.failedMetrics = f.read().splitlines()
            os.remove('failedMetrics.txt')
            
            
            if len(self.failedMetrics) > 0:
                failedMetricsList = list()
                failedThresholdsList = list()
                
                for line in self.failedMetrics:
                    if line.split(':')[0] == 'threshold':
                        failedThresholdsList.append(line.split()[1])
                    elif line.split(':')[0] == 'metric':
                        failedMetricsList.append(line.split()[1])
                
                warningText = "WARNING: There were errors Finding Issues.\n\n"
                if len(failedThresholdsList) > 0:
                    warningText = warningText + "THRESHOLDS\nThese thresholds were not found - this is likely because the threshold has been deleted (through the Edit Thresholds form)\nbut not removed from this Preference File (in the Threshold Groups):\n    %s\n\n" % '\n    '.join(failedThresholdsList)
                if len(failedMetricsList) > 0:
                    warningText = warningText + "METRICS\nThese metrics were unable to be retrieved: \n    %s" % '\n    '.join(failedMetricsList)
                 
                self.warning_popup(warningText)
        except:
            self.warning_popup("WARNING: There was an error running FindIssues.py. Check the command line for more information.")
 
    def exit_confirmation(self,*kwargs):
        content = ExitDialog(exit=ExitDialog.do_exit, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Confirm Exit", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
    
    
    def remove_dir(self):
        masterDict["_html_popup"].dismiss()
        if os.path.isfile(self.report_fullPath): os.remove(self.report_fullPath)
        if os.path.isdir(self.zipDir): shutil.rmtree(self.zipDir)
        print('Previous copy removed, generating new Report')
        self.do_generate()
  
#### REMOVE IF NO ISSUES ARISE OUT OF ITS ABSENCE ###
#     def date_checked(self, option, value):
#         if value is True:
#             self.query_options.append(option)
#         else:
#             self.query_options = [v for v in self.query_options if v != option]
#####################################################
            
    def get_ticket_inputs(self, *kwargs):
        main_screen = screen_manager.get_screen('mainScreen')

        masterDict["query_nets"] = main_screen.query_net.text
        masterDict["query_stas"] = main_screen.query_sta.text
        masterDict["query_locs"] = main_screen.query_loc.text
        masterDict["query_chans"] = main_screen.query_cha.text
        masterDict["query_start"] = main_screen.query_start.text
        masterDict["query_start_before"] = main_screen.query_start_before.state
        masterDict["query_end"] = main_screen.query_end.text
        masterDict["query_end_before"] = main_screen.query_end_before.state
        masterDict["query_status"] = main_screen.query_status_btn2.text
        masterDict["query_tracker"] = main_screen.query_tracker_btn2.text
        masterDict["query_cat"] = main_screen.query_category_btn2.text
        masterDict["query_updated"] = main_screen.query_updated.text
        masterDict["query_updated_before"] = main_screen.query_updated_before.state
                
    def find_tickets(self):
        self.get_ticket_inputs(self)
        self.grab_tickets(self)
        
        try:
            if not masterDict["query_start"] == "":
                datetime.datetime.strptime(masterDict["query_start"], '%Y-%m-%d')
            if not masterDict["query_end"] == "":    
                datetime.datetime.strptime(masterDict["query_end"], '%Y-%m-%d')
            if not masterDict["query_updated"] == "":
                datetime.datetime.strptime(masterDict["query_updated"], '%Y-%m-%d')
        
        except:
            self.warning_popup("WARNING: Dates must be formatted YYYY-mm-dd - improper dates have been ignored")

        
        SelectedTicketsScreen.go_to_selectedTickets(SelectedTicketsScreen)
     

            
        
    def grab_tickets(self, *kwargs):
        # Decided it would be easier to be nimble with the querying if it pulls back all tickets
        # and then subsets from there, rather than building a complex sql query that accounts for 
        # all of the different ways that channels (in particular) may be listed/grouped

        # Pull back tickets, subsetting here for status, category, tracker, and dates (if applicable)
        SQL = "SELECT * FROM tickets WHERE "
        
        if not masterDict["query_status"] == "-":
            SQL = SQL + "AND status = '" + masterDict["query_status"] + "' "
        if not masterDict["query_tracker"] == "-":
            SQL = SQL + "AND tracker = '" + masterDict["query_tracker"] +"' "
        if not masterDict["query_cat"] == "-":
            SQL = SQL + "AND category = '" + masterDict["query_cat"] + "' "
        
        if not masterDict["query_start"] == "":
            if masterDict["query_start_before"] == "down":
                SQL = SQL + "AND (start_date <= '" + masterDict["query_start"] + "' OR start_date ='') "
            else:
                SQL = SQL + "AND (start_date >= '" + masterDict["query_start"] + "' OR start_date ='') "
        
        if not masterDict["query_end"] == "":
            if masterDict["query_end_before"] == "down":
                SQL = SQL + "AND (end_date <= '" + masterDict["query_end"] + "' OR end_date ='') "
            else:
                SQL = SQL + "AND (end_date >= '" + masterDict["query_end"] + "' OR end_date ='') "
        
        if not masterDict["query_updated"] == "":
            if masterDict["query_updated_before"] == "down":
                SQL = SQL + "AND (updated <= '" + masterDict["query_updated"] + "' OR updated ='') "
            else:
                SQL = SQL + "AND (updated >= '" + masterDict["query_updated"] + "' OR updated ='') "  
         
        
        if SQL.endswith("WHERE "):
            SQL = SQL.replace("WHERE", "")
        else:
            SQL = SQL.replace("WHERE AND", "WHERE")
         
         
        try:    
            conn = NewTicketScreen.create_connection(NewTicketScreen,database)
            
            if not conn == None:
                allTickets = pd.read_sql_query(SQL, conn)
                conn.close()
            else:
                self.warning_popup("WARNING: Could not retrieve tickets")
                allTickets = ''
                masterDict["tickets"] = ''
                return
        except:
            self.warning_popup("WARNING: Could not retrieve tickets")
            masterDict["tickets"] = ''
            return
        
        try:
            # convert any cases of BH[EHZ] (for example) to lists 
            for ind,row in allTickets.iterrows():
                
                # network(s)
                networks = reportUtils.expandCodes(row['network'])
                allTickets.at[ind,'networks'] = networks
                
                # station(s)
                stations = reportUtils.expandCodes(row['station'])
                allTickets.at[ind,'stations'] = stations
                    
                # location(s)
                locations = reportUtils.expandCodes(row['location'])
                allTickets.at[ind,'locations'] = locations
                
                # channel(s)
                channels = reportUtils.expandCodes(row['channel'])
                allTickets.at[ind,'channels'] = channels
                     
            # Now start subsetting
            subsettedTickets = pd.DataFrame(columns = allTickets.columns)
            
            tmpTickets = pd.DataFrame()  
            for net in masterDict["query_nets"].split(','):
                if net == "" or net == "*" or net == "%" or net == "???":
                    tmpTickets =tmpTickets.append(allTickets)
                else:
                    tmpTickets = tmpTickets.append(allTickets[allTickets['networks'].str.contains(',%s,' % net.replace('?', '.?').replace('*','.*')) == True])
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['networks'].str.match(",\*,")])
            subsettedTickets = tmpTickets.copy()
            
            tmpTickets = pd.DataFrame()  
            for sta in masterDict["query_stas"].split(','):
                if sta == "" or sta == "*" or sta == "%" or sta == "???":
                    tmpTickets =tmpTickets.append(subsettedTickets)
                else:
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['stations'].str.contains(',%s,' % sta.replace('?', '.?').replace('*','.*')) == True])
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['stations'].str.match(",\*,")])
            subsettedTickets = tmpTickets.copy()
            
            tmpTickets = pd.DataFrame()  
            for loc in masterDict["query_locs"].split(','):
                if loc == "" or loc == "*" or loc == "%" or loc == "???":
                    tmpTickets =tmpTickets.append(subsettedTickets)
                else:
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['locations'].str.contains(',%s,' % loc.replace('?', '.?').replace('*','.*')) == True])
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['locations'].str.match(",\*,")])
            subsettedTickets = tmpTickets.copy()
            
            tmpTickets = pd.DataFrame()  
            for chan in masterDict["query_chans"].split(','):
                if chan == "" or chan == "*" or chan == "%" or chan == "???":
                    tmpTickets =tmpTickets.append(subsettedTickets)
                else:
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['channels'].str.contains(',%s,' % chan.replace('?', '.?').replace('*','.*')) == True])
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['channels'].str.match(",\*,")])
            
            subsettedTickets = tmpTickets.copy() 
            subsettedTickets.drop_duplicates(inplace=True)
            
            try:
                masterDict["tickets"] = subsettedTickets.drop(['networks', 'stations','locations','channels'], axis=1).sort_index(axis = 0) 
            except:
                try:
                    masterDict["tickets"] = pd.DataFrame(columns = allTickets.columns).drop(['networks', 'stations','locations','channels'], axis=1)   
                except:
                    masterDict["tickets"] = ""
           
        except:
            masterDict["tickets"] = ""
    
    
    
      
    
    def go_To_NewTickets(self, *kwargs):
        NewTicketScreen.go_to_newTicketsScreen(NewTicketScreen)
 
    def generate_csv(self):   
        self.get_generate_inputs()
        
        if self.csv == "":
            self.warning_popup("WARNING: CSV File required")
            return 0
    
        if self.generate_directory == "":
            self.warning_popup("WARNING: CSV Directory required")
            return 0
        
        with open(self.preference) as f:
                local_dict = locals()
                exec(compile(f.read(), self.preference, "exec"),globals(), local_dict)
        
        try:
            if not self.generate_start == "":
                datetime.datetime.strptime(self.generate_start, '%Y-%m-%d')
            if not self.generate_end == "":    
                datetime.datetime.strptime(self.generate_end, '%Y-%m-%d')
        
        except:
            self.warning_popup("WARNING: Dates must be formatted YYYY-mm-dd")
            return
        

        
        # Do we need to generate a CSV file first? Yes if using internal ticketing system:
        self.generate_csv_state = self.ids.generate_internal_id.active
        
        
        # Pull back tickets, subsetting here for status, category, tracker, and dates (if applicable)
        SQL = "SELECT * FROM tickets WHERE "
        
        statusList = list()
        for status in ['New','In Progress','Resolved','Closed','Rejected']:
            if self.ids['generate_%s_id' % status.replace(' ','_').lower()].state == 'down':
                statusList.append(status)
        statusList = "' OR status = '".join(statusList)
        
        if statusList:
            SQL = SQL + "(status = '" + statusList + "') AND "

        trackerList = list()
        for tracker in ['Data Problems', 'Support']:
            if self.ids['generate_%s_id' % tracker.replace(' ','_').lower()].state == 'down':
                trackerList.append(tracker)
        trackerList = "' OR tracker = '".join(trackerList)
          
        if trackerList:
            SQL = SQL + "(tracker = '" + trackerList + "') "      
        
        if not self.generate_start == "":
            if self.generate_start_after == "down":
                SQL = SQL + "AND (start_date >= '" + self.generate_start + "' OR start_date ='') "
            else:
                SQL = SQL + "AND (start_date <= '" + self.generate_start + "' OR start_date ='') "
        
        if not self.generate_end == "":
            if self.generate_end_before == "down":
                SQL = SQL + "AND (end_date <= '" + self.generate_end + "' OR end_date ='') "
            else:
                SQL = SQL + "AND (end_date >= '" + self.generate_end + "' OR end_date ='') " 
         
        
        if SQL.endswith("WHERE "):
            SQL = SQL.replace("WHERE", "")
        else:
            SQL = SQL.replace("WHERE AND", "WHERE")
         
         
        try:    
            conn = NewTicketScreen.create_connection(NewTicketScreen,database)
            
            if not conn == None:
                allTickets = pd.read_sql_query(SQL, conn)
                conn.close()
            else:
                self.warning_popup("WARNING: Could not retrieve tickets")
                return
        except:
            self.warning_popup("WARNING: Could not retrieve tickets")
            return
                
        try:
            # convert any cases of BH[EHZ] (for example) to lists 
            for ind,row in allTickets.iterrows():
                
                # network(s)
                networks = reportUtils.expandCodes(row['network'])
                allTickets.at[ind,'networks'] = networks
                
                # station(s)
                stations = reportUtils.expandCodes(row['station'])
                allTickets.at[ind,'stations'] = stations
                    
                # location(s)
                locations = reportUtils.expandCodes(row['location'])
                allTickets.at[ind,'locations'] = locations
                
                # channel(s)
                channels = reportUtils.expandCodes(row['channel'])
                allTickets.at[ind,'channels'] = channels
                     
            # Now start subsetting
            subsettedTickets = pd.DataFrame(columns = allTickets.columns)
            
            tmpTickets = pd.DataFrame()  
            for net in self.generate_network.split(','):
                if net == "" or net == "*" or net == "%" or net == "???":
                    tmpTickets =tmpTickets.append(allTickets)
                else:
                    tmpTickets = tmpTickets.append(allTickets[allTickets['networks'].str.contains(',%s,' % net.replace('?', '.?').replace('*','.*')) == True])
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['networks'].str.match(",\*,")])
            subsettedTickets = tmpTickets.copy()
            
            tmpTickets = pd.DataFrame()  
            for sta in self.generate_station.split(','):
                if sta == "" or sta == "*" or sta == "%" or sta == "???":
                    tmpTickets =tmpTickets.append(subsettedTickets)
                else:
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['stations'].str.contains(',%s,' % sta.replace('?', '.?').replace('*','.*')) == True])
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['stations'].str.match(",\*,")])
            subsettedTickets = tmpTickets.copy()
            
            tmpTickets = pd.DataFrame()  
            for loc in self.generate_location.split(','):
                if loc == "" or loc == "*" or loc == "%" or loc == "???":
                    tmpTickets =tmpTickets.append(subsettedTickets)
                else:
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['locations'].str.contains(',%s,' % loc.replace('?', '.?').replace('*','.*')) == True])
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['locations'].str.match(",\*,")])
            subsettedTickets = tmpTickets.copy()
            
            tmpTickets = pd.DataFrame()  
            for chan in self.generate_channel.split(','):
                if chan == "" or chan == "*" or chan == "%" or chan == "???":
                    tmpTickets =tmpTickets.append(subsettedTickets)
                else:
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['channels'].str.contains(',%s,' % chan.replace('?', '.?').replace('*','.*')) == True])
                    tmpTickets = tmpTickets.append(subsettedTickets[subsettedTickets['channels'].str.match(",\*,")])
            
            subsettedTickets = tmpTickets.copy() 
            subsettedTickets.drop_duplicates(inplace=True)
            
            try:
                selected_tickets = subsettedTickets.drop(['networks', 'stations','locations','channels'], axis=1).sort_index(axis = 0) 
            except:
                try:
                    selected_tickets = pd.DataFrame(columns = allTickets.columns).drop(['networks', 'stations','locations','channels'], axis=1)   
                except:
                    selected_tickets = pd.DataFrame(columns=['id','tracker','target','start_date','category','subject','thresholds','images','caption','links','status','end_date','description'])
            
            selected_tickets['target'] = selected_tickets['network'] + " " + selected_tickets['station'] + " " + selected_tickets['location'] + " " + selected_tickets['channel']
        
        except:
            selected_tickets = pd.DataFrame(columns=['id','tracker','target','start_date','category','subject','thresholds','images','caption','links','status','end_date','description'])
        

        sorted_tickets = selected_tickets[['id','tracker','target','start_date','category','subject','thresholds','images','caption','links','status','end_date','description']]
        self.sorted_tickets = sorted_tickets.sort_values(by=['tracker','subject','target','start_date'])
        
        if os.path.isfile(self.directory + '/' + self.csv):
            self.fileType = self.directory + '/' + self.csv
            content = OverwriteDialog(dontDoIt=self.dismiss_popup, doIt=self.remove_file)
            masterDict["_popup"] = Popup(title=self.csv, content=content,
                            size_hint=(0.9, 0.9))
            masterDict["_popup"].open()
        else:
            try: 
                self.write_csv()
            except:
                self.warning_popup("WARNING: Could not create directory %s, is a directory specified?" % self.directory)
                return
        
        return 1
    

    
    def write_csv(self):
        self.get_generate_inputs()
        
        dir = self.directory
        if not os.path.isdir(dir):
            print("INFO: Creating new directory: %s" % dir)
            os.makedirs(dir)
        
        
        self.sorted_tickets.to_csv(self.directory + '/' + self.csv, index=False)
        print("INFO: CSV file generated")
    
    def generate_report(self):
        self.get_generate_inputs()

        if self.generate_csv_state == True:
            # We need to first generate the CSV file using the local ticketing system
            print("INFO: Using internal ticketing system")
            
            
            
            try:
                with open(self.preference) as f:
                    local_dict = locals()
                    exec(compile(f.read(), self.preference, "exec"),globals(), local_dict)
            except:
                self.warning_popup("WARNING: Preference File Required")
                return
            
            YYYYmmdd = ''.join(self.start.split('-'))
            if YYYYmmdd == "":
                # Then it's not filled in at the top, and we need to use it from the preference file.
                try:
                    with open(self.preference) as f:
                        local_dict = locals()
                        exec(compile(f.read(), self.preference, "exec"),globals(), local_dict)
                    YYYYmmdd = ''.join(local_dict["startday"].split('-'))
#                     self.startDate.text = local_dict["startday"]
                except:
                    self.warning_popup("WARNING: Tried to get Start Date from Preference file(since it was left empty),\nbut failed to read Preference File")
                    return
            if not self.generate_network == "":
                network = self.generate_network
            else:
                network = local_dict['network']
            
            # The network report should be put into the same directory as the csv file even if that differs from the preference)files
#             dirToUse = os.path.dirname(self.csv)
            dirToUse = self.directory
            print(dirToUse)
#             self.report_filename = dirToUse + '/' + local_dict['network'] +'_Netops_Report_' + month
            self.report_filename = network +'_Netops_Report_' + YYYYmmdd
#             self.zipDir = local_dict["directory"] + self.report_filename
            self.zipDir = dirToUse + '/' + self.report_filename
            self.report_fullPath =  self.zipDir +'/' + self.report_filename + '.html' 
            
            
            
            
            if os.path.isfile(self.directory + '/' + self.csv):
                self.fileType = self.directory + '/' + self.csv
                content = OverwriteDialog(dontDoIt=self.dismiss_csv_popup, doIt=self.remove_file)
                masterDict["_popup"] = Popup(title=self.csv, content=content,
                                             size_hint=(0.9, 0.9))
                masterDict["_popup"].open()
            else:
                doGenerate = self.generate_csv()
                if doGenerate == 1:
                    self.generate_report_pt2()
            
        else:

            try:
                YYYYmmdd = ''.join(self.start.split('-'))
            except:
                self.warning_popup("WARNING: Unable to parse start date, is it formatted correctly?")
                return
            try:
                with open(self.preference) as f:
                    local_dict = locals()
                    exec(compile(f.read(), self.preference, "exec"),globals(), local_dict)
            except:
                self.warning_popup("WARNING: Preference File required")
                return
            
            
            # The network report should be put into the same directory as the csv file even if that differs from the preference)files
#             dirToUse = os.path.dirname(self.csv)
            dirToUse = self.directory
            
            self.report_filename = network +'_Netops_Report_' + YYYYmmdd
#             self.zipDir = local_dict["directory"] + self.report_filename
            self.zipDir = dirToUse + '/' + self.report_filename

            self.report_fullPath =  self.zipDir +'/' + self.report_filename + '.html' 
            
            self.generate_report_pt2()   
            
    def generate_report_pt2(self):
        self.get_generate_inputs()

        try:
            with open(self.preference) as f:
                local_dict = locals()
                exec(compile(f.read(), self.preference, "exec"),globals(), local_dict)
        
            network = local_dict["network"]
        except:
            self.warning_popup("WARNING: Preference File required")
            return
        
        if os.path.isdir(self.zipDir) or os.path.isfile(self.report_fullPath):
            content = ReportDialog(a =self.dismiss_html_popup, b=self.remove_dir)
            masterDict["_html_popup"] = Popup(title=self.zipDir, content=content,
                            size_hint=(0.9, 0.9))
            masterDict["_html_popup"].open()
            
        else:
            try:
                self.do_generate()
            except:
                self.warning_popup("WARNING: Problem while generating report")
                             
    def do_generate(self):
        
        
        try: 
            if not self.start == '':
                datetime.datetime.strptime(self.start, '%Y-%m-%d').strftime('%B %d, %Y')
            if not self.end == '':
                datetime.datetime.strptime(self.end, '%Y-%m-%d').strftime('%B %d, %Y')
        except:
            self.warning_popup('WARNING: Are the dates properly formatted? YYYY-mm-dd')
            return
           
        if self.start == '' or self.end == '':
            self.warning_popup('WARNING: Start and/or End not provided, report filled in missing values from Preference File\n                      Fill in missing dates and Generate Report again if that was unintended') 


        command = 'python generateHTML.py --start=' + self.start + " --end=" + self.end
        if self.preference:
            command = command + ' --preference_file=' + self.preference
        if self.csv:
            command = command + ' --ticketsfile=' + self.directory + '/' + self.csv  
        if self.generate_network:
            command = command + ' --network=' + self.generate_network
        command = command + ' --htmldir=' + self.zipDir + ' --html_file_path=' + self.report_fullPath 
        command = command + ' --metrics_file=' + masterDict['metrics_file']
        command = command + ' --thresholds_file=' + masterDict['thresholds_file']
        print(command)
        os.system(command)
        
        
        # Provide a popup that indicates the success or failure of report generation
        # generateHTML now produces a file that indicates anything that went wrong, if anything did
        try:
            with open('generateHTML_status.txt','r') as f:
                self.generateReport_status = f.read()
            os.remove('generateHTML_status.txt')
            
            print(self.generateReport_status)
            
            
            if len(self.generateReport_status) > 0:
                self.warning_popup("WARNING: There were errors generating the report: \n%s" % self.generateReport_status)
            else:
                self.warning_popup("Report successfully generated in %s" % (self.report_fullPath))
                masterDict["warning_popup"].title = "Success"
        except Exception as e:
            print(e)
            self.warning_popup("WARNING: There was an error running generateHTML.py. Check the command line for more information.")
 


    def help_text(self,whichOne):
        
        if whichOne == 0:
            helpText = '''QUICK INTRODUCTION TO QuARG

This is a very simple overview of the use of QuARG. Use the "Next" and "Previous" buttons
to the right to scroll through the images and and short descriptions of each page. 

To see more detailed documentation, you can use the "Detailed Documentation" button below.  
This takes you to a page with a dense and detailed amount of information. 
It may be more difficult to digest, but you can do a control-find to narrow down your search.  
This is good for very specific and particular questions about how to use QuARG. 


QuARG is composed of 4 tabs that are associated with 4 processes or actions:
- Find Issues
- Examine Issues
- View Tickets
- Generate Report

Each of those tabs corresponds to a step in the process of creating your Quality Assurance Report.
            '''
        
        if whichOne == 1:
            helpText = '''FIND ISSUES

  1. Navigate to and select your Preference File using the Browse button - an example file 
      preference_file_IRIS.py is provided in the base quarg/ directory
  2. Autofill the remaining fields from the Preference File
  3. Change any of the fields, if necessary - QuARG will use the values in the form over those in 
      the Preference File. If you change the Directory field, use the Apply Changes button to propagate
      that new directory to the other tabs so that you don't have to change in manually in each tab. 
  4. Hit the Find Issues button - this will write to the file specified by the Directory and Issue
      File fields

  To view the issues, move on to the Examine Issues tab.

  There are two other important buttons on this tab:

  A. Edit Preferences
      This is where you can edit the preference file to suit your network and report needs
  B. Edit Thresholds
      This is where you can edit, add, or remove threshold definitions
 
            '''
        
        if whichOne == 2:
            helpText = '''PREFERENCE FILE
            
  The Preference File is where you specify a number of parameters that will be used consistently
  for your network reports. This way, QuARG can make some smart choices about filling in 
  repetitive fields, reducing the amount of input you need to provide as a user to run the program. 
  This is where you can create a new or edit an existing Preference File.
    
  1. Provide a filename or Browse to an existing file
  2. If an existing Preference File, load the file
  3. Update Target information
  4. Update directory and files
  5. Select which Instrument Groups should be used when Finding Issues
  6. Select which Threshold Groups should be used when Finding Issues
  7. Associate Thresholds with their Threshold Groups - push the button to open new screen
  8. Select where the Metrics and Metadata should be sourced from
  9. Select the frequency of the reports (determines the dates that will be autofilled)
  10. Update the header fields
  11. IMPORTANT: Save the changes

  
'''
            
        if whichOne == 3:
            helpText = '''PREFERENCE FILE THRESHOLD GROUPS
            
  This is where you group Thresholds together in Threshold Groups. When the Threshold Group is
  run during Find Issues, all thresholds in that group will be run. In the previous page, you can
  turn on or off entire groups, which will prevent that group from getting run during Find Issues.
  If you never want a threshold to run, then you can leave it unassociated with any group.  
  
  Adding Thresholds
  1. Select one or more thresholds
  2. Select the group to associate the thresholds with
  3. Hit Add button
  
  Removing Thresholds
  1. Select Group:Threshold(s) to remove
  2. Hit Remove button
  
'''
        
        if whichOne == 4: 
            helpText = '''THRESHOLDS FILE
            
  Thresholds are, in many ways, at the heart of QuARG. Thresholds are combinations of metrics
  (with associated cutoff values) that have been shown to find some common issues. These are 
  used to find issues in the data, which are then reviewed by you to determine the cause. 
  
  This is where you can add, update, or remove thresholds. It is a complex form and it is suggested
  that you look more closely at the detailed documentation before you alter the thresholds. 
  
  1. Select the Threshold and Instrument Group that you want to work on 
  2. Select the Metric or Metadata Field that the threshold should use
  3. Select Threshold Options (if any)
  4. Apply Channel Options (if applicable)
  5. Supply Cutoff values
  6. Add Metric to Threshold Definition
  7. Delete part of a threshold definition by selecting it and hitting the delete button
  8. IMPORTANT: Save all changes
  
  You can also Add/Remove/Edit:
  A. Threshold names
  B. Instrument Groups
  C. Threshold Groups
  
  And... 
  D. View all current thresholds
  
  
  
            '''
            
        if whichOne == 5:
            helpText = '''EXAMINE ISSUES

  1. Ensure that the Directory and Issue File fields point to the file you want to look at
  2. Hit the Examine Issues button

  The Examine Issues button will take you to another screen that will allow you to navigate 
  through all of the issues that QuARG found. There you can access common tools used to diagnose 
  the issues, keep track of which issues you've looked at, and create new tickets, amongst other
  things.
            '''
            
        if whichOne == 6:
            helpText = '''EXAMINE ISSUES PANE
            
  After hitting "Examine Issues" from the previous screen, you will be brought here. This is
  where you can navigate through all of the potential issues as you diagnose and ticket true issues. 
  
  There are several general sections to the screen:
  1. Target, Metric, Threshold, and Dates - used for the diagnosis tools, as well as for some of the 
       navigation options.
  2. Navigation tools - go to a specific target or threshold, thumb through issues one station
       at a time, view only those marked as 'TODO' or see all of the issues. 
  3. Notes - and notes to the selected lines in the Issue Pane. These notes are for your own
       tracking but can be imported into a ticket description if you wish.
  4. Diagnosis Tools - links to web services that may be helpful in diagnosing the issue. 
       They draw on the target, dates, and/or metric fields depending on the service. 
  5. Status Options - mark the status of the selected issues: this is used for your
       own tracking and is not directly connected to any ticket. 
  6. Issue Pane - this will populate with a selectable list all of the issues that match the 
       criteria determined with the Navigation Tools. 
  7. IMPORTANT: Save any progress you have made using the Save button. Closing without saving
       will lose any progress since the last save.
  8. Create Ticket - takes you to the Create Ticket screen, described next. 
            '''
        
        if whichOne == 7:
            helpText = '''CREATE TICKET
            
  Tickets are the backbone of the final report. They track which issues are open and closed and
  are imported as the content to the report - therefore, any information that should be included
  in the final report should be included in the ticket. 
  
  Fill out the required fields - Tracker, Subject, Status, Category, Target
       1. Tracker:  there are two trackers, Data Problems and Support.
       2. Subject: the subject line of the ticket, a very short description of the issue
       3. Status: the status of the problem, very generally speaking it is Open vs Closed
       4. Category: broad category that the issue falls under
       5. Target: the Network, Station, Location, and Channel(s) affected by the issue.
       
  Supply any other fields
       A. Description: more informative description of the issue
       B. Images: attach images and captions, using popup, to the ticket if that helps describe the issue
       C. URLs: attach links, using popup, to the ticket if that helps describe the issue
       D. Start/End: dates that the issue began or was resolved, respectively
       E. Thresholds: selectable list of all possible thresholds - select those used to find this issue
       
  6. Submit the ticket to save it
             ''' 
            
        if whichOne == 8:
            helpText = '''VIEW TICKETS
            
  This is where you can see and edit existing tickets, or create a new ticket.
  
  1. (Optional) Fill in any fields that you may want in your query to limit which tickets are retrieved 
      A. Targets - any of the target fields can be comma-separated lists and include wildcards (*,?)
      B. Updated - the date that the ticket was last updated, and associated on/after or on/before
      C. Start and End dates - the start and end times supplied in the ticket for when the issue
            began and was resolved, respectively. If no start or end is supplied in the ticket, 
            then it will still show up even if Start/End constraints are put on the query. 
      D. Status/Tracker/Category - select the specific Status, Tracker, and/or Category that the ticket
            belongs to. You can either select one option from the dropdown, or "Select All" ("-")
  
  2. Hit the See Tickets button

  This will pull up another screen that has a list of all tickets that match your criteria (if any).
  Clicking on any line will bring up a page that contains all of the information for that ticket and
  allow you to edit or delete the ticket. 
  
  Notes: 1. Be wary of being too restrictive in the query - tickets that are missing may show up if 
  the filters are relaxed.  2. All date fields has an on/before or on/after option. 3. Leaving 
  any fields blank will act as a wildcard.'''
            
        if whichOne == 9:
            helpText = '''VIEW TICKETS LIST
            
  This is a relatively simple screen. It contains a list of all tickets that matched the query criteria
  supplied in the previous screen.  Each line is selectable, and clicking on one will take you to the 
  Update Ticket Screen where you can see the ticket and update or delete it if you want.
  
  1. (Optional) Use the dropdown in the top right to sort the tickets 
  2. Select the ticket by clicking on it. 
  
   
'''
        
        if whichOne == 10:
            helpText = '''UPDATE TICKET
            
  The Update Ticket form is very similar to the Create Ticket form, except with the option to update
  or delete the ticket, rather than create one. When entering this form, all fields from the ticket
  will automatically display.  You can edit any of them from there. 
  
  Required Fields
  1. Tracker
  2. Subject
  3. Status
  4. Category
  5. Target
  
  All other fields are optional
  
  6. Update Ticket - this will update the ticket to reflect any changes you have made
  7. Delete Ticket - deletes the ticket, first asking if you are sure
  
  8. After Updating the ticket, the Last Updated time will change
            
'''
        
        if whichOne == 11:
            helpText = '''GENERATE REPORT
  
  Reports are generated from the tickets that you've created. Here, you specify which tickets should
  be used for the report, and then create it.
  
  1. Ensure that the Preference File field points to the correct Preference File. 
  2. Autofill the Start and End Dates, as well as Directory and CSV file from the Preference File (alter 
      as necessary)
  3. Fill in any fields that you want in your query to limit which tickets are used in the report
  4. Hit the Generate Report button
  
  Note: it is possible to use another ticketing system, if you already have one that you use. In this
  case, uncheck the "Use QuARG Tickets for Report?" button and ensure that you have exported your 
  tickets into a properly-formatted csv file at the location specified by the Directory and CSV File
  fields. [See detailed documentation for the format.]
            '''

#         if whichOne == 12:
#             helpText = '''
#             
#             '''   
        
        
        return helpText
     
    def open_detailed_documentation(self):
        command = 'open docs/DOCUMENTATION.html'
        os.system(command)

class PreferencesScreen(Screen):
    instrument_list_rv = ObjectProperty()
    thresholdGroups_list_rv = ObjectProperty()
    metric_source_btn = ObjectProperty()
    metadata_source_btn = ObjectProperty()
    metric_source_text = ObjectProperty()
    metric_browse_btn = ObjectProperty()
    metadata_source_text = ObjectProperty()
    metadata_browse_btn = ObjectProperty()
    preference_file = ObjectProperty()
    pref_net = ObjectProperty()
    pref_sta = ObjectProperty()
    pref_loc = ObjectProperty()
    pref_cha = ObjectProperty()
    pref_H = ObjectProperty()
    pref_V = ObjectProperty()
    pref_dir = ObjectProperty()
    pref_issue = ObjectProperty()
    pref_ticket = ObjectProperty()
    pref_author = ObjectProperty()
    pref_project = ObjectProperty()
    pref_email = ObjectProperty()
    frequency_btn = ObjectProperty()
    
    instrument_selectionIndices = list()
    threshold_selectionIndices = list()
    thresholdGroups_selectionIndices = list()
    
    

    def go_to_preferencesLayout(self):
        preferences_screen = screen_manager.get_screen('preferencesScreen')
        preferenceFile = ''
        masterDict['groups_and_names'] = list()
            
        try:
            preferenceFile = masterDict['preference_file']
            if os.path.dirname(preferenceFile) == os.getcwd():
                preferences_screen.preference_file.text = "./%s" % os.path.basename(preferenceFile)
            else:
                preferences_screen.preference_file.text = preferenceFile
            
        except Exception as e:
            masterDict['preference_file'] = preferenceFile
            
        
        with open(masterDict['thresholds_file']) as f:
            local_dict = locals()
            exec(compile(f.read(), masterDict['thresholds_file'], "exec"), globals(), local_dict)
            
        masterDict['groupsDict'] = local_dict['groupsDict']  
        masterDict['thresholdsDict'] = local_dict['thresholdsDict']
        masterDict['instrumentGroupsDict'] = local_dict['instrumentGroupsDict']
        masterDict['thresholdGroups'] = local_dict['thresholdGroups']
        masterDict['pref_threshold_names'] = sorted(list(masterDict['thresholdsDict'].keys()))
        
        
        
        my_instruments = [{'text': x} for x in masterDict['groupsDict']]
        preferences_screen.instrument_list_rv.data = my_instruments 
        
        my_threshold_groups =  [{'text': x} for x in masterDict['thresholdGroups']]  
        preferences_screen.thresholdGroups_list_rv.data = my_threshold_groups 
        
        if not preferenceFile == '':
            self.load_preference_file(self, preferenceFile)


    def load_preference_file(self, preferenceFile):
        preferences_screen = screen_manager.get_screen('preferencesScreen')

        masterDict['preference_file'] = preferenceFile
        if os.path.isfile(preferenceFile):
            try: 
                with open(preferenceFile) as f:
                    local_dict = locals()
                    exec(compile(f.read(), preferenceFile, "exec"),globals(), local_dict)
                    
                masterDict['preference_groupsDict'] = local_dict['groupsDict']
                masterDict['preference_thresholdGroups'] = local_dict['thresholdGroups']
                masterDict['preference_chanTypes'] = local_dict['chanTypes']
                masterDict['preference_instruments'] = local_dict['instruments']
                masterDict['preference_reportFrequency'] = local_dict['reportFrequency']
                masterDict['preference_network'] = local_dict['network']
                masterDict['preference_station'] = local_dict['station']
                masterDict['preference_channels'] = local_dict['channels']
                masterDict['preference_location'] = local_dict['location']
                masterDict['preference_metricSource'] = local_dict['metricSource']
                masterDict['preference_metadataSource'] = local_dict['metadataSource']
                masterDict['preference_issueFile'] = local_dict['filename']
                masterDict['preference_ticketFile'] = local_dict['csvfilename']
                masterDict['preference_author'] = local_dict['author']
                masterDict['preference_project'] = local_dict['project']
                masterDict['preference_email'] = local_dict['email']
                masterDict['preference_directory'] = local_dict['mainDir']
    
                preferences_screen.pref_net.text = masterDict['preference_network'] 
                preferences_screen.pref_sta.text = masterDict['preference_station']
                preferences_screen.pref_loc.text = masterDict['preference_location']
                preferences_screen.pref_cha.text = masterDict['preference_channels']
                
                preferences_screen.pref_dir.text = masterDict['preference_directory'] 
                preferences_screen.pref_issue.text = masterDict['preference_issueFile'] 
                preferences_screen.pref_ticket.text = masterDict['preference_ticketFile'] 
                preferences_screen.pref_author.text = masterDict['preference_author'] 
                preferences_screen.pref_project.text = masterDict['preference_project'] 
                preferences_screen.pref_email.text = masterDict['preference_email'] 
                preferences_screen.frequency_btn.text = masterDict['preference_reportFrequency'] 
                
                preferences_screen.pref_H.text = ','.join(masterDict['preference_chanTypes']['H'])
                preferences_screen.pref_V.text = ','.join(masterDict['preference_chanTypes']['V'])
                
                if masterDict['preference_metricSource'] == 'IRIS':
                    preferences_screen.metric_source_text.text = ''
                    preferences_screen.metric_source_text.disabled = True
                    preferences_screen.metric_browse_btn.disabled = True
                    preferences_screen.metric_source_btn.text = 'IRIS'
                else:
                    preferences_screen.metric_source_text.text = masterDict['preference_metricSource']
                    preferences_screen.metric_source_btn.text = 'Local ISPAQ SQLite Database'
                    preferences_screen.metric_source_text.disabled = False
                    preferences_screen.metric_browse_btn.disabled = False
                
                if masterDict['preference_metadataSource'] == 'IRIS':
                    preferences_screen.metadata_source_text.text = ''
                    preferences_screen.metadata_source_text.disabled = True
                    preferences_screen.metadata_browse_btn.disabled = True
                    preferences_screen.metadata_source_btn.text = 'IRIS'
                else:
                    preferences_screen.metadata_source_text.text = masterDict['preference_metadataSource']
                    preferences_screen.metadata_source_btn.text = 'Local Metadata File'
                    preferences_screen.metadata_source_text.disabled = False
                    preferences_screen.metadata_browse_btn.disabled = False
    
                for instrument in [x.strip() for x in masterDict['preference_instruments']]:
                    if not instrument == '':
                        try:
                            node = masterDict['groupsDict'].index(instrument)
                            preferences_screen.instrument_list_rv._layout_manager.select_node(node)
                            if node not in self.instrument_selectionIndices:
                                self.instrument_selectionIndices.append(node)
                                
                        except:
                            print("INFO: Could not load Instrument Group %s from preference file" % instrument)
                
                for group in [x.strip() for x in masterDict['preference_thresholdGroups']]:
                    if not group == '':
                        try:
                            node = masterDict['thresholdGroups'].index(group)
                            preferences_screen.thresholdGroups_list_rv._layout_manager.select_node(node)
                            if node not in self.thresholdGroups_selectionIndices:
                                self.thresholdGroups_selectionIndices.append(node)
                        except:
                            # Then the group has been deleted elswhere and it shouldn't be included   
                            pass
                  
                  
                group_threshold_pairs = list()          
                if not masterDict['preference_file'] == '':
                    for group in masterDict['preference_groupsDict'].keys():
                        for threshold in masterDict['preference_groupsDict'][group]:
                            group_threshold_pairs.append(group + " :: " + threshold)
                masterDict['groups_and_names'] = [ x for x in group_threshold_pairs]
                masterDict['groups_and_names'].sort()         
        
            except:
                self.warning_popup(self, "WARNING: Unable to load file")
        else:
            self.warning_popup("WARNING: Preference File not found")
                
        
        
    
    def pref_file_load(self):
        content = LoadDialog(load=self.load_pref_file, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load preference file", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def load_pref_file(self, path, filename):
        preferences_screen = screen_manager.get_screen('preferencesScreen')

        try:
            if os.path.dirname(filename[0]) == os.getcwd():
                preferences_screen.preference_file.text = "./%s" % os.path.basename(filename[0])
            else:
                preferences_screen.preference_file.text = filename[0]
        except:
            self.warning_popup("WARNING: No file selected")
        self.dismiss_popup()
        
    def thresh_file_load(self):
        content = LoadDialog(load=self.load_thresh_file, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load thershold file", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def load_thresh_file(self, path, filename):
        preferences_screen = screen_manager.get_screen('preferencesScreen')

        try:
            if os.path.dirname(filename[0]) == os.getcwd():
                preferences_screen.pref_thresh.text = "./%s" % os.path.basename(filename[0])
            else:
                preferences_screen.pref_thresh.text = filename[0]
        except:
            self.warning_popup("WARNING: No file selected")
        self.dismiss_popup()        
        
    def working_dir_load(self):
        content = LoadDialog2(load=self.load_working_dir, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load working directory", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def load_working_dir(self, path, filename):
        preferences_screen = screen_manager.get_screen('preferencesScreen')

        try:
            if filename[0] == os.getcwd():
                preferences_screen.pref_dir.text = "./"
            else:
                preferences_screen.pref_dir.text = filename[0]
        except:
            self.warning_popup("WARNING: No file selected")
        self.dismiss_popup()  
        
    def meta_file_load(self):
        content = LoadDialog(load=self.load_meta_file, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load metadata file", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def load_meta_file(self, path, filename):
        preferences_screen = screen_manager.get_screen('preferencesScreen')

        try:
            if os.path.dirname(filename[0]) == os.getcwd():
                preferences_screen.metadata_source_text.text = "./%s" % os.path.basename(filename[0])
            else:
                preferences_screen.metadata_source_text.text = filename[0]
        except:
            self.warning_popup("WARNING: No file selected")
        self.dismiss_popup()    
        
    def metric_file_load(self):
        content = LoadDialog(load=self.load_metric_file, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load metric file", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def load_metric_file(self, path, filename):
        preferences_screen = screen_manager.get_screen('preferencesScreen')

        try:
            if os.path.dirname(filename[0]) == os.getcwd():
                preferences_screen.metric_source_text.text = "./%s" % os.path.basename(filename[0])
            else:
                preferences_screen.metric_source_text.text = filename[0]
        except:
            self.warning_popup("WARNING: No file selected")
        self.dismiss_popup()   
              
    def deactivate_metric_source_text(self, *kwargs):
        preferences_screen = screen_manager.get_screen('preferencesScreen')
        if preferences_screen.metric_source_btn.text == 'IRIS':
            preferences_screen.metric_source_text.disabled = True
            preferences_screen.metric_browse_btn.disabled = True
        else:
            preferences_screen.metric_source_text.disabled = False
            preferences_screen.metric_browse_btn.disabled = False
            
    def deactivate_metadata_source_text(self, *kwargs):
        preferences_screen = screen_manager.get_screen('preferencesScreen')
        if preferences_screen.metadata_source_btn.text == 'IRIS':
            preferences_screen.metadata_source_text.disabled = True
            preferences_screen.metadata_browse_btn.disabled = True
        else:
            preferences_screen.metadata_source_text.disabled = False
            preferences_screen.metadata_browse_btn.disabled = False

    def go_to_thresholdGroups(self):
#         if not masterDict['preference_file'] == "":
#             try: 
#                 masterDict['preference_groupsDict']
#             except:
#                 self.warning_popup("WARNING: Preference File has been selected but not loaded\n       Either load the file")
            
        ThresholdGroupsScreen.go_to_thresholdGroups(ThresholdGroupsScreen)
        
    def exit_confirmation(self,*kwargs):
        content = ExitDialog(exit=ExitDialog.do_exit, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Confirm Exit", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
        
    def dismiss_popup(self,*kwargs):
        masterDict["_popup"].dismiss()

    def warning_popup(self, txt):
        
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=txt, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_warning_popup)


        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        masterDict["warning_popup"] = Popup(title="Warning", content=popupContent, size_hint=(.66, .66))
        masterDict["warning_popup"].open()

    def dismiss_warning_popup(self,*kwargs):
        masterDict["warning_popup"].dismiss()
        
    def doubleCheck_popup(self, txt):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        warningLabel = Label(text=txt)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)
        
        continueButton = Button(text="Continue Anyway")
        continueButton.bind(on_release=self.do_writing)
        continueButton.bind(on_release=self.dismiss_popup)
        
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(warningLabel)
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(returnButton)
        popupContent.add_widget(continueButton)
        
        masterDict["_popup"] = Popup(title="Warning", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()
        
    def confirmation_popup(self):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        warningLabel = Label(text="Preference File Successfully saved")
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)
        
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(warningLabel)
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(returnButton)
        
        masterDict["_popup"] = Popup(title="Success", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()   
             
    def save_preference_file(self):
        preferences_screen = screen_manager.get_screen('preferencesScreen')

        # This is broken out like this for instrument_seelctionIndices in case the instrument group has been deleted and 
        # is still "selected" but not in the masterDict['groupsDict'] anymore. 
        self.selected_instrumentGroups = list()
        for x in self.instrument_selectionIndices:
            try:
                    if not masterDict['groupsDict'][x] in self.selected_instrumentGroups:
                        self.selected_instrumentGroups.append(masterDict['groupsDict'][x])
            except:
                pass
#         self.selected_instrumentGroups = list(set([masterDict['groupsDict'][x] for x in self.instrument_selectionIndices]))
        
        self.selected_thresholdGroups = list(set([masterDict['thresholdGroups'][x] for x in self.thresholdGroups_selectionIndices]))
        self.chanTypes = {'H': tuple(preferences_screen.pref_H.text.split(',')), 'V': tuple(preferences_screen.pref_V.text.split(','))}

        if preferences_screen.metadata_source_btn.text == "IRIS":
            self.metadataSource = 'IRIS'
        else:
            self.metadataSource  = preferences_screen.metadata_source_text.text
        
        if preferences_screen.metric_source_btn.text == "IRIS":
            self.metricSource = 'IRIS'
        else:
            self.metricSource  = preferences_screen.metric_source_text.text
        
        self.groupsDict = dict()
        self.groupsList = list(set([x.split('::')[0].strip() for x in masterDict['groups_and_names']]))
        self.groupsList.sort()
        
        for tmpGroup in self.groupsList:
            threshList = list()
            for tmpthresh in [x.split('::')[-1].strip() for x in masterDict['groups_and_names'] if x.startswith(tmpGroup + " :: ")]:
                threshList.append(tmpthresh)
            self.groupsDict[tmpGroup] = threshList
        
        
        # Check that all fields are filled
        missingList = list()
        warningList = list()
        imissing = 0
        iwarning = 0
        
        if preferences_screen.preference_file.text == '':
            imissing = 1
            missingList.append("Preference File")
        if  preferences_screen.pref_net.text == '':
            imissing = 1
            missingList.append("Network")
        
        if preferences_screen.pref_sta.text == '':
            imissing = 1
            missingList.append("Station")
            
        if preferences_screen.pref_loc.text == '':
            imissing = 1
            missingList.append("Location")
        if preferences_screen.pref_cha.text == '':
            imissing = 1
            missingList.append("Channels")
        if preferences_screen.pref_H.text == '':
            imissing = 1
            missingList.append("H")
        if preferences_screen.pref_H.text == '':
            imissing = 1
            missingList.append("V") 
        if preferences_screen.frequency_btn.text == '':
            imissing = 1
            missingList.append("Report Frequency")
        
        if self.metricSource == '':
            imissing = 1
            missingList.append("Metric Source")
            
        if self.metadataSource == '':
            imissing = 1
            missingList.append("Metadata Source")    
              
              
        if  preferences_screen.pref_dir.text == '':
            imissing = 1
            missingList.append("Working Directory")  
            
        if  preferences_screen.pref_issue.text == '':
            imissing = 1
            missingList.append("Issues File")  
        
        if  preferences_screen.pref_ticket.text == '':
            imissing = 1
            missingList.append("Ticket File")  
            
        if  preferences_screen.pref_author.text == '':
            imissing = 1
            missingList.append("Author")  
            
        if  preferences_screen.pref_project.text == '':
            imissing = 1
            missingList.append("Project Name")  
            
        if  preferences_screen.pref_email.text == '':
            imissing = 1
            missingList.append("Email")  
            
        if self.selected_instrumentGroups == []:
            iwarning = 1
            warningList.append("Instrument Groups")
        
        if self.selected_thresholdGroups == []:
            iwarning = 1
            warningList.append("Threshold Groups")
        
        if self.groupsDict == {}:
            iwarning = 1
            warningList.append("Threshold-Group Associations")
            
        if imissing == 1:
            self.warning_popup("WARNING: The following fields are required: %s " % missingList)
            return
        
        if iwarning == 1:
            self.doubleCheck_popup("Just so you know: the following are empty: %s" % warningList)
            return 
        
        self.do_writing()
        
       
    def do_writing(self, *kwargs):    
        preferences_screen = screen_manager.get_screen('preferencesScreen')

        with open(preferences_screen.preference_file.text, 'w') as f:
            hdr = """#!/usr/bin/env python

# The preference file is a place to define values that will be used for
# reports each time a report is generated. This is to reduce the amount
# that the analyst needs to input each time, since they can set up a 
# preference file once and use that for each subsequent report.
#
# General categories include:
#    Target information
#    Report frequency
#    Thresholds to use
#    Directory and filenames for common files
#    Report header information
# 
# The preference file is a python script that is loaded during various parts of the 
# QuARG report generation process.  As such, variable names cannot be changed.
# For example, groupsDict cannot be renamed unless the same change is 
# made in every other script that calls on 'groupsDict'.  But, the contents of groupsDict
# can be changed, so you can choose which thresholds belong to which thresholds groups.
# 
# For a more detailed description of each variable, see below.


import reportUtils

## Target and instrument information:
"""
            
            f.write(hdr)
            f.write("network = '%s'\nstation = '%s'\nlocation = '%s'\nchannels = '%s'" % (preferences_screen.pref_net.text,preferences_screen.pref_sta.text,preferences_screen.pref_loc.text, preferences_screen.pref_cha.text))

            f.write('\n\n')
            f.write("instruments = ")
            print(self.selected_instrumentGroups, file=f)
            
            f.write("chanTypes = ")
            print(self.chanTypes, file=f) 
            
            f.write('\n\n## Report frequency: \n')            
            f.write("reportFrequency = '%s'" % preferences_screen.frequency_btn.text)
            f.write("\n[startday, endday, subdir] = reportUtils.calculate_dates(reportFrequency)    # Determines default start and end dates, directory for report")

            f.write("\n\n# Metric source: either 'IRIS' or the path to the local sqlite database file that ISPAQ generated\n")
            f.write("metricSource = '%s'\nmetadataSource = '%s'" % (self.metricSource, self.metadataSource))
            
            f.write('\n\n## Thresholds:')
            f.write("\nthresholdGroups = ")
            print(self.selected_thresholdGroups, file=f)
            
            f.write('\ngroupsDict = ')
            print(self.groupsDict, file=f)

            
            
            f.write('\n\n## Directories and Filenames:\n')
            f.write("mainDir = '%s'" % preferences_screen.pref_dir.text)
            
            f.write("\ndirectory = mainDir + network + '/' + subdir + '/'        # creates a new directory for each report")
            f.write("\nfilename = '%s'        # file to write to in FIND ISSUES tab" % preferences_screen.pref_issue.text)
            f.write('\nif not subdir == "": ')
            f.write('\n    outfile = directory + filename')
            f.write("\nelse:")
            f.write("\n    # This alerts the user that something didn't fill in properly")
            f.write("\n    outfile = ''")
            f.write("\ncsvfilename = '%s'" %  preferences_screen.pref_ticket.text)
            f.write("\ncsvfile = directory + csvfilename    # file to write tickets to, used to generate report in GENERATE REPORT tab" )
            
            f.write('\n\n## Report Header Information:')
            f.write('\nauthor = "%s"' % preferences_screen.pref_author.text)
            f.write('\nproject = "%s"' % preferences_screen.pref_project.text)
            
            f.write('\nemail = "%s"' % preferences_screen.pref_email.text)

            ftr = """\n\n\n
####################################
# Detailed description of each field.
#
## Target and instrument information:
#   network - Two letter network code, ex IU.
#   station - Station codes to be used in report. Can be wildarded or lists. Default is "*" for all stations in network.
#   channels - Channels to use in the report. Can be wildcarded and/or lists. Currently we only have thresholds for broadband and short period instruments
#           so make sure that the channels listed here fall within one or both of those categories.
#   location - Location codes to use in the report.
#   instruments - Type of instruments included in the report. Currently we only have thresholds for broadband and short period 
#               instruments. This field is used to know which thresholds to print on the end of the HTML network report.
#  
#  
## Report Frequency: 
#   reportFrequency - how often reports will be generated. Options include: 'Quarterly', 'Monthly', 'Weekly', 'Daily'
#   startday - First day of the report, generated using calculate_dates for the frequency specified in reportFrequency
#   endday - Final day of the report, generated using calculate_dates for the frequency specified in reportFrequency
#   subdir - The subdirectory that to be used for the report, generated using calculate_dates for the frequency specified in reportFrequency.
#         If the reportFrequency is 'Quarterly' or 'Monthly' then the directory will be YYYYmm. If the report is more frequent,
#         'Weekly' or 'Daily' then the directory will be YYYYmmdd
#  
#
## Thresholds:
#   thresholdGroups - List of all threshold groups to be used to find issues. Groups include: 'Completeness','Amplitudes','Timing','State of Health','Metadata'
#   groupsDict - Where each threshold group is defined. Thresholds can be added or removed to various threshold groups here. The actual definition of a given 
#         threshold happens in the thresholds.py file.
#           
#        All default groupings are as follows:
#           groupsDict = {'Completeness':['avgGaps','gapsRatioGt12','noData'],
#                         'Amplitudes' : ['flat','lowRms','hiAmp','lowAmp','badResp',
#                                         'avgSpikes','pegged','dead','noise1','noise2',
#                                          'medianUnique','rmsRatio','xTalk',
#                                         'gainRatio','nonCoher','polarity',
#                                         'dcOffsets','nSpikes','rmsRatio'],
#                         'Timing' : ['poorTQual','suspectTime','noTime'],
#                        'State of Health' : ['ampSat','filtChg','clip',
#                                             'spikes','glitch','padding','tSync'],
#                         'Metadata' : ['zDip','horDip','zeroZ','lowScale','nonMSUnits']}
#
#
## Directories and Filenames:
#   directory - Directory where all files will be written and found
#   filename - Filename for the issue file that is generated during the FIND ISSUES portion of the reporting process
#   outfile - Full pathname for the issue file
#   csvfile - Full pathname for an intermediate csv file, generated from the tickets and used to generate the final report
#   
#   
## Report Header Information:   
#   author - Name of the person that prepared the report
#   project - Information about the particular report. This is a bit more flexible and describe what is covered in the report.
#             For example, it could be something like "UU ::  University of Utah Regional Network"
#             Or, if you have multiple reports for the same network, it could be something like "UU :: Broadband Channels"
#   
####################################

            
            
            """

            f.write(ftr)

        self.confirmation_popup()
                 
class ThresholdGroupsScreen(Screen):
    thresholdNames_rv = ObjectProperty()
    thresholdNames_selectionIndices = list()
    thresholdGroups_rv = ObjectProperty()
    thresholdGroups_selectionIndices = list()
    thresholdGroupAndNames_rv = ObjectProperty()
    thresholdGroupAndNames_selectionIndices = list()
    
    def go_to_thresholdGroups(self):
        threshGroups_screen = screen_manager.get_screen('thresholdGroupsScreen')
        
        # The data for the thresholds should be just the ones that aren't in the thresh-Group data
        # The data for the groups should come directly from the masterDict['']
        used_groups = list()
        used_thresholds = list()
        group_threshold_pairs = list()

        try:
            masterDict['preference_groupsDict']

            for group in masterDict['preference_groupsDict'].keys():
                used_groups.append(group)
                for threshold in masterDict['preference_groupsDict'][group]:
                    used_thresholds.append(threshold)
                    group_threshold_pairs.append(group + " :: " + threshold)
        except:
            pass  
                  
        try:
            my_groups_and_names = [{'text': x} for x in masterDict['groups_and_names']]
        except:
            group_threshold_pairs.sort()
            my_groups_and_names = [{'text': x} for x in group_threshold_pairs]
            masterDict['groups_and_names'] = [ x for x in group_threshold_pairs]

        threshGroups_screen.thresholdGroupAndNames_rv.data = my_groups_and_names

        masterDict['groups_and_names'].sort()
        
        unused_thresholds = [x for x in masterDict['pref_threshold_names'] if x not in used_thresholds]
        unused_thresholds.sort()
        masterDict['my_threshes'] = unused_thresholds
        my_threshes = [{'text': x} for x in unused_thresholds]
        masterDict['my_threshes'].sort()
        
        threshGroups_screen.thresholdNames_rv.data = my_threshes
        
        masterDict['thresholdGroups'].sort()
        my_threshold_groups = [{'text': x} for x in masterDict['thresholdGroups']]  
        threshGroups_screen.thresholdGroups_rv.data = my_threshold_groups
        
    def add_threshGroup(self):
        threshGroups_screen = screen_manager.get_screen('thresholdGroupsScreen')
        
        if not self.thresholdNames_selectionIndices or not self.thresholdGroups_selectionIndices:
            self.warning_popup("WARNING: Must select both threshold Name and Group")
            return
        
        
        completed_thresholdName_idx = list()
        for thresholdName_idx in sorted(self.thresholdNames_selectionIndices, reverse=True):
            self.thresholdNames_rv._layout_manager.deselect_node(thresholdName_idx)
            ThresholdGroupsScreen.thresholdNames_selectionIndices = [v for v in ThresholdGroupsScreen.thresholdNames_selectionIndices if v != thresholdName_idx]
            if thresholdName_idx in completed_thresholdName_idx:
                continue
            
            try:
                thisThreshold = masterDict['my_threshes'][thresholdName_idx]
            except Exception as e:
                print("ERROR: %s" % e)
                return
            
            #Only one group can be selected
            thisGroup = masterDict['thresholdGroups'][self.thresholdGroups_selectionIndices[0]]
            
            itemToAdd = '%s :: %s' % (thisGroup, thisThreshold)
            
            if itemToAdd not in masterDict['groups_and_names']:
                masterDict['groups_and_names'].append(itemToAdd)
              
            try:
                masterDict['my_threshes'].remove(thisThreshold)
            except:
                print("It didn't remove from my_threshes")
                pass
            
            
            completed_thresholdName_idx.append(thresholdName_idx)
            
        masterDict['my_threshes'].sort()
        masterDict['pref_threshold_names'] = masterDict['my_threshes']
        masterDict['groups_and_names'].sort()
        
        my_groups_and_names = [{'text': x} for x in masterDict['groups_and_names']]
        threshGroups_screen.thresholdGroupAndNames_rv.data = my_groups_and_names
        
        my_threshes = [{'text': x} for x in masterDict['my_threshes']] 
        threshGroups_screen.thresholdNames_rv.data = my_threshes 
                
        self.deselect_names()
    
    def remove_threshGroup(self):
        threshGroups_screen = screen_manager.get_screen('thresholdGroupsScreen')
        
        if not self.thresholdGroupAndNames_selectionIndices:
            self.warning_popup('WARNING: Must select at least one Group :: Threshold item to remove it')
            return 
        
        for groupThreshold_idx in sorted(self.thresholdGroupAndNames_selectionIndices, reverse=True):
            this_groupThresh = masterDict['groups_and_names'][groupThreshold_idx]
            this_thresh = this_groupThresh.split('::')[-1].strip()
            masterDict['my_threshes'].append(this_thresh)
            del masterDict['groups_and_names'][groupThreshold_idx]
        
        
        masterDict['groups_and_names'].sort()
        masterDict['my_threshes'].sort()
        masterDict['pref_threshold_names'] = masterDict['my_threshes']  
          
        my_groups_and_names = [{'text': x} for x in masterDict['groups_and_names']]

        threshGroups_screen.thresholdGroupAndNames_rv.data = my_groups_and_names
        
        my_threshes = [{'text': x} for x in masterDict['my_threshes']] 
        threshGroups_screen.thresholdNames_rv.data = my_threshes 
          
        self.deselect_groupNames()  
            
    def clear_all_on_return(self):
        self.deselect_groupNames()
        self.deselect_groups()
        self.deselect_names()
        
        # Also have to assign any changes we've made to the variables that need them!
        self.groupsDict = dict()
        self.groupsList = list(set([x.split('::')[0].strip() for x in masterDict['groups_and_names']]))
        self.groupsList.sort()
        
        for tmpGroup in self.groupsList:
            threshList = list()
            for tmpthresh in [x.split('::')[-1].strip() for x in masterDict['groups_and_names'] if x.startswith(tmpGroup + " :: ")]:
                threshList.append(tmpthresh)
            self.groupsDict[tmpGroup] = threshList
        
        masterDict['preference_groupsDict'] = self.groupsDict
        
    def deselect_names(self):
        threshGroups_screen = screen_manager.get_screen('thresholdGroupsScreen')
        threshGroups_screen.thresholdNames_rv._layout_manager.clear_selection()
        
    def deselect_groups(self):
        threshGroups_screen = screen_manager.get_screen('thresholdGroupsScreen')
        threshGroups_screen.thresholdGroups_rv._layout_manager.clear_selection()
            
    def deselect_groupNames(self):
        threshGroups_screen = screen_manager.get_screen('thresholdGroupsScreen')
        threshGroups_screen.thresholdGroupAndNames_rv._layout_manager.clear_selection()
        
    def warning_popup(self, txt):
        
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=txt, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_warning_popup)


        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
                
        masterDict["warning_popup"] = Popup(title="Warning", content=popupContent, size_hint=(.66, .66))
        masterDict["warning_popup"].open()
  
    def exit_confirmation(self,*kwargs):
        content = ExitDialog(exit=ExitDialog.do_exit, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Confirm Exit", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
        
    def dismiss_popup(self,*kwargs):
        masterDict["_popup"].dismiss()    

    def dismiss_warning_popup(self,*kwargs):
        masterDict["warning_popup"].dismiss() 

class ThresholdsScreen(Screen):       
    
    threshold_definition = ObjectProperty()
    threshold_list_rv = ObjectProperty()
    threshold_group_rv = ObjectProperty()
    threshold_def_rv = ObjectProperty()
    metrics_rv = ObjectProperty()
    metadata_rv = ObjectProperty()
    metric_text = ObjectProperty()
    channel_avg_button = ObjectProperty()
    channel_vs_button = ObjectProperty()
    
    selected_threshold = list()
    selected_group = list()
    selected_metric = list()    # this is almost obsolete, but keeping for now
    selected_metadata = list()
    selected_definition = ''
            
    def warning_popup(self, txt):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=txt, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_warning_popup)


        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        masterDict["warning_popup"] = Popup(title="Warning", content=popupContent, size_hint=(.66, .66))
        masterDict["warning_popup"].open()

    def go_to_thresholdsLayout(self):
        
        thresholds_screen = screen_manager.get_screen('thresholdsScreen')
        
        with open(masterDict['thresholds_file']) as f:
            local_dict = locals()
            exec(compile(f.read(), masterDict['thresholds_file'], "exec"), globals(), local_dict)
            
        masterDict['thresholdsDict'] = local_dict['thresholdsDict']
        masterDict['instrumentGroupsDict'] = local_dict['instrumentGroupsDict']        
        masterDict['thresholdGroups'] = local_dict['thresholdGroups']
        
        ## Threshold names
        masterDict['threshold_names'] = sorted(list(masterDict['thresholdsDict'].keys()))
        
        my_thresholds = [{'text': x} for x in masterDict['threshold_names']]
        thresholds_screen.threshold_list_rv.data = my_thresholds
        thresholds_screen.threshold_list_rv._layout_manager.select_node(0)
#         selectable_nodes = thresholds_screen.threshold_list_rv.get_selectable_nodes()
#         thresholds_screen.threshold_list_rv.select_node(selectable_nodes[0])

        ## Threshold groups
        instrument_groups = list()
        for val in masterDict['thresholdsDict'].values():
            for key in val.keys():
                if key not in instrument_groups:
                    instrument_groups.append(key)
        
        for key in masterDict['instrumentGroupsDict'].keys():
            if key not in instrument_groups:
                instrument_groups.append(key)
                
        masterDict['instrument_groups'] = sorted(instrument_groups)
        
        my_groups = [{'text': x} for x in masterDict['instrument_groups']]
        thresholds_screen.threshold_group_rv.data = my_groups
        thresholds_screen.threshold_group_rv._layout_manager.select_node(0)
     
     
        ## Metric names
        # Try to get a list of metrics from service.iris.edu, but if fails
        # then just use the old list.
        URL="http://service.iris.edu/mustang/metrics/1/query?output=xml&nodata=404"
        
        try:
            metrics = list()
            with urllib.request.urlopen(URL) as f:
                for line in f.read().decode('utf-8').split('<'):
                    if line.startswith('metric name'):
                        metric_name = line.split('"')[1]
                        if (metric_name == 'transfer_function'):
                            # these metrics don't have 'value' and instead have a series of other fields that need
                            # to be accessible for thresholds.
                            
                            today = datetime.datetime.now()
                            yesterday = today - datetime.timedelta(days=1)
                            subURL = "http://service.iris.edu/mustang/measurements/1/query?metric=transfer_function&format=text&timewindow=%s,%s&nodata=404" % (yesterday.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
                            response = requests.get(subURL) 
                            subMets = [x.strip('"') for x in response.text.split('\n')[1].split(',') if x not in ['"lddate"','"target"','"start"','"end"']]
                            
                            for subMet in subMets:
                                metrics.append(metric_name + "::" + subMet)
                            
                        elif (metric_name == 'orientation_check'):
                            continue
                            
                        else:                                           
                            metrics.append(metric_name)
                        
            with open(masterDict['metrics_file'],'w') as f:
                f.writelines("%s\n" % metric for metric in metrics)
        except Exception as e:
            print("WARNING: %s" % e)
            
        try:
            with open(masterDict['metrics_file'],'r') as f:
                metricsList = f.read().splitlines()
                
            masterDict['metrics'] = metricsList            
            
            my_metrics = [{'text': x} for x in masterDict['metrics']]
            thresholds_screen.metrics_rv.data = my_metrics       
        except Exception as e:
            print("ERROR: %s" % e)
          
        ## Do the same for the metadata fields  
        URL="http://service.iris.edu/fdsnws/station/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&level=channel&format=text&includecomments=true&nodata=404"

        try:
            metadata = pd.read_csv(URL, nrows=1, sep="|").columns
            metadata = [m.strip().strip('#') for m in metadata]
                        
            with open(masterDict['metadata_file'],'w') as f:
                f.writelines("%s\n" % metric for metric in metadata)
        except Exception as e:
            print("WARNING: %s" % e)
            
        try:
            with open(masterDict['metadata_file'],'r') as f:
                metadataList = f.read().splitlines()
                
            masterDict['metadata'] = metadataList            
            
            my_metadata = [{'text': x} for x in masterDict['metadata']]
            thresholds_screen.metadata_rv.data = my_metadata 
               
        except Exception as e:
            print("ERROR: %s" % e)
     
    def disable_rvs(self):        
        thresholds_screen = screen_manager.get_screen('thresholdsScreen')
        
        if self.ids.thresh_metadata_id.state == 'down':
            thresholds_screen.metrics_rv.disabled = True
            thresholds_screen.metadata_rv.disabled = False
            self.ids.thresh_avg_id.disabled = True
            self.ids.thresh_avg_id.state = 'normal'
            self.ids.thresh_median_id.disabled = True
            self.ids.thresh_median_id.state = 'normal'
            
        else:
            thresholds_screen.metrics_rv.disabled = False
            thresholds_screen.metadata_rv.disabled = True
            self.ids.thresh_avg_id.disabled = False
            self.ids.thresh_median_id.disabled = False
            
        if self.ids.thresh_ratio_id.state == 'down' or self.ids.thresh_compare_id.state == 'down':
            if self.ids.horiz_chans_id.state == 'down':
                thresholds_screen.channel_avg_button.disabled = False
                thresholds_screen.channel_vs_button.disabled = False
        else:
            thresholds_screen.channel_avg_button.disabled = True
            thresholds_screen.channel_avg_button.state = 'normal'
            thresholds_screen.channel_vs_button.disabled = True
            thresholds_screen.channel_vs_button.state = 'normal'

    def disable_chan_options(self):
        thresholds_screen = screen_manager.get_screen('thresholdsScreen')
        
        if self.ids.horiz_chans_id.state == 'down':
            if self.ids.thresh_ratio_id.state == 'down' or self.ids.thresh_compare_id.state == 'down':

                thresholds_screen.channel_avg_button.disabled = False
                thresholds_screen.channel_vs_button.disabled = False
        else:
            thresholds_screen.channel_avg_button.disabled = True
            thresholds_screen.channel_avg_button.state = 'normal'
            thresholds_screen.channel_vs_button.disabled = True
            thresholds_screen.channel_vs_button.state = 'normal'
        
    def display_definition(self):
        thresholds_screen = screen_manager.get_screen('thresholdsScreen')
        if (not self.selected_threshold == []) and (not self.selected_group == []):
            try:
                thisDefinition = [{'text': x} for x in masterDict['thresholdsDict'][self.selected_threshold[0]][self.selected_group[0]]]
            except Exception as e:
                thisDefinition = ''
             
        else:
            thisDefinition = ''
        
        thresholds_screen.threshold_def_rv.data = thisDefinition
          
    def new_threshold_popup(self):
        
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        additionContent = BoxLayout( orientation='horizontal',spacing=10)
        additionContent.bind(minimum_height=additionContent.setter('height'))
        
        nameLabel = Label(text="Threshold Name: ", size_hint_x=.66)
#         self.thresholdTextInput = TextInput(id='thresholdNameID')
        self.thresholdTextInput = TextInput()

        self.selectExistingThreshold = DropDown()
        for threshold in masterDict['threshold_names']:
            btn = Button(text=threshold, size_hint_y=None, height=55)
            btn.bind(on_release=lambda btn: self.selectExistingThreshold.select(btn.text))
            self.selectExistingThreshold.add_widget(btn)
            
        mainbutton = Button(text='Existing Thresholds')
        mainbutton.bind(on_release=self.selectExistingThreshold.open)
        
        self.selectExistingThreshold.bind(on_select=lambda instance, x: setattr(self.thresholdTextInput, 'text', x))
        
        additionContent.add_widget(nameLabel)
        additionContent.add_widget(self.thresholdTextInput)
        additionContent.add_widget(mainbutton)
        
        buttonsContent = BoxLayout(orientation='horizontal', spacing=10)
        
        addButton = Button(text="Add Threshold")
        addButton.bind(on_release=self.add_new_threshold)
        addButton.bind(on_release=self.clear_fields)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)
        
        deleteButton = Button(text='Delete')
        deleteButton.bind(on_release=self.confirm_threshold_removal_popup)
        
        buttonsContent.add_widget(deleteButton)
        buttonsContent.add_widget(addButton)
        
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(additionContent)
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(buttonsContent)
        popupContent.add_widget(returnButton)
        
        masterDict["_popup"] = Popup(title="Edit Thresholds", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()
        
    def add_new_threshold(self, *kwargs):
        newThreshold = self.thresholdTextInput.text
        if newThreshold == "":
            self.warning_popup("WARNING: Threshold name must be specified")
            return 
        
        if not newThreshold in masterDict['threshold_names']:
            masterDict['threshold_names'].append(newThreshold)
            masterDict['threshold_names'].sort()
            masterDict['thresholdsDict'].update({newThreshold: dict()})

            my_thresholds = [{'text': x} for x in masterDict['threshold_names']]

            thresholds_screen = screen_manager.get_screen('thresholdsScreen')
            thresholds_screen.threshold_list_rv.data = my_thresholds 
            self.clear_fields('threshold')
        else:
            self.warning_popup("WARNING: Threshold name already in use")

    def all_thresholds_popup(self, *kwargs):
        # a popup with all of the thresholds listed in a digestable way
        # very similar to the thresholds listed on the final report
               
        # create text that will be displayed
        thresholdsDict = sorted(masterDict['thresholdsDict'].keys())
        displayList = []
        for thresholdName in thresholdsDict:
#             print(thresholdName)
            displayList.append(thresholdName)
#             f.write("<b>%s</b>    \t" % thresholdName);            
            for instrumentGroup in masterDict['thresholdsDict'][thresholdName].keys():
               
                defStr = ' && '.join(masterDict['thresholdsDict'][thresholdName][instrumentGroup])

#                 print("     %s - %s" % (instrumentGroup,defStr));
                displayList.append("     %s - %s" % (instrumentGroup,defStr))
                
            displayList.append("")
        
        displayFull = '\n'.join(displayList)
        
        # create the popup
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=displayFull, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)


        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        masterDict["_popup"] = Popup(title="Existing Threshold Definition", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()

    def new_group_popup(self):
        
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        nameContent = BoxLayout( orientation='horizontal', spacing=10, size_hint_y=7)
        nameContent.bind(minimum_height=nameContent.setter('height'))
        nameLabel = Label(text="Name of new group: ")
#         self.groupTextInput = TextInput(id='groupNameID')
        self.groupTextInput = TextInput()
        
        self.selectExisting = DropDown()
        for group in masterDict['instrument_groups']:
            btn = Button(text=group, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.selectExisting.select(btn.text))
            self.selectExisting.add_widget(btn)
            
        mainbutton = Button(text='Existing Groups')
        mainbutton.bind(on_release=self.selectExisting.open)
        
        self.selectExisting.bind(on_select=self.set_group_settings)
        
        col1a = BoxLayout(orientation='vertical', size_hint_x=.5)
        col1 = BoxLayout(orientation='vertical', spacing=10)
        col2 = BoxLayout(orientation='vertical', spacing=10)
        col3 = BoxLayout(orientation='vertical', spacing=10)
        col3b = BoxLayout(orientation='vertical', size_hint_x=.5)
        
        col1.add_widget(Label())
        col1.add_widget(Label(text="Group Name: "))
        col1.add_widget(Label(text="Networks: "))
        col1.add_widget(Label(text="Stations: "))
        col1.add_widget(Label(text="Locations: "))
        col1.add_widget(Label(text="Channels: "))
        col1.add_widget(Label())
        
#         self.groupTextInput = TextInput(id='groupNameID')
        self.groupTextInput = TextInput()
        self.netTextInput = TextInput(write_tab=False)
        self.staTextInput = TextInput(write_tab=False)
        self.locTextInput = TextInput(write_tab=False)
        self.chanTextInput = TextInput(write_tab=False)
        
        col2.add_widget(Label())
        col2.add_widget(self.groupTextInput)
        col2.add_widget(self.netTextInput)
        col2.add_widget(self.staTextInput)
        col2.add_widget(self.locTextInput)
        col2.add_widget(self.chanTextInput)
        col2.add_widget(Label())
        
        col3.add_widget(Label())
        col3.add_widget(mainbutton)
        col3.add_widget(Label())
        col3.add_widget(Label())
        col3.add_widget(Label())
        col3.add_widget(Label())
        col3.add_widget(Label())
        
        nameContent.add_widget(col1a)    
        nameContent.add_widget(col1)
        nameContent.add_widget(col2)
        nameContent.add_widget(col3)
        nameContent.add_widget(col3b)
        
        buttonsContent = BoxLayout(orientation='horizontal', spacing=10)
        
        addButton = Button(text="Add/Update Group")
        addButton.bind(on_release=self.add_new_grouping)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)
        
        deleteButton = Button(text='Delete')
        deleteButton.bind(on_release=self.confirm_group_removal_popup)
        
        buttonsContent.add_widget(deleteButton)
        buttonsContent.add_widget(addButton)
        
        popupContent.add_widget(nameContent)
        popupContent.add_widget(buttonsContent)
        popupContent.add_widget(returnButton)
        
        masterDict["_popup"] = Popup(title="Edit Instrument Groups", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()
        
    def set_group_settings(self, instance, txt):
        try:
            self.groupTextInput.text = txt
            self.netTextInput.text = ','.join(masterDict['instrumentGroupsDict'][txt]['network'])
            self.staTextInput.text = ','.join(masterDict['instrumentGroupsDict'][txt]['station'])
            self.locTextInput.text = ','.join(masterDict['instrumentGroupsDict'][txt]['location'])
            self.chanTextInput.text = ','.join(masterDict['instrumentGroupsDict'][txt]['channel'])
            
        except Exception as e:
            print("ERROR: %s" % e)
        
    def add_new_grouping(self, *kwargs):
        newGroup = self.groupTextInput.text

        if newGroup == '':
            print("WARNING: Group name must be specified")
            return
        
        if not newGroup in masterDict['instrument_groups']:
            masterDict['instrument_groups'].append(newGroup)
            masterDict['instrument_groups'].sort()
            my_groups = [{'text': x} for x in masterDict['instrument_groups']]

            thresholds_screen = screen_manager.get_screen('thresholdsScreen')
            thresholds_screen.threshold_group_rv.data = my_groups 
        
        if not newGroup in masterDict['instrumentGroupsDict']:
            masterDict['instrumentGroupsDict'].update({newGroup: list()})
                
        #Updating masterDict['thresholdGroupsDict']
        theseNets = [x.strip() for x in self.netTextInput.text.split(',')]
        theseStas = [x.strip() for x in self.staTextInput.text.split(',')]
        theseLocs = [x.strip() for x in self.locTextInput.text.split(',')]
        theseChas = [x.strip() for x in self.chanTextInput.text.split(',')] 
        masterDict['instrumentGroupsDict'][newGroup] = {'network': theseNets, 'station': theseStas, 'location': theseLocs, 'channel':theseChas}                
        
        self.dismiss_popup()
        self.new_group_popup()
        self.clear_fields('group')

    def new_threshold_group_popup(self):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        additionContent = BoxLayout( orientation='horizontal',spacing=10)
        additionContent.bind(minimum_height=additionContent.setter('height'))
        
        nameLabel = Label(text="Group Name: ", size_hint_x=.66)
#         self.thresholdGroupTextInput = TextInput(id='thresholdGroupID')
        self.thresholdGroupTextInput = TextInput()

        self.selectExistingThresholdGroup = DropDown()
        for group in masterDict['thresholdGroups']:
            btn = Button(text=group, size_hint_y=None, height=55)
            btn.bind(on_release=lambda btn: self.selectExistingThresholdGroup.select(btn.text))
            self.selectExistingThresholdGroup.add_widget(btn)
            
        mainbutton = Button(text='Existing Groups')
        mainbutton.bind(on_release=self.selectExistingThresholdGroup.open)
        
        self.selectExistingThresholdGroup.bind(on_select=lambda instance, x: setattr(self.thresholdGroupTextInput, 'text', x))
        
        additionContent.add_widget(nameLabel)
        additionContent.add_widget(self.thresholdGroupTextInput)
        additionContent.add_widget(mainbutton)
        
        buttonsContent = BoxLayout(orientation='horizontal', spacing=10)
        
        addButton = Button(text="Add Group")
        addButton.bind(on_release=self.add_new_thresholdGroup)
        addButton.bind(on_release=self.clear_fields)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)
        
        deleteButton = Button(text='Delete')
        deleteButton.bind(on_release=self.confirm_thresholdGroup_removal_popup)
        
        buttonsContent.add_widget(deleteButton)
        buttonsContent.add_widget(addButton)
        
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(additionContent)
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(buttonsContent)
        popupContent.add_widget(returnButton)
        
        masterDict["_popup"] = Popup(title="Edit Threshold Groups", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()
        
    def add_new_thresholdGroup(self, *kwargs):
        newGroup = self.thresholdGroupTextInput.text
        if newGroup == "":
            self.warning_popup("WARNING: Threshold Group name must be specified")
            return 
        
        if not newGroup in masterDict['thresholdGroups']:
            masterDict['thresholdGroups'].append(newGroup)
            masterDict['thresholdGroups'].sort()

            self.dismiss_popup()
            self.new_threshold_group_popup()
            self.clear_fields('threshold_group')
        else:
            self.warning_popup("WARNING: Threshold Group name already in use")
        
    def clear_fields(self, which_one):  
        if which_one == 'threshold':
            self.thresholdTextInput.text = ''
            
        if which_one == 'group':
            self.groupTextInput.text=''
            self.chanTextInput.text = ''
            self.staTextInput.text = ''
            
        if which_one == 'threshold_group':
            self.thresholdGroupTextInput.text = ''
    
    def remove_defintion_line(self):
        try:
            masterDict['thresholdsDict'][self.selected_threshold[0]][self.selected_group[0]] = [v for v in masterDict['thresholdsDict'][self.selected_threshold[0]][self.selected_group[0]] if v != self.selected_definition]
            if masterDict['thresholdsDict'][self.selected_threshold[0]][self.selected_group[0]] == []:
                del masterDict['thresholdsDict'][self.selected_threshold[0]][self.selected_group[0]]
            self.display_definition()
            
            thresholds_screen = screen_manager.get_screen('thresholdsScreen')
            thresholds_screen.threshold_def_rv._layout_manager.clear_selection()
        except Exception as e:
            print("WARNING: cannot delete %s" % e)

    def confirm_group_removal_popup(self, *kwargs):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        warningLabel = Label(text="This will remove this Instrument Group. Any thresholds associated with it will be broken. Are you sure?")

        
        deleteButton = Button(text='Delete')
        deleteButton.bind(on_release=self.remove_instrument_group)
        
        returnButton = Button(text="Cancel")
        returnButton.bind(on_release=self.dismiss_confirm_popup)
        
        popupContent.add_widget(warningLabel)
        popupContent.add_widget(deleteButton)
        popupContent.add_widget(returnButton)
        
        masterDict["confirm_popup"] = Popup(title="Delete?", content=popupContent, size_hint=(.5, .5))
        masterDict["confirm_popup"].open()   
      
    def confirm_threshold_removal_popup(self, *kwargs):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        warningLabel = Label(text="This will remove all definitions for this threshold. Are you sure?")
        
        deleteButton = Button(text='Delete')
        deleteButton.bind(on_release=self.remove_threshold)

        returnButton = Button(text="Cancel")
        returnButton.bind(on_release=self.dismiss_confirm_popup)
        
        popupContent.add_widget(warningLabel)
        popupContent.add_widget(deleteButton)
        popupContent.add_widget(returnButton)
        
        masterDict["confirm_popup"] = Popup(title="Delete?", content=popupContent, size_hint=(.5, .5))
        masterDict["confirm_popup"].open()   
     
    def confirm_thresholdGroup_removal_popup(self, *kwargs):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        warningLabel = Label(text="This will remove this Threshold Group. Any metrics associated with it will be broken. Are you sure?")

        
        deleteButton = Button(text='Delete')
        deleteButton.bind(on_release=self.remove_thresholdGroup)

        returnButton = Button(text="Cancel")
        returnButton.bind(on_release=self.dismiss_confirm_popup)
        
        popupContent.add_widget(warningLabel)
        popupContent.add_widget(deleteButton)
        popupContent.add_widget(returnButton)
        
        masterDict["confirm_popup"] = Popup(title="Delete?", content=popupContent, size_hint=(.5, .5))
        masterDict["confirm_popup"].open()  
              
    def remove_threshold(self, *kwargs):
        threshToRemove = self.thresholdTextInput.text
        
        try:
            masterDict['threshold_names'] = [x for x in masterDict['threshold_names'] if x != threshToRemove]
            del masterDict['thresholdsDict'][threshToRemove]
        
        except Exception as e:
            print("WARNING: cannot remove %s" % e)
        
        thresholds_screen = screen_manager.get_screen('thresholdsScreen')
        my_thresholds = [{'text': x} for x in masterDict['threshold_names']]
        thresholds_screen.threshold_list_rv.data = my_thresholds 

        self.dismiss_popup()
        self.new_threshold_popup()
        
        self.thresholdTextInput.text = ''
        self.dismiss_confirm_popup()
        
    def remove_instrument_group(self, *kwargs):
        groupToRemove = self.groupTextInput.text
        
        try:
            masterDict['instrument_groups'] = [x for x in masterDict['instrument_groups'] if x != groupToRemove]            
            del masterDict['instrumentGroupsDict'][groupToRemove]
            
            for key in masterDict['thresholdsDict']:
                
                thisDict = masterDict['thresholdsDict'][key]
                try:
                    del thisDict[groupToRemove]
                    masterDict['thresholdsDict'][key] = thisDict
                except Exception as e:
                    continue
        
        except Exception as e:
            print("WARNING: cannot remove %s" % e)
        
        thresholds_screen = screen_manager.get_screen('thresholdsScreen')
        my_groups = [{'text': x} for x in masterDict['instrument_groups']]
        thresholds_screen.threshold_group_rv.data = my_groups

        self.dismiss_popup()
        self.new_group_popup()
        self.dismiss_confirm_popup()
      
    def remove_thresholdGroup(self, *kwargs):
        threshGroupToRemove = self.thresholdGroupTextInput.text

        try:
            masterDict['thresholdGroups'] = [x for x in masterDict['thresholdGroups'] if x != threshGroupToRemove]
        
        except Exception as e:
            print("WARNING: cannot remove %s" % e)
        
        thresholds_screen = screen_manager.get_screen('thresholdsScreen')

        self.dismiss_popup()
        self.new_threshold_group_popup()
        
        self.thresholdGroupTextInput.text = ''
        self.dismiss_confirm_popup()        
        
    def add_metric_to_threshold(self,*kwargs):
        def ensure_threshold():
            # If this threshold doesn't have any associated definitions yet, get it into the thresholdsDict
            if (not thresh in masterDict['thresholdsDict'].keys()):
                masterDict['thresholdsDict'].update({thresh: dict()})
                
        def get_existing_defintion():
            try:
                prevDef = masterDict['thresholdsDict'][thresh][group]
            except:
                prevDef = list()
            
            return prevDef
        
        def what_type_of_field(field):
            if "abs(" in field:
                field = field.replace('abs(','').replace(')','')
                
            if field in masterDict['metrics']:
                return "Metrics"
            elif field in masterDict['metadata']:
                return "Metadata"
            else:
                self.warning_popup("WARNING: Field type not recognized")
                return
            
        threshold_screen = screen_manager.get_screen('thresholdsScreen')
        ireturn=0
        
        gr =  self.ids.threshold_greater_id.state
        le = self.ids.threshold_less_id.state
        eq =  self.ids.threshold_equal_id.state
        neq = self.ids.threshold_notequal_id.state
        metric_cutoff =self.ids.metric_cutoff_id.text
        try:
            metric_cutoff = float(metric_cutoff)
        except:
            metric_cutoff = metric_cutoff
        metric = threshold_screen.metric_text.text

        try:
            thresh =  self.selected_threshold[0]
        except:
            self.warning_popup("WARNING: Threshold must be selected")
            return
        try:
            group = self.selected_group[0]
        except:
            self.warning_popup("WARNING: Instrument Group must be selected")
            return
        
            
        ## There are different requirements depending on what 'kind' of threshold definition it is
        # Metadata
        if self.ids.thresh_metadata_id.state == 'down':
            is_metadata = True
        else:
            is_metadata = False
          
        if self.ids.horiz_chans_id.state == 'down':
            chanToDo = 'H'
            if threshold_screen.channel_vs_button.state == 'down':
                chanToDo = '%s:%s'% (chanToDo,threshold_screen.channel_vs_button.text)
            elif threshold_screen.channel_avg_button.state == 'down':
                chanToDo = '%s:%s'% (chanToDo,threshold_screen.channel_avg_button.text)
        elif self.ids.vertical_chans_id.state == 'down':
            chanToDo = "V"
        else:
            chanToDo = ""  
            
        # Average
        if self.ids.thresh_avg_id.state == 'down':
            # Then all three (field, operator, cutoff) need to be present
            # Then the "field" must be in the metric list
            # Then the cutoff must be numeric
            if is_metadata:
                field_passes = metric in masterDict['metadata']
            else:
                field_passes = metric in masterDict['metrics']
            if not field_passes:
                if is_metadata:
                    self.warning_popup("WARNING: Field must be an IRIS metadata field")
                else:
                    self.warning_popup("WARNING: Field must be a MUSTANG metric")
                return
            if (gr == "normal") and (le == "normal") and (eq == "normal") and (neq == "normal"):
                self.warning_popup("WARNING: Greater Than, Less Than, and/or Equal To must be selected")
                return

            if (metric_cutoff == "") or not isinstance(metric_cutoff, float):
                self.warning_popup("WARNING: Metric cutoff value required, must be numeric")
                return
            
            ensure_threshold()
            prevDef = get_existing_defintion()

            if (not prevDef == '') and (not prevDef == []):
                self.warning_popup("WARNING: Average thresholds can only have one definition")
                return
            
            if chanToDo != "":
                metric = "%s[%s]" %(metric, chanToDo)
                
            if self.ids.absolute_id.state == 'down':
                newPart =  'abs(' + metric + ") "
            else:
                newPart =  metric + " "
            if neq == 'down':
                newPart = newPart + "!"     # this is split so that the "!" can be at the beginning of the operator
            if gr == 'down':
                newPart = newPart + '>'
            if le == 'down':
                newPart = newPart + "<"
            if eq == 'down':
                newPart = newPart + "="
            if neq == 'down':
                newPart = newPart + "="     # completing the !=
            newPart = newPart + " " + str(metric_cutoff) 
            newPart = 'average :: ' + newPart 
        
        # Median
        elif self.ids.thresh_median_id.state == 'down':
            # Then all three (field, operator, cutoff) need to be present
            # Then the "field" must be in the metric list
            # Then the cutoff must be numeric
            if is_metadata:
                field_passes = metric in masterDict['metadata']
            else:
                field_passes = metric in masterDict['metrics']
            if not field_passes:
                if is_metadata:
                    self.warning_popup("WARNING: Field must be an IRIS metadata field")
                else:
                    self.warning_popup("WARNING: Field must be a MUSTANG metric")
                    print("WARNING: Field must be a MUSTANG metric")
                return
            if (gr == "normal") and (le == "normal") and (eq == "normal") and (neq == "normal"):
                self.warning_popup("WARNING: Greater Than, Less Than, and/or Equal To must be selected")
                return

            if (metric_cutoff == "") or not isinstance(metric_cutoff, float):
                self.warning_popup("WARNING: Metric cutoff value required, must be numeric")
                return
            
            ensure_threshold()
            prevDef = get_existing_defintion()

            if (not prevDef == '') and (not prevDef == []):
                self.warning_popup("WARNING: Median thresholds can only have one definition")
                return
            
            if chanToDo != "":
                metric = "%s[%s]" %(metric, chanToDo)
                
            if self.ids.absolute_id.state == 'down':
                newPart =  'abs(' + metric + ") "
            else:
                newPart =  metric + " "
            if neq == 'down':
                newPart = newPart + "!"     # this is split so that the "!" can be at the beginning of the operator
            if gr == 'down':
                newPart = newPart + '>'
            if le == 'down':
                newPart = newPart + "<"
            if eq == 'down':
                newPart = newPart + "="
            if neq == 'down':
                newPart = newPart + "="     # completing the !=
            newPart = newPart + " " + str(metric_cutoff) 
            newPart = 'median :: ' + newPart 
        
        # Ratio
        elif self.ids.thresh_ratio_id.state == 'down':
            # Then either metric OR operator/cutoff must be provided
            # Then, if a metric, the "field" must be in the metric list
            # Then, if a operator/cutoff, the cutoff must be numeric
            
            if is_metadata:
                field_passes = metric in masterDict['metadata']
            else:
                field_passes = metric in masterDict['metrics']
                
            if not field_passes:
                if not metric == '':
                    if is_metadata:
                        self.warning_popup("WARNING: Field must be an IRIS metadata field")
                    else:
                        self.warning_popup("WARNING: Field must be a MUSTANG metric")
                    return
                
                # Then we need to have the operator and cutoff values provided, and cutoff must be numeric
                if (   ( (gr == "normal") and (le == "normal") and (eq == "normal") and (neq == "normal") ) or 
                                    ( (metric_cutoff == "") or not isinstance(metric_cutoff, float) )  ):
                    self.warning_popup("WARNING: Metric name OR operator and numeric value required")
                    return
            else:
                # Then we are simply adding the metric without the operator and cutoff
                try:
                    thisDef = masterDict['thresholdsDict'][thresh][group]
                    
                except Exception as e:
                    pass
#                     print("WARNING: %s" % e)
                    
            ensure_threshold()
            prevDef = get_existing_defintion()
            
            if any("average ::" in s for s in prevDef) or any("median ::" in s for s in prevDef):
                self.warning_popup("WARNING: Average and Median thresholds can only have one definition")
                return
            
            if metric == '':
                # if we aren't adding a metric, then we need to make sure there are already two metrics in place
                indices = [i for i, s in enumerate(prevDef) if ':: ratio' in s]
                if len(indices) < 2:
                    self.warning_popup("WARNING: Need to specify two metrics before providing the cutoff information")
                    return
                
                met1 = prevDef[indices[0]].split()[0]
                met2 = prevDef[indices[1]].split()[0]
                met1_type = what_type_of_field(met1.split('[')[0])
                met2_type = what_type_of_field(met2.split('[')[0])
                if met1_type != met2_type:
                    self.warning_popup("WARNING: Cannot compare MUSTANG metric with IRIS Metadata field")
                    return
                newPart = "%s / %s " %(met1, met2)
               
                if neq == 'down':
                    newPart = newPart + "!"     # this is split so that the "!" can be at the beginning of the operator         
                if gr == 'down':
                    newPart = newPart + '>'
                if le == 'down':
                    newPart = newPart + "<"
                if eq == 'down':
                    newPart = newPart + "="
                if neq == 'down':
                    newPart = newPart + "="     # completing the !=
                    
                newPart = newPart + " " + str(metric_cutoff)
                del prevDef[indices[1]]             
                del prevDef[indices[0]]
            else:
                # If we are adding a new metric, need to check that there aren't already two in place
                indices = [i for i, s in enumerate(prevDef) if ':: ratio' in s]
                if len(indices) >=2:
                    self.warning_popup("WARNING: Two metrics already listed - waiting for cutoff value")
                    return
                
                if chanToDo != "":
                    if len(indices) == 0:
                            metric = "%s[%s]" %(metric, chanToDo)
                            
                    elif len(indices) == 1:
                        prevMetric = prevDef[0].replace(']', '[').split('[')[0].replace('abs(','')
                        try:
                            prevChanType = prevDef[0].replace(']', '[').split('[')[1]
                        except:
                            prevChanType = ''
                        
                        
                        if chanToDo == 'V':
                            if prevChanType == '':
                                self.warning_popup("WARNING: Unable to compare verticals to all channels")
                                return
                            if prevChanType == 'V':
                                if prevMetric == metric:
                                    self.warning_popup("WARNING: Cannot compare verticals to verticals of same metric")
                                    return
                                else:
                                    metric = "%s[%s]" %(metric, chanToDo)
                            if prevChanType == 'H:vs':
                                self.warning_popup("WARNING: H:vs can only be used with another H:vs")
                                return
                            if prevChanType == 'H' or prevChanType == 'H:avg':
                                metric = "%s[%s]" %(metric, chanToDo)
                                
                        elif chanToDo == 'H':
                            if prevChanType == '':
                                self.warning_popup("WARNING: Unable to compare horizontals to all channels")
                                return
                            if prevChanType == 'H':
                                if prevMetric == metric:
                                    self.warning_popup("WARNING: Cannot compare horizontals to horizontals of same metric")
                                    return
                                else:
                                    metric = "%s[%s]" %(metric, chanToDo)
                            if prevChanType == 'H:vs':
                                self.warning_popup("WARNING: H:vs can only be used with another H:vs")
                                return
                            if prevChanType == 'V' or prevChanType == 'H:avg':
                                metric = "%s[%s]" %(metric, chanToDo)
                            
                        elif chanToDo == 'H:vs':
                            # This can only exist if it is the first part of the definition, or the first one is also H:vs
                            if prevChanType != 'H:vs':
                                self.warning_popup("WARNING: H:vs can only be used with another H:vs")
                                return 
                            else:
                                # if the previous one is H:vs, then it must be the same metric
                                
                                if prevMetric != metric:
                                    self.warning_popup("WARNING: H:vs can only be used for a single metric")
                                    return 
                            metric = "%s[%s]" %(metric, chanToDo)
                        
                        elif chanToDo == 'H:avg':
                            # can compare H:avg to all channels, can compare H:avg to H, to V.
                            if prevChanType == 'H:vs':
                                self.warning_popup("WARNING: H:vs can only be used with another H:vs")
                                return
                            else:
                                metric = "%s[%s]" %(metric, chanToDo)

                    else:
                        metric = "%s[%s]" %(metric, chanToDo)
                    
                    
                
                if self.ids.absolute_id.state == 'down':
                    newPart =  'abs(' + metric + ") :: ratio"
                else:
                    newPart =  metric + " :: ratio"        
        
        # Direct Comparison 
        # nearly the same as ratio, except uses the operator instead of division
        elif self.ids.thresh_compare_id.state == 'down':
            if is_metadata:
                field_passes = metric in masterDict['metadata']
            else:
                field_passes = metric in masterDict['metrics']
                
            if not field_passes:
                if not metric == '':
                    if is_metadata:
                        self.warning_popup("WARNING: Field must be an IRIS metadata field")
                    else:
                        self.warning_popup("WARNING: Field must be a MUSTANG metric")
                    return
                
                # Then we need to have the operator and cutoff values provided, and cutoff must be numeric
                if  (gr == "normal") and (le == "normal") and (eq == "normal") and (neq == "normal"):
                    self.warning_popup("WARNING: Metric name OR operator must be selected")
                    return
            else:
                # Then we are simply adding the metric without the operator and cutoff
                try:
                    thisDef = masterDict['thresholdsDict'][thresh][group]
                    
                except Exception as e:
                    pass
#                     print("WARNING: %s" % e)
                    
            ensure_threshold()
            prevDef = get_existing_defintion()
            
            if any("average ::" in s for s in prevDef) or any("median ::" in s for s in prevDef):
                self.warning_popup("WARNING: Average and Median thresholds can only have one definition")
                return
            
            if metric == '':
                # if we aren't adding a metric, then we need to make sure there are already two metrics in place
                indices = [i for i, s in enumerate(prevDef) if ':: compare' in s]
                if len(indices) < 2:
                    self.warning_popup("WARNING: Need to specify two metrics before providing the cutoff information")
                    return
                
                met1 = prevDef[indices[0]].split()[0]
                met2 = prevDef[indices[1]].split()[0]
                met1_type = what_type_of_field(met1.split('[')[0])
                met2_type = what_type_of_field(met2.split('[')[0])
                if met1_type != met2_type:
                    self.warning_popup("WARNING: Cannot compare MUSTANG metric with IRIS Metadata field")
                    return
#                 newPart = "%s / %s " %(met1, met2)
                
                
                newPart = met1 + " "
                
                if neq == 'down':
                    newPart = newPart + "!"     # this is split so that the "!" can be at the beginning of the operator
                if gr == 'down':
                    newPart = newPart + '>'
                if le == 'down':
                    newPart = newPart + "<"
                if eq == 'down':
                    newPart = newPart + "="
                if neq == 'down':
                    newPart = newPart + "="     # completing the !=
                
                newPart = newPart + " "
#                 newPart = "compare :: " + newPart + " " + metric_cutoff
                newPart = '%s %s' % (newPart, met2)
                del prevDef[indices[1]]             
                del prevDef[indices[0]]
            else:
                # If we are adding a new metric, need to check that there aren't already two in place
                indices = [i for i, s in enumerate(prevDef) if ':: compare' in s]
                if len(indices) >=2:
                    self.warning_popup("WARNING: Two metrics already listed: waiting for operator")
                    return
                
#                 if chanToDo != "":
#                     metric = "%s[%s]" %(metric, chanToDo)
                    
                    
                if chanToDo != "":
                    if len(indices) == 0:
                            metric = "%s[%s]" %(metric, chanToDo)
                            
                    elif len(indices) == 1:
                        prevMetric = prevDef[0].replace(']', '[').split('[')[0].replace('abs(','')
                        try:
                            prevChanType = prevDef[0].replace(']', '[').split('[')[1]
                        except:
                            prevChanType = ''
                        
                        
                        if chanToDo == 'V':
                            if prevChanType == '':
                                self.warning_popup("WARNING: Unable to compare verticals to all channels")
                                return
                            if prevChanType == 'V':
                                if prevMetric == metric:
                                    self.warning_popup("WARNING: Cannot compare verticals to verticals of same metric")
                                    return
                                else:
                                    metric = "%s[%s]" %(metric, chanToDo)
                            if prevChanType == 'H:vs':
                                self.warning_popup("WARNING: H:vs can only be used with another H:vs")
                                return
                            if prevChanType == 'H' or prevChanType == 'H:avg':
                                metric = "%s[%s]" %(metric, chanToDo)
                                
                        elif chanToDo == 'H':
                            if prevChanType == '':
                                self.warning_popup("WARNING: Unable to compare horizontals to all channels")
                                return
                            if prevChanType == 'H':
                                if prevMetric == metric:
                                    self.warning_popup("WARNING: Cannot compare horizontals to horizontals of same metric")
                                    return
                                else:
                                    metric = "%s[%s]" %(metric, chanToDo)
                            if prevChanType == 'H:vs':
                                self.warning_popup("WARNING: H:vs can only be used with another H:vs")
                                return
                            if prevChanType == 'V' or prevChanType == 'H:avg':
                                metric = "%s[%s]" %(metric, chanToDo)
                            
                        elif chanToDo == 'H:vs':
                            # This can only exist if it is the first part of the definition, or the first one is also H:vs
                            if prevChanType != 'H:vs':
                                self.warning_popup("WARNING: H:vs can only be used with another H:vs")
                                return 
                            else:
                                # if the previous one is H:vs, then it must be the same metric
                                
                                if prevMetric != metric:
                                    self.warning_popup("WARNING: H:vs can only be used for a single metric")
                                    return 
                            metric = "%s[%s]" %(metric, chanToDo)
                        
                        elif chanToDo == 'H:avg':
                            # can compare H:avg to all channels, can compare H:avg to H, to V.
                            if prevChanType == 'H:vs':
                                self.warning_popup("WARNING: H:vs can only be used with another H:vs")
                                return
                            else:
                                metric = "%s[%s]" %(metric, chanToDo)

                    else:
                        metric = "%s[%s]" %(metric, chanToDo)
                
                if self.ids.absolute_id.state == 'down':
                    newPart =  'abs(' + metric + ") :: compare"
                else:
                    newPart =  metric + " :: compare"
#                 newPart = metric + ' :: compare'
        
        
        
        # Everything else (ie, 'normal')
        else:
            # Then all three must be present
            # Then the field must be ametric
            # Then the cutoff must be numeric
            if is_metadata:
                field_passes = metric in masterDict['metadata']
            else:
                field_passes = metric in masterDict['metrics']
                
            if not field_passes:
                if is_metadata:
                    self.warning_popup("WARNING: Field must be an IRIS metadata field")
                else:
                    self.warning_popup("WARNING: Field must be a MUSTANG metric")
                return
            
            if (gr == "normal") and (le == "normal") and (eq == "normal") and (neq == "normal"):
                self.warning_popup("WARNING: Greater Than, Less Than, and/or Equal To must be selected")
                return
            
            if (metric_cutoff == ""):
                self.warning_popup("WARNING: Metric cutoff value required")
                return
                
            if (not is_metadata) and (not isinstance(metric_cutoff, float)):
                self.warning_popup("WARNING: Metric cutoff value required, must be numeric")
                return

            
            ensure_threshold()
            prevDef = get_existing_defintion()
            
            if any("average ::" in s for s in prevDef) or any("median ::" in s for s in prevDef):
                self.warning_popup("WARNING: Average and Median thresholds can only have one definition")
                return
            
            if chanToDo != "":
                metric = "%s[%s]" %(metric, chanToDo)
                

                
            if self.ids.absolute_id.state == 'down':
                newPart =  'abs(' + metric + ") "
            else:
                newPart =  metric + " "
#             newPart =  metric + " "
            if neq == 'down':
                newPart = newPart + "!"     # this is split so that the "!" can be at the beginning of the operator
            if gr == 'down':
                newPart = newPart + '>'
            if le == 'down':
                newPart = newPart + "<"
            if eq == 'down':
                newPart = newPart + "="
            if neq == 'down':
                newPart = newPart + "="     # completing the !=
                
            newPart = newPart + " " + str(metric_cutoff) 

        if not newPart in prevDef:
            prevDef.append(newPart)
        elif ("[H:vs] :: ratio" in newPart) or ("[H:vs] :: compare" in newPart) or ("[H:vs]) :: ratio" in newPart) or ("[H:vs]) :: compare" in newPart):
            prevDef.append(newPart)
                        
        masterDict['thresholdsDict'][thresh][group] = prevDef
        
        self.display_definition()

    def clear_all_on_return(self):
        thresholds_screen = screen_manager.get_screen('thresholdsScreen')

        thresholds_screen.threshold_list_rv._layout_manager.clear_selection()
        thresholds_screen.threshold_group_rv._layout_manager.clear_selection()
        thresholds_screen.metrics_rv._layout_manager.clear_selection()
        thresholds_screen.threshold_def_rv._layout_manager.clear_selection()
        
        thresholds_screen.threshold_def_rv.data = '' 
        self.ids.metric_cutoff_id.text = ''
        self.ids.threshold_greater_id.state = 'normal'
        self.ids.threshold_less_id.state = 'normal'
        self.ids.threshold_equal_id.state = 'normal'
        
    def exit_confirmation(self,*kwargs):
        content = ExitDialog(exit=ExitDialog.do_exit, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Confirm Exit", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
    
    def dismiss_popup(self,*kwargs):
        masterDict["_popup"].dismiss()
      
    def dismiss_warning_popup(self,*kwargs):
        masterDict["warning_popup"].dismiss()  
        
    def dismiss_confirm_popup(self, *kwargs):
        masterDict["confirm_popup"].dismiss()

    def write_definition_to_file(self):

        try:
            with open(masterDict['thresholds_file'], 'w') as f:
                ## list of all instrument groups - I dont think this is actually used and doesn't need to be written
                f.write("groupsDict = ")
                print(masterDict['instrument_groups'], file = f)
                
                ## List of threshold groups (like Amplitudes, Completeness)
                f.write('\n')
                f.write("thresholdGroups = ")
                print(masterDict['thresholdGroups'], file=f)
                
                ## Dict of instrument groups and the associated stations/channels
                f.write('\n')
                f.write("instrumentGroupsDict = ")
                print(masterDict['instrumentGroupsDict'], file=f) 
                
                ## Dict of all threshold definitions
                f.write('\n')
                f.write("thresholdsDict = ")
                print(masterDict['thresholdsDict'], file=f)
                
                ## Dict of metrics associated with each threshold name - combines all groups for the threshold 
                metricThreshDict = dict()
                for threshold in masterDict['thresholdsDict'].keys():
                    metricsInThresh = list()
                    for group in masterDict['thresholdsDict'][threshold].keys():
                        defs = masterDict['thresholdsDict'][threshold][group]
                        for definition in defs:
                            if ('average ::' in definition) or ('median ::' in definition):
                                mets = definition.split('::')[1].split()
                            else:
                                mets = definition.split()
                                
                                
                            if "/" in mets:
                                for met in [mets[i] for i in [0,2]]:
                                    met_sub = met.split()[0].replace('abs(','').replace(')','').strip().split('[')[0]
                                    if met_sub not in metricsInThresh:
                                        metricsInThresh.append(met_sub)
                            else:
                                
                                metric = mets[0].replace('abs(','').replace(')','').strip().split('[')[0]
                                if metric not in metricsInThresh:
                                    metricsInThresh.append(metric) 
                                
                                field3 = mets[2].replace('abs(','').replace(')','').strip().split('[')[0]
                                if ~field3.isnumeric():
                                    if field3 not in metricsInThresh:
                                        metricsInThresh.append(field3) 
    
                    metricThreshDict.update({threshold : metricsInThresh})
                    
                f.write('\n')
                f.write("thresholdsMetricsDict = ")
                print(metricThreshDict, file=f)
            
            self.confirmation_popup()
        except:
            self.warning_popup("Error while saving Thresholds")
 
    def confirmation_popup(self):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        warningLabel = Label(text="Thresholds Successfully saved")
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)
        
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(warningLabel)
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(returnButton)
        
        masterDict["_popup"] = Popup(title="Success", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()   
                                
class ExamineIssuesScreen(Screen):
    
    issues_rv = ObjectProperty()
    start_day = ObjectProperty()
    end_day = ObjectProperty()
    selectionIndices = list()   #used to track which lines are selected
    

    def warning_popup(self, txt):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=txt, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_warning_popup)


        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        masterDict["warning_popup"] = Popup(title="Warning", content=popupContent, size_hint=(.66, .66))
        masterDict["warning_popup"].open()
    
    def initiate_screen(self):
        self.load_issueFile(self)
        self.update_data(self)
    
    def set_dates(self):
        self.startday = self.ids.start_id.text
        self.endday = self.ids.end_id.text
        
    def load_issueFile(self):
        # self.issueFile is set while loading preferences, etc, in mainlayout
        self.df = pd.DataFrame(columns=("STATE", "ISSUE","SNCL","SN","START", "END", "DAYS", "VALUE", "NOTES","NET","STA","LOC","CHA"))

        try:
            with open(self.issueFile, 'r') as f:
                for line in f:
    
                    fields = line.split('|')
                    if '#' in line:
                        continue
                    issue = fields[0]
                    sncl = fields[1]
                    startd = fields[2].split('T')[0].replace('-','/')
    
                    endd = fields[3].split('T')[0].replace('-','/')
                    days = fields[4]
                    try:
                        if float(days) < 0:
                            days = ''
                    except:
                        continue
                    value = fields[5]
                    state = fields[6]
                    notes = fields[7].strip()
                    sn = sncl.split('.')[0] + '.' + sncl.split('.')[1]
                    net = sncl.split('.')[0]
                    sta = sncl.split('.')[1]
                    loc = sncl.split('.')[2]
                    cha = sncl.split('.')[3]
                    self.df.loc[len(self.df)] = [state,issue,sncl, sn, startd, endd, days, value, notes, net, sta, loc, cha]

        except:
            ExamineIssuesScreen.warning_popup(ExamineIssuesScreen,"WARNING:  Unable to open Issue File. Either Directory and/or Filename were omitted, or the file does not exist.")
            
        self.df = self.df.sort_values(by=['SN','START'])  
  
        # set the To Do flag to 0, to automatically show all issues
        self.iTodo = 0
        self.iRemaining = 0
        self.listOfSncls = self.df.SN.unique()

        self.iSelection = 0
        
        self.currentDF = self.df.drop(['SN','NET','STA','LOC','CHA'], axis=1)
    
    def update_data(self):
        
        examine_screen = screen_manager.get_screen('examineIssuesScreen')
        main_screen = screen_manager.get_screen('mainScreen')
        
        # Set up a spacing for each field
        spacing_dict = {0:10, 1: 15, 2: 22, 3: 13, 4: 13, 5: 6, 6: 7, 7:20}
        currentList = [{'text': ''.join([x[y].replace('\n', ' ').ljust(spacing_dict[y])[0:spacing_dict[y]] for y in range(len(x))])} for x in self.currentDF.values.tolist()]

        examine_screen.issues_rv.data = currentList
        examine_screen.start_day.text = main_screen.startDate.text
        examine_screen.end_day.text  = main_screen.endDate.text
    
    def get_examine_inputs(self):
#         if self.ids.examine_start_id.text:
        self.startday = self.ids.examine_start_id.text
#         if self.ids.examine_end_id.text:
        self.endday = self.ids.examine_end_id.text
        self.metrics = self.ids.metrics_id.text
        self.threshold = self.ids.threshold_id.text
        self.network = self.ids.network_id.text
        self.station = self.ids.station_id.text
        self.location = self.ids.location_id.text
        self.channel = self.ids.channel_id.text
        self.notes = self.ids.notes_id.text

    def set_target(self):
        try:
            self.target = self.currentSNCL.split('.')[0] + "." + self.currentSNCL.split('.')[1] + ".*.*H*"
        except:
            self.target = ''
        return self.target
    
    def dismiss_popup(self, *kwargs):
        masterDict["_popup"].dismiss()
      
    def dismiss_warning_popup(self, *kwargs):
        masterDict["warning_popup"].dismiss()  
        
    def exit_confirmation(self):
        content = ExitDialog(exit=ExitDialog.do_exit, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Confirm Exit", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
        
#     def create_ticket(self):
#         pass
    
    def see_databrowser(self):
        webbrowser.open("http://www.iris.edu/mustang/databrowser/", new=2)

    def see_waveforms(self):
        self.get_examine_inputs()
        
        if self.startday == "" or self.endday == "":
            self.warning_popup("WARNING: Start and End times required")
            return 
        
        if not self.network or not self.station or not self.location or not self.channel:
            self.warning_popup("WARNING: All target fields must be specified. Lists are allowed.")
            return
        
        image_dir = masterDict["imageDir"]     
        # create a directory for the waveform plots
        if not os.path.exists(image_dir):
            os.mkdir(image_dir)
            
        # Grab all of the pngs and save in the directory
        imageURL = "http://service.iris.edu/irisws/timeseries/1/query?"
       
        if len(self.startday.split('T')) == 1:
            starttime = self.startday + 'T00:00:00'
        else:
            starttime = self.startday
        if len(self.endday.split('T')) == 1:
            endtime = self.endday + 'T00:00:00'
        else:
            endtime = self.endday
            
        filename_list = []
        for net in self.network.split(','):
            net = net.strip()
            imageURL_net = imageURL + "net=" + net
            
            for sta in self.station.split(','):
                sta = sta.strip()
                imageURL_sta = imageURL_net + "&sta=" + sta
                
                for loc in self.location.split(','):
                    loc = loc.strip()
                    imageURL_loc = imageURL_sta + "&loc=" + loc
                    
                    for cha in self.channel.split(','):
                        cha = cha.strip()
                        imageURL_cha = imageURL_loc + "&cha=" + cha
                        
                        #imageURL_complete = imageURL_cha + "&starttime=" + self.startday + "&endtime=" + self.endday + "&helicordermode=false&format=png"
                        imageURL_complete = imageURL_cha + "&starttime=" + starttime + "&endtime=" + endtime + "&format=plot"
                        
                        print(imageURL_complete)
                        image_filename = image_dir + 'tmp.' + net +"_"+ sta +"_"+ loc +"_"+ cha + "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%s") + ".png"
                        
                        try:
                            urllib.request.urlretrieve(imageURL_complete, image_filename)
                            filename_list.append(image_filename)
                        except urllib.error.URLError as e:
                            print("WARNING: %s" % e.read())
                            self.warning_popup("WARNING: Could not retrieve waveforms")
                        except urllib.error.HTTPerror as e:
                            print("WARNING: %s" % e.read())
                            self.warning_popup("WARNING: Could not retrieve waveforms")
        
        # Open images
        if filename_list:
            for file in filename_list:
                subprocess.run(['open', file], check=True)

    def see_metrics(self):
        self.get_examine_inputs()
        
        if self.metrics == "":
            self.warning_popup("WARNING: Must specify metric name(s)")
            return 
        if self.network == "":
            self.warning_popup("WARNING: Must specify Network(s)")
            return
        if self.startday == "" or self.endday == "":
            self.warning_popup("WARNING: Start and End times required")
            return
        
        metricURL = "http://service.iris.edu/mustang/measurements/1/query?metric=" + self.metrics 
        
        if self.network:
            metricURL = metricURL + "&net=" + self.network 
        if self.station:
            metricURL = metricURL + "&sta=" + self.station
        if self.location:
            metricURL = metricURL + "&loc=" + self.location
        if self.channel:
            metricURL = metricURL + "&cha=" + self.channel
        
        metricURL = metricURL + "&format=text&timewindow=" + self.startday + "," + self.endday + \
                    "&orderby=start_asc&nodata=404"
        webbrowser.open(metricURL)

    def see_metric_timeseries(self):
        try:
            self.get_examine_inputs()
            if not os.path.exists(masterDict["imageDir"]):
                os.mkdir(masterDict["imageDir"])
            
            if not self.network:
                self.warning_popup("WARNING: Network field required")
                return
            if not self.station:
                self.warning_popup("WARNING: Station field required")
                return
            if not self.metrics:
                self.warning_popup("WARNING: Metric field required")
                return
            if not self.startday or not self.endday:
                self.warning_popup("WARNING: Start and End times required")
                return
            
    
            datelist = pd.date_range(self.startday, self.endday, freq='D')
            
            self.startday = self.startday.split('T')[0]
            self.endday = self.endday.split('T')[0]
            startday = self.startday.split('-')
            endday = self.endday.split('-')
            
            startdate = datetime.date(int(startday[0]),int(startday[1]),int(startday[2]))
            enddate = datetime.date(int(endday[0]), int(endday[1]), int(endday[2]))
              
            if enddate <= startdate:
                print("End Date must be after Start Date")
                return
            
            for metric in [i.lower().strip() for i in self.metrics.split(',')]:
                masterDict["plot_filename"] = masterDict["imageDir"] + "tmp.metric_timeseries_" + metric + '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%s") + ".png"
                metricURL = "http://service.iris.edu/mustang/measurements/1/query?metric=" + metric 
    
                if self.network:
                    metricURL = metricURL + "&net=" + self.network 
                if self.station:
                    metricURL = metricURL + "&sta=" + self.station
                if self.location:
                    metricURL = metricURL + "&loc=" + self.location
                if self.channel:
                    metricURL = metricURL + "&cha=" + self.channel
                
                metricURL = metricURL + "&format=text&timewindow=" + self.startday + "," + self.endday + \
                            "&orderby=start_asc&nodata=404"
                
                print(metricURL)
                
                try:            
                    metricDF = pd.read_csv(metricURL, header=1, parse_dates=['start'])
                    
                except:
                    print("Unable to retrieve metrics")
                    continue
                
                earliestDate = mdates.date2num(metricDF.start.min())
                latestDate = mdates.date2num(metricDF.start.max())
    
                metricDF['date'] = [mdates.date2num(d) for d in metricDF['start']]
                    
                if metric != "orientation_check":
                    targets_list =  metricDF.target.unique()
                    plotDF = pd.DataFrame(columns=targets_list, index=metricDF['date'])
                            
                    for index, row in metricDF.iterrows():
                        plotDF.loc[row['date'],row['target']] = row['value']
                
                else:
                    targets_list = [sncl+'-'+field for sncl in metricDF.target.unique() for field in ['azimuth_Y_obs','azimuth_X_obs','difference']]
                    plotDF = pd.DataFrame(columns=targets_list, index=metricDF['date'])
                    
                    for field in ['azimuth_Y_obs','azimuth_X_obs']:
                        for index, row in metricDF.iterrows():
                            plotDF.loc[row['date'],row['target']+'-'+field] = row[field]
                    
                    for index, row in metricDF.iterrows():
                        meta_field = field.replace('obs','meta')
                        diff = float(row[meta_field]) - float(row[field])
                        plotDF.loc[row['date'],row['target']+'-difference'] = diff
                    
                nDays = latestDate - earliestDate
                nTargets = len(targets_list)
                if nDays < 100:       
                    fig_width = 10
                elif nDays >= 100 and nDays < 200:
                    fig_width = 0.1 * nDays
                else:
                    fig_width = 20
                if nTargets < 2:    
                    fig_height = 3
                else: 
                    fig_height = 2 * nTargets
    
                axes = plotDF.plot(style='.', color='k', title=list(plotDF),  legend=False, subplots=True, sharex=True, sharey=True, figsize=(fig_width, fig_height))
                
                if nDays < 21:
                    for ax in axes:
                        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                        plt.minorticks_off()
                    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b-%d'))
                elif nDays < 60 and nDays >= 21:
                    for ax in axes:
                        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
                        ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
                    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b-%d'))
                elif nDays < 365 and nDays >= 60:
                    for ax in axes:
                        ax.xaxis.set_minor_locator(mdates.DayLocator(interval=7))
                        ax.xaxis.set_major_locator(mdates.MonthLocator())
                    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                     
                elif nDays >= 365 and nDays < 1000:
                    for ax in axes:
                        ax.xaxis.set_major_locator(mdates.MonthLocator())
                    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                    plt.minorticks_off()
                else:
                    for ax in axes:
                        ax.xaxis.set_major_locator(mdates.YearLocator())
                    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                    plt.minorticks_off()
        
                if metric == "orientation_check":
                    plt.setp(axes, yticks=[-360,-270,-180,-90,0,90,180,270,360], yticklabels=['','-270','','-90','','90','','270',''])
                    for ax in axes:
                        ax.yaxis.grid(True,linestyle='--')
                    
                    
                fig = axes[-1].get_figure()
                ax.set_xlim([datelist[0]-1, datelist[-1]+1])
                ax = fig.add_subplot(111, frameon=False)
                plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
                ax.set_ylabel(metric, labelpad=20)
                plt.tight_layout(1, .5, .5)
                
                plt.savefig(masterDict["plot_filename"])
                plt.close()
                subprocess.run(['open', masterDict["plot_filename"]], check=True)

        except:
            print("Error producing plot.")

    def see_pdfs(self):
        self.get_examine_inputs()
        pdfURL = "http://service.iris.edu/mustang/noise-pdf-browser/1/gallery?"
        
        if self.network == "":
            self.warning_popup("WARNING: Network field required")
            return 
        if self.startday == "":
            self.warning_popup("WARNING: Start field required")
            return 
        
        pdfstartday = self.startday.split('T')[0]
        startdate = datetime.datetime.strptime(self.startday, '%Y-%m-%d').strftime('%Y-%m-01')
        if self.network:
            pdfURL = pdfURL + "net=" + self.network + "&"
        if self.station:
            pdfURL = pdfURL + "sta=" + self.station + "&"
        if self.location:
            pdfURL = pdfURL + "loc=" + self.location + "&"
        if self.channel: 
            pdfURL = pdfURL + "cha=" + self.channel + "&"     
        pdfURL = pdfURL + "interval=month&maxintervals=5&starttime=" + startdate
        webbrowser.open(pdfURL)

    def see_spectrograms(self):
        self.get_examine_inputs()
        
        if self.network == "":
            self.warning_popup("WARNING: Network field required")
            return 
        
        spectURL = "http://service.iris.edu/mustang/noise-pdf-browser/1/spectrogram?"
        
        if self.network:
            spectURL = spectURL + "&net=" + self.network
        if self.station:
            spectURL = spectURL + "&sta=" + self.station
        if self.location:
            spectURL = spectURL + "&loc=" + self.location
        if self.channel:
            spectURL = spectURL + "&cha=" + self.channel  
         
        if self.startday:
            spectURL = spectURL + "&starttime=" + self.startday
        if self.endday:
            spectURL = spectURL + "&endtime=" + self.endday
        webbrowser.open(spectURL)

    def see_nmt(self):
        self.get_examine_inputs()

        if not self.network:
            self.warning_popup("WARNING: Network code required for Noise Mode Timeseries (cannot be wildcarded)")
            return
        if not self.station:
            self.warning_popup("WARNING: Station code required for  Noise Mode Timeseries (cannot be wildcarded)")
            return
        if not self.location:
            self.warning_popup("WARNING: Location code required for  Noise Mode Timeseries (cannot be wildcarded)")
            return
        if not self.channel:
            self.warning_popup("WARNING: Channel code required for  Noise Mode Timeseries (cannot be wildcarded)")
            return
        
        if not self.startday or not self.endday:
            self.warning_popup("WARNING: Start and End times required")
            return

        nmtURL = "http://service.iris.edu/mustang/noise-mode-timeseries/1/query?net=" + self.network + \
                "&sta="+ self.station +"&loc="+ self.location +"&cha="+ self.channel + \
                "&quality=M&starttime="+ self.startday + "&endtime=" + self.endday + "&output=power&format=plot&nodata=404"

        webbrowser.open(nmtURL)

    def see_goat(self):
        self.get_examine_inputs()
       
        if not self.network:
            self.warning_popup("WARNING: Network code required for GOAT (can be wildcarded)")
            return
        if not self.station:
            self.warning_popup("WARNING: Station code required for GOAT (can be wildcarded)")
            return
        if not self.location:
            self.warning_popup("WARNING: Location code required for GOAT (can be wildcarded)")
            return
        if not self.channel:
            self.warning_popup("WARNING: Channel code required for GOAT (can be wildcarded)")
#             print("Channel code required for GOAT (can be wildcarded)")
            return
        if not self.startday or not self.endday:
            self.warning_popup("WARNING: Start and End times required")
            return


        self.startday = self.startday.split('T')[0]
        self.endday = self.endday.split('T')[0]
        startdate = datetime.datetime.strptime(self.startday, '%Y-%m-%d').strftime('%Y/%m/%d')
        enddate = datetime.datetime.strptime(self.endday, '%Y-%m-%d').strftime('%Y/%m/%d')
        
        goatURL = "http://ds.iris.edu/data_available/" + self.network + \
                "/"+ self.station +"/"+ self.location +"/"+ self.channel + \
                "?scaling=time_range&both=on&bysta=off&byday=off&timewindow="+ \
                startdate +"-"+ enddate
        webbrowser.open(goatURL)

    def see_mda(self):
        self.get_examine_inputs()
        mdaURL = "http://ds.iris.edu/mda/"

        if not self.network:
            self.warning_popup("WARNING: Network code required for MDA")
            return
        if self.network:
            mdaURL = f"{mdaURL}{self.network}"
            if self.station:
                mdaURL = f"{mdaURL}/{self.station}"
                if self.location:
                    mdaURL = f"{mdaURL}/{self.location}"
                    if self.channel:
                        mdaURL = f"{mdaURL}/{self.channel}"

        
        webbrowser.open(mdaURL)


    def see_events(self):
        self.get_examine_inputs()
        
        if self.startday == "" or self.endday == "":
            self.warning_popup("WARNING: Start and End times required")
            return 
        
        self.startday = self.startday.split('T')[0]
        self.endday = self.endday.split('T')[0]
        eventURL = "https://earthquake.usgs.gov/fdsnws/event/1/query?starttime=" + \
                   self.startday + "&endtime=" + self.endday + "&minmag=5.5&orderby=time&format=text&nodata=404"
        webbrowser.open(eventURL)
        
    def see_stations(self):
        self.get_examine_inputs()
        
        if self.network == "":
            self.warning_popup("WARNING: Network field required")
            return 
        
        stationURL = "http://service.iris.edu/fdsnws/station/1/query?"
        
        if self.network:
            stationURL = stationURL + "net=" + self.network
        if self.station:
            stationURL = stationURL + "&sta=" + self.station
        if self.location:
            stationURL = stationURL + "&loc=" + self.location
        if self.channel:
            stationURL = stationURL + "&cha=" + self.channel
        stationURL = stationURL + "&level=channel&format=text&includecomments=true&nodata=404"
        
        webbrowser.open(stationURL)

    def load_issue_file(self):
        try:
            self.sncln
        except:
            if len(self.listOfSncls) == 0:
                pass
            else:
                self.sncln = 0
                self.currentSNCL = self.listOfSncls[self.sncln]
                ExamineIssuesScreen.currentDF = self.df[self.df['SN'] == self.currentSNCL].drop(['SN','NET','STA','LOC','CHA'], axis=1)
                self.update_data()
                self.ids.network_id.text = self.currentSNCL.split('.')[0]
                self.ids.station_id.text = self.currentSNCL.split('.')[1]
                self.ids.threshold_id.text = ''
                ExamineIssuesScreen.selectionIndices = list()  # have to clear the selection list if we've switched the displayed issues
                self.deselect_all()
        
    def go_to_next(self):
        try:
            self.sncln+=1
        except:
            self.sncln = 0
            
        if len(self.listOfSncls) <= self.sncln:
            self.sncln=0
            
        if len(self.listOfSncls) == 0:
                pass
        else:
            self.currentSNCL = self.listOfSncls[self.sncln]
            
            if self.iTodo == 1:
                ExamineIssuesScreen.currentDF = self.df[(self.df['SN'] == self.currentSNCL) &
                                (self.df['STATE'] == 'TODO')].drop(['SN','NET','STA','LOC','CHA'], axis=1)
            else:
                ExamineIssuesScreen.currentDF = self.df[self.df['SN'] == self.currentSNCL].drop(['SN','NET','STA','LOC','CHA'], axis=1)
    
            self.update_data()
            self.ids.network_id.text = self.currentSNCL.split('.')[0]
            self.ids.station_id.text = self.currentSNCL.split('.')[1]
            self.ids.threshold_id.text = ''
            ExamineIssuesScreen.selectionIndices = list()  # have to clear the selection list if we've switched the displayed issues
            self.deselect_all()

        if self.iRemaining == 1:
            self.iRemaining = 0
            self.ids.remianing_id.state = 'normal'
          
    def go_to_previous(self):
        try:
            self.sncln= self.sncln - 1
        except:
            self.sncln = 0
        if len(self.listOfSncls) < abs(self.sncln):
            self.sncln=-1
            
        if len(self.listOfSncls) == 0:
                pass
        else:
            self.currentSNCL = self.listOfSncls[self.sncln]
            
            if self.iTodo == 1:
                ExamineIssuesScreen.currentDF = self.df[(self.df['SN'] == self.currentSNCL) &
                                (self.df['STATE'] == 'TODO')].drop(['SN','NET','STA','LOC','CHA'], axis=1)
            else:
                ExamineIssuesScreen.currentDF = self.df[self.df['SN'] == self.currentSNCL].drop(['SN','NET','STA','LOC','CHA'], axis=1)
            self.update_data()
            self.ids.network_id.text = self.currentSNCL.split('.')[0]
            self.ids.station_id.text = self.currentSNCL.split('.')[1]
            self.ids.threshold_id.text = ''
            ExamineIssuesScreen.selectionIndices = list()  # have to clear the selection list if we've switched the displayed issues
            self.deselect_all()

        if self.iRemaining == 1:
            self.iRemaining = 0
            self.ids.remianing_id.state = 'normal'
            
    def see_all_issues(self):
        self.get_examine_inputs() 
        ExamineIssuesScreen.currentDF = self.df.drop(['SN','NET','STA','LOC','CHA'], axis=1)
        self.update_data()
        
        ExamineIssuesScreen.selectionIndices = list()  # have to clear the selection list if we've switched the displayed issues
        self.deselect_all()
        
        if self.iTodo == 1:
            self.iTodo = 0
            self.ids.todo_id.state = 'normal'
        if self.iRemaining == 1:
            self.iRemaining = 0
            self.ids.remianing_id.state = 'normal'
    
    def see_todo(self):
        self.get_examine_inputs() 
        if not hasattr(self,'sncln'):
            self.sncln = 0
        if self.iTodo == 1:
            # if iTodo is 1, then show only TODOs for given station or threshold
            if self.threshold:
                ExamineIssuesScreen.currentDF = self.df[(self.df['ISSUE'].isin([x.strip() for x in self.threshold.split(',')])) &
                            (self.df['STATE'] == 'TODO')].drop(['SN','NET','STA','LOC','CHA'], axis=1)
                self.update_data()
            else:
                if len(self.listOfSncls) == 0:
                    pass
                else:
                    currentSNCL = self.listOfSncls[self.sncln]
                    ExamineIssuesScreen.currentDF = self.df[(self.df['SN'] == currentSNCL) &
                                                      (self.df['STATE'] == 'TODO')].drop(['SN','NET','STA','LOC','CHA'], axis=1)
                    self.update_data()

        elif self.iTodo == 0:
            # if iTodo is 0, then show everything
            if self.threshold:
                self.go_to_threshold()
            else:
                if len(self.listOfSncls) == 0:
                    pass
                else:
                    currentSNCL = self.listOfSncls[self.sncln]
                    ExamineIssuesScreen.currentDF = self.df[(self.df['SN'] == currentSNCL)].drop(['SN','NET','STA','LOC','CHA'], axis=1)
                    self.update_data()
        
        ExamineIssuesScreen.selectionIndices = list()  # have to clear the selection list if we've switched the displayed issues
        self.deselect_all()
        
    def set_todo(self,state):
        if state == "normal":
            self.iTodo = 0
        elif state == "down":
            self.iTodo = 1
            if self.iRemaining == 1:
                self.iRemaining = 0
        self.see_todo()    
            
    def see_remaining(self):
        self.get_examine_inputs() 
        if not hasattr(self,'sncln'):
            self.sncln = 0
        if self.iRemaining == 1:
            # if iRemaining is 1, then we want to see all remaining TODO tickets
            ExamineIssuesScreen.currentDF = self.df[(self.df['STATE'] == 'TODO')].drop(['SN','NET','STA','LOC','CHA'], axis=1)
            self.update_data()

        elif self.iRemaining == 0:
            # if iRemaining is 0, then we want to go back to the particular station, seeing issues depending on if iTodo is 0 or 1
            if self.iTodo == 0:
                if len(self.listOfSncls) == 0:
                    pass
                else:
                    currentSNCL = self.listOfSncls[self.sncln]
                    ExamineIssuesScreen.currentDF = self.df[(self.df['SN'] == currentSNCL)].drop(['SN','NET','STA','LOC','CHA'], axis=1)
                    self.update_data()
                
            elif self.iTodo == 1:
                if len(self.listOfSncls) == 0:
                    pass
                else:
                    currentSNCL = self.listOfSncls[self.sncln]
                    ExamineIssuesScreen.currentDF = self.df[(self.df['SN'] == currentSNCL) &
                                 (self.df['STATE'] == 'TODO')].drop(['SN','NET','STA','LOC','CHA'], axis=1)
                    self.update_data()

        ExamineIssuesScreen.selectionIndices = list()  # have to clear the selection list if we've switched the displayed issues
        self.deselect_all()
           
    def set_remaining(self,state):
        if state == "normal":
            self.iRemaining = 0

        elif state == "down":
            self.iRemaining = 1
            if self.iTodo == 1:
                self.iTodo = 0
            
        self.see_remaining()    
          
    def go_to_target(self):
        self.get_examine_inputs()     
        tmpDF = self.df.copy()
        try:
            if self.network:
                tmpDF = tmpDF[tmpDF['NET'].str.upper().isin([x.strip().upper() for x in self.network.split(',')])]
            if self.station:
                tmpDF = tmpDF[tmpDF['STA'].str.upper().isin([x.strip().upper() for x in self.station.split(',')])]
            if self.location:
                tmpDF = tmpDF[tmpDF['LOC'].str.upper().isin([x.strip().upper() for x in self.location.split(',')])]
            if self.channel:
                tmpDF = tmpDF[tmpDF['CHA'].str.upper().isin([x.strip().upper() for x in self.channel.split(',')])]

            if self.iTodo == 1:
                tmpDF = tmpDF[tmpDF['STATE'] == 'TODO']
            
            ExamineIssuesScreen.currentDF = tmpDF.drop(['SN','NET','STA','LOC','CHA'], axis=1)
               
            if tmpDF.empty:
                firstN = [x.strip() for x in self.network.split(',')][0]
                firstS = [x.strip() for x in self.station.split(',')][0]
                firstSN = firstN + '.' + firstS
                self.sncln = np.where(self.listOfSncls == firstSN)[0][0]
                
            else:
                # update the sncln so that you go to the next/previous station when hitting next/previous
                sncln, = np.where(self.listOfSncls == tmpDF['SN'].iloc[0])
                self.sncln = sncln[0]
            
            self.ids.threshold_id.text = ''
            self.update_data()
            ExamineIssuesScreen.selectionIndices = list()  # have to clear the selection list if we've switched the displayed issues
            self.deselect_all()
        except:
            print("Cannot subset to provided target")
            
    def go_to_threshold(self):
        self.get_examine_inputs()     
        tmpDF = self.df.copy()

        try:
            if self.threshold:
                
                if self.iTodo == 1:
                    tmpDF = tmpDF[(tmpDF['ISSUE'].str.upper().isin([x.strip().upper() for x in self.threshold.split(',')])) &
                                  (tmpDF['STATE'] == 'TODO')]
                else:
                    tmpDF = tmpDF[tmpDF['ISSUE'].str.upper().isin([x.strip().upper() for x in self.threshold.split(',')])]
                            
                ExamineIssuesScreen.currentDF = tmpDF.drop(['SN','NET','STA','LOC','CHA'], axis=1)

                self.update_data()
                ExamineIssuesScreen.selectionIndices = list()  # have to clear the selection list if we've switched the displayed issues
                self.deselect_all()
                self.ids.station_id.text = ''
            else:
                print("No Threshold provided")
        except:
            print("Cannot subset to provided threshold")
            
    def deselect_all(self):
        examine_screen = screen_manager.get_screen('examineIssuesScreen')
        examine_screen.issues_rv._layout_manager.clear_selection()
        ExamineIssuesScreen.selectionIndices = list()

    def select_all(self):
        examine_screen = screen_manager.get_screen('examineIssuesScreen')
        try:
            nRow = len(self.currentDF.index)
            for node in range(nRow):
                examine_screen.issues_rv._layout_manager.select_node(node)
                self.selectionIndices.append(node)
        except:
            print("No issues loaded yet")

    def add_notes(self):
        self.get_examine_inputs()  
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
        except:
            print("No issues loaded yet")
            return
        
        self.df['NOTES'].ix[indToChange] = self.notes
        ExamineIssuesScreen.currentDF['NOTES'].ix[indToChange] = self.notes
        self.update_data()
    
    def see_notes(self):
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            currentNotes = self.currentDF.ix[indToChange]
        except:
            print('No issues loaded yet')
            return
        
        # The series of notes to display is in a StackLayout to get the top alignment correct
        notes_layout = StackLayout(orientation='lr-tb', size_hint_y = None, spacing=[0,20])
        notes_layout.bind(minimum_height=notes_layout.setter('height'))
        
        for ind in indToChange:
            t = Label(text=currentNotes['SNCL'][ind],size_hint_y=None, size_hint_x=.15)
            notes_layout.add_widget(t)
            
            s = Label(text=currentNotes['START'][ind],size_hint_y=None, size_hint_x=.1)
            notes_layout.add_widget(s)
            
            e = Label(text=currentNotes['END'][ind],size_hint_y=None, size_hint_x=.1)
            notes_layout.add_widget(e)
            
            l = Label(text=currentNotes['NOTES'][ind],size_hint_y=None, size_hint_x=.65)
            l.bind(width=lambda S, W:
                   S.setter('text_size')(S, (W, None)))
            
            # Don't want the bind if it's only one line, but if it is more than that, then do
            nline = currentNotes['NOTES'][ind].count('\n')
            nchar = len(currentNotes['NOTES'][ind])
            if (nline * 92) + nchar > 92:
                l.bind(texture_size=l.setter('size'))
            notes_layout.add_widget(l)
        
        # The notes (in a box layout) go into a ScrollView
        scrl = ScrollView(size=(Window.width, Window.height*.8), size_hint_y=None)
        scrl.add_widget(notes_layout)
        
        # The scrollable notes list and a 'return' button go into a box layout
        content = BoxLayout(orientation='vertical')
        content.add_widget(scrl)
        
        btnclose = Button(text = "Return", size_hint_y = None)
        content.add_widget(btnclose)
        
        # That single box layout widget, with everything, goes in the popup
        masterDict["_popup"] = Popup(title='', separator_height=0, 
                      content = content,
                      size_hint=(0.9, 0.9), auto_dismiss = True)
    
        btnclose.bind(on_press = masterDict["_popup"].dismiss)
        masterDict["_popup"].open()

    def thresholds_popup_orig(self, *kwargs):
        # a popup with all of the thresholds listed in a digestable way
        # very similar to the thresholds listed on the final report
        
        
        # create text that will be displayed
        try:
            # If it is already loaded because the user has been to the thresholds editor, use that
            thresholdsDict = sorted(masterDict['thresholdsDict'].keys())
        except:
            # But if they haven't, then load up the file
            with open(masterDict['thresholds_file']) as f:
                local_dict = locals()
                exec(compile(f.read(), masterDict['thresholds_file'], "exec"), globals(), local_dict)
            
            masterDict['thresholdsDict'] = local_dict['thresholdsDict']
            masterDict['instrumentGroupsDict'] = local_dict['instrumentGroupsDict']        
            masterDict['thresholdGroups'] = local_dict['thresholdGroups']
            thresholdsDict = sorted(masterDict['thresholdsDict'].keys())
            
        displayList = []
        for thresholdName in thresholdsDict:
#             print(thresholdName)
            displayList.append(thresholdName)
#             f.write("<b>%s</b>    \t" % thresholdName);            
            for instrumentGroup in masterDict['thresholdsDict'][thresholdName].keys():
               
                defStr = ' && '.join(masterDict['thresholdsDict'][thresholdName][instrumentGroup])

#                 print("     %s - %s" % (instrumentGroup,defStr));
                displayList.append("     %s - %s" % (instrumentGroup,defStr))
                
            displayList.append("")
        
        displayFull = '\n'.join(displayList)
        
        # create the popup
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=displayFull, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)


        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        masterDict["_popup"] = Popup(title="Existing Threshold Definition", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()

    def thresholds_popup(self, *kwargs):
        
        # create text that will be displayed
        try:
            # If it is already loaded because the user has been to the thresholds editor, use that
            thresholdsDict = sorted(masterDict['thresholdsDict'].keys())
        except:
            # But if they haven't, then load up the file
            with open(masterDict['thresholds_file']) as f:
                local_dict = locals()
                exec(compile(f.read(), masterDict['thresholds_file'], "exec"), globals(), local_dict)
            
            masterDict['thresholdsDict'] = local_dict['thresholdsDict']
            masterDict['instrumentGroupsDict'] = local_dict['instrumentGroupsDict']        
            masterDict['thresholdGroups'] = local_dict['thresholdGroups']
            thresholdsDict = sorted(masterDict['thresholdsDict'].keys())
            
        displayList = []
        for thresholdName in thresholdsDict:
#             print(thresholdName)
            displayList.append(thresholdName)
#             f.write("<b>%s</b>    \t" % thresholdName);            
            for instrumentGroup in masterDict['thresholdsDict'][thresholdName].keys():
               
                defStr = ' && '.join(masterDict['thresholdsDict'][thresholdName][instrumentGroup])

#                 print("     %s - %s" % (instrumentGroup,defStr));
                displayList.append("     %s - %s" % (instrumentGroup,defStr))
                
            displayList.append("")
        
        
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        
        metricContent = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        metricContent.bind(minimum_height=metricContent.setter('height'))

        for line in displayList:
            t = TextInput(text=line, padding=[0,0], readonly=True, background_color=[.2,.2,.2,0], foreground_color=[1,1,1,1], background_active='', background_normal='', size_hint_y=None, height=40)
            t.bind(minimum_height=t.setter('height'))
            metricContent.add_widget(t)

        scrlvw = ScrollView(size_hint_y=6)
        scrlvw.add_widget(metricContent)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)

        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrlvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        
        masterDict["_popup"] = Popup(title="Existing Thresholds", content=popupContent, size_hint=(.4, .66))
        masterDict["_popup"].open()



    def metrics_popup(self, *kwargs):
        masterDict['metrics_file']
        
        try:
            with open(masterDict['metrics_file'],'r') as f:
                metricList = f.read().splitlines()
        except:
            print("ERROR: Unable to open metric file %s, does it still exist?" % masterDict['metrics_file'])        
            return 
        
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        
        metricContent = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        metricContent.bind(minimum_height=metricContent.setter('height'))

        metricsAdded = list()
        for metric in metricList:
            if "::" in metric:
                metric = metric.split('::')[0]
            if metric not in metricsAdded:    
                t = TextInput(text=metric, padding=[20,5], readonly=True, background_color=[.2,.2,.2,0], foreground_color=[1,1,1,1], background_active='', background_normal='', size_hint_y=None,height=50)
                metricContent.add_widget(t)
                metricsAdded.append(metric)

            
        scrlvw = ScrollView(size_hint_y=6)
        scrlvw.add_widget(metricContent)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)

        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrlvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        
        masterDict["_popup"] = Popup(title="List of Metrics", content=popupContent, size_hint=(.2, .66))
        masterDict["_popup"].open()
    
    def mark_as_todo(self):
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            self.df['STATE'].ix[indToChange] = 'TODO'
            self.currentDF['STATE'].ix[indToChange] = 'TODO'
            self.update_data()
        except:
            print("No issues loaded yet")
            pass
    
    def mark_as_new(self):
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            self.df['STATE'].ix[indToChange] = 'New'
            self.currentDF['STATE'].ix[indToChange] = 'New'
            self.update_data()
        except:
            print("No issues loaded yet")
            pass
    
    def mark_as_closed(self):
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            self.df['STATE'].ix[indToChange] = 'Closed'
            self.currentDF['STATE'].ix[indToChange] = 'Closed'
            self.update_data()
        except:
            print("No issues loaded yet")
            pass
    
    def mark_as_existing(self):
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            self.df['STATE'].ix[indToChange] = 'Existing'
            self.currentDF['STATE'].ix[indToChange] = 'Existing'
            self.update_data()
        except:
            print("No issues loaded yet")
            pass
    
    def mark_as_support(self):
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            self.df['STATE'].ix[indToChange] = 'Support'
            self.currentDF['STATE'].ix[indToChange] = 'Support'
            self.update_data()
        except:
            print("No issues loaded yet")
            pass
        
    def mark_as_no_ticket(self):
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            self.df['STATE'].ix[indToChange] = 'No Ticket'
            self.currentDF['STATE'].ix[indToChange] = 'No Ticket'
            self.update_data()
        except:
            print("No issues loaded yet")
            pass
        
    def mark_as_false_positive(self):
        try:
            indToChange = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            self.df['STATE'].ix[indToChange] = 'False Pos'
            self.currentDF['STATE'].ix[indToChange] = 'False Pos'
            self.update_data()
        except:
            print("No issues loaded yet")
            pass
    
    def get_selected_values(self):
        # This one gets the values of the selected rows
        # It is used in the NewTickets screen
        
        try:
            selectedInd = list(set(self.currentDF.iloc[self.selectionIndices].index.values.tolist()))
            NewTicketScreen.targets = self.df['SNCL'].ix[selectedInd].values.tolist()
            NewTicketScreen.descriptions = self.df['NOTES'].ix[selectedInd].values.tolist()
        except:
            print("No issues loaded yet")
            NewTicketScreen.targets = []
            NewTicketScreen.descriptions = []
        
    def go_To_NewTickets(self, *kwargs):
        NewTicketScreen.go_to_newTicketsScreen(NewTicketScreen)
        
    def save_progress(self):
        output_file = self.issueFile
        backup_copy = output_file + '.bck'
        self.df[['ISSUE','SNCL','START','END','DAYS','VALUE', 'STATE','NOTES']].to_csv(output_file, sep='|', header=False, index=False)
        self.df[['ISSUE','SNCL','START','END','DAYS','VALUE', 'STATE','NOTES']].to_csv(backup_copy, sep='|', header=False, index=False)
        print("Committed to " + output_file + " at " + str(datetime.datetime.now().time()))

class NewTicketScreen(Screen):
    selectedThresholds = list()   #used to track which thresholds are selected
    selectionIndices = list()   #used to track which lines are selected
    selectedImages = list()
    selectedLinks = list()
        
    newTicket_thresholds_rv = ObjectProperty()
 
    def warning_popup(self, txt):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=txt, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_warning_popup)


        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        masterDict["warning_popup"] = Popup(title="Warning", content=popupContent, size_hint=(.66, .66))
        masterDict["warning_popup"].open()
    
    def go_to_newTicketsScreen(self):
        newTicket_screen = screen_manager.get_screen('newTicketsScreen')
        
        with open(masterDict['thresholds_file']) as f:
            local_dict = locals()
            exec(compile(f.read(), masterDict['thresholds_file'], "exec"),globals(), local_dict)
            
        masterDict['thresholdsDict'] = local_dict['thresholdsDict']
        masterDict['instrumentGroupsDict'] = local_dict['instrumentGroupsDict']        
            
        ## Threshold names
        masterDict['threshold_names'] = sorted(list(masterDict['thresholdsDict'].keys()))
        
        my_thresholds = [{'text': '   %s' % x} for x in masterDict['threshold_names']]
        newTicket_screen.newTicket_thresholds_rv.data = my_thresholds 
        
    def exit_confirmation(self, *kwargs):
        content = ExitDialog(exit=ExitDialog.do_exit, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Confirm Exit", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def dismiss_popup(self, *kwargs):
        masterDict["_popup"].dismiss()
    
    def dismiss_warning_popup(self, *kwargs):
        masterDict["warning_popup"].dismiss()
    
    def dismiss_image_popup(self, *kwargs):
        masterDict["image_popup"].dismiss()
        
    def clear_images(self):
        masterDict['imageList'] = dict()
        self.selectedImages = []

    def image_popup(self, *kwargs):
       
        # The scrollview and the navigation buttons at the bottom go into this boxlayout
        masterDict["image_content"] = BoxLayout(orientation='vertical')
        
        # This contains the scrollview of images and the buttons to add/remove
        upperLayout = GridLayout(cols=2)
        upperLayout.bind(minimum_height=upperLayout.setter('height'))
        
        # The individual buttons will go in here, then this boxlayout goes into the scrollview
        image_layout = BoxLayout(size_hint_y = None, orientation='vertical', spacing=5)
        image_layout.bind(minimum_height=image_layout.setter('height'))
        
        if len(masterDict["imageList"]) > 0:
            image_id=0
            for row in masterDict["imageList"]:
                b = ToggleButton(text = row, size_hint_y = None, halign = 'left',
                                background_color = (.5,.5,.5,1), group='imageButtons')
                b.bind(state=self.check_image)
                 
                image_layout.add_widget(b)
                image_id += 1
        
            # The notes (in a box layout) go into a ScrollView
            scrl = ScrollView(size_hint_y=4)
            scrl.add_widget(image_layout)

            upperLayout.add_widget(scrl)
                
        else:
            upperLayout.add_widget(Label(text='No Images'))
        
        # Add the navigation buttons for the bottom of the popup
        actionButtons = BoxLayout(orientation='vertical', size_hint_x=.25,padding=10, spacing=5)
        
        actionButtons.add_widget(Button(text="Add image", on_release=self.image_load))
        actionButtons.add_widget(Button(text="View image", on_release=self.open_image))
        actionButtons.add_widget(Button(text="Remove image", on_release=self.remove_images))
        for i in range(4):
            actionButtons.add_widget(Label())
        
        upperLayout.add_widget(actionButtons)
        
        
        labelLayout = BoxLayout(orientation='vertical', size_hint_y=0.1)
        labelsBox = BoxLayout(orientation='horizontal')
        label1 =  Label(text="Existing Caption:", size_hint=(1.0, 1.0), halign="left", valign="middle")
        label1.bind(size=label1.setter('text_size'))    
        labelsBox.add_widget(label1)
        
        label2 = Label(text="New Caption:", size_hint=(1.0, 1.0), halign="left", valign="middle")
        label2.bind(size=label2.setter('text_size'))   
        labelsBox.add_widget(label2) 

        labelLayout.add_widget(labelsBox)
        
        
        captionBox = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        
        # Label of existing caption text, and copy-the-text-to-the-input button
        captionLabelBox = BoxLayout(orientation='horizontal',padding=10, spacing=5)
        scrvw = ScrollView()
        
        self.captionLabel = Label(text="", size_hint_y=None, halign='left')
        self.captionLabel.bind(width=lambda S, W:
                   S.setter('text_size')(S, (W, None)),
                    texture_size=self.captionLabel.setter('size'))
        
        scrvw.add_widget(self.captionLabel)
        
        captionLabelBox.add_widget(scrvw)
        captionLabelBox.add_widget(Button(text="Copy\nCaption", on_release=self.copy_caption, size_hint_x=0.25 ))
        
        # Text input for adding new caption, and the Add caption button
        captionInputBox = BoxLayout(orientation='horizontal',padding=10, spacing=5)
        self.captionInput = TextInput(text="")
        self.captionInput.bind()
        captionInputBox.add_widget(self.captionInput)
        captionInputBox.add_widget(Button(text="Add caption", on_release=self.add_caption, size_hint_x=0.25))
        
        captionBox.add_widget(captionLabelBox)
        captionBox.add_widget(captionInputBox)
        
        navButtons=BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=(0,10,0,0), spacing=5)
        navButtons.add_widget(Button(text="Return", on_release=self.dismiss_image_popup))

        masterDict["image_content"].add_widget(upperLayout)
        masterDict["image_content"].add_widget(labelLayout)
        masterDict["image_content"].add_widget(captionBox)
        masterDict["image_content"].add_widget(navButtons)
        
        masterDict["image_popup"] = Popup(title="Select Images", content=masterDict["image_content"],
                            size_hint=(0.9, 0.9))
        masterDict["image_popup"].open()

    def check_image(self, image, state):
        if state == "down":
            if image.text not in self.selectedImages:
                self.selectedImages.append(image.text)
                self.captionLabel.text = masterDict['imageList'][self.selectedImages[0]]
#                 self.captionInput.text = masterDict['imageList'][self.selectedImages[0]]
            
        else:
            self.selectedImages = [v for v in self.selectedImages if v != image.text]
            self.captionLabel.text = ""

    def open_image(self, *kwargs):
        for file in self.selectedImages:
            try:
                subprocess.run(['open', file], check=True)
            except Exception as e:
                self.warning_popup("WARNING: Unable to open %s: %s" %(file, e))
#                 print("WARNING: Unable to open %s: %s" %(file, e))
  
    def remove_images(self, *kwargs):
        for file in self.selectedImages:
            try:
                del masterDict['imageList'][file]
            except KeyError as e:
                self.warning_popup("WARNING: File not found in list - %s" % e)
#                 print("WARNING: File not found in list - %s" % e)
            
            self.selectedImages = [v for v in self.selectedImages if v != file]
            
        self.dismiss_image_popup()
        self.image_popup()
        self.ids.image_id.text = "\n".join([i.split('/')[-1] for i in masterDict["imageList"]])
   
    def copy_caption(self, *kwargs):
        self.captionInput.text = self.captionLabel.text
        
    def add_caption(self, button, *kwargs):
        try:
            masterDict['imageList'][self.selectedImages[0]] = self.captionInput.text
            self.captionLabel.text = masterDict['imageList'][self.selectedImages[0]]
            print("INFO: Caption added")
        except Exception as e:
            if str(e) == "list index out of range":
                self.warning_popup("WARNING: could not add caption to file - no image selected")
            else:
                self.warning_popup("WARNING: could not add caption to file - %s" % e)
            print("WARNING: could not add caption to file -- %s" % e)
  
    def image_load(self, *kwargs):
        content = LoadDialog(load=self.load_image, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load image", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
    
    def load_image(self,path, filename):
        self.dismiss_image_popup()
        
        if not filename[0] in masterDict["imageList"]:
            masterDict["imageList"].update({filename[0]:""})
        
        self.ids.image_id.text = "\n".join([i.split('/')[-1] for i in masterDict["imageList"]])
        self.dismiss_popup()
        self.image_popup()  

    def link_popup(self, *kwargs):
        # The scrollview and the navigation buttons at the bottom go into this boxlayout
        masterDict["link_content"] = BoxLayout(orientation='vertical')
        
        # This contains the scrollview of images and the buttons to add/remove
        upperLayout = GridLayout(cols=2)
        upperLayout.bind(minimum_height=upperLayout.setter('height'))
        
        # The individual buttons will go in here, then this boxlayout goes into the scrollview
        image_layout = BoxLayout(size_hint_y = None, orientation='vertical', spacing=5)
        image_layout.bind(minimum_height=image_layout.setter('height'))
        
        if len(masterDict["linkList"]) > 0:
            link_id=0
            for row in masterDict["linkList"]:
#                 b = ToggleButton(text = row, size_hint_y = None, halign = 'left', id=str(link_id),
#                                 background_color = (.5,.5,.5,1), group='imageButtons')
                b = ToggleButton(text = row, size_hint_y = None, halign = 'left',
                                background_color = (.5,.5,.5,1), group='imageButtons')
                b.bind(state=self.check_link)
                 
                image_layout.add_widget(b)
                link_id += 1
#         
            # The notes (in a box layout) go into a ScrollView
            scrl = ScrollView(size_hint_y=4)
            scrl.add_widget(image_layout)

            upperLayout.add_widget(scrl)
                
        else:
            upperLayout.add_widget(Label(text='No Links'))
        
        # Add the navigation buttons for the bottom of the popup
        actionButtons = BoxLayout(orientation='vertical', size_hint_x=.25,padding=10, spacing=5)
    
        actionButtons.add_widget(Button(text="Remove link", on_release=self.remove_link))
        for i in range(4):
            actionButtons.add_widget(Label())
        actionButtons.add_widget(Button(text="Add link", on_release=self.add_link))
        
        upperLayout.add_widget(actionButtons)
        
        captionBox = BoxLayout(orientation='horizontal', size_hint_y=0.25)
#         self.linkInput = TextInput(text="", id='linkID')
        self.linkInput = TextInput(text="")
        self.linkInput.bind()
        captionBox.add_widget(self.linkInput)
        
        navButtons=BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=(0,10,0,0), spacing=5)
        navButtons.add_widget(Button(text="Return", on_release=self.dismiss_link_popup))

        masterDict["link_content"].add_widget(upperLayout)
        masterDict["link_content"].add_widget(captionBox)
        masterDict["link_content"].add_widget(navButtons)
        
        masterDict["link_popup"] = Popup(title="Add Links", content=masterDict["link_content"],
                            size_hint=(0.9, 0.9))
        masterDict["link_popup"].open()    

    def check_link(self, link, state):
        if state == "down":
            if link.text not in self.selectedLinks:
                self.selectedLinks.append(link.text)
        else:
            self.selectedLinks = [v for v in self.selectedLinks if v != linkn.text]
        
    def remove_link(self, *kwargs):
        for file in self.selectedLinks:
            try:
                masterDict['linkList'] = [v for v in masterDict['linkList'] if v != file]
            except KeyError as e:
                print("WARNING: File not found in list - %s" % e)
            
            self.selectedLinks = [v for v in self.selectedLinks if v != file]
            
        self.dismiss_link_popup()
        self.link_popup()
        self.ids.links_id.text = "\n".join([i for i in masterDict["linkList"]])

    def add_link(self, button, *kwargs):
        try:
            masterDict['linkList'].append(self.linkInput.text)
            self.ids.links_id.text = "\n".join([i for i in masterDict["linkList"]])
            print("INFO: Link added")
        except Exception as e:
            print("WARNING: could not add link to list -- %s" % e)
            
        self.dismiss_link_popup()
        self.link_popup() 
        
    def dismiss_link_popup(self, *kwargs):
        masterDict["link_popup"].dismiss()
        
    def import_target(self):
        ExamineIssuesScreen.get_selected_values(ExamineIssuesScreen)

        if len(self.targets) == 0:
            self.warning_popup("WARNING: No targets selected")
            return
        
        if len(set(self.targets)) > 1:
            netList = set([n.split('.')[0] for n in self.targets])
            self.ids.ticket_net_id.text = ','.join(netList)  
            
            staList = set([s.split('.')[1] for s in self.targets])
            self.ids.ticket_sta_id.text = ','.join(staList)  
            
            locList = set([l.split('.')[2] for l in self.targets])
            self.ids.ticket_loc_id.text = ','.join(locList)  
            if self.ids.ticket_loc_id.text == '':
                self.ids.ticket_loc_id.text = '--'
                
            chanList = set([c.split('.')[3] for c in self.targets])
            chaCombo = []
            for cha in chanList:
                chaA = cha[0]
                chaB = cha[1]
                chaC = cha[2]
                cha1 = [];    cha2 = []; cha3 = []
                if chaA not in cha1:
                    cha1.append(chaA)
                if chaB not in cha2:
                    cha2.append(chaB)
                if chaC not in cha3:
                    cha3.append(chaC)
                                
                cha1 = ''.join(cha1)
                if len(cha1) > 1:
                    cha1 = '[' + cha1 + ']'
                cha2 = ''.join(cha2)
                if len(cha2) > 1:
                    cha2 = '[' + cha2 + ']'
                cha3 = ''.join(cha3)
                if len(cha3) > 1:
                    cha3 = '[' + cha3 + ']'
                chaStr = cha1 + cha2 + cha3
                chaStr = ''.join(chaStr)
                        
                if chaStr not in chaCombo:
                    chaCombo.append(chaStr) 
            self.ids.ticket_chan_id.text = ','.join(chaCombo)    
            
                    
        else:
            self.ids.ticket_net_id.text = self.targets[0].split('.')[0]
            self.ids.ticket_sta_id.text = self.targets[0].split('.')[1]
            self.ids.ticket_loc_id.text = self.targets[0].split('.')[2]
            if self.ids.ticket_loc_id.text == '':
                self.ids.ticket_loc_id.text = '--'
            self.ids.ticket_chan_id.text = self.targets[0].split('.')[3]

        pass
    
    def import_description(self):
        ExamineIssuesScreen.get_selected_values(ExamineIssuesScreen)
        if len(self.targets) == 0:
            self.warning_popup("WARNING: No descriptions selected")
            return
        
        if len(set(self.descriptions)) > 1:
            self.warning_popup("WARNING: Multiple Descriptions selected, please select only one for importing")
        else:
            self.ids.description_id.text = self.descriptions[0]

    def clear_thresholds(self):
        newTicket_screen = screen_manager.get_screen('newTicketsScreen')
        newTicket_screen.newTicket_thresholds_rv._layout_manager.clear_selection()
        self.selectedThresholds = list()    #this isn't necessary because it will remove them as deselected, but jic

    def create_connection(self,db_file):
        """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print("WARNING: %s" % e)
            return None
            
    def create_table(self, conn):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        
        # Add the tickets table to the database, if it doesn't exist
        create_table_sql = """ CREATE TABLE IF NOT EXISTS tickets (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            tracker text NOT NULL,
                                            subject text NOT NULL,
                                            category text NOT NULL,
                                            network text NOT NULL,
                                            station text NOT NULL,
                                            location text NOT NULL,
                                            channel text NOT NULL,
                                            description text,
                                            start_date datetime,
                                            end_date datetime,
                                            status text NOT NULL,
                                            thresholds text NOT NULL,
                                            images text,
                                            caption text,
                                            links text,
                                            updated datetime
                                        ); """
        
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print("WARNING: %s" % e)
    
    def insert_ticket(self, conn, project):
        """
        Create a new project into the projects table
        :param conn:
        :param project:
        :return: project id
        """
        sql = ''' INSERT INTO tickets(tracker,subject,category,network,station,location,channel,description,start_date,end_date,status,thresholds,images,caption,links,updated)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
        

        cur = conn.cursor()
        cur.execute(sql, project)
        return cur.lastrowid
    
    def update_ticket(self, conn, ticket):
        """
        update priority, begin_date, and end date of a ticket
        :param conn:
        :param ticket:
        :return: project id
        """
        sql = ''' UPDATE tickets
                  SET priority = ? ,
                      begin_date = ? ,
                      end_date = ?
                  WHERE id = ?'''
        cur = conn.cursor()
        cur.execute(sql, ticket)
        
    def delete_ticket(self, conn, id):
        """
        Delete a ticket by ticket id
        :param conn:  Connection to the SQLite database
        :param id: id of the ticket
        :return:
        """
        sql = 'DELETE FROM tickets WHERE id=?'
        cur = conn.cursor()
        cur.execute(sql, (id,))
        
    def select_ticket(self, conn, sql):
        """
        Query tickets by priority
        :param conn: the Connection object
        :param priority:
        :return:
        """
        cur = conn.cursor()
        cur.execute(sql)
     
        rows = cur.fetchall()
        return rows
    
    def select_all_tickets(self, conn):
        """
        Query all rows in the tickets table
        :param conn: the Connection object
        :return:
        """
        cur = conn.cursor()
        cur.execute("SELECT * FROM tickets")
     
        rows = cur.fetchall()

    def clear_ticket_fields(self):
        self.ids.tracker_btn.text = "-"
        self.ids.subject_id.text = ""
        self.ids.description_id.text = ""
        self.ids.status_btn.text = "-"
        self.ids.category_btn.text = "-"
        self.ids.ticket_net_id.text = ""
        self.ids.ticket_sta_id.text = ""
        self.ids.ticket_chan_id.text = ""
        self.ids.ticket_loc_id.text = ""
        self.ids.image_id.text = ""
        self.ids.links_id.text = ""
        self.ids.start_id.text = ""
        self.ids.end_id.text = ""

        self.clear_thresholds()
        self.clear_images()
        
    def prep_ticket(self, *arg):
        self.tracker_str = self.ids.tracker_btn.text
        self.subject_str = self.ids.subject_id.text
        self.description_str = self.ids.description_id.text
        self.status_str = self.ids.status_btn.text
        self.category_str = self.ids.category_btn.text
        self.network_str = self.ids.ticket_net_id.text
        self.station_str = self.ids.ticket_sta_id.text
        self.channel_str = self.ids.ticket_chan_id.text
        self.location_str = self.ids.ticket_loc_id.text
        
        self.image_str = ';;;;'.join(list(masterDict['imageList'].keys()))
        self.caption_str = ';;;;'.join(list(masterDict['imageList'].values()))
        
        self.links_str = self.ids.links_id.text
        self.start_str = self.ids.start_id.text
        self.end_str = self.ids.end_id.text
        self.threshold_str = ", ".join(self.selectedThresholds)
            
        if (self.subject_str == "" or 
            self.network_str == "" or self.station_str == "" or
            self.channel_str == "" or self.location_str == "" or        
            self.status_str == "" or self.tracker_str == "-" or 
            self.status_str == "-" or self.category_str == "-"):
            self.warning_popup("WARNING: Required fields: Tracker, Subject, Status, Category, and Target Info (N, S, L, C)")
        else:
            self.do_submit()
        
    def do_submit(self):
       
        # Create connection to database -- will create the database if it doesn't exist
        conn = self.create_connection(database)

        if conn is not None:
            #create tickets table
            self.create_table(conn)
    
        else:
            self.warning_popup("WARNING: Cannot create the database connection")
            return

        # Add rows to the tickets table
        with conn:
            now = datetime.datetime.now()
            newTicket = (self.tracker_str, self.subject_str, self.category_str, self.network_str,
                         self.station_str, self.location_str, self.channel_str,
                         self.description_str, self.start_str,self.end_str,self.status_str,
                         self.threshold_str,self.image_str,self.caption_str,self.links_str, now);
            newTicket_id = self.insert_ticket(conn, newTicket)

        # See what's in the tickets table
        self.select_all_tickets(conn)
        
        # Close the connection to the database
        conn.close()   
        
        self.clear_ticket_fields()             

class UpdateTicketScreen(Screen):
    
    selectedThresholds = list()   #used to track which thresholds are selected
    selectedImages = list()
    selectedLinks = list()

    update_tracker_btn = ObjectProperty()
    update_category_btn = ObjectProperty()
    update_status_btn = ObjectProperty()
        
    update_subject = ObjectProperty()
        
    update_net = ObjectProperty()
    update_sta = ObjectProperty()
    update_loc = ObjectProperty()
    update_cha = ObjectProperty()
    update_description  = ObjectProperty()
    update_start  = ObjectProperty()
    update_end = ObjectProperty()
    update_image = ObjectProperty()
    update_linkss = ObjectProperty()
    update_last_updated = ObjectProperty()
    updateTicket_thresholds_rv = ObjectProperty()


    def warning_popup(self, txt):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        scrvw = ScrollView(size_hint_y=6)
        threshLabel = Label(text=txt, size_hint_y=None)
        threshLabel.bind(texture_size=threshLabel.setter('size'))
        scrvw.add_widget(threshLabel)
        
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_warning_popup)


        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(scrvw)
        popupContent.add_widget(Label(size_hint_y=.5))
        popupContent.add_widget(returnButton)
        
        masterDict["warning_popup"] = Popup(title="Warning", content=popupContent, size_hint=(.66, .66))
        masterDict["warning_popup"].open()

    def find_tickets(self):
        ## This function gets called whenever the ticket list is generated  after viewing 
        # a ticket from updateTicketScreen - we need to clear out some things from those 
        # udpateTickets forms.
        
        ## Clear out any potentially selected tickets
        selected_tickets_screen = screen_manager.get_screen('selectedTicketsScreen')
        selected_tickets_screen.ticket_list_rv._layout_manager.clear_selection()
        
        ## Clear out any images
        masterDict['imageList'] = dict()
        
        ## Now get a fresh ticket list - so that any updates just made are reflected
        MainScreen.get_ticket_inputs(MainScreen)
        MainScreen.grab_tickets(MainScreen)
        SelectedTicketsScreen.go_to_selectedTickets(SelectedTicketsScreen)

    def load_ticket_information(self):
        self.selectedThresholds = list()
        self.selectedImages = list()
        
        update_screen = screen_manager.get_screen('updateTicketsScreen')
        
        update_screen.update_tracker_btn.text = SelectedTicketsScreen.selected_ticket["tracker"].item()
        update_screen.update_category_btn.text = SelectedTicketsScreen.selected_ticket["category"].item()
        update_screen.update_status_btn.text = SelectedTicketsScreen.selected_ticket["status"].item()
        
        update_screen.update_subject.text = SelectedTicketsScreen.selected_ticket["subject"].item()
        
        update_screen.update_net.text = SelectedTicketsScreen.selected_ticket["network"].item()
        update_screen.update_sta.text = SelectedTicketsScreen.selected_ticket["station"].item()
        update_screen.update_loc.text = SelectedTicketsScreen.selected_ticket["location"].item()
        update_screen.update_cha.text = SelectedTicketsScreen.selected_ticket["channel"].item()
        update_screen.update_description.text = SelectedTicketsScreen.selected_ticket["description"].item()
        update_screen.update_start.text = SelectedTicketsScreen.selected_ticket["start_date"].item()
        update_screen.update_end.text = SelectedTicketsScreen.selected_ticket["end_date"].item()
        
        update_screen.update_image.text = '\n'.join([i.split('/')[-1] for i in SelectedTicketsScreen.selected_ticket["images"].item().split(';;;;')])

        update_screen.update_links.text = '\n'.join([i for i in SelectedTicketsScreen.selected_ticket["links"].item().split(';;;;')])
        masterDict['linkList'] = SelectedTicketsScreen.selected_ticket["links"].item().split(';;;;')

        update_screen.update_last_updated.text = "Last Updated: " + SelectedTicketsScreen.selected_ticket["updated"].item().split('.')[0]

        masterDict['imageList'] = dict()
        imagesList = SelectedTicketsScreen.selected_ticket["images"].item().split(';;;;')
        captionsList = SelectedTicketsScreen.selected_ticket["caption"].item().split(';;;;')
        for i in range(len(imagesList)):
            thisImCap = {imagesList[i]: captionsList[i]}
            masterDict['imageList'].update(thisImCap)

        thisTicket = masterDict["tickets"][masterDict["tickets"]['id']== int(SelectedTicketsScreen.selected_ticket["id"].item())]
        masterDict["thisId"] = thisTicket['id'].item()
        masterDict["thisTracker"] = thisTicket['tracker'].item()
        masterDict["thisSubject"] = thisTicket['subject'].item()
        masterDict["thisCategory"] = thisTicket['category'].item()
        masterDict["thisNetwork"] = thisTicket['network'].item()
        masterDict["thisStation"] = thisTicket['station'].item()
        masterDict["thisLocation"] = thisTicket['location'].item()
        masterDict["thisChannel"] = thisTicket['channel'].item()
        
        masterDict["thisDescription"] = thisTicket['description'].item()
        masterDict["thisStartDate"] = thisTicket['start_date'].item()
        masterDict["thisEndDate"] = thisTicket['end_date'].item()
        masterDict["thisStatus"] = thisTicket['status'].item()
        masterDict["thisThresholds"] = thisTicket['thresholds'].item()
        masterDict["thisImages"] = thisTicket['images'].item()
        masterDict["thisCaption"] = thisTicket['caption'].item()
        masterDict["thisLinks"] = thisTicket['links'].item()
        masterDict["thisUpdated"] = thisTicket['updated'].item()

        with open(masterDict['thresholds_file']) as f:
            local_dict = locals()
            exec(compile(f.read(), masterDict['thresholds_file'], "exec"),globals(), local_dict)
            
        masterDict['thresholdsDict'] = local_dict['thresholdsDict']
        masterDict['instrumentGroupsDict'] = local_dict['instrumentGroupsDict']        
            
        ## Threshold names
        masterDict['threshold_names'] = sorted(list(masterDict['thresholdsDict'].keys()))
        
        my_thresholds = [{'text': '   %s' % x} for x in masterDict['threshold_names']]
        update_screen.updateTicket_thresholds_rv.data = my_thresholds 

        for threshold in [x.strip() for x in SelectedTicketsScreen.selected_ticket["thresholds"].item().split(',')]:
            if not threshold == '':
                node = masterDict['threshold_names'].index(threshold)
        
                update_screen.updateTicket_thresholds_rv._layout_manager.select_node(node)
                self.selectedThresholds.append(threshold)

    def return_to_ticketList(self):
        
        # IF you want to return to the popup, then uncomment these (right now the popup does not update properly, so have it disabled)
#         masterDict["ticket_instance"].disabled = False  # reenables the button that had been clicked and disabled
#         masterDict["ticketList_popup"].open()
        self.clear_ticket_fields()
     
    def exit_confirmation(self):
        content = ExitDialog(exit=ExitDialog.do_exit, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Confirm Exit", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def dismiss_popup(self, *kwargs):
        masterDict["_popup"].dismiss()
    
    def dismiss_warning_popup(self, *kwargs):
        masterDict["warning_popup"].dismiss()
             
    def dismiss_image_popup(self, *kwargs):
        masterDict["image_popup"].dismiss()
        
    def clear_images(self):
        masterDict['imageList'] = dict()
        self.selectedImages = []

    def image_popup(self, *kwargs):
        # The scrollview and the navigation buttons at the bottom go into this boxlayout
        masterDict["image_content"] = BoxLayout(orientation='vertical')
        
        # This contains the scrollview of images and the buttons to add/remove
        upperLayout = GridLayout(cols=2)
        upperLayout.bind(minimum_height=upperLayout.setter('height'))
        
        # The individual buttons will go in here, then this boxlayout goes into the scrollview
        image_layout = BoxLayout(size_hint_y = None, orientation='vertical', spacing=5)
        image_layout.bind(minimum_height=image_layout.setter('height'))
        
        if len(masterDict["imageList"]) > 0:
            image_id=0
            for row in masterDict["imageList"]:
                b = ToggleButton(text = row, size_hint_y = None, halign = 'left',
                                background_color = (.5,.5,.5,1), group='imageButtons')
                b.bind(state=self.check_image)
                 
                image_layout.add_widget(b)
                image_id += 1
        
            # The notes (in a box layout) go into a ScrollView
            scrl = ScrollView(size_hint_y=4)
            scrl.add_widget(image_layout)

            upperLayout.add_widget(scrl)
                
        else:
            upperLayout.add_widget(Label(text='No Images'))
        
        # Add the navigation buttons for the bottom of the popup
        actionButtons = BoxLayout(orientation='vertical', size_hint_x=.25,padding=10, spacing=5)
        
        actionButtons.add_widget(Button(text="Add image", on_release=self.image_load))
        actionButtons.add_widget(Button(text="View image", on_release=self.open_image))
        actionButtons.add_widget(Button(text="Remove image", on_release=self.remove_images))
        for i in range(4):
            actionButtons.add_widget(Label())
        
        upperLayout.add_widget(actionButtons)
        
        
        labelLayout = BoxLayout(orientation='vertical', size_hint_y=0.1)
        labelsBox = BoxLayout(orientation='horizontal')
        label1 =  Label(text="Existing Caption:", size_hint=(1.0, 1.0), halign="left", valign="middle")
        label1.bind(size=label1.setter('text_size'))    
        labelsBox.add_widget(label1)
        
        label2 = Label(text="New Caption:", size_hint=(1.0, 1.0), halign="left", valign="middle")
        label2.bind(size=label2.setter('text_size'))   
        labelsBox.add_widget(label2) 

        labelLayout.add_widget(labelsBox)
        
        
        captionBox = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        
        # Label of existing caption text, and copy-the-text-to-the-input button
        captionLabelBox = BoxLayout(orientation='horizontal',padding=10, spacing=5)
        scrvw = ScrollView()
        
        self.captionLabel = Label(text="", size_hint_y=None, halign='left')
        self.captionLabel.bind(width=lambda S, W:
                   S.setter('text_size')(S, (W, None)),
                    texture_size=self.captionLabel.setter('size'))
        
        scrvw.add_widget(self.captionLabel)
        
        captionLabelBox.add_widget(scrvw)
        captionLabelBox.add_widget(Button(text="Copy\nCaption", on_release=self.copy_caption, size_hint_x=0.25 ))
        
        # Text input for adding new caption, and the Add caption button
        captionInputBox = BoxLayout(orientation='horizontal',padding=10, spacing=5)
        self.captionInput = TextInput(text="")
        self.captionInput.bind()
        captionInputBox.add_widget(self.captionInput)
        captionInputBox.add_widget(Button(text="Add caption", on_release=self.add_caption, size_hint_x=0.25))
        
        captionBox.add_widget(captionLabelBox)
        captionBox.add_widget(captionInputBox)
        
        navButtons=BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=(0,10,0,0), spacing=5)
        navButtons.add_widget(Button(text="Return", on_release=self.dismiss_image_popup))

        masterDict["image_content"].add_widget(upperLayout)
        masterDict["image_content"].add_widget(labelLayout)
        masterDict["image_content"].add_widget(captionBox)
        masterDict["image_content"].add_widget(navButtons)
        
        masterDict["image_popup"] = Popup(title="Select Images", content=masterDict["image_content"],
                            size_hint=(0.9, 0.9))
        masterDict["image_popup"].open()


    def check_image(self, image, state):
        if state == "down":
            if image.text not in self.selectedImages:
                self.selectedImages.append(image.text)
                self.captionLabel.text = masterDict['imageList'][self.selectedImages[0]]
             
        else:
            self.selectedImages = [v for v in self.selectedImages if v != image.text]
            self.captionLabel.text = ""

    def open_image(self, *kwargs):
        for file in self.selectedImages:
            try:
                subprocess.run(['open', file], check=True)
            except Exception as e:
                print("WARNING: Unable to open %s: %s" %(file, e))
     
    def remove_images(self, *kwargs):
        for file in self.selectedImages:
            try:
                del masterDict['imageList'][file]
            except KeyError as e:
                print("WARNING: File not found in list - %s" % e)
            
            self.selectedImages = [v for v in self.selectedImages if v != file]
            
        self.dismiss_image_popup()
        self.image_popup()
        self.ids.update_image_id.text = "\n".join([i.split('/')[-1] for i in masterDict["imageList"]])
    
    def copy_caption(self, *kwargs):
        self.captionInput.text = self.captionLabel.text
        
    def add_caption(self, button, *kwargs):
        try:
            masterDict['imageList'][self.selectedImages[0]] = self.captionInput.text
            self.captionLabel.text = masterDict['imageList'][self.selectedImages[0]]
            print("INFO: Caption added")
        except Exception as e:
            if str(e) == "list index out of range":
                self.warning_popup("WARNING: could not add caption to file - no image selected")
            else:
                self.warning_popup("WARNING: could not add caption to file - %s" % e)
            print("WARNING: could not add caption to file -- %s" % e)
        

    def image_load(self, *kwargs):
        content = LoadDialog(load=self.load_image, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Load image", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
    
    def load_image(self,path, filename):
        self.dismiss_image_popup()
        
        if not filename[0] in masterDict["imageList"]:
            masterDict["imageList"].update({filename[0]:""})
        
        self.ids.update_image_id.text = "\n".join([i.split('/')[-1] for i in masterDict["imageList"]])
        self.dismiss_popup()
        self.image_popup()

    def link_popup(self, *kwargs):
        # The scrollview and the navigation buttons at the bottom go into this boxlayout
        masterDict["link_content"] = BoxLayout(orientation='vertical')
        
        # This contains the scrollview of images and the buttons to add/remove
        upperLayout = GridLayout(cols=2)
        upperLayout.bind(minimum_height=upperLayout.setter('height'))
        
        # The individual buttons will go in here, then this boxlayout goes into the scrollview
        image_layout = BoxLayout(size_hint_y = None, orientation='vertical', spacing=5)
        image_layout.bind(minimum_height=image_layout.setter('height'))
        
        if len(masterDict["linkList"]) > 0:
            link_id=0
            for row in masterDict["linkList"]:
#                 b = ToggleButton(text = row, size_hint_y = None, halign = 'left', id=str(link_id),
#                                 background_color = (.5,.5,.5,1), group='imageButtons')
                b = ToggleButton(text = row, size_hint_y = None, halign = 'left',
                                background_color = (.5,.5,.5,1), group='imageButtons')
                b.bind(state=self.check_link)
                 
                image_layout.add_widget(b)
                link_id += 1
#         
            # The notes (in a box layout) go into a ScrollView
            scrl = ScrollView(size_hint_y=4)
            scrl.add_widget(image_layout)
            

            upperLayout.add_widget(scrl)
                
        else:
            upperLayout.add_widget(Label(text='No Links'))
        
        # Add the navigation buttons for the bottom of the popup
        actionButtons = BoxLayout(orientation='vertical', size_hint_x=.25,padding=10, spacing=5)
    
        actionButtons.add_widget(Button(text="Remove link", on_release=self.remove_link))
        for i in range(4):
            actionButtons.add_widget(Label())
        actionButtons.add_widget(Button(text="Add link", on_release=self.add_link))

        
        upperLayout.add_widget(actionButtons)
        
        captionBox = BoxLayout(orientation='horizontal', size_hint_y=0.25)
#         self.linkInput = TextInput(text="", id='linkID')
        self.linkInput = TextInput(text="")
        self.linkInput.bind()
        captionBox.add_widget(self.linkInput)
        
        navButtons=BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=(0,10,0,0), spacing=5)
        navButtons.add_widget(Button(text="Return", on_release=self.dismiss_link_popup))

        masterDict["link_content"].add_widget(upperLayout)
        masterDict["link_content"].add_widget(captionBox)
        masterDict["link_content"].add_widget(navButtons)
        
        masterDict["link_popup"] = Popup(title="Add Links", content=masterDict["link_content"],
                            size_hint=(0.9, 0.9))
        masterDict["link_popup"].open()    

    def check_link(self, link, state):
        if state == "down":
            if link.text not in self.selectedLinks:
                self.selectedLinks.append(link.text)
        else:
            self.selectedLinks = [v for v in self.selectedLinks if v != linkn.text]
        
    def remove_link(self, *kwargs):
        for file in self.selectedLinks:
            try:
                masterDict['linkList'] = [v for v in masterDict['linkList'] if v != file]
            except KeyError as e:
                print("WARNING: File not found in list - %s" % e)
            
            self.selectedLinks = [v for v in self.selectedLinks if v != file]
            
        self.dismiss_link_popup()
        self.link_popup()
        self.ids.update_links_id.text = "\n".join([i for i in masterDict["linkList"]])

    def add_link(self, button, *kwargs):
        try:
            masterDict['linkList'].append(self.linkInput.text)
            self.ids.update_links_id.text = "\n".join([i for i in masterDict["linkList"]])
            print("INFO: Link added")
        except Exception as e:
            print("WARNING: could not add link to list -- %s" % e)
            
        self.dismiss_link_popup()
        self.link_popup() 
        
    def dismiss_link_popup(self, *kwargs):
        masterDict["link_popup"].dismiss()

    def clear_thresholds(self):
        updateTicket_screen = screen_manager.get_screen('updateTicketsScreen')
        updateTicket_screen.updateTicket_thresholds_rv._layout_manager.clear_selection()

    def clear_ticket_fields(self):
        self.ids.update_tracker_btn.text = '-'
        self.ids.update_category_btn.text = '-'
        self.ids.update_status_btn.text = '-'
         
        self.ids.update_subject_id.text = ''
        self.ids.update_net_id.text = ''
        self.ids.update_sta_id.text = ''
        self.ids.update_loc_id.text = ''
        self.ids.update_chan_id.text = ''
        self.ids.update_description_id.text = ''
        self.ids.update_start_id.text = ''
        self.ids.update_end_id.text = ''
        self.ids.update_image_id.text = ''

        self.ids.update_links_id.text = ''
        self.ids.update_last_updated_id.text = ''
        self.clear_thresholds()
        self.clear_images()

    def create_connection(self,db_file):
        """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print("WARNING: %s" % e)
     
        return None

    def update_ticket(self, conn, ticket):
        """
        update priority, begin_date, and end date of a ticket
        :param conn:
        :param ticket:
        :return: project id
        """
        sql = ''' UPDATE tickets
                  SET tracker = ?,
                      subject = ?,
                      category = ?,
                      network = ?,
                      station = ?,
                      location = ?,
                      channel = ?,
                      description = ?,
                      start_date = ?,
                      end_date = ?,
                      status = ?,
                      thresholds = ?,
                      images = ?,
                      caption = ?,
                      links = ?,
                      updated = ?
                  WHERE id = ?'''
        
        cur = conn.cursor()
        cur.execute(sql, ticket)
       
    def prep_ticket(self, *arg):
        update_screen = screen_manager.get_screen('updateTicketsScreen')
        
        self.tracker_str = update_screen.update_tracker_btn.text
        self.subject_str = update_screen.update_subject.text
        self.description_str = update_screen.update_description.text
        self.status_str = update_screen.update_status_btn.text
        self.category_str = update_screen.update_category_btn.text
        self.network_str = update_screen.update_net.text
        self.station_str = update_screen.update_sta.text
        self.location_str = update_screen.update_loc.text
        self.channel_str = update_screen.update_cha.text
        
        self.image_str = ';;;;'.join(list(masterDict['imageList'].keys()))
        self.caption_str = ';;;;'.join(list(masterDict['imageList'].values()))
        
        self.links_str = ';;;;'.join(list(masterDict['linkList']))
        self.start_str = update_screen.update_start.text
        self.end_str = update_screen.update_end.text
        uniqueThresholds = list(set(self.selectedThresholds))
        self.threshold_str = ", ".join(uniqueThresholds)

        if (self.subject_str == "" or
            self.network_str == "" or self.station_str == "" or 
            self.location_str == "" or self.channel_str == "" or 
            self.status_str =="" or self.tracker_str == "-" or 
            self.status_str == "-" or self.category_str == "-"):
            self.warning_popup("Required fields: Tracker, Subject, Status, Category, and Target Fields (N,S,L,C)")
            return False
        else:
            return True
    
    def delete_confirmation(self):
        content = DeleteDialog(cancel=self.dismiss_popup, deleteit=self.delete_ticket)
        masterDict["_popup"] = Popup(title="Confirm Delete", content=content,
                        size_hint=(0.9, 0.9))
        masterDict["_popup"].open()
                    
    def delete_ticket(self):
        """
        Delete a ticket by ticket id
        :param conn:  Connection to the SQLite database
        :param id: id of the ticket
        :return:
        """
        
        self.dismiss_popup()
        id = masterDict["thisId"]
        
        print("INFO: Deleting this ticket: " + str(id))
        conn = self.create_connection(database)
        
        with conn:
        
            sql = 'DELETE FROM tickets WHERE id=?'
            cur = conn.cursor()
            cur.execute(sql, (id,))
        conn.close()
    
        self.clear_ticket_fields()
    
    def do_delete(self):
        self.delete_confirmation()
      
    def do_update(self):
        #Just for testing, until I set this up better
        id = masterDict["thisId"]
        
        # Get all fields
        iDoUpdate = self.prep_ticket()
     
        # Add rows to the tickets table
        if iDoUpdate:
            # Create connection to database
            conn = self.create_connection(database)
            with conn:
                now = datetime.datetime.now()
                updateTicket = (self.tracker_str, self.subject_str, self.category_str, self.network_str,
                                self.station_str, self.location_str, self.channel_str,
                                self.description_str, self.start_str,self.end_str,self.status_str,
                                self.threshold_str,self.image_str,self.caption_str,self.links_str, now,id)
                updateTicket_id = self.update_ticket(conn, updateTicket)

            conn.close()   
            self.ids.update_last_updated_id.text = "Last Updated: " + now.strftime("%Y-%m-%d %H:%M:%S")
            self.confirmation_popup()
            
    def confirmation_popup(self):
        popupContent = BoxLayout(orientation='vertical', spacing=10)
        popupContent.bind(minimum_height=popupContent.setter('height'))
        
        warningLabel = Label(text="Ticket successfully updated")
    
        returnButton = Button(text="Return")
        returnButton.bind(on_release=self.dismiss_popup)
        
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(warningLabel)
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(Label())
        popupContent.add_widget(returnButton)
        
        masterDict["_popup"] = Popup(title="Success", content=popupContent, size_hint=(.66, .66))
        masterDict["_popup"].open()   
        
class SelectedTicketsScreen(Screen):
    ticket_list_rv = ObjectProperty()
    selected_ticket = ''
    header_label = ObjectProperty()
    ticket_order = ObjectProperty()
    theseTickets = pd.DataFrame()

    def exit_confirmation(self,*kwargs):
        content = ExitDialog(exit=ExitDialog.do_exit, cancel=self.dismiss_popup)
        masterDict["_popup"] = Popup(title="Confirm Exit", content=content,
                            size_hint=(0.9, 0.9))
        masterDict["_popup"].open()

    def dismiss_popup(self, *kwargs):
        masterDict["_popup"].dismiss()

    def go_to_selectedTickets(self):
        tickets_screen = screen_manager.get_screen('selectedTicketsScreen')
        
        spacing_dict = {0:6, 1:22, 2: 12, 3: 12, 4: 30, 5: 18, 6: 14, 7: 10}
        try:
            try:
                masterDict['ticket_order']
                
            except:
                masterDict['ticket_order'] = 'id'
            else:
                masterDict['ticket_order'] = tickets_screen.ticket_order.text.lower().replace(" ", "_")
            
            self.theseTickets = masterDict['tickets']
            self.theseTickets['target'] = self.theseTickets['network'] + '.' + self.theseTickets['station'] + '.' + self.theseTickets['location'] + '.' + self.theseTickets['channel']
            

            self.theseTickets = self.theseTickets.sort_values(by=[masterDict['ticket_order']]).reset_index(drop=True)            
            
            ticketList = list()
 
            for id, row in self.theseTickets.iterrows():
                row_sub = [str(row['id']), row['target'], row['start_date'],row['end_date'], row['subject'], row['status'], row['tracker'], row['updated']]
                row_sub = [row_sub[y].ljust(spacing_dict[y])[0:spacing_dict[y]]  for y in range(len(row_sub))]
                label = '  '.join(row_sub)
                ticketList.append({'text': label})
     
            tickets_screen.ticket_list_rv.data = ticketList 
        except Exception as e:
            print("Warning: could not retrieve tickets - %s" % e)
            tickets_screen.ticket_list_rv.data = ''
            
        header_list = ['id', 'Target','Start Date', 'End Date','Subject','Status','Tracker','Updated']
        header_list = [header_list[y].ljust(spacing_dict[y])[0:spacing_dict[y]] for y in range(len(header_list))]
        header_text = '  '.join(header_list)
        tickets_screen.header_label.text = header_text

    def reload_sorted(self):   
        MainScreen.find_tickets(MainScreen)


# ####################
### RECYCLEVIEW CLASSES ###



class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''


class Issues_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Issues_RV, self).__init__(**kwargs)
        self.data = []
    def set_issue_frame(self):
        ExamineIssuesScreen.load_issueFile(ExamineIssuesScreen)

class issues_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(issues_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(issues_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                ExamineIssuesScreen.selectionIndices.append(index)
            except:
                pass
            
        else:
            try:
                # Can't just do a simple .remove(index) because it'll build up multipl of 
                # the same index, and remove only removes one of them - leads to bad markings
                ExamineIssuesScreen.selectionIndices = [v for v in ExamineIssuesScreen.selectionIndices if v != index]

            except:
                pass


class Preference_Instruments_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Preference_Instruments_RV, self).__init__(**kwargs)
        self.data = []

class preference_instruments_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(preference_instruments_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(preference_instruments_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                if index not in PreferencesScreen.instrument_selectionIndices:
                    PreferencesScreen.instrument_selectionIndices.append(index)
            except:
                pass
            
        else:
            try:
                # Can't just do a simple .remove(index) because it'll build up multipl of 
                # the same index, and remove only removes one of them - leads to bad markings
                PreferencesScreen.instrument_selectionIndices = [v for v in PreferencesScreen.instrument_selectionIndices if v != index]

            except:
                pass


class Preference_ThresholdGroups_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Preference_ThresholdGroups_RV, self).__init__(**kwargs)
        self.data = []

class preference_thresholdGroups_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(preference_thresholdGroups_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(preference_thresholdGroups_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                if index not in PreferencesScreen.thresholdGroups_selectionIndices:
                    PreferencesScreen.thresholdGroups_selectionIndices.append(index)
            except:
                pass
            
        else:
            try:
                # Can't just do a simple .remove(index) because it'll build up multipl of 
                # the same index, and remove only removes one of them - leads to bad markings
                PreferencesScreen.thresholdGroups_selectionIndices = [v for v in PreferencesScreen.thresholdGroups_selectionIndices if v != index]

            except:
                pass


class ThresholdNames_RV(RecycleView):
    # THRESHOLDGROUPS SCREEN
    def __init__(self, **kwargs):
        super(ThresholdNames_RV, self).__init__(**kwargs)
        self.data = []

class thresholdNames_SelectableLabel(RecycleDataViewBehavior, Label):
    # THRESHOLDGROUPS SCREEN
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(thresholdNames_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(thresholdNames_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                if index not in ThresholdGroupsScreen.thresholdNames_selectionIndices:
                    ThresholdGroupsScreen.thresholdNames_selectionIndices.append(index)
            except:
                pass
        else:
            try:
                # Can't just do a simple .remove(index) because it'll build up multipl of 
                # the same index, and remove only removes one of them - leads to bad markings
                ThresholdGroupsScreen.thresholdNames_selectionIndices = [v for v in ThresholdGroupsScreen.thresholdNames_selectionIndices if v != index]
            except:
                pass


class ThresholdGroups_RV(RecycleView):
    # THRESHOLDGROUPS SCREEN
    def __init__(self, **kwargs):
        super(ThresholdGroups_RV, self).__init__(**kwargs)
        self.data = []

class thresholdGroups_SelectableLabel(RecycleDataViewBehavior, Label):
    # THRESHOLDGROUPS SCREEN

    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(thresholdGroups_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(thresholdGroups_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                if index not in ThresholdGroupsScreen.thresholdGroups_selectionIndices:
                    ThresholdGroupsScreen.thresholdGroups_selectionIndices.append(index)
            except:
                pass
        else:
            try:
                # Can't just do a simple .remove(index) because it'll build up multipl of 
                # the same index, and remove only removes one of them - leads to bad markings
                ThresholdGroupsScreen.thresholdGroups_selectionIndices = [v for v in ThresholdGroupsScreen.thresholdGroups_selectionIndices if v != index]

            except:
                pass


class ThresholdGroupAndNames_RV(RecycleView):
    # THRESHOLDGROUPS SCREEN
    def __init__(self, **kwargs):
        super(ThresholdGroupAndNames_RV, self).__init__(**kwargs)
        self.data = []

class thresholdGroupAndNames_SelectableLabel(RecycleDataViewBehavior, Label):
    # THRESHOLDGROUPS SCREEN

    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(thresholdGroupAndNames_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(thresholdGroupAndNames_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                if index not in  ThresholdGroupsScreen.thresholdGroupAndNames_selectionIndices:
                    ThresholdGroupsScreen.thresholdGroupAndNames_selectionIndices.append(index)
            except:
                pass
        else:
            try:
                # Can't just do a simple .remove(index) because it'll build up multipl of 
                # the same index, and remove only removes one of them - leads to bad markings
                ThresholdGroupsScreen.thresholdGroupAndNames_selectionIndices = [v for v in ThresholdGroupsScreen.thresholdGroupAndNames_selectionIndices if v != index]
            except:
                pass


class Threshold_names_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Threshold_names_RV, self).__init__(**kwargs)
        self.data = []

class threshold_names_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(threshold_names_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(threshold_names_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                ThresholdsScreen.selected_threshold = [masterDict['threshold_names'][index]]
            except Exception as e:
                print("WARNING: %s" % e) 
        else:
            try:
                ThresholdsScreen.selected_threshold = [v for v in ThresholdsScreen.selected_threshold if v != masterDict['threshold_names'][index]]
            except Exception as e:
                ThresholdsScreen.selected_threshold = []
        ThresholdsScreen.display_definition(ThresholdsScreen)
        

class Instrument_groups_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Instrument_groups_RV, self).__init__(**kwargs)
        self.data = []

class instrument_groups_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(instrument_groups_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(instrument_groups_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                ThresholdsScreen.selected_group = [masterDict['instrument_groups'][index]]
            except Exception as e:
                print("WARNING: %s" % e)
        else:
            try:
                ThresholdsScreen.selected_group = [v for v in ThresholdsScreen.selected_group if v != masterDict['instrument_groups'][index]]
            except Exception as e:
                ThresholdsScreen.selected_group = []
        ThresholdsScreen.display_definition(ThresholdsScreen)


class Threshold_definition_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Threshold_definition_RV, self).__init__(**kwargs)
        self.data = []

class threshold_definition_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(threshold_definition_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(threshold_definition_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                ThresholdsScreen.selected_definition = masterDict['thresholdsDict'][ThresholdsScreen.selected_threshold[0]][ThresholdsScreen.selected_group[0]][index]
            except Exception as e:
                print(e)
        else:
            ThresholdsScreen.selected_definition = ''
        ThresholdsScreen.display_definition(ThresholdsScreen)


class Metrics_List_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Metrics_List_RV, self).__init__(**kwargs)
        self.data = []

class metrics_list_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(metrics_list_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(metrics_list_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        threshold_screen = screen_manager.get_screen('thresholdsScreen')
        if is_selected:
            try:
                ThresholdsScreen.selected_metric = [masterDict['metrics'][index]]
                threshold_screen.metric_text.text = masterDict['metrics'][index]
            except Exception as e:
                print(e)
        else:
            ThresholdsScreen.selected_metric = [v for v in ThresholdsScreen.selected_metric if v != masterDict['metrics'][index]]
            try:
                threshold_screen.metric_text.text = ThresholdsScreen.selected_metric[0]
            except:
                threshold_screen.metric_text.text = ""


class Metadata_List_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Metadata_List_RV, self).__init__(**kwargs)
        self.data = []

class metadata_list_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(metadata_list_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(metadata_list_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        threshold_screen = screen_manager.get_screen('thresholdsScreen')
        if is_selected:
            try:
                ThresholdsScreen.selected_metadata = [masterDict['metadata'][index]]
                threshold_screen.metric_text.text = masterDict['metadata'][index]
#                 print("The selected metric is: %s " % ThresholdsScreen.selected_metric)
            except Exception as e:
                print(e)
        else:
            ThresholdsScreen.selected_metadata = [v for v in ThresholdsScreen.selected_metadata if v != masterDict['metadata'][index]]
            try:
                threshold_screen.metric_text.text = ThresholdsScreen.selected_metadata[0]
            except:
                threshold_screen.metric_text.text = ""


class Selected_tickets_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Selected_tickets_RV, self).__init__(**kwargs)
        self.data = []
        
class selected_tickets_SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(selected_tickets_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(selected_tickets_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                ### THIS DOESN"T FIX THE PROBLEM ###
                SelectedTicketsScreen.selected_ticket = SelectedTicketsScreen.theseTickets.iloc[[index]]
                screen_manager.current = 'updateTicketsScreen'
                UpdateTicketScreen.load_ticket_information(UpdateTicketScreen)

            except Exception as e:
                print("WARNING: %s" % e)


class Create_ticket_thresholds_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Create_ticket_thresholds_RV, self).__init__(**kwargs)
        self.data = []

class create_ticket_threshold_SelectableLabel(RecycleDataViewBehavior, Label):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(create_ticket_threshold_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(create_ticket_threshold_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                NewTicketScreen.selectedThresholds.append(masterDict['threshold_names'][index])
            except:
                pass
            
        else:
            try:
                # Can't just do a simple .remove(index) because it'll build up multipl of 
                # the same index, and remove only removes one of them - leads to bad markings

                NewTicketScreen.selectedThresholds = [v for v in NewTicketScreen.selectedThresholds if v != masterDict['threshold_names'][index]]
            except:
                pass


class Update_ticket_thresholds_RV(RecycleView):
    def __init__(self, **kwargs):
        super(Update_ticket_thresholds_RV, self).__init__(**kwargs)
        self.data = []

class update_ticket_threshold_SelectableLabel(RecycleDataViewBehavior, Label):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(update_ticket_threshold_SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(update_ticket_threshold_SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            try:
                UpdateTicketScreen.selectedThresholds.append(masterDict['threshold_names'][index])
            except:
                pass
            
        else:
            try:
                # Can't just do a simple .remove(index) because it'll build up multipl of 
                # the same index, and remove only removes one of them - leads to bad markings

                UpdateTicketScreen.selectedThresholds = [v for v in UpdateTicketScreen.selectedThresholds if v != masterDict['threshold_names'][index]]
            except:
                pass





# Set up some "Global" variables

masterDict={}
masterDict["thisId"] = ""
masterDict["thisTracker"] = ""
masterDict["thisSubject"] = ""
masterDict["thisCategory"] = ""
masterDict["thisTarget"] = ""
masterDict["thisDescription"] = ""
masterDict["thisStartDate"] = ""
masterDict["thisEndDate"] = ""
masterDict["thisStatus"] = ""
masterDict["thisThresholds"] = ""
masterDict["thisImages"] = ""
masterDict["thisCaption"] = ""
masterDict["thisLinks"] = ""
masterDict["thisUpdated"] = ""
masterDict["imageDir"] = 'quarg_plots/'
masterDict["imageList"] = dict()
masterDict['linkList'] = list()
masterDict['thresholds_file'] = "./thresholds.txt"
masterDict['metrics_file'] = "./MUSTANG_metrics.txt"
masterDict['metadata_file'] = "./IRIS_metadata.txt"

databaseDir = "./db/"
databaseName = "quargTickets.db"
database = databaseDir + databaseName


# Check that the database and table exists:
if os.path.exists(database):
    # the file exists, check that it has the table in it 
    checkTableSQL = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='tickets';"
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(checkTableSQL)
    if c.fetchone()[0] == 1:
        pass
    else:
        # We should create the table
        NewTicketScreen.create_table(NewTicketScreen,conn)
    conn.close
elif os.path.exists(databaseDir):
    # the directory exists, but we need to create the file and table
    conn = sqlite3.connect(database)
    NewTicketScreen.create_table(NewTicketScreen,conn)
    conn.close
else:
    # We need to make the direcotory, database file, and tickets table
    os.mkdir(databaseDir)
    conn = sqlite3.connect(database)
    NewTicketScreen.create_table(NewTicketScreen,conn)
    conn.close


 
#####################
screen_manager = ScreenManager(transition=NoTransition())

#### RUN THE APP ####
class QuARGApp(App):
    
    def build(self):
        # Set the background color for the window
        Window.clearcolor = (1, 1, 1, 1)
        Window.size = (1377, 700)
        
        self.title = 'IRIS Quality Assurance Report Generator'
        screen_manager.add_widget(MainScreen(name="mainScreen"))
        screen_manager.add_widget(PreferencesScreen(name='preferencesScreen'))
        screen_manager.add_widget(ThresholdGroupsScreen(name='thresholdGroupsScreen'))
        screen_manager.add_widget(ThresholdsScreen(name="thresholdsScreen"))
        screen_manager.add_widget(ExamineIssuesScreen(name="examineIssuesScreen"))
        screen_manager.add_widget(NewTicketScreen(name="newTicketsScreen"))
        screen_manager.add_widget(UpdateTicketScreen(name="updateTicketsScreen"))
        screen_manager.add_widget(SelectedTicketsScreen(name="selectedTicketsScreen"))
        return screen_manager
 
if __name__ == '__main__':
    QuARGApp().run()
    
