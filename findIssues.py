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


import reportUtils
import thresholds
import os
import pandas as pd


# TODO: If ts_ metrics are used, must propagate through into the thresholds file

# ============================#
# LOAD INPUT ARGUMENTS
network = ""
station = ""
location = ""
channels = ""
start = ""
end = ""
outfile = ""

args = reportUtils.getArgs()
start = args.start
end = args.end
# month = args.month

preferenceFile = args.preference_file

if not preferenceFile:
    # If no preference file included, run everything
    thresholdGroups = [
        "Completeness",
        "Amplitudes",
        "Timing",
        "State of Health",
        "Metadata",
    ]
    groupsDict = {
        "Completeness": ["avgGaps", "gapsRatioGt12", "noData"],
        "Amplitudes": [
            "flat",
            "lowRms",
            "hiAmp",
            "lowAmp",
            "badResp",
            "avgSpikes",
            "pegged",
            "dead",
            "noise1",
            "noise2",
            "medianUnique",
            "rmsRatio",
            "xTalk",
            "gainRatio",
            "nonCoher",
            "polarity",
            "dcOffsets",
            "nSpikes",
            "rmsRatio",
        ],
        "Timing": ["poorTQual", "suspectTime", "noTime"],
        "State of Health": [
            "ampSat",
            "filtChg",
            "clip",
            "spikes",
            "glitch",
            "padding",
            "tSync",
        ],
        "Metadata": ["zDip", "horDip", "zeroZ", "lowScale", "nonMSUnits"],
    }

else:
    try:
        with open(preferenceFile) as f:
            exec(compile(f.read(), preferenceFile, "exec"))
    except OSError:
        print("Cannot open", preferenceFile)
        quit()

# Commandline arguments override preference file values, if provided
if args.network:
    network = args.network
if args.stations:
    station = args.stations
if args.locations:
    location = args.locations
if args.channels:
    channels = args.channels
if args.outfile:
    outfile = args.outfile
if args.metricsource:
    metricSource = args.metricsource
if args.metadatasource:
    metadataSource = args.metadatasource
if args.metadata_file:
    metadata_file = args.metadata_file
if args.metrics_file:
    metrics_file = args.metrics_file
if args.thresholds_file:
    thresholdFile = args.thresholds_file
else:
    print("WARNING: No threshold file provided. Exiting.")
    quit()


directory = os.path.dirname(outfile)

if not directory:
    print("No path provided for issue file, exiting")
    quit()

if not os.path.exists(directory):
    print("Creating directory: " + directory)
    os.makedirs(directory)


if os.path.isfile(outfile):
    resp1 = input("This file already exists - overwrite?[y/n]:  ")
    if (resp1.upper() == "Y") or (resp1.upper() == "YES"):
        print("Removing existing file")
        os.remove(outfile)

    elif (resp1.upper() == "N") or (resp1.upper() == "NO"):
        resp2 = input("Should I append to the existing file?[y/n]: ")
        if (not resp2.upper() == "Y") and (not resp2.upper() == "YES"):
            quit("Exiting")
    else:
        print("Input not recognized, cancelling")
        quit()

# Load up list of metrics and metadata, for reference later on
if os.path.isfile(metrics_file):
    with open(metrics_file, "r") as f:
        metricsList = f.read().splitlines()
else:
    # This should not happen unless running outside of QuARG since QuARG.py has a check before running findIssues.py
    print(
        "WARNING: Could not find list of MUSTANG metrics in file %s - does it exist?"
        % metrics_file
    )
    print(
        "         You can create this list by entering the Thresholds Editor - it will automatically generate there"
    )
    quit()

if os.path.isfile(metadata_file):
    with open(metadata_file, "r") as f:
        metadataList = f.read().splitlines()
else:
    # This should not happen unless running outside of QuARG since QuARG.py has a check before running findIssues.py
    print(
        "WARNING: Could not find list of EarthScope metadata fields in file %s - does it exist?"
        % metadata_file
    )
    print(
        "         You can create this list by entering the Thresholds Editor - it will automatically generate there"
    )
    quit()


# ============================#
# GO THROUGH THRESHOLDS

# Add the header to the file
with open(outfile, "w") as f:
    f.write("# Threshold|Target|Start|End|Ndays|Status|Value|Notes\n")
f.close()

# Get metadata dataframe at the beginning to use wherever necessary, since it is always the same
metadataDF = reportUtils.getMetadata(
    network, station, location, channels, start, end, metadataSource
)


failedMetricsAll = list()
failedThresholdsAll = list()
for thresholdGroup in thresholdGroups:
    print()
    print("Running %s Thresholds" % thresholdGroup)
    try:
        thresholdsList = list(set(groupsDict[thresholdGroup]))
    except:
        print("   Could not find any thresholds for %s" % thresholdGroup)
        continue

    thresholdsList.sort()

    allMetrics, failedThresholds = thresholds.get_threshold_metrics(
        thresholdsList, thresholdFile
    )
    metadatas = [e for e in metadataList if e in allMetrics]
    metrics = [e for e in metricsList if e in allMetrics]

    hasMetrics = False
    if len(metrics) > 0:
        hasMetrics = True

    if hasMetrics:
        metricDF, failedMetrics = reportUtils.mergeMetricDF(
            network, station, location, channels, start, end, metrics, metricSource
        )
    else:
        metricDF = pd.DataFrame(
            columns=[
                "value",
                "target",
                "start",
                "end",
                "network",
                "station",
                "location",
                "channel",
            ]
        )
        failedMetrics = list()

    for failedThreshold in failedThresholds:
        if not failedThreshold in failedThresholdsAll:
            failedThresholdsAll.append(failedThreshold)

    for failedMetric in failedMetrics:
        if not failedMetric in failedMetricsAll:
            failedMetricsAll.append(failedMetric)

    for threshold in thresholdsList:
        if not threshold in failedThresholds:
            thresholds.do_threshold(
                threshold,
                thresholdFile,
                metricDF,
                metadataDF,
                outfile,
                instruments,
                start,
                end,
                hasMetrics,
                chanTypes,
            )

with open("failedMetrics.txt", "w") as f:
    for failedThreshold in failedThresholdsAll:
        f.write("threshold: %s\n" % failedThreshold)
    for failedMetric in failedMetricsAll:
        f.write("metric: %s\n" % failedMetric)

print("INFO: Completed generating issue file")
