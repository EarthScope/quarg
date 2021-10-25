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
import reportUtils
import numpy as np
import datetime
import os
from matplotlib.dates import epoch2num


def load_thresholdDicts(thresholdFile):
    
# FIRST, Read in the file and genrate two Dictionaries
#    One will be the thresholdDict, which is used when initially grabbing metrics from webservices
#    The other will provide defitinions of the thresholds

    thresholdDefDict = {}
    thresholdDict = {}
    
    
    with open(thresholdFile) as f:
            local_dict = locals()
            exec(compile(f.read(), thresholdFile, "exec"),globals(), local_dict)
    

    return local_dict['thresholdsDict'], local_dict['thresholdsMetricsDict'], local_dict['instrumentGroupsDict']


def get_threshold_metrics(thresholds, thresholdFile):
    metrics = list()
    failedThresholds = list()
    
    thresholdDefDict, thresholdMetDict, instrumentGroupsDict = load_thresholdDicts(thresholdFile)
    
    for threshold in thresholds:
        try:
            for metric in thresholdMetDict[threshold]:
                metrics.append(metric)
        except:
            if threshold not in failedThresholds:
                failedThresholds.append(threshold)
            print("WARNING: Unable to understand threshold %s: the threshold has likely been deleted from the Edit Thresholds form, but not removed from this Preference File" % threshold)
            
    metrics = list(set(metrics))
    return metrics, failedThresholds


def load_metric_and_metadata():
    metrics_file = "./MUSTANG_metrics.txt"
    metadata_file = "./IRIS_metadata.txt"
    
    try:
        with open(metrics_file,'r') as f:
            metricList = f.read().splitlines()
    except Exception as e:
        print("Warning: %s" % e)
        metricList = list()
                    
    try:
        with open(metadata_file,'r') as f:
            metadataList = f.read().splitlines()
    except Exception as e:
        print("Warning: %s" % e)
        metadataList = list()
        
    return metricList, metadataList

    
def do_threshold(threshold, thresholdFile, metricDF, metaDF, outfile, instruments, specified_start, specified_end, hasMetrics, chanTypes):
    print("Running %s" % threshold)
    thresholdDefDict, thresholdMetDict, instrumentGroupsDict = load_thresholdDicts(thresholdFile)
    metricList, metadataList = load_metric_and_metadata()
#     doRatio = 0
#     doAverage = 0
    
    pd.options.mode.chained_assignment = None

    def get_channel_lists(CH1, CH2):
        ch1 = ''
        ch2 = ''
        if not CH1 == '':
            ch1 = chanTypes[CH1]
        if not CH2 == '':
            ch2 = chanTypes[CH2]
        return ch1, ch2
                
    def do_channel_figuring(dfToUse, CH1, CH2, ch1, ch2, chType1, chType2, doAbs1, doAbs2):
        columnsToNotChange = ['target', 'start', 'end', 'network', 'station', 'location', 'channel','snl', 'new_target']
        metricsInDF = [x  for x in dfToUse.columns if x not in columnsToNotChange]
        dfToUse['snl'] = dfToUse['target'].apply(lambda x: os.path.splitext(os.path.splitext(x)[0])[0])    # use snl instead of station to do merging, in case multiple location codes

        #### CASES WITH AVG ###
        if chType1 == '' and chType2 == 'avg':
            # CH2 must be H, CH1 can be V or H
            for col in dfToUse.columns:
                if col in columnsToNotChange:
                    continue
                dfToUse.rename(columns={col : col + '_' + chType1}, inplace = True)            
             
               
            tmpDF = dfToUse[dfToUse['channel'].str.endswith(ch2)]
            
#             horzAvg = tmpDF.groupby(['station','start']).mean()
            horzAvg = tmpDF.groupby(['snl','start'],as_index=False).mean().reset_index()

            for col in horzAvg.columns:
                if col in columnsToNotChange:
                    continue
#                 if doAbs2:
#                     horzAvg[col] = horzAvg[col].abs()
                horzAvg.rename(columns={col : col + chType2}, inplace = True)  

#             dfToUse = pd.merge(dfToUse, horzAvg, how='inner', on=['station','start'])
            dfToUse = pd.merge(dfToUse, horzAvg, how='inner', on=['snl','start'])
            
#             if doAbs1:
#                 for col in dfToUse.columns[dfToUse.columns.str.endswith("_%s" % chType1)]:
#                     dfToUse[col] = dfToUse[col].abs()

            newTargets = list()
            for idx, row in dfToUse.iterrows():
                splitTarget = row['target'].split('.')
                thisSNL = row['snl']
                ch2ThisSNL = ''.join([i for i in list(set(dfToUse[dfToUse['snl'] == thisSNL].channel.str.strip().str[-1])) if i in ch2])
#                 ch2Channels = unique(tmpDF['channel'].str.strip().str[-1])
                newChannel = '%s/[%s]' % (splitTarget[3], ch2ThisSNL)
                splitTarget[3] = newChannel
                     
                newTarget = '.'.join(splitTarget)
                newTargets.append(newTarget)
            dfToUse['new_target'] = newTargets


        if chType1 == 'avg' and chType2 == '':
            # CH1 must be H, CH2 can be H or V
            for col in dfToUse.columns:
                if col in columnsToNotChange:
                    continue
                dfToUse.rename(columns={col : col + '_' + chType2}, inplace = True)   
                
            tmpDF = dfToUse[dfToUse['channel'].str.endswith(ch1)]
            
            horzAvg = tmpDF.groupby(['snl','start']).mean().reset_index()
#             horzAvg = tmpDF.groupby(['station','start']).mean().reset_index()
            for col in horzAvg.columns:
                if col in columnsToNotChange:
                    continue
#                 if doAbs1:
#                     horzAvg[col] = horzAvg[col].abs()
                horzAvg.rename(columns={col : col + chType1}, inplace = True) 
                           
#             dfToUse = pd.merge(dfToUse, horzAvg, how='inner', on=['station','start']) 
            dfToUse = pd.merge(dfToUse, horzAvg, how='inner', on=['snl','start']) 
            
            newTargets = list()
            for idx, row in dfToUse.iterrows():
                splitTarget = row['target'].split('.')
                thisSNL = row['snl']
                ch1ThisSNL = ''.join([i for i in list(set(dfToUse[dfToUse['snl'] == thisSNL].channel.str.strip().str[-1])) if i in ch1])
#                 ch2Channels = unique(tmpDF['channel'].str.strip().str[-1])
                newChannel = '%s[%s]/%s' % (splitTarget[3][0:2], ch1ThisSNL, splitTarget[3][-1])
                splitTarget[3] = newChannel
                     
                newTarget = '.'.join(splitTarget)
                newTargets.append(newTarget)
            dfToUse['new_target'] = newTargets


        if chType1 == 'avg' and chType2 == 'avg':
            # This case can only happen if we are comparing two different metrics
            # Create dataframe average of horizontals for metric 1
                 
            tmpDF = dfToUse[dfToUse['channel'].str.endswith(ch1)]
            
#             horzAvg = tmpDF.groupby(['station','start']).mean().reset_index()
            horzAvg = tmpDF.groupby(['snl','start']).mean().reset_index()
            for col in horzAvg.columns:
                if col in columnsToNotChange:
                    continue
#                 if doAbs2:
#                     horzAvg[col] = horzAvg[col].abs()
                horzAvg.rename(columns={col : col + '_' + chType2}, inplace = True) 
            
            dfToUse = pd.merge(dfToUse, horzAvg, how='inner', on=['snl','start'])    
#             dfToUse = pd.merge(dfToUse, horzAvg, how='inner', on=['station','start']) 

            newTargets = list()
            for idx, row in dfToUse.iterrows():
                splitTarget = row['target'].split('.')
                thisSNL = row['snl']
                ch1ThisSNL = ''.join([i for i in list(set(dfToUse[dfToUse['snl'] == thisSNL].channel.str.strip().str[-1])) if i in ch1])
#                 ch2Channels = unique(tmpDF['channel'].str.strip().str[-1])
                newChannel = '%s[%s]' % (splitTarget[3][0:2], ch1ThisSNL)
                splitTarget[3] = newChannel
                     
                newTarget = '.'.join(splitTarget)
                newTargets.append(newTarget)
            dfToUse['new_target'] = newTargets
            
            

        
        #### CASES WITH VS ####    
        if (chType1 == '' and chType2 == 'vs') or (chType1 == 'vs' and chType2 == ''):
            print("INFO: comparing 'all' with a 'vs' - this shouldn't happen")
            
        if (chType1 == 'avg' and chType2 == 'vs') or (chType1 == 'vs' and chType2 == 'avg'):
            print("INFO: comparing 'avg' with 'vs' - this shouldn't happen")
            
        if chType1 == 'vs' and chType2 == 'vs':
            # CH1 and CH2 must be H
            dfToUse = dfToUse[~dfToUse['channel'].str.endswith(chanTypes['V'])]
            
            for col in dfToUse.columns:
                if col in columnsToNotChange:
                    continue
                dfToUse.rename(columns={col : col + '_' + chType1}, inplace = True)  
            #  Horizontal vs horizontal: need to copy the value of both horizontals for each NSL,
            # such that both E/N and N/E can be computed
            # Since it is H-vs v H-vs, both ch1 and ch2 should be exaclty the same
            
            # create a column for snl, to use as a join later:
            dfToUse['snl'] = dfToUse['target'].apply(lambda x: os.path.splitext(os.path.splitext(x)[0])[0])

            dtToStore = dfToUse.copy()
            colList = list()
            chanDict = dict()
            for tmpChan in ch1:
                # get all values for each channel, then create a new column with those values, associated with the snl
                tmpValues = dtToStore[dtToStore.channel.str.endswith(tmpChan)]
                tmpValues.drop(['station', 'location','channel','end','target','network'], axis = 1, inplace = True) 
                for col in tmpValues.columns:
#                     if col in columnsToNotChange or col == 'snl':
                    if col in columnsToNotChange:
                        continue
                    newcol = col + '_' + tmpChan
                    if newcol not in colList:
                        colList.append(newcol)
                    tmpValues.rename(columns={col : newcol}, inplace = True) 
                for snl in set(tmpValues['snl']):
                    try:
                        chanDict[snl] = chanDict[snl] + tmpChan
                    except:
                        chanDict[snl] = tmpChan
                dfToUse.dropna(subset = ["channel"], inplace=True)
                mergedDF = pd.merge(dfToUse[~dfToUse['channel'].str.endswith(tmpChan)], tmpValues, how='outer', on=['snl','start'])
                dfToUse = pd.merge(dfToUse, mergedDF, how='outer')
               
            for metric in metricsInDF:
                theseCols = [x for x in colList if x.startswith(metric)]
                sncl2 = metric + '_sncl2'
                dfToUse[sncl2] = dfToUse[theseCols[0]]
                
                for col in theseCols:
                    dfToUse[sncl2] = dfToUse[sncl2].fillna(dfToUse[col])
                    dfToUse.drop([col], axis = 1, inplace = True)
              
            dfToUse.dropna(subset = ["target"], inplace=True)
            newTargets = list()
            for idx, row in dfToUse.iterrows():
                try:
                    splitTarget = row['target'].split('.')
                except:
                    newTargets.append(row['target'])
                    continue
                thisSNL = row['snl']
                thisChan = splitTarget[3][-1]
                
                try:
                    ch1ThisSNL = chanDict[thisSNL].replace(thisChan,'')
                except:
                    print("INFO: unable to process %s - maybe it has H[orizontal] channels not included in the preference file?" % thisSNL)
                    newTargets.append('')
                    continue
#                 ch2Channels = unique(tmpDF['channel'].str.strip().str[-1])
                newChannel = '%s/%s' % (splitTarget[3], ch1ThisSNL)
                splitTarget[3] = newChannel
                     
                newTarget = '.'.join(splitTarget)
                newTargets.append(newTarget)
            dfToUse['new_target'] = newTargets 
            
#             mergedDF.update(mergedDF[colList].merge(df2, 'left'))


        #### CASES WITHOUT VS OR AVG ####                
        if chType1 == '' and chType2 == '': 
            # Can be any combination of H and V (H-V, V-H, H-H, V-V)
            # CH1 == CH2 is handled directly in the dp_ method, since we already have a dataframe with the two metrics joined on target-day
            
            #### V vs H, or H vs V ####
            if CH1 != CH2:
                # Can be same or different metrics, either way we need to get the different channels into a single row                
                
                for col in dfToUse.columns:
                    if col in columnsToNotChange:
                        continue
                    dfToUse.rename(columns={col : col + '_'}, inplace = True)
                    
                dfToUse['snl'] = dfToUse['target'].apply(lambda x: os.path.splitext(os.path.splitext(x)[0])[0])    
                
                dtToStore = dfToUse.copy()  # copy all values before subsetting for only ch1, so that all are availble as sncl2
                dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]  # now there will only be ch1 channels in the main slot
                newChanDF = dfToUse[['channel','target','start']]

                newChanList = list()
                oldChanList = list()                
                
                
                
                for tmpChanA in dfToUse['channel']:
                    for tmpChanB in ch2:

                        newChanList.append("%s%s" % (tmpChanA[0:2], tmpChanB))
                        oldChanList.append(tmpChanA)
                ncDF = pd.DataFrame(newChanList, columns=['second_channel'])
                ncDF['channel'] = oldChanList
                
#                 newChanDF = pd.concat([ncDF,pd.concat([newChanDF]*len(ch2)).set_index(ncDF.index)]).sort_index().ffill()
                
                newChanDF = pd.merge(newChanDF, ncDF).drop_duplicates().reset_index(drop=True)
                dfToUse = pd.merge(dfToUse, newChanDF)
                colList = list()
                for tmpChan in ch2:
                    # get all values for each channel, then create a new column with those values, associated with the snl
                    tmpValues = dtToStore[dtToStore.channel.str.endswith(tmpChan)]
                    
                    tmpValues.drop(['station', 'location','end','network','target'], axis = 1, inplace = True) 

                    for col in tmpValues.columns:
                        if col in columnsToNotChange or col == 'second_channel' or col == 'snl':
                            continue
                        newcol = col  + tmpChan
                        if newcol not in colList:
                            colList.append(newcol)
                        tmpValues.rename(columns={col : newcol}, inplace = True) 
                    tmpValues.rename(columns={'channel' : 'second_channel'}, inplace = True) 
                    mergedDF = pd.merge(dfToUse, tmpValues,  on=['snl','start','second_channel'])

                    
                    dfToUse = pd.merge(dfToUse, mergedDF, how='outer')
                
                newTargets = list()
                for idx, row in dfToUse.iterrows():
                    splitTarget = row['target'].split('.')
                    newChannel = '%s/%s' % (splitTarget[3], row['second_channel'][-1])
                    splitTarget[3] = newChannel
                     
                    newTarget = '.'.join(splitTarget)
                    newTargets.append(newTarget)
                dfToUse['new_target'] = newTargets
                
                for metric in metricsInDF:
                    theseCols = [x for x in colList if x.startswith(metric)]
                    sncl2 = metric + '_sncl2'
                    dfToUse[sncl2] = dfToUse[theseCols[0]]
                    
                    for col in theseCols:
                        dfToUse[sncl2] = dfToUse[sncl2].fillna(dfToUse[col])
                        dfToUse.drop([col], axis = 1, inplace = True)
                    
            
        if chType1 == '' and chType2 == 'V':
            pass
        if chType1 == '' and chType2 == 'V':
            pass
        if chType1 == '' and chType2 == 'V': 
            pass
    
        return dfToUse
    
    def do_comparison(dfToUse, field1, operator, field2, doAbs1, doAbs2):
        
        if operator == '>=':
            if doAbs1 and doAbs2:
                dfToUse = dfToUse[field1.abs() >= field2.abs()]
            elif doAbs1: 
                dfToUse = dfToUse[field1.abs() >= field2]
            elif doAbs2:
                dfToUse = dfToUse[field1 >= field2.abs()]
            else:
                dfToUse = dfToUse[field1 >= field2]
        if operator == '!>=':
            if doAbs1 and doAbs2:
                dfToUse = dfToUse[ field1.abs() < field2.abs()]
            elif doAbs1: 
                dfToUse = dfToUse[ field1.abs() < field2]
            elif doAbs2:
                dfToUse = dfToUse[ field1 < field2.abs()]
            else:
                dfToUse = dfToUse[ field1 < field2]
        if operator == '>':
            if doAbs1 and doAbs2:
                dfToUse = dfToUse[field1.abs() > field2.abs()]
            elif doAbs1: 
                dfToUse = dfToUse[field1.abs() > field2]
            elif doAbs2:
                dfToUse = dfToUse[field1 > field2.abs()]
            else:
                dfToUse = dfToUse[field1 > field2]
        if operator == '=':
            if doAbs1 and doAbs2:
                dfToUse = dfToUse[field1.abs() == field2.abs()]
            elif doAbs1: 
                dfToUse = dfToUse[field1.abs() == field2]
            elif doAbs2:
                dfToUse = dfToUse[field1 == field2.abs()]
            else:
                dfToUse = dfToUse[field1 == field2]
        if operator == '!=':
            if doAbs1 and doAbs2:
                dfToUse = dfToUse[field1.abs() != field2.abs()]
            elif doAbs1: 
                dfToUse = dfToUse[field1.abs() != field2]
            elif doAbs2:
                dfToUse = dfToUse[field1 != field2.abs()]
            else:
                dfToUse = dfToUse[field1 != field2]
        if operator == '<=':
            if doAbs1 and doAbs2:
                dfToUse = dfToUse[field1.abs() <= field2.abs()]
            elif doAbs1: 
                dfToUse = dfToUse[field1.abs() <= field2]
            elif doAbs2:
                dfToUse = dfToUse[field1 <= field2.abs()]
            else:
                dfToUse = dfToUse[field1 <= field2]
        if operator == '!<=':
            if doAbs1 and doAbs2:
                dfToUse = dfToUse[ field1.abs() > field2.abs()]
            elif doAbs1: 
                dfToUse = dfToUse[ field1.abs() > field2]
            elif doAbs2:
                dfToUse = dfToUse[ field1 > field2.abs()]
            else:
                dfToUse = dfToUse[ field1 > field2]
        if operator == '<':
            if doAbs1 and doAbs2:
                dfToUse = dfToUse[field1.abs() < field2.abs()]
            elif doAbs1: 
                dfToUse = dfToUse[field1.abs() < field2]
            elif doAbs2:
                dfToUse = dfToUse[field1 < field2.abs()]
            else:
                dfToUse = dfToUse[field1 < field2]
    
        return dfToUse
    

    def simple_threshold(chanMetricDF, chanMetaDF, subDef):
        # Whether we use chanMetricDF or chanMetaDF depends on whether this definition has metrics or metadata...
        doAbs1 = 0
        doAbs2 = 0
        CH1 = ''

        
        #Get the definition
        threshDefs = thresholdDefDict[threshold]

        try:
            
            field = subDef.split()[0].split('[')[0]
            try:
#                 ch1 = subDef.split()[0].split('[')[1].replace(']','').split(':')[0]     # Only Ratio and Comparison can have H: avg/vs
                CH1 = subDef.split()[0].split('[')[1].replace(']','')
                ch1, ch2 = get_channel_lists(CH1, '')

            except:
                ch1 = ''
            
            if 'abs' in field:
                doAbs1 = 1
                field = field.replace('abs(','').replace(')','')
                
            if field in metricList:
                fieldType = 'metric'
                dfToUse = chanMetricDF
            elif field in metadataList:
                fieldType = 'metadata'
                field = field.lower()
                dfToUse = chanMetaDF
            else:
                print("WARNING unknown field type")
                return chanMetricDF, chanMetaDF, "simple"
 
            try:
                field = field.split("::")[1]
            except:
                pass
                
            
            operator = subDef.split()[1]
            
            try:
                # it's numeric
                value = float(subDef.split()[2])
            except:
                # it's not numeric, so the fielf better be a metadata field
                if fieldType != 'metadata':
                    print("Warning, only metadata fields can have non-numeric cutoff values")
                    return chanMetricDF, chanMetaDF, "simple"
                else:
                    value = subDef.split()[2]

            # If the threshold is only for horixontal or verticals, then subset it now:
            if ch1 != '':
                dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]
                
        except Exception as e:
            print("Warning: could not calculate threshold %s - %s" % (subDef, e))
            return chanMetricDF, chanMetaDF, "simple"
                
                
        dfToUse =   do_comparison(dfToUse, dfToUse[field], operator, value, doAbs1, doAbs2)  
                    
        if fieldType == 'metric':
            chanMetricDF = dfToUse
        elif fieldType == 'metadata':
            chanMetaDF = dfToUse
        
        return chanMetricDF, chanMetaDF, "simple"
    # ============================#
    # COMPLETENESS THRESHOLDS

    def ratio_threshold(chanMetricDF, chanMetaDF, subDef):
        doAbs1 = 0  # first metric
        doAbs2 = 0  # second metric
        doAbs3 = 0  # "ratio" - unused currently, placeholder
        doAbs4 = 0  # cutoff value - unused currently, placeholder
        chType1 = ''
        chType2 = ''
        
        try:
            met1 = subDef.split('/')[0].split()[-1].split('[')[0]
            met2 = subDef.split('/')[1].split()[0].split('[')[0]
        except Exception as e:
            print("Warning: Could not parse ratio threshold %s - %s" % (subDef, e))
            return chanMetricDF, chanMetaDF, "ratio"
        
        if 'abs' in met1:
            doAbs1 = 1
            met1 = met1.replace('abs(','').replace(')','')
        if 'abs' in met2:
            doAbs2 = 1
            met2 = met2.replace('abs(','').replace(')','')
                
        if met1 in metricList:
            fieldType = 'metric'
            dfToUse = chanMetricDF
        elif met1 in metadataList:
            fieldType = 'metadata'
            dfToUse = chanMetaDF
        else:
            print("WARNING: unknown field type")
            return chanMetricDF, chanMetaDF, "ratio"
        
        try:
            met1 = met1.split("::")[1]
        except:
            pass
        try:
            met2 = met2.split("::")[1]
        except:
            pass  
        
        # figure out what's going on with H/V, if anything
        try:
            CH1 = subDef.split('/')[0].split()[-1].split('[')[1].replace(']','').replace(')','')
            try:
                chType1 = CH1.split(':')[1]
                CH1 = CH1.split(':')[0]
            except:
                pass
            
        except:
            CH1 = ''
        
        try:
            CH2 = subDef.split('/')[1].split()[0].split('[')[1].replace(']','').replace(')','')
            try:
                chType2 = CH2.split(':')[1]
                CH2 = CH2.split(':')[0]
            except:
                pass
        except:
            CH2 = ''
        
        
        ## Only in the ratio threshold do we have to handle the absolute values outside of the do_comparison function        
        ch1, ch2 = get_channel_lists(CH1, CH2)
        columnsToNotChange = ['target', 'start', 'end', 'network', 'station', 'location', 'channel','snl','ratio','new_target']
        
            
        if CH1 == CH2 and chType1 == chType2 == "":
            if doAbs1:
                dfToUse[met1] = dfToUse[met1].abs()
            if doAbs2:
                dfToUse[met2] = dfToUse[met2].abs()
            dfToUse['ratio'] = dfToUse[met1] / dfToUse[met2]    # Later we will whittle down to just the V or just the H, if necessary
            
#             dfToUse['ratio'] = dfToUse['ratio'].apply(lambda x: x*100)    # OLD

        else:
            # Do the figuring on what needs to happen to the dataframe based on chType1 and chyType2
            dfToUse = do_channel_figuring(dfToUse, CH1, CH2, ch1, ch2, chType1, chType2, doAbs1, doAbs2)

            
            # Subset based on the channel indicated by ch1:
#             dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]
                        
            # create the ratio column:
            if chType1 == 'vs' or chType2 == 'vs':
                if doAbs1:
                    dfToUse[met1+ "_" + chType1] = dfToUse[met1+ "_" + chType1].abs()
                if doAbs2:
                    dfToUse[met2 + "_sncl2"] = dfToUse[met2 + "_sncl2"].abs()
                dfToUse['ratio'] = dfToUse[met1+ "_" + chType1] / dfToUse[met2 + "_sncl2"]
                
                # delete extra columns, revert names of main metrics
                for col in dfToUse.columns:
                    if col.endswith('_sncl2'):
                        dfToUse.drop([col], axis = 1, inplace = True)
                    elif col not in columnsToNotChange:
                        dfToUse.rename(columns={col : col.rsplit('_', 1)[0]}, inplace = True)
        
            
            else:

                if chType1 == chType2 == '':
                    if doAbs1:
                        dfToUse[met1+ "_"] = dfToUse[met1+ "_"].abs()
                    if doAbs2:
                        dfToUse[met2 + "_sncl2"] = dfToUse[met2 + "_sncl2"].abs()
                    dfToUse['ratio'] = dfToUse[met1+ "_"] / dfToUse[met2 + "_sncl2"]
                    
                    # delete extra columns, revert names of main metrics
                    for col in dfToUse.columns:
                        if col.endswith('_sncl2'):
                            dfToUse.drop([col], axis = 1, inplace = True)
                        elif col not in columnsToNotChange:
#                             dfToUse.rename(columns={col : '_'.join(col.split("_")[:-1])})
                            dfToUse.rename(columns={col : col.rsplit('_', 1)[0]}, inplace = True)
                        
                else:
#                     if chType1 == chType2 == 'avg':
                    if doAbs1:
                        dfToUse[met1+ "_" + chType1] = dfToUse[met1+ "_" + chType1].abs()
                    if doAbs2:
                        dfToUse[met2+ "_" + chType2] = dfToUse[met2+ "_" + chType2].abs()

                    dfToUse['ratio'] = dfToUse[met1+ "_" + chType1] / dfToUse[met2 + "_" + chType2]
                    
                    # delete extra columns, revert names of main metrics
                    for col in dfToUse.columns:
                        if col.endswith("_" + chType2):
                            dfToUse.drop([col], axis = 1, inplace = True)
                        elif col not in columnsToNotChange:
#                             dfToUse.rename(columns={col : '_'.join(col.split("_")[:-1])})
                            dfToUse.rename(columns={col : col.rsplit('_', 1)[0]}, inplace = True)
#                 dfToUse['ratio'] = dfToUse['ratio'].apply(lambda x: x*100)    # OLD

        if ch1 != '':
            dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]
            
#             dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]

        ##### 

        try:
            fields = subDef.split()
            operator = fields[3]
            value = float(fields[4])
        except Exception as e:
            print("Warning: could not calculate threshold %s - %s" % (subDef, e))
            return
        dfToUse =   do_comparison(dfToUse, dfToUse['ratio'], operator, value, doAbs3, doAbs4)

        if fieldType == 'metric':
            chanMetricDF = dfToUse
        elif fieldType == 'metadata':
            chanMetaDF = dfToUse
        
       
        return chanMetricDF, chanMetaDF, "ratio"
#         return dfToUse, fieldType, "ratio"
    
    def average_threshold(chanMetricDF, chanMetaDF, subDef):
        # Shouldn't have metadata in here, but keeping it open for future-proofing
        doAbs1 = 0
        doAbs2 = 0
        CH1 = ''
        CH2 = ''
        
        try:
            fields = subDef.split("::")[1].split()
            
            field = fields[0].split('[')[0]
            operator = fields[1]
            value = float(fields[2])
            
            try:
#                 ch1 = fields[0].split('[')[1].replace(']','').split(':')[0]    # only Ratio and Comparison can have H: avg/vs
                CH1 = fields[0].split('[')[1].replace(']','')
                ch1, ch2 = get_channel_lists(CH1, CH2)
#                 ch1 = chanTypes[CH1]
#                 if ch1 == 'V':
#                     ch1 = Vchans
#                 elif ch1 == 'H':
#                     ch1 = Hchans
            except:
                ch1 = ''
            
            
            if 'abs' in field:
                doAbs1 = 1
                field = field.replace('abs(','').replace(')','')
                
            if field in metricList:
                fieldType = 'metric'
                dfToUse = chanMetricDF
            elif field in metadataList:
                fieldType = 'metadata'
                dfToUse = chanMetaDF
            else:
                print("WARNING: unknown field type")
                return 
            
            try:
                field = field.split("::")[1]
            except:
                pass
            
            dfToUse = dfToUse.groupby('target', as_index=False)[field].mean().round(1)
            dfToUse.rename(columns={field : 'value'}, inplace = True)
            dfToUse['channel'] = [t.split('.')[3] for t in dfToUse['target']]
            dfToUse['start'] = datetime.datetime.strptime(specified_start, '%Y-%m-%d')
            dfToUse['end'] = datetime.datetime.strptime(specified_end, '%Y-%m-%d')
            
            # If the threshold is only for horixontal or verticals, then subset it now:
            if ch1 != '':
                dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]
            
        except Exception as e:
            print("WARNING: Unable to calculate %s - %s" % (subDef, e))
            return dfToUse, fieldType, "average"
        
        dfToUse =   do_comparison(dfToUse, dfToUse['value'], operator, value, doAbs1, doAbs2)

        if fieldType == 'metric':
            chanMetricDF = dfToUse
        elif fieldType == 'metadata':
            chanMetaDF = dfToUse
        
        return chanMetricDF, chanMetaDF, "average"
#         return dfToUse, fieldType, "average"

    def median_threshold(chanMetricDF, chanMetaDF, subDef):
        # Shouldn't have metadata in here, but keeping it open for future-proofing
        doAbs1 = 0
        doAbs2 = 0
        CH1 = ''
        CH2 = ''
        
        try:
            fields = subDef.split("::")[1].split()
            
            field = fields[0].split('[')[0]
            operator = fields[1]
            value = float(fields[2])
            
            try:
#                 ch1 = fields[0].split('[')[1].replace(']','').split(':')[0]    # Only Ratio and Comparison can have H: avg/vs
                CH1 = fields[0].split('[')[1].replace(']','')
                ch1, ch2 = get_channel_lists(CH1, CH2)
#                 ch1 = chanTypes[CH1]
            except:
                ch1 = ''
            
            if 'abs' in field:
                doAbs1 = 1
                field = field.replace('abs(','').replace(')','')
                
            if field in metricList:
                fieldType = 'metric'
                dfToUse = chanMetricDF
            elif field in metadataList:
                fieldType = 'metadata'
                dfToUse = chanMetaDF
            else:
                print("WARNING: unknown field type")
                return chanMetricDF, chanMetaDF, "median" 
            
            
            try:
                field = field.split("::")[1]
            except:
                pass
            
            dfToUse = dfToUse.groupby('target', as_index=False)[field].median().round(1)
            dfToUse.rename(columns={field : 'value'}, inplace = True)
            dfToUse['channel'] = [t.split('.')[3] for t in dfToUse['target']]
            dfToUse['start'] = datetime.datetime.strptime(specified_start, '%Y-%m-%d')
            dfToUse['end'] = datetime.datetime.strptime(specified_end, '%Y-%m-%d')
            
            # If the threshold is only for horixontal or verticals, then subset it now:
            if ch1 != '':
                dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]
        except Exception as e:
            print("WARNING: Unable to calculate %s - %s" % (subDef, e))
            return chanMetricDF, chanMetaDF, "median"
        
        dfToUse =   do_comparison(dfToUse, dfToUse['value'], operator, value, doAbs1, doAbs2)

        if fieldType == 'metric':
            chanMetricDF = dfToUse
        elif fieldType == 'metadata':
            chanMetaDF = dfToUse
        
        return chanMetricDF, chanMetaDF, "median"
    
    def compare_threshold(chanMetricDF, chanMetaDF, subDF):
        doAbs1 = 0
        doAbs2 = 0
        CH1 = ''
        CH2 = ''
        chType1 = ''
        chType2 = ''
        columnsToNotChange = ['target', 'start', 'end', 'network', 'station', 'location', 'channel','snl','ratio', 'new_target']
        
        try:
            fields = subDef.split()
            met1 = fields[0].split('[')[0]
            operator = fields[1]
            met2 = fields[2].split('[')[0]
                        
        except Exception as e:
            print("WARNING: Unable to calculate %s - %s" % (subDef, e))
            return chanMetricDF, chanMetaDF, "comparison"
        
        if 'abs' in met1:
            doAbs1 = 1
            met1 = met1.replace('abs(','').replace(')','')
        if 'abs' in met2:
            doAbs2 = 1
            met2 = met2.replace('abs(','').replace(')','')
        
        if met1 in metricList:
            fieldType = 'metric'
            dfToUse = chanMetricDF
        elif met1 in metadataList:
            fieldType = 'metadata'
            dfToUse = chanMetaDF
        else:
            print("WARNING: unknown field type")
            return chanMetricDF, chanMetaDF, "comparison"
        
        try:
            met1 = met1.split("::")[1]
        except:
            pass
        try:
            met2 = met2.split("::")[1]
        except:
            pass
        
        # figure out what's going on with H/V, if anything
        try:
            CH1 = fields[0].split('[')[1].replace(']','').replace(')','')
            try:
                chType1 = CH1.split(':')[1]
                CH1 = CH1.split(':')[0]
            except:
                pass
            
        except:
            CH1 = ''

        try:
            CH2 = fields[2].split('[')[1].replace(']','').replace(')','')
            try:
                chType2 = CH2.split(':')[1]
                CH2 = CH2.split(':')[0]
            except:
                pass
        except:
            CH2 = ''

        ch1, ch2 = get_channel_lists(CH1, CH2)

        # Simplest case: ch1 and ch2 are both empty, or we are doing V-V or H-H and we just run everything like normal
        if CH1 == CH2 and chType1 == chType2 == "":
            dfToUse = do_comparison(dfToUse, dfToUse[met1], operator, dfToUse[met2], doAbs1, doAbs2)
            # No extra columns to figure out here, since this case doesn't need do_channel_figuring()
            
        else:
            # Do the figuring on what needs to happen to the dataframe based on chType1 and chyType2
            dfToUse = do_channel_figuring(dfToUse, CH1, CH2, ch1, ch2, chType1, chType2, doAbs1, doAbs2)
            # Subset based on the channel indicated by ch1:
            dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]

            if chType1 == 'vs' or chType2 == 'vs':
                df1 =  dfToUse[met1+ "_" + chType1]
                df2 = dfToUse[met2 + "_sncl2"]
                
                # each one of these cases has it's own do_comparison so that it is easier to remove the extra columns afterward
                dfToUse = do_comparison(dfToUse, df1, operator, df2, doAbs1, doAbs2)
                
                # delete extra columns, revert names of main metrics
                for col in dfToUse.columns:
                    if col.endswith('_sncl2'):
                        dfToUse.drop([col], axis = 1, inplace = True)
                    elif col not in columnsToNotChange:
                        dfToUse.rename(columns={col : col.rsplit('_', 1)[0]}, inplace = True)
            
            
            else:
                if chType1 == chType2 == '':
                    df1 = dfToUse[met1+ "_"]
                    df2 = dfToUse[met2 + "_sncl2"]
                    
                    dfToUse = do_comparison(dfToUse, df1, operator, df2, doAbs1, doAbs2)
                    
                    # delete extra columns, revert names of main metrics
                    for col in dfToUse.columns:
                        if col.endswith('_sncl2'):
                            dfToUse.drop([col], axis = 1, inplace = True)
                        elif col not in columnsToNotChange:
                            dfToUse.rename(columns={col : col.rsplit('_', 1)[0]}, inplace = True)
                    
                else:
#                     if chType1 == chType2 == 'avg':
#                         if doAbs1:
#                             dfToUse[met1+ "_" + chType1] = dfToUse[met1+ "_" + chType1].abs()
#                         if doAbs2:
#                             dfToUse[met1+ "_" + chType2] = dfToUse[met1+ "_" + chType2].abs()
                    df1 = dfToUse[met1+ "_" + chType1]
                    df2 = dfToUse[met2 + "_" + chType2]
        
                    dfToUse = do_comparison(dfToUse, df1, operator, df2, doAbs1, doAbs2)
                    
                    # delete extra columns, revert names of main metrics
                    for col in dfToUse.columns:
                        if col.endswith('_' + chType2):
                            dfToUse.drop([col], axis = 1, inplace = True)
                        if col not in columnsToNotChange:
                            dfToUse.rename(columns={col : col.rsplit('_', 1)[0]}, inplace = True)
        
        dfToUse = dfToUse[dfToUse['channel'].str.endswith(ch1)]
        

        if fieldType == 'metric':
            chanMetricDF = dfToUse
        elif fieldType == 'metadata':
            chanMetaDF = dfToUse
        
        return chanMetricDF, chanMetaDF, "comparison"
#         return dfToUse, fieldType, "comparison"
    
    
        
    # Within a single threshold, there can be multiple instrument groups, so need to loop over each of those
    # But before we do, we need to do some organization to figure out what stations are specifically spelled
    # out, so they that they can be withheld from any potential "*" so that it's not doubled up

    threshDefs = thresholdDefDict[threshold]
    
    if metricDF.empty:
        if hasMetrics:
            return 

    for group in threshDefs.keys():

        # loop over each group in the threshold, and run them if we have included them in the preference file
        if group in instruments:
            instDef = threshDefs[group]
            
            # For every group, regenerate specificSNCLs
            specificSNCLs = []
            for instGroup in threshDefs.keys():
                if instGroup in instruments:
                    specificSNCLs.append(instrumentGroupsDict[instGroup])
            
            

            # remove this group from specificSNCLS, so that it doesn't compare against itself
            thisIdx = specificSNCLs.index(instrumentGroupsDict[group])
            del specificSNCLs[thisIdx]
            
            if (len(instDef) > 1) and any("average :: " in s for s in instDef):
                print("WARNING: thresholds with 'ratio' cannot have multiple parts, skipping")
                continue
            
            thisMetricDF = metricDF.copy()
            thisMetaDF = metaDF.copy()
            
            for net in instrumentGroupsDict[group]['network']:
                if net == "*" or net == "%" or net == "":
                    netMetricDF = thisMetricDF
                    netMetaDF = thisMetaDF
                    # If it can be any net, look at all other groups and make sure to remove any that might be specified
                    for idx, specificSNCL in enumerate(specificSNCLs):
                        if (not specificSNCL['network'] == ['*']):
                            # Then a network has been specified - work down the NSLC chain to remove specific targets
                            for net2 in specificSNCL['network']:
                                for sta2 in specificSNCL['station']:
                                    if sta2 == "*" or sta2=="%" or sta2=="":
                                        sta2 = ".*"
                                    for loc2 in specificSNCL['location']:
                                        if loc2 == "*" or loc2=="%" or loc2=="":
                                            loc2 = ".*"
                                        for cha2 in specificSNCL['channel']:
                                            if cha2 == "*" or cha2=="%" or cha2=="":
                                                cha2 = ".*"
                                                
                                            thisTarget = "%s\.%s\..*%s.*\..*%s.*\..*" % (net2, sta2, loc2, cha2)
                                            
                                            netMetricDF = netMetricDF[~netMetricDF['target'].str.contains(thisTarget,regex= True)] 
                                            netMetaDF = netMetaDF[~netMetaDF['target'].str.contains(thisTarget,regex= True)]
                            del specificSNCLs[idx]              
                else:
                    netMetricDF = thisMetricDF[thisMetricDF['network'] == net]
                    netMetaDF = thisMetaDF[thisMetaDF['network'] == net]
                    
                for sta in instrumentGroupsDict[group]['station']:
                    if sta == "*" or sta == "%" or sta == "":
                        staMetricDF = netMetricDF
                        staMetaDF = netMetaDF
                        for idx, specificSNCL in enumerate(specificSNCLs):
                            if (not specificSNCL['station'] == ['*']):
                                for sta2 in specificSNCL['station']:
                                    if sta2 == "*" or sta2=="%" or sta2=="":
                                        sta2 = ".*"
                                    for loc2 in specificSNCL['location']:
                                        if loc2 == "*" or loc2=="%" or loc2=="":
                                            loc2 = ".*"
                                        for cha2 in specificSNCL['channel']:
                                            if cha2 == "*" or cha2=="%" or cha2=="":
                                                cha2 = ".*"
                                                
                                            thisTarget = ".*\.%s\..*%s.*\..*%s.*\..*" % (sta2, loc2, cha2)
                                            staMetricDF = staMetricDF[~staMetricDF['target'].str.contains(thisTarget,regex= True)] 
                                            staMetaDF = staMetaDF[~staMetaDF['target'].str.contains(thisTarget,regex= True)] 
                                del specificSNCLs[idx]  
                    else:
                        staMetricDF = netMetricDF[netMetricDF['station'] == sta]
                        staMetaDF = netMetaDF[netMetaDF['station'] == sta]
                        
                    for loc in instrumentGroupsDict[group]['location']:
                        if loc == "*" or loc == "%" or loc == "":
                            locMetricDF = staMetricDF
                            locMetaDF = staMetaDF
                            
                            for idx, specificSNCL in enumerate(specificSNCLs):
                                if (not specificSNCL['location'] == ['*']):

                                    for loc2 in specificSNCL['location']:
                                        if loc2 == "*" or loc2=="%" or loc2=="":
                                            loc2 = ".*"
                                        for cha2 in specificSNCL['channel']:
                                            if cha2 == "*" or cha2=="%" or cha2=="":
                                                cha2 = ".*"
                                                
                                            thisTarget = ".*\..*\..*%s.*\..*%s.*\..*" % (loc2, cha2)#     
                                            
                                            locMetricDF = locMetricDF[~locMetricDF['target'].str.contains(thisTarget,regex= True)]
                                            locMetaDF = locMetaDF[~locMetaDF['target'].str.contains(thisTarget,regex= True)]
                                    del specificSNCLs[idx]
                            
                            
                            
                        else:
                            # some metrics compare two loc
                            locMetricDF = staMetricDF[staMetricDF['location'].str.contains(loc)]
                            locMetaDF = staMetaDF[staMetaDF['location'].str.contains(loc)]
                            
                         
                           
                        for chan in instrumentGroupsDict[group]['channel']:
                            if chan == "*" or chan =="%" or chan == "":
                                chanMetricDF = locMetricDF
                                chanMetaDF = locMetaDF
                                
                                for idx, specificSNCL in enumerate(specificSNCLs):
                                    if (not specificSNCL['channel'] == ['*']):

                                        for cha2 in specificSNCL['channel']:
                                            if cha2 == "*" or cha2=="%" or cha2=="":
                                                cha2 = ".*"
                                            thisTarget = ".*\..*\..*\..*%s.*\..*" % (cha2)  
                                            if hasMetrics:
                                                chanMetricDF = chanMetricDF[~chanMetricDF['target'].str.contains(thisTarget,regex=True)]
                                            chanMetaDF = chanMetaDF[~chanMetaDF['target'].str.contains(thisTarget,regex=True)]
                                        del specificSNCLs[idx] 
                                         
                            else:
                                # Note the .startswith() rather than .contains() - this is because HN? brought up BHN channels
                                # Checks indicate that this change is ok, but be aware that this MAY have other effects 
                                chanMetricDF = locMetricDF[locMetricDF['channel'].str.startswith(chan)]
                                chanMetaDF = locMetaDF[locMetaDF['channel'].str.startswith(chan)]
                            

                            # each definition may have multiple entries that need to be met. For each, check on what kind
                            # of definition it is, send it to the right place, then get the return to pass on to the next 
                            # part of the definition. This way we may have different 'types' of definitions within a 
                            # single definition.
                            for subDef in instDef:
                                itype = ""  # assign a dummy itype, mostly for the metadata-only thresholds    
                                if "average ::" in subDef:
                                    try:
                                        chanMetricDF, chanMetaDF, itype = average_threshold(chanMetricDF, chanMetaDF, subDef)
                                    except Exception as e:
                                        print("WARNING: Did not run because of %s" % e)
                                elif "median ::" in subDef:
                                    try:
                                        chanMetricDF, chanMetaDF, itype = median_threshold(chanMetricDF, chanMetaDF, subDef)
                                    except Exception as e:
                                        print("WARNING: Did not run because of %s" % e)
                                elif "/" in subDef.split():
                                    try:
                                        chanMetricDF, chanMetaDF, itype = ratio_threshold(chanMetricDF, chanMetaDF, subDef)
                                    except Exception as e:
                                        print("WARNING: Did not run because of %s" % e)
                                else:
                                    # Could be 3 situations: 
                                    # metric operator value - simple
                                    # metadata operator string - simple
                                    # metric/metadata operator/metadata metric - comparison
                                    # 
                                    try:
                                        try:
                                            fields = subDef.split()
                                            pos1 = fields[0].replace('abs(','').replace(')','').split('[')[0]
                                            pos2 = fields[1].replace('abs(','').replace(')','').split('[')[0]
                                            pos3 = fields[2].replace('abs(','').replace(')','').split('[')[0]
                                        except Exception as e:
                                            print("WARNING: could not split definition - %s" % e)   
                                            
                                        if (pos3 in metricList) or (pos3 in metadataList):
                                            chanMetricDF, chanMetaDF, itype  = compare_threshold(chanMetricDF, chanMetaDF, subDef)
#                                             quit("Stopping here to make sure it's working")
                                        else:
                                            chanMetricDF, chanMetaDF, itype = simple_threshold(chanMetricDF, chanMetaDF, subDef)

                                    except Exception as e:
                                        print("WARNING: Did not run because of %s" % e)
                                        # If it cannot run one part of the threshold definition, it should exit out of this script
                                        # and move onto the next threshold
                                        return


                            # At this point, we have two different dataframes that have been subsetted (or not, depending on the specifics)
                            # If within a single threshold, there are both mustang metrics AND metadata, then we need to make sure that the 
                            # two are in alignment
                            # Since any given threshold is an AND statement, any targets that have been eliminated from one must also be
                            # eliminated from the other. Metadata has no real day values, so it's just the targets that can be used. 
                            # If metrics are flagged for 3 days but the metadata for none, then none should be in the issue list
                            # If metrics are flagged for 3 days and the metadata is also flagged, then all three should be in the list
                            
                            #starting in a probably inefficient way and then can make it more efficient later
                            # First check to see if either are empty... if one is empty, then the end result should be empty!
                            
                            if hasMetrics == True:
                                if not itype == 'average':
                                    chanMetricDF['start'] = pd.to_datetime(chanMetricDF['start'])
                                    chanMetricDF['end'] = pd.to_datetime(chanMetricDF['end'])
                            
                                cols = chanMetricDF.columns
                                finalDF = pd.DataFrame(columns=cols)
                            
                                if chanMetricDF.empty or chanMetaDF.empty:
                                    continue
                                else:   # both of them have stuff in them
                                    # the metadata dataframe is probably going to be shorter (of course, maybe not)
                                    for index, row in chanMetaDF.iterrows():
                                        # The metadata dataframe will never have complex targets in it, so I need to allow for those
                                        complexTarget = "%s\.%s\..*%s.*\..*%s.*\.." % (row['network'], row['station'], row['location'], row['channel'])
                                        starttime = datetime.datetime.strptime(row['starttime'], '%Y-%m-%dT%H:%M:%S.%f')
                                        if pd.isnull(row['endtime']):
                                            endtime = datetime.datetime.now()
                                        else:
                                            endtime = datetime.datetime.strptime(row['endtime'], '%Y-%m-%dT%H:%M:%S.%f')
                                        thisSet = chanMetricDF[chanMetricDF['target'].str.contains(complexTarget,regex=True)]

                                        if 'new_target' in thisSet.columns:
                                            thisSet['target'] = thisSet['new_target']
#                                             thisSet.drop('new_target', axis = 1, inplace = True)
                                            
                                        if not itype == 'average':
                                            thisSet = thisSet[thisSet['start'] >= starttime]
                                            thisSet = thisSet[thisSet['end'] <= endtime]
                                        ## GET DATES FROM ROW AND SUBSET THISSET TO ONLY THOSE BETWEEN THOSE DATES!
                                        ## ALSO HANDLE THE CASE WHERE IT IS ONLY METADATA AND NO METRICS ARE EXPECTED... ADD IN AN IF CLAUSE?
                                        finalDF = pd.concat([finalDF, thisSet])
                                finalDF = finalDF.drop_duplicates(subset=['target','start','end'])
                                
                                issues = reportUtils.sortIssueFile(finalDF, threshold, itype)
                            else:
                                # If this threshold doesn't have any metrics anyway, then just convert the metadata dataframe into the finalDF format
                                issues = reportUtils.sortMetaFile(chanMetaDF, threshold)
                             
                             
                            reportUtils.writeToOutfile(issues, outfile)
                                    
    return
    
    