
## OSIsoft Summer 2019 Intern on Academic Hub 

### Info about JupyterLab

* JupyterLab user guide: https://jupyterlab.readthedocs.io/en/stable/user/interface.html


### Access to OCS / Academic Hub

1. **Send an email to Christian (cfoisy@osisoft.com) and Erica (etrump@osisoft.com) from your OSIsoft email**
2. You'll receive 2 email invites, one for OCS and another for Academic Hub. In each cases, click the link in the email to connect your account. 
3. Next time you log in, go to https://cloud.osisoft.com. Our Account Id is `osisoft-academia`

### Academic Hub / Beer Dataset 

#### Portals 

* Main Portal: https://academic.osisoft.com
* Data Portal: https://academic.osisoft.com/data-portal

#### Beer Dataset

1. Log into Data Portal: username / password : `reader0` / `OSIsoft2017`
2. Click green bar "Select Database" and pick `Food and Beverage`
3. Expand tree structure by clicking on small triangles on the left of tree elements: 
![Data Portal Beer](https://academicpi.blob.core.windows.net/images/data-portal-beer.png)

A subset of this dataset (fermenter vessels ID 31 up to 36) has been transfered on OCS into namespace `fermenter__vessels` (2 underscore characters). 



### Info about OCS

* Short online course: https://university.osisoft.com/series/all-offerings/ocs-for-support (note: you may not have access to all features due to the permissions on your user account)
* OCS code samples on Github: https://github.com/osisoft/OSI-Samples/tree/master/ocs_samples
* OCS API Documentation (full): https://ocs-docs.osisoft.com/
    
    * In our case we're gonna use only a subset of Sequential Data Store: https://ocs-docs.osisoft.com/Documentation/SequentialDataStore/Data_Store_and_SDS.html
    * But mainly the Data Views which are still in Preview (beta-level): https://ocs-docs.osisoft.com/Documentation/DataViews/DataViews_Overview.html
    
### Main development environment

* We run a private [JupyterHub](https://jupyterhub.readthedocs.io/en/stable/) which serves Jupyter notebooks for multiple users. All you need is a Github account and a web browser. **Send your Github handle to Christian to get access at https://jhub.academic.osisoft.com.**

* We have three active notebooks:

    * [Exercise/Solution "Beer Cooling Prediction"](./OCS_DV_Beer_Cooling_Solution_intern.ipynb): from solution notebook we extract the exercise one by selecting which parts students should fill in. This notebook is in Python only. 
    * ["Class Demo" ADF Prediction](./Dataviews_Demo-intern.ipynb): presented before Exercise/Solution to introduce concepts like REST API, Data Views. This notebooks mixes Python and R code. 
    * ["PI World Demo"](./Dataviews_PIWorld_2019.ipynb): notebook to be used in slideshow mode to demo Academic Hub to wider audience
   
* We also have a skeleton for a Data View portal. 
   
### Projects - in order of difficulty 

1. Familiarize yourself with Beer Cooling notebook. 

2. Add Set Point streams to Fermenter Vessel Data Views: each of Bottom, Middle and Top temperature sensor have an associated Set Point data stream. Find those streams and add it to the Data View

3. Modify and improve Data View portal skeleton to download data from actual data view instead of academic plug in. [Skeleton code](https://academicpi.blob.core.windows.net/public/DataviewPortal.zip)

4. Things to improve: overall presentation of concepts and code (e.g. the legacy code for Beer Cooling)

5. Transfer more interesting data from Beer dataset, expose new data through Data Views, give access to Data Views through new Data Portal 

6. Build new content from new dataset, e.g. UC Davis thermal storage 








