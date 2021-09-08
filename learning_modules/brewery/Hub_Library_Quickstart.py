#!/usr/bin/env python
# coding: utf-8

# # OSIsoft Academic Hub Library Quick Start
# 
# Version 0.97
# 
# Academic Hub datasets are hosted by the OSIsoft Cloud Service (OCS, https://www.osisoft.com/solutions/cloud/vision/), a cloud-native realtime data infrastructure to perform enterprise-wide analytics using tools and languages of their choice. 
# 
# **Raw operational data has specific characteristics making it difficult to deal with directly**, among them:
# 
# * variable data collection frequencies
# * bad values (system error codes)
# * data gaps 
# 
# 
# **But data science projects against operational data needs to be:**
# 
# * **Time-aligned** to deal with the characteritics above in consistent way according to the data type (e.g. interpolation for float values, repeat last good value for categorical data, etc)
# * **Context aware** so that the data can be understandable, across as many real-world assets that you need it for
# * **Shaped and filtered** to ensure you have the data you need, in the form you need it
# 
# **OCS solution for application-ready data are Data Views:**
# 
# ![](https://academichub.blob.core.windows.net/images/piworld-dse-dataview-p2.png)
# 
# **Each Academic Hub datasets comes endowed with a set of asset-centric data views.** The goal of Academic Hub Python library is to allow in a very generic and consistent way to access:
# 
# * the list of existing datasets
# * for a given dataset: 
#   * get the list of its assets
#   * get the OCS namespace where the dataset is hosted
# * for a given asset, get the list data views it belongs to
# 
# The rest of this notebook is a working example of the functionality listed above. 

# ## Install Academic Hub Python library 

# In[1]:


# get_ipython().system('pip install ocs-academic-hub==0.99.2')


# ## Use the `pip uninstall` only in case of library issues

# In[2]:


# It's sometimes necessary to uninstall previous versions, uncomment and run the following line. Then restart kernel and reinstall with previous cell
# !pip uninstall -y ocs-academic-hub ocs-sample-library-preview

# WARNING: uncomment only for testing
#%env OCS_HUB_CONFIG=config.ini


# ## Import HubClient, necessary to connect and interact with OCS

# In[3]:


from ocs_academic_hub import HubClient


# ## Running the following cell initiate the login sequence
# 
# **Warning:** a new brower tab will open offering the choice of identifying with Microsoft or Google. You should always pick Google:
# <img src="https://academichub.blob.core.windows.net/images/ocs-login-page-google.png" alt="Login screen" width="600"/>
# 
# Return to this web page when done

# In[4]:


hub = HubClient()


# ## Get list of published hub datasets
# 

# In[5]:


hub.datasets()


# ## Display current active dataset
# 
# NOTE: it will be possible to switch it once other datasets support the new asset interface. 

# In[6]:


hub.current_dataset()


# ## Get list of assets with Data Views
# 
# Returned into the form of a pandas dataframe, with column `Asset_Id` and `Description`. The cell above with `print` and `.to_string()` allows to see the whole dataframe content. 

# In[7]:


print(hub.assets().to_string())


# ## List of all Data Views
# 
# Those are all single-asset default (with all data available for the asset) Data Views

# In[8]:


hub.asset_dataviews()


# ## List of Data Views exclusive to Fermenter Vessel #32 (FV32)
# 
# Empty filter (`filter=""`) allows to see all dataviews for the asset instead of simply the default one

# In[9]:


dvs_fv32 = hub.asset_dataviews(asset="FV32", filter="")
dvs_fv32


# ## List Multi-Asset Data Views Containing FV32
# 
# The column `Asset_Id` in data view results indicates which asset the row of data belongs to 

# In[10]:


hub.asset_dataviews(asset="FV32", multiple_asset=True, filter="")


# ## Get the OCS namespace associated to the dataset
# 
# Each data set belongs to a namespace within the Academic Hub OCS account. Since dataset may move over time, the function below always return the active namespace for the given dataset. 

# In[11]:


dataset = hub.current_dataset()
namespace_id = hub.namespace_of(dataset)
namespace_id


# ## Get Data View structure
# 
# With Stream Name, the column name under which stream data appears, its value type and engineering units if available. We display below the structure of the default data view. 

# In[12]:


dataview_id = hub.asset_dataviews(asset="FV32", filter="default")[0]
print(dataview_id)
print(hub.dataview_definition(namespace_id, dataview_id).to_string(index=False))


# ## Getting data from a Data View
# 
# Return interpolated data between a start and end date, with the requested interpolation interval (format is HH:MM:SS)

# In[13]:


# Use the first commented out line to access a full 3-year worth of data
# df_fv32= hub.dataview_interpolated_pd(namespace_id, dataview_id, "2017-01-19", "2020-01-19", "00:30:00")
# 
# This next line is for a single month of data
df_fv32= hub.dataview_interpolated_pd(namespace_id, dataview_id, "2017-01-19", "2017-02-19", "00:30:00")
df_fv32


# In[14]:


# Information about the dataframe - this is a Pandas operation 
df_fv32.info()


# ## Data Views with multiple assets
# 
# Some Data Views return data for fermenter vessels 31 up to 36. Cell below is how to get their names. 

# In[15]:


multi_asset_dvs = hub.asset_dataviews(multiple_asset=True)
multi_asset_dvs


# ## Get result
# 
# The column "Asset_Id" indicates which asset the data row belongs to. The data order is all data for FV31 in increasing time, followed by FV32 and so on up to FV36. 
# 

# In[16]:


df_fv31_36 = hub.dataview_interpolated_pd(namespace_id, multi_asset_dvs[1], "2017-02-01", "2017-03-01", "00:30:00")
df_fv31_36


# In[17]:


df_fv31_36.info()


# ## Change datasets
# 
# As seen above, the other available dataset is `Campus_Energy`. 

# In[18]:


hub.set_dataset("Campus_Energy")


# ## Verify that it's now the current dataset

# In[19]:


hub.current_dataset()


# ## Update the namespace Id 
# 
# It can be different from dataset to dataset 

# In[20]:


namespace_id = hub.namespace_of(hub.current_dataset())
namespace_id


# ## Assets of new dataset 

# In[21]:


print(hub.assets().to_string(index=False))


# ## Data view discovery and interpolation data methods are the same
# 
# The difference is that for `Campus_Energy` dataset, the default data view is the same as the `-electricity` data view. The reason is that the `electricity` data view is the only one which is common to all buildings. The `chilled_water` and `steam` data views are optional. Please consult the `Campus_Energy` dataset documentation for details. 

# ## Refresh datasets information (experimental)
# 
# When new datasets are published and/or existing ones are extended, you can access the updated information using `refresh_datasets`. 
# 
# Note: after execution of this method, a file named `hub_datasets.json` will be created in the same directory as this notebook. The data in this file supersedes the one built-in with the `ocs_academic_hub` module. To get back to the built-in datasets information, move/rename/delete `hub_datasets.json`.  

# In[22]:


hub.refresh_datasets()


# In[23]:


hub.current_dataset()

