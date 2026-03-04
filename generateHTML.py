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


# Read in issues.csv and output the Network Report as an html file

import datetime
import urllib
import os
import shutil
import pandas as pd
import reportUtils

args = reportUtils.getArgs()
start = args.start
end = args.end


zipDir = args.htmldir
report_fullPath = args.html_file_path
iShort = 0
iBroad = 0
iStrong = 0

metricsFile = args.metrics_file
thresholdFile = args.thresholds_file
preferenceFile = args.preference_file

if not preferenceFile:
    quit("WARNING: Preference File required")

else:
    try:
        with open(preferenceFile) as f:
            exec(compile(f.read(), preferenceFile, "exec"))
    except:
        print("Cannot open ", preferenceFile)
        quit()
    if ("short period" in map(str.lower, instruments)) or (
        "shortperiod" in map(str.lower, instruments)
    ):
        iShort = 1
    if ("broad band" in map(str.lower, instruments)) or (
        "broadband" in map(str.lower, instruments)
    ):
        iBroad = 1
    if ("strong motion" in map(str.lower, instruments)) or (
        "strongmotion" in map(str.lower, instruments)
    ):
        iStrong = 1

if start == "" or end == "":
    pref_start, pref_end, subdir = reportUtils.calculate_dates(reportFrequency)
    if start == "":
        start = pref_start
    if end == "":
        end = pref_end

try:
    startDate = datetime.datetime.strptime(start, "%Y-%m-%d").strftime("%B %d, %Y")
    endDate = datetime.datetime.strptime(end, "%Y-%m-%d").strftime("%B %d, %Y")
    dates = [startDate, endDate]
except:
    print("ERROR: Are the dates properly formatted? YYYY-mm-dd")

    quit("")

try:
    with open(thresholdFile) as f:
        exec(compile(f.read(), thresholdFile, "exec"))

except Exception as e:
    print("WARNING: Cannot open thresholds File - %s" % e)

if args.network:
    network = args.network
if args.ticketsfile:
    csvfile = args.ticketsfile


if not os.path.isdir(zipDir):
    print("Creating new directory: %s" % zipDir)
    os.mkdir(zipDir)


infile = csvfile
print(infile)
if not os.path.isfile(infile):
    quit("Input csv file does not exist")


summaryFile = report_fullPath + ".summary"
detailFile = report_fullPath + ".detail"

#########################
# Define useful utilities
#########################


def printPreamble(net, dates, authors, email, outfile):
    # This prints the header of the html
    with open(outfile, "a+") as f:
        # print("Writing Header")
        f.write("<html>\n\n")
        f.write("    <head>\n")
        f.write(
            '\t<meta name=Title content="Data Quality Report for Network '
            + str(", ".join(net.split(",")))
            + " "
            + str(" - ".join(dates))
            + '">\n'
        )
        f.write(
            "\t<title>Data Quality Report for Network "
            + str(net)
            + " "
            + str(" - ".join(dates))
            + "</title>\n"
        )
        f.write("    </head>\n\n")

        f.write("    <body>\n\n")
        f.write(
            "\t<h1>Data Quality Report for " + str(", ".join(net.split(","))) + "</h1>"
        )
        f.write("\t<h2>    " + str(" - ".join(dates)) + "</h2>\n\n")

        f.write("\t    <i>" + str(authors) + "</i><br>\n")
        f.write("\t    <i>" + str(email) + "</i><br>\n")

        today = datetime.datetime.today().strftime("%B %d, %Y")
        f.write("\t    <i>Issued " + str(today) + "</i>\n\n")

    f.close()


def printFirstProject(project, summaryFile, detailFile):
    # Start the summary and detail files, which will be combined into one later
    with open(summaryFile, "a+") as f:
        f.write("\t    <h2>Summary</h2>\n\n")

        f.write(
            "\t    <p>Clicking on each issue Summary link takes you to a more detailed description of \n"
        )
        f.write(
            "\t       that issue, including the metrics used to identify the problem.</b>\n"
        )
        f.write("\t       Sorted by category, then station.\n")
        f.write("\t    </p>\n")
        f.write("\t    <p>\n")
        f.write("\t      <b>" + str(project) + "</b>\n\n")
        f.write("\t      <table>\n")
        f.write("\t        <tr>\n")
        f.write("\t          <td width=100><u>Category</u></td>\n")
        f.write("\t          <td width=200><u>Channel(s)</u></td>\n")
        f.write("\t          <td width=100><u>Status</u></td>\n")
        f.write("\t          <td width=125><u>Start Date</u></td>\n")
        f.write("\t          <td width=400><u>Summary</u></td>\n")
        f.write("\t        </tr>\n")
    f.close()

    with open(detailFile, "a+") as f:
        f.write("\t    <h2>Details</h2>\n\n")
        f.write(
            "\t    <p>Detailed description of the issues. Sorted by station, with resolved issues at bottom</p> \n"
        )
    f.close()


def PrintNextProject():
    # Necessary only if there is more than one network in the report
    with open(summaryFile, "a+") as f:
        f.write("\t      </table>\n")
        f.write("\t    </p>\n\n")
        f.write("\t    <p>\n")
        f.write("\t      <b>" + str(project) + "</b>\n\n")
        f.write("\t      <table>\n")
        f.write("\t        <tr>\n")
        f.write("\t          <td width=100><u>Category</u></td>\n")
        f.write("\t          <td width=200><u>Channel(s)</u></td>\n")
        f.write("\t          <td width=100><u>Status</u></td>\n")
        f.write("\t          <td width=125><u>Start Date</u></td>\n")
        f.write("\t          <td width=400><u>Summary</u></td>\n")
        f.write("\t        </tr>\n")

    f.close()

    with open(detailFile, "a+"):
        f.write("\t    <b>" + str(project) + "</b>\n\n")

    f.close()


def printTicketSummary(inum, category, sncl, status, start, summary, summaryFile):
    # Create a summary for the top of the final report, initially created separately
    if status == "New":
        status = "Open"
    with open(summaryFile, "a+") as f:
        f.write("\t        <tr>\n")
        f.write("\t          <td width=100>" + str(category) + "</td>\n")
        f.write(
            "\t          <td width=200>"
            + str(sncl).replace(" ", ".").replace("--", "")
            + "</td>\n"
        )
        f.write("\t          <td width=100>" + str(status) + "</td>\n")
        f.write("\t          <td width=150>" + str(start) + "</td>\n")
        f.write(
            '\t          <td width=400><a href="#'
            + str(inum)
            + '">'
            + str(summary)
            + "</a></td>\n"
        )
        f.write("\t        </tr>\n")
    f.close()


def closeSummary():
    # Wrap up the summary file
    with open(summaryFile, "a+") as f:
        f.write("\t    </table>\n\n")
    f.close()


def printTicketDetails(
    inum,
    snclq,
    start,
    subject,
    thresholds,
    description,
    imageurl,
    imagecaption,
    status,
    end,
    link,
    detailFile,
):
    # Create the detailed report, the meat of the final report. Initially created separately
    #     global iFlag
    with open(detailFile, "a+") as f:
        if start == "":
            start = "(Start not identified)"
        if status == "New":
            status = "Open"
            f.write(
                '\t    <p><a name="'
                + str(inum)
                + '"><b><i>'
                + str(snclq).replace(" ", ".").replace("--", "")
                + " "
                + str(subject)
                + " -- "
                + str(start)
                + "</i></b></a><br>\n"
            )
        else:
            f.write(
                '\t    <p><a name="'
                + str(inum)
                + '"><b><i>'
                + str(snclq)
                + " "
                + str(subject)
                + " -- "
                + str(start)
                + " to "
                + str(end)
                + " </i></b></a><br>\n"
            )
        f.write('\t      <font color="black">STATUS: ' + str(status) + "</font><br>\n")
        f.write('\t      <font color="green">Thresholds: </font>\n')
        f.write('\t      <font color="black">' + str(thresholds) + "</font>\n")
        f.write('\t      <a href="#thresh">(what is this?)</a><br>\n')
        f.write("\t      " + str(str(description).replace("\n", "<br>")) + "\n")
        f.write("\t    <p></p>\n")

        links = link.split(";;;;")
        if not links == [""]:
            f.write("\t    Links:<br>")
            for thisLink in links:
                f.write(
                    '\t      <a href="'
                    + thisLink
                    + '" target="_blank">'
                    + thisLink
                    + "</a>"
                )
                f.write("<br>")

        if not imageurl == "":
            images = imageurl.split(";;;;")
            captions = imagecaption.split(";;;;")
            nImages = len(images)

            for image_number in range(nImages):
                thisImage = images[image_number]
                thisCaption = captions[image_number]
                printTicketDetails.iFlag = 1
                imgfile = "%s_%s.png" % (inum, image_number)

                try:

                    try:
                        shutil.copyfile(thisImage, zipDir + "/" + imgfile)
                    except:
                        urllib.request.urlretrieve(thisImage, zipDir + "/" + imgfile)

                    gotPhoto = 1
                except:
                    print("WARNING: Unable to retrieve image: %s" % thisImage)
                    gotPhoto = 0

                f.write("\t    <p></p>\n")

                if gotPhoto == 1:
                    if not thisCaption == "":
                        f.write("\t    " + str(thisCaption) + ":<br>\n")
                    f.write('\t    <a href="./' + str(imgfile) + '">\n')
                    f.write(
                        '\t        <img src="'
                        + str(imgfile)
                        + '" style="border: 1px solid #000; max-width:75%;">\n'
                    )
                    f.write("\t    </a>\n")
                f.write("\t    <p></p>\n")

        f.write('\t       <a href="#top">(Top)</a>\n')
        f.write("\t    </p>\n\n")

    f.close()


def closeHTML():
    with open(metricsFile, "r") as f:
        metricsList = f.read().splitlines()

    nCol = 4

    # Wrap up the final report
    with open(report_fullPath, "a+") as f:
        f.write('\t    <a name="diag"><h2>Diagnostics</h2></a>\n')
        f.write(
            "\t    <p>The links below take you to the metrics and other data quality tools used to identify the data issues in this report.\n"
        )
        f.write("\t    </p>\n\n")

        f.write(
            '\t    <p><a href="https://service.earthscope.org/mustang/measurements/1">MUSTANG measurement service metrics:</a>\n'
        )
        f.write("\t    <table>\n")
        f.write("\t        <tr>\n")

        # Use the metrics file (which is updated when connected to the internet) to write out most current list of metrics
        ii = 0
        for metric in metricsList:
            f.write("\t            <td>%s</td>\n" % metric)
            if ii % nCol == 0:
                f.write("\t        </tr>\n")
                f.write("\t        <tr>\n")
            ii += 1
        f.write("\t        </tr>\n")
        f.write("\t    </table>\n")
        f.write("\t    </p>\n")

        f.write(
            '\t    <p><a href="https://service.earthscope.org/mustang/noise-psd/1" target="_blank" >MUSTANG noise-psd service</a></p>\n'
        )
        f.write(
            '\t    <p><a href="https://service.earthscope.org/mustang/noise-pdf/1" target="_blank">MUSTANG noise-pdf service</a></p>\n'
        )
        f.write(
            '\t    <p><a href="https://service.earthscope.org/mustang/noise-mode-timeseries/1" target="_blank">MUSTANG noise-mode-timeseries service</a></p>\n'
        )
        f.write(
            '\t    <p><a href="http://ds.iris.edu/data_available/" target="_blank">GOAT/data_available</a></p>\n'
        )
        for net in network.split(","):
            net = net.strip()
            f.write(
                '\t    <p><a href="http://ds.iris.edu/mda/%s" target="_blank">Metadata Aggregator for %s</a></p>\n'
                % (net, net)
            )
        f.write(
            '\t    <p><a href="http://ds.iris.edu/servlet/budstat/topLevel.do?source=BUD" target="_blank">BUD stats</a></p>\n'
        )
        f.write(
            '\t    <p><a href="http://ds.iris.edu//SeismiQuery/index.html" target="_blank">SeismiQuery</a></p>\n'
        )

        # Loop over the thresholds dictionary to print the definitions for instrument groups that are being used.
        f.write('\t    <a name="thresh"><h2>Thresholds</h2></a>\n')
        f.write(
            "\t    <p>Thresholds used to identify potential data issues for this report were:\n"
        )
        f.write("\t    </p>\n\n")

        for thresholdName in sorted(thresholdsDict.keys()):
            f.write("<DL>")
            f.write("<DT><b>%s</b>" % thresholdName)

            for instrumentGroup in thresholdsDict[thresholdName].keys():

                if instrumentGroup in instruments:
                    defStr = " && ".join(thresholdsDict[thresholdName][instrumentGroup])

                    f.write("<DD><i>%s - </i>    %s<br>" % (instrumentGroup, defStr))

            f.write("</DL")

            f.write("\t   </ul>\n\n")

        f.write("\t</body>\n\n")
        f.write("<html>\n")

    f.close()


######################
# Create the Report


try:
    printPreamble(network, dates, author, email, report_fullPath)

    # lastProject is used in case more than one network is included in the same report
    iFirst = 1
    lastProject = ""

    # Create an empty dataframe to be filled by the csv file - not loading directly
    # because of the complcated description section
    issueDF = pd.read_csv(infile).fillna("")

    # The summary should be sorted by category
    summaryDF = issueDF.copy().sort_values(by=["category", "target"])

    printFirstProject(project, summaryFile, detailFile)
    for index, row in summaryDF.iterrows():

        printTicketSummary(
            row["id"],
            row["category"],
            row["target"],
            row["status"],
            row["start_date"],
            row["subject"],
            summaryFile,
        )

    # The detailed portion should be sorted by sncl
    detailDF = issueDF.copy()
    detailDF["Status"] = pd.Categorical(
        detailDF["status"], ["New", "In Progress", "Closed", "Resolved", "Rejected"]
    )
    detailDF = detailDF.sort_values(by=["Status", "target"])

    for index, row in detailDF.iterrows():

        printTicketDetails(
            row["id"],
            row["target"],
            row["start_date"],
            row["subject"],
            row["thresholds"],
            row["description"],
            row["images"],
            row["caption"],
            row["Status"],
            row["end_date"],
            row["links"],
            detailFile,
        )

    closeSummary()

    # Combine the summary and detail files into one
    filenames = [summaryFile, detailFile]
    with open(report_fullPath, "a+") as ofile:
        for fname in filenames:
            with open(fname) as infile:
                ofile.write(infile.read())

    closeHTML()

    # Remove the temporary summary and detail files
    os.remove(summaryFile)
    os.remove(detailFile)

    # If we have images, make a new directory with all images and files, and zip
    # print(printTicketDetails.iFlag)
    try:
        printTicketDetails.iFlag
    except:
        pass
    else:
        files = os.listdir(directory)

        shutil.make_archive(zipDir, "zip", zipDir)

    with open("generateHTML_status.txt", "w") as f:
        f.write("")
        print("Completed HTML report")

except Exception as e:
    with open("generateHTML_status.txt", "w") as f:
        f.write("%s" % e)

    print("Error while generating HTML report")
