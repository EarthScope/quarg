#!/usr/bin/env python

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
network = 'IU'
station = '*'
location = '*'
channels = 'BH?,HH?'

instruments = ['short period', 'broadband', 'strongmotion']
chanTypes = {'H': ('1', '2', 'E', 'N'), 'V': ('3', 'Z')}


## Report frequency: 
reportFrequency = 'Weekly'
[startday, endday, subdir] = reportUtils.calculate_dates(reportFrequency)    # Determines default start and end dates, directory for report

# Metric source: either 'EarthScope' or the path to the local sqlite database file that ISPAQ generated
metricSource = 'EarthScope'
metadataSource = 'EarthScope'

## Thresholds:
thresholdGroups = ['Timing', 'State of Health', 'Completeness', 'Amplitudes', 'Metadata']

groupsDict = {'Amplitudes': ['avgSpikes', 'badResp', 'badResp2', 'dcOffsets', 'dead', 'flat', 'gainRatio', 'gainRatioB', 'hiAmp', 'lowAmp', 'lowRms', 'medianUnique', 'nSpikes', 'noise1', 'noise2', 'nonCoher', 'pegged', 'polarity', 'rmsRatio', 'rmsRatio_horiz', 'xTalk'], 'Completeness': ['avgGaps', 'gapsRatioGt12', 'noData'], 'Metadata': ['horDip', 'lowScale', 'nonMSUnits', 'zDip', 'zeroZ'], 'State of Health': ['ampSat', 'clip', 'filtChg', 'glitch', 'padding', 'spikes', 'tSync'], 'Timing': ['noTime', 'poorTQual', 'suspectTime']}


## Directories and Filenames:
mainDir = './'
directory = mainDir + network + '/' + subdir + '/'        # creates a new directory for each report
filename = 'issues.txt'        # file to write to in FIND ISSUES tab
if not subdir == "": 
    outfile = directory + filename
else:
    # This alerts the user that something didn't fill in properly
    outfile = ''
csvfilename = 'tickets.csv'
csvfile = directory + csvfilename    # file to write tickets to, used to generate report in GENERATE REPORT tab

## Report Header Information:
author = "Author"
project = "Project"
email = "email@email"



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

            
            
            