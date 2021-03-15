# QuARG

#### Questions or comments can be directed to the IRIS DMC Quality Assurance Group at <a href="mailto:dmc_qa@iris.washington.edu">dmc_qa@iris.washington.edu</a>.
For detailed documentation, check out [iris-edu.github.io/quarg/](https://iris-edu.github.io/quarg/DOCUMENTATION.html)  
<br />

QuARG, the Quality Assurance Report Generator, is a Python client that allows network operators to generate quality assurance (QA) reports from start to finish. These reports utilize IRIS’s database of [MUSTANG](http://service.iris.edu/mustang/) data quality metrics to find and highlight potential issues in the data, reducing the amount of time that analysts need to spend scanning the data for problems. 

Over the years that IRIS has been producing Quality Assurance Reports,  we have refined the process of generating a report into four primary steps:

*	Find potential issues by utilizing MUSTANG metrics
*	Examine all potential issues
*	Ticket any true problems
*	Generate a final report derived from the open or existing tickets

The QuARG utility follows this same workflow to help guide users through the process from start to finish. 
<br /> 

Users have the ability to customize QuARG to adapt to their particular network.  Some features that can be personalized:  

* Add, edit, or remove Thresholds based on what best fits the network instrumentation.
* Group instrumentation by Network, Station, Locations, or Channels, defining thresholds individually for each group. 
* Use metric values sourced from either IRIS or a local ISPAQ database. Similarly, locally-sourced or IRIS-provided metadata.
* Create preference files to minimize the number of fields that users need to input, easily track what thresholds were used to find issues, and potentially create a series of files to be utilized for different use-cases within a network.  An example file preference_file_IRIS.py is provided in the base quarg directory. 
* Use the built-in ticketing system or an external one, whichever works better for your workflow. 

This utility guides users through the process of generating a list of potential issues, examining and tracking issues, and generating a report.  

An example report:
<p align="center">
<img src="https://github.com/iris-edu/quarg/blob/main/docs/figures/ExampleReport.png" width="500">
</p>


For more detailed documentation, see https://iris-edu.github.io/quarg/
<br /> 

# Installation

QuARG can be installed on Linux and macOS.  

QuARG is distributed through _GitHub_, via IRIS's public repository (_iris-edu_). You will use a ```git``` 
client command to get a copy of the latest stable release. In addition, you will use the ```miniconda``` 
python package manager to create a customized Python environment designed to run QuARG properly.

If running macOS, Xcode command line tools should be installed. Check for existence and install if 
missing:
```
xcode-select --install
```

Follow the steps below to begin running QuARG.

### Download the Source Code

You must first have ```git``` installed your system. This is a commonly used source code management system
and serves well as a mode of software distribution as it is easy to capture updates. See the 
[Git Home Page](https://git-scm.com/) to begin installation of git before proceeding further.

After you have git installed, you will download the QuARG distribution into a directory of your choosing 
from GitHub by opening a text terminal and typing:

```
git clone https://github.com/iris-edu/quarg.git
```

This will produce a copy of this code distribution in the directory you have chosen. When new quarg versions 
become available, you can update QuARG by typing:

```
cd quarg
git pull origin main
```

### Install the Anaconda Environment

[Anaconda](https://www.anaconda.com) is quickly becoming the *defacto* package manager for 
scientific applications written python or R. [Miniconda](http://conda.pydata.org/miniconda.html) is a trimmed 
down version of Anaconda that contains the bare necessities without loading a large list of data science packages 
up front. With miniconda, you can set up a custom python environment with just the packages you need to run QuARG.

Proceed to the [Miniconda](http://conda.pydata.org/miniconda.html) web site to find the installer for your
operating system before proceeding with the instructions below. If you can run ```conda``` from the command 
line, then you know you have it successfully installed.

By setting up a [conda virtual environment](https://conda.io/projects/conda/en/latest/user-guide/concepts.html#conda-environments), we assure that our 
QuARG installation is entirely separate from any other installed software.


### Creating the quarg environment for macOS or Linux

You will go into the quarg directory that you created with git, update miniconda, then create an 
environment specially for QuARG. You have to ```activate``` the quarg environment whenever you 
perform installs, updates, or run QuARG.

```
cd quarg
conda update conda
conda create --name quarg -c conda-forge --file quarg-conda-install.txt
conda activate quarg
```

See what is installed in our (quarg) environment with:

```
conda list
```
<br /> 
Every time you use QuARG, make sure that you `conda activate quarg` to ensure that it will run smoothly. 

<br /> 

### Using QuARG 

Every time you use QuARG you must ensure that you are running in the proper Anaconda
environment. If you followed the instructions above you only need to type:

```
cd quarg
conda activate quarg
```

after which your prompt should begin with ```(quarg) ```. To run QuARG, you use the ```QuARG.py``` 
python script that lives in the quarg directory. The example below shows how to get the QuARG GUI to start up.  A leading ```./``` 
is used to indicate that the script is in the current directory.

```
(quarg) bash-3.2$ ./QuARG.py
```

or

```
(quarg) bash-3.2$ python QuARG.py
```
<br /> 

## More Information
Detailed documentation can be found here:  [iris-edu.github.io/quarg/](https://iris-edu.github.io/quarg/DOCUMENTATION.html)

Within QuARG, a simple overview of the program can be found in the "Help" tab. In addition, there is a file called DOCUMENTATION.html in the Documentation directory that has much more detailed information about using QuARG - the same information as iris-edu.github.io/quarg/ listed above - which can be accessed through the Help Tab within QuARG as well. 

