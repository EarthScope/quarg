#!/usr/bin/env python
# -*- coding: utf-8 -*-
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


import pandas as pd
import numpy as np
import datetime
import argparse
import sys
import os
import xml.etree.ElementTree as et
# from urllib.request import Request, urlopen
import requests
from io import StringIO
import re

# ============================#
# PREFERENCE FILE - DETERMINE START AND END DATES
def calculate_dates(reportFrequency):
    today = datetime.date.today()

    if reportFrequency.lower() == 'daily':
        # For daily reports, we do two days ago to allow for metrics to have calculated
        endday = datetime.date.today() - datetime.timedelta(days=1)    
        startday = endday - datetime.timedelta(days=1)
        subdir = '%s' % startday.strftime('%Y%m%d')  
        
                    
    elif reportFrequency.lower() == 'weekly':
        weekday = today.weekday()
        start_delta = datetime.timedelta(days=weekday, weeks=1)
        startday = today - start_delta
        endday = startday + datetime.timedelta(days=7)
        subdir = '%s' % startday.strftime('%Y%m%d')
                    
    elif reportFrequency.lower() == 'monthly':
        endday= today.replace(day=1)
        endLastMonth = endday - datetime.timedelta(days=1)
        startday = endLastMonth.replace(day=1)
        subdir = '%s' % startday.strftime('%Y%m')
                    
    elif reportFrequency.lower() == 'quarterly':
        thisMonth = today.month
        year = datetime.date.today().year
        month_delta = (thisMonth-1) % 3
        endMonth = thisMonth - month_delta
        startMonth = endMonth - 3
        if endMonth < 1:
            endMonth += 12
            year = year - 1
        endday = datetime.date(year=year, month=endMonth, day=1)
                        
        if startMonth < 1:
            startMonth += 12
            year = year - 1
        startday = datetime.date(year=year, month=startMonth, day=1)
        subdir = '%s' % startday.strftime('%Y%m')

    else:
#         print('Report frequency not recognized')
        return '', '', ''
    
    #month = '%s' % startday.strftime('%Y%m')                
    startday = startday.strftime("%Y-%m-%d")
    endday = endday.strftime("%Y-%m-%d")

    return startday, endday, subdir

# ============================#
# UTILITY FOR PARSING COMMAND LINE ARGUMENTS

def getArgs():
    parser = argparse.ArgumentParser(description="Parse inputs to Find QA issues", formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog,max_help_position=35))
    parser._optionals.title = "single arguments"
    inputs = parser.add_argument_group('arguments for running metrics')
    inputs.add_argument('-P', '--preference_file', required=False, help='path to preference file, default=./preference_files/default.txt')
    inputs.add_argument('-T', '--thresholds', required=False,
                        help='thresholds to be run, as defined in preference file or a list of threshold names, defaults to all')
    inputs.add_argument('-N', '--network', required=False,
                        help='Required unless specified in preference file')
    inputs.add_argument('-S', '--stations', required=False,
                        help='Required unless specified in preference file')
    inputs.add_argument('-C', '--channels', required=False,
                        help='Required unless specified in preference file')
    inputs.add_argument('-L', '--locations', required=False,
                        help='Required unless specified in preference file')
    inputs.add_argument('--start', required=True, 
                      help='start date in YYYY-MM-DD format, time defaults to 00:00:00, required')
    inputs.add_argument('--end', required=True, 
                      help='end date in YYYY-MM-DD format, timedefaults to 00:00:00, required')
    inputs.add_argument('--outfile', required=False,
                      help='Location file will be written, directory included. Required if preference file not included')
    inputs.add_argument('--ticketsfile', required=False,
                      help='File that contains ticketing information, directory included. Required if preference file not included')
    inputs.add_argument('--htmldir', required=False,
                        help='Location to write the final HTML QA report to.')
    inputs.add_argument('--html_file_path', required=False,
                        help='Full path and filename of final HTML QA report.')
    inputs.add_argument('--metricsource', required=False,
                        help='Where metrics should be found - "IRIS" or the path the to ISPAQ-generated sqlite database file.')
    inputs.add_argument('--metadatasource', required=False,
                        help='Location to find metadata - "IRIS" or the path to the XML file')
    inputs.add_argument('--metrics_file', required=False,
                        help='Full path to file containing list of MUSTANG metrics')
    inputs.add_argument('--metadata_file', required=False,
                        help='Full path to file containing list of IRIS station service metadata fields')
    inputs.add_argument('--thresholds_file', required=False,
                        help='Full path to the file containing threshold definitions and groupings')

    args = parser.parse_args(sys.argv[1:])
#     try: 
#         args.month = args.start.split('-')[0] + args.start.split('-')[1]
#     except:
#         args.month = ''

    return args      

# ============================#
# UTILITIES FOR GENERATING DATAFRAMES

def getMetrics(nets, stas, locs, chans, start, end, metric, metricSource, failedMetrics):
    # This will create a temporary dataframe with the columns:
    # $metric target start end
    # Where $metric is the current metric, and within it are the
    # values for that metric
    
   
    if metricSource.upper() == 'IRIS':
        
        URL = "http://service.iris.edu/mustang/measurements/1/query?metric=" + metric + \
        "&net=" + nets +"&sta=" + stas + "&loc=" + locs + "&cha=" + chans + \
        "&format=text&timewindow="+start +"," + end +"&nodata=404"
        print(URL)
        
        try:
            response = requests.get(URL) 
            DF = pd.read_csv(StringIO(response.text), header=1)

            if not 'transfer_function' in metric:
                DF.rename(columns = {'value': metric}, inplace=True)
                DF[metric] = DF[metric].map(float)

            DF.drop('lddate', axis=1, inplace=True)
        except Exception as e:
            print("Unable to get metrics for %s - %s" % (metric, e))
            if not metric in failedMetrics:
                failedMetrics.append(metric)
            DF = pd.DataFrame()
    
    
    else:
        # then it must be a local database
        import sqlite3
                # ISPAQ does not calculate dc_offset:
        if metric == "dc_offset":
            print("ISPAQ does not run dc_offset, skipping.")
            DF = pd.DataFrame()
            return DF, failedMetrics
        
        # ISPAQ is based on targets, not individual net/sta/loc/chan so need to put them all together
        targetList = []
        for network in nets.split(','):
            network = network.replace("?", "_").replace("*","%")
            for station in stas.split(','):
                station  = station.replace("?", "_").replace("*","%")
                for location in locs.split(','):
                    location = location.replace("?", "_").replace("*","%")
                    for channel in chans.split(','):
                       channel = channel.replace("?", "_").replace("*","%")
                       
                       # Include a wildcard for the quality code at this point
#                        thisTarget = "%s\.%s\..*%s.*\..*%s.*\..*" % (net2, sta2, loc2, cha2)
                       targetList.append(network + '.' + station + '.%' + location + '%.%' + channel + '%.%')
#                        targetList.append("%s.%s.%s.%s._" % (network, station, location, channel)) 
        
        targets = "' or target like '".join(targetList)
     
        SQLcommand = "SELECT * FROM " + metric + \
                     " WHERE start >= '" + start + "' " \
                     "and start < '" + end + "' " \
                     "and (target like '" + targets + "');"
                     

        try:
            conn = sqlite3.connect(metricSource)
            
            DF = pd.read_sql_query(SQLcommand, conn)
            if (not metric == 'transfer_function') and (not metric == 'orientation_check'):
                DF.rename(columns = {'value': metric}, inplace=True)
                DF[metric] = DF[metric].map(float)
            DF.drop('lddate', axis=1, inplace=True)
        except:

            print("Error connecting to %s %s" % (metricSource, metric))
            if not metric in failedMetrics:
                failedMetrics.append(metric)
            DF = pd.DataFrame()

        finally:
            if conn:
                conn.close()
        

    return DF, failedMetrics
    
   
    
def mergeMetricDF(nets, stas, locs, chans, start, end, metrics, metricSource):
    # This will create a dataframe that joins on any matching
    # Target, Start, End pairs.  If one or the other dataframes has a 
    # target, start, end that isn't in the other, then tack it on
    # and fill the missing slots with NaN
    
    DF = pd.DataFrame()
    emptyMets = []
    failedMetrics = list()
    skipTransferFunction = False; skipOrientationCheck = False    # since multiple 'metrics' can have these metrics, only do it once

    for metric in metrics:
        metric_part = metric.split("::")[0]
        
        if metric_part == 'transfer_function':
            if skipTransferFunction:
                continue
            else:
                skipTransferFunction = True
                
        if metric_part == 'orientation_check':
            if skipOrientationCheck:
                continue
            else:
                skipOrientationCheck = True

        
        tempDF, failedMetrics = getMetrics(nets, stas, locs, chans, start, end, metric_part, metricSource, failedMetrics)
        if tempDF.empty:
            # add it to a list for later
            emptyMets.append(metric_part)
            if len(tempDF.columns) == 0:
                ## This is TRULY empty - there wasn't a table for the metric in the database
                continue
        
        
        if DF.empty:
            DF = tempDF.copy()
        else:
            try:
                DF = pd.merge(DF, tempDF, how='outer', left_on=['target', 'start', 'end'], right_on=['target', 'start', 'end'])
            except:
                print("ERROR: Something went wrong with the metric. You should try again.")
                quit()
        
#     # If any metrics didn't return any results, add them to the DF as NaNs
#     for metric_part in emptyMets:
#         if not DF.empty:
#             DF[metric_part] = np.nan
    
    
    # Add a channel column so that it's easier to divide the thresholds
    if DF.empty:
        return DF, failedMetrics
    else:
        DF['network'] = pd.DataFrame([ x.split('.')[0] for x in DF['target'].tolist() ])
        DF['station'] = pd.DataFrame([ x.split('.')[1] for x in DF['target'].tolist() ])
        DF['location'] = pd.DataFrame([ x.split('.')[2] for x in DF['target'].tolist() ])
        DF['channel'] = pd.DataFrame([ x.split('.')[3] for x in DF['target'].tolist() ])
           
#         print(DF)
        return DF, failedMetrics
    
    
    
def parse_XML(xml_file, df_cols): 
    """Parse the input XML file and store the result in a pandas 
    DataFrame with the given columns. 
    
    The first element of df_cols is supposed to be the identifier 
    variable, which is an attribute of each node element in the 
    XML data; other features will be parsed from the text content 
    of each sub-element. 
    """
    
    xtree = et.parse(xml_file)
    xroot = xtree.getroot()
    rows = []

    
#     def get_namespace(element):
#         m = re.match('\{.*\}', element.tag)
#         return m.group(0) if m else ''
#   
#     namespace = get_namespace(xtree.getroot())
#     print(namespace)

    for rootNode in xroot: 
        if "}" in rootNode.tag:
            field = rootNode.tag.split('}')[1]
        else:
            field = rootNode.tag
            
        if field == 'Network': 
            thisNetwork = rootNode.attrib['code']
#             print(thisNetwork)
            
            for netNode in rootNode:
                if "}" in netNode.tag:
                    field = netNode.tag.split('}')[1]
                else:
                    field = netNode.tag
                    
                if field == 'Station':
                    thisStation = netNode.attrib['code']
#                     print(thisStation)
                    
                    for staNode in netNode:
                        if "}" in staNode.tag:
                            field = staNode.tag.split('}')[1]
                        else:
                            field = staNode.tag
                            
                        if field == 'Channel':
                            thisChannel = staNode.attrib['code']
#                             print(thisChannel)
                            thisLocation = staNode.attrib['locationCode']
#                             print(thisLocation)
                            thisStart = staNode.attrib['startDate']
#                             print(thisStart)
                            try:
                                thisEnd = staNode.attrib['endDate']
                            except:
                                thisEnd = np.nan
#                                 thisEnd = ''
#                             print(thisEnd)
                                
                            
                            for fieldNode in staNode:
                                if "}" in fieldNode.tag:
                                    field = fieldNode.tag.split('}')[1]
                                else:
                                    field = fieldNode.tag
                                
                                if field in df_cols:
                                    if field == 'Latitude':
                                        thisLatitude = fieldNode.text
#                                         print(thisLatitude)
                                    if field == 'Longitude':
                                        thisLongitude = fieldNode.text
#                                         print(thisLongitude)
                                    if field == 'Elevation':
                                        thisElevation = fieldNode.text
#                                         print(thisElevation)
                                    if field == 'Depth':
                                        thisDepth = fieldNode.text
#                                         print(thisDepth)
                                    if field == 'Azimuth':
                                        thisAzimuth = fieldNode.text
#                                         print(thisAzimuth)
                                    if field == 'Dip':
                                        thisDip = fieldNode.text
#                                         print(thisDip)
                                    if field == 'SampleRate':
                                        thisSampleRate = fieldNode.text
#                                         print(thisSampleRate)
                                                
                                if field == "Response":
                                    for subFieldNode in fieldNode:
                                        if "}" in subFieldNode.tag:
                                            field = subFieldNode.tag.split('}')[1]
                                        else:
                                            field = subFieldNode.tag
                                        

                                        if field == 'InstrumentSensitivity':
                                            
                                           
                                            for subFieldNode2 in subFieldNode:
                                                if "}" in subFieldNode2.tag:
                                                    field = subFieldNode2.tag.split('}')[1]
                                                else:
                                                    field = subFieldNode2.tag

                                                if field == 'Value':
                                                    thisScale = subFieldNode2.text
#                                                     print(thisScale)
                                                elif field == 'Frequency':
                                                    thisScaleFreq = subFieldNode2.text
#                                                     print(thisScaleFreq)
                                                elif field == 'InputUnits':
                                                    for unitNode in subFieldNode2:
                                                        if "}" in unitNode.tag:
                                                            field = unitNode.tag.split('}')[1]
                                                        else:
                                                            field = unitNode.tag
                                                        
                                                        if field == 'Name':
                                                            thisScaleUnits = unitNode.text
#                                                             print(thisScaleUnits)
                            rows.append([thisNetwork, thisStation, thisLocation, thisChannel, thisLatitude, thisLongitude,thisElevation, thisDepth,thisAzimuth, thisDip, thisScale, thisScaleFreq, thisScaleUnits, thisSampleRate, thisStart, thisEnd])                          
    out_df = pd.DataFrame(rows, columns=df_cols)
#     out_df['EndTime']= pd.to_datetime(out_df['EndTime']) 
#     out_df['StartTime']= pd.to_datetime(out_df['StartTime'])
    for column in ['Latitude','Longitude','Elevation','Depth','Azimuth','Dip', 'Scale','ScaleFreq','SampleRate']:
        out_df[column] = out_df[column].astype(float) 

    return out_df

    
def getMetadata(nets, stas, locs, chans, start, end, metadataSource):
    # This goes to the IRIS station service and pulls back the metadata
    # about all specified SNCLs - for all time. 
    
    # TODO: change it so that it only looks for current metadata epochs?

    if metadataSource.upper() == 'IRIS':

        URL = 'http://service.iris.edu/fdsnws/station/1/query?net=' + nets + \
              '&sta=' + stas + '&loc=' + locs + '&cha=' + chans + '&starttime=' + start + \
              '&endtime=' + end + '&level=channel&format=text&includecomments=true&nodata=404'
        print(URL)
        
        try:
            DF = pd.read_csv(URL, header=0, delimiter='|', dtype={' Location ': str,' Station ': str})
            
            # Since station service returns headers with whitespace around them
            DF.rename(columns=lambda x: x.strip(), inplace=True)
            # And with a '#' in front of Network
            DF.rename(columns = {'#Network': 'Network'}, inplace=True)
            DF['Location'] = DF.Location.replace(np.nan, '', regex=True)
            DF['Target'] = DF[['Network', 'Station', 'Location','Channel']].apply(lambda x: '.'.join(x.map(str)), axis=1)
            DF.columns = DF.columns.str.lower()
            
        except Exception as e:
            print("Unable to retrieve metadata from IRIS Station Service - %s" % e)
            DF = pd.DataFrame()
    else:
        # Then use local response-level XML files that were used in ISPAQ
        if metadataSource is None:
            print("No local metadata XML file provided. Skipping.")
            return None
        else:
            if metadataSource.endswith('.txt'):
                print("Will parse text file using %s" % metadataSource)
                DF = pd.read_csv(metadataSource, header=0, delimiter='|', dtype={' Location ': str,' Station ': str})
            
                # Since station service returns headers with whitespace around them
                DF.rename(columns=lambda x: x.strip(), inplace=True)
                # And with a '#' in front of Network
                DF.rename(columns = {'#Network': 'Network'}, inplace=True)
            
            else:
                print("Will parse XML using %s" % metadataSource)
                df_cols = ['Network','Station','Location','Channel','Latitude','Longitude','Elevation','Depth','Azimuth','Dip', 'Scale','ScaleFreq','ScaleUnits','SampleRate','StartTime','EndTime']
                DF = parse_XML(metadataSource, df_cols)
            
            DF['Location'] = DF.Location.replace(np.nan, '', regex=True)
            DF['Target'] = DF[['Network', 'Station', 'Location','Channel']].apply(lambda x: '.'.join(x.map(str)), axis=1)
            DF.columns = DF.columns.str.lower()
    return DF

# ============================#
# UTILITIES FOR WRITING ISSUE FILES

def sortIssueFile(issueDF, threshold, itype):
    # Here we take the list of issues and make it more compact
    # Combining sequential days into a single line
    #print "  -> Combining days to make more compact"


    printDF = pd.DataFrame(columns=['#Threshold','Target','Start','End','Ndays','Value', 'Status','Notes'])
    if itype == "average" or itype == 'median':
        for ind, row in issueDF.iterrows():
            nday = (row['end'] - row['start']).days
            printDF.loc[len(printDF)] = [threshold, row['target'], row['start'], row['end'], nday, row['value'], 'TODO', '']

    else:
        
#         printDF = pd.DataFrame(columns=['#Threshold','Target','Start','End','Ndays','Status','Notes'])
        
        for sncl in sorted(issueDF.target.unique()):

            tmpDF = issueDF[issueDF['target']==sncl].sort_values(['start'])
            start = ''
            end = ''
            nday=0
            for ind in tmpDF.index:
                tmpStart = tmpDF['start'].loc[ind]
                tmpEnd = tmpDF['end'].loc[ind]

                if tmpEnd.time() == datetime.time(0, 0):
                    tmpEnd = tmpEnd - datetime.timedelta(seconds=1)
                    
                if start == "":
                    start = tmpStart
                
                if end == "":
                    end = tmpEnd
                
                
                    
                else:
                    if end == tmpStart - datetime.timedelta(seconds=1):
                        end = tmpEnd
                        nday += 1
                                
                    else:
                        nday += 1
                        printDF.loc[len(printDF)] = [threshold,sncl, start.date(), end.date(), nday,'', 'TODO', '']
                        nday = 0
                                    
                        start = tmpStart
                        end = tmpEnd

            # When done with that sncl, need to add to list
            nday += 1
            printDF.loc[len(printDF)] = [threshold,sncl, start.date(), end.date(), nday, '', 'TODO', '']

    return printDF
    

def sortMetaFile(issueDF, threshold):
    # Here we take the list of issues and make it more compact
    # Combining sequential days into a single line
    #print "  -> Combining days to make more compact"
    issueDF['target'] = issueDF['network'] +'.'+ issueDF['station'] +'.'+ issueDF['location'].map(str) +'.'+  issueDF['channel']
    printDF = pd.DataFrame(columns=['#Threshold','Target','Start','End','Ndays','Value', 'Status','Notes'])

    
    if len(issueDF) > 0:
        for ind, row in issueDF.iterrows():
            start = datetime.datetime.strptime(row['starttime'], '%Y-%m-%dT%H:%M:%S.%f').date()
            if pd.isnull(row['endtime']):
                end = datetime.datetime.now().date()
            else:
                end = datetime.datetime.strptime(row['endtime'], '%Y-%m-%dT%H:%M:%S.%f').date()
                
            Ndays =  len(pd.period_range(start, end, freq='D'))
            target = row['target'].strip()
                
                            
            printDF.loc[len(printDF)] = [threshold,target, start, end, Ndays,'', 'TODO', '']

    return printDF



def writeToOutfile(issueDF, filename):
    
    with open(filename, 'a') as f:
        issueDF.to_csv(f, sep='|', index=False, header=False)
    f.close()

 
def expandCodes(s):
    
    codes = list()
    codeList = s.split(',')
    for code in codeList:
        codeSplit = code.split('[')
        lcodeSplit = len(codeSplit)
        
        if lcodeSplit == 1:
            codes.append(codeSplit[0].strip())
            
        if lcodeSplit == 2:
            first = codeSplit[0].strip()
            second = codeSplit[1].strip()
            
            if first == "":
                first = '%s]' % second.split(']')[0]
                second = second.split(']')[1]
            
            if first.endswith(']'):
                for f in first.strip(']'):
                    if second.endswith(']'):
                        for s in second.strip(']'):
                            codes.append('%s%s' % (f,s))
                    else:
                        codes.append('%s%s' % (f,second))
            else:
                if second.endswith(']'):
                    for s in second.strip(']'):
                        codes.append('%s%s' % (first,s))
                else:
                    codes.append('%s%s' % (first,second))

                
                
                
        if lcodeSplit == 3:
            first = codeSplit[0].strip()
            second = codeSplit[1].strip()
            third = codeSplit[2].strip()
            
            if first == "":
                first = '%s]' % second.split(']')[0]
                second = second.split(']')[1]
    
            if first.endswith(']'):
                for f in first.strip(']'):
                    if second.endswith(']'):
                        for s in second.strip(']'):
                            if third.endswith(']'):
                                for t in third:
                                    codes.append('%s%s%s' % (f,s,t))
                            else:
                                codes.append('%s%s%s' % (f,s,third))
                    else:
                        if third.endswith(']'):
                            for t in third.strip(']'):
                                codes.append('%s%s%s' % (f,second,t))
                        else:
                            codes.append('%s%s%s' % (f,second,third))
            else:
                if second.endswith(']'):
                    for s in second.strip(']'):
                        if third.endswith(']'):
                            for t in third.strip(']'):
                                codes.append('%s%s%s' % (first,s,t))
                        else:
                            codes.append('%s%s%s' % (first,s,third))
                else:
                    if third.endswith(']'):
                        for t in third.strip(']'):
                            codes.append('%s%s%s' % (first,second,t))
                    else:
                        codes.append('%s%s%s' % (first,second,third))
            
    codes = ",%s," % (','.join(codes))
    return codes  