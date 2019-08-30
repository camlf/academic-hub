# OSIsoft Academic Hub host Deschutes Brewery Dataset!
___

![Hub Overview](https://academichub.blob.core.windows.net/images/Nav_markdown_hub-overview.png)

OSIsoft Academic Hub is a cloud-based platform that supports data analytics for classroom education in Universities. Part of what we do is we host course contents made based on the real data shared from Deschutes Brewery. The Deschutes Brewery dataset represents the process data collected during their beer-making process, compiled from January 2, 2016 to January 1, 2017. Deschutes brewers have identified the critical process parameters that can have significant impact on their organizational performance. In the learning modules, students will visualize, analyze, and apply data analytics on the brewing process data that reflect the real-world problems.

The learning modules are presented in the students’ private environment in [Jupyterlab]( https://jupyterlab.readthedocs.io/en/stable/getting_started/overview.html). This guide help navigating through different notebooks that suit your interest, while providing a hint of what each notebook contains. To navigate to the learning modules, tutorials, or dataset document, click the hyper-linked title of the part to direct to and explore the notebook instantly.


---

# Overview:

__Part 1. Learning modules:__

There are three different learning modules, encompassing the topic that the Deschutes brewer identified as critical to their process optimization. Deschutes brewers optimizing these parametes saved $750K in capital investment and reduced production time loss. By exercising the learning modules, students solve the process analysis problems that reflect real-world industry challenges.

1a. [Apparent Degree of Fermentation notebook](#section_1a)

1b. [Beer Cooling Prediction notebook](#section_1b)

1c. [Principal Component Analysis notebook](#section_1c)



__Part 2. Tutorials and dataset document:__


Alongside, the dataset document and tutorials are provided covering the fundamental and the complementary concepts that students should have the understanding of for the learning modules.

2a. [Dataset Document Notebook](./2019-08-03_Dataset_documentation_ver0.48AS.ipynb)


2b. [Pandas tutorial](./Tutorial_AS/PandasGuide_0528_AS_rev2.ipynb) 

2c. [Dataview tutorial](./2019-07-15_Dataviews_demo_tutorial_ver0.48.ipynb)


---

## Learning modules

### Part 1a. [Apparent Degree of Fermentation notebook]():

In this learning module, students will analyze the Apparent Degree of Fermentation (ADF) during the beer-making process, which is a critical process parameter that inform brewers how much of batch has fermented over time. Brewers use this parameter to make a shift from fermentation phase to free rise phase. Through this exercise, students will learn how to build the predictive linear, and predictive piecewise linear model on ADF.

<a id="section_1a">

![ADF Prediction](https://academicpi.blob.core.windows.net/images/NB1_Analyze_Fit.png)

</a>

---

### Part 1b. [Beer Cooling Prediction notebook]():

Consistent cooling temperature profile of every batch is directly related to the quality of beer production. During the cooling phase of the brewing process, the temperature of the solution in the fermenter drops from 70°F to 30°F. In the learning module of Beer Cooling Prediction, students will visualize and analyze the data, and will build the predictive model of the cooling temperature. 

<a id="section_1b">

![Beer Cooling Prediction](https://academicpi.blob.core.windows.net/images/NB2_Cooling_Prediction.png)

</a>

---

### Part 1c. [Principal Component Analysis notebook]():


Principal Component Analysis is a statistical technique that compresses the dimensionality of large datasets to a few Principal Components to represent the data. In the learning module, students use PCA to determine the anomalous production batch, and the contributing factors for such deviation behavior. 

<a id="section_1c">

![Principal Component Analysis](https://academicpi.blob.core.windows.net/images/NB3_PCA_plot.png)

</a>

---

### Part 2a. [Dataset Document Notebook](./2019-08-03_Dataset_documentation_ver0.48AS.ipynb):

The primary purpose of the dataset document was to provide students the basic understanding of Deschutes brewery dataset, including both straight-forward description and counter-intuitive concepts as non-Computer Science students. The dataset document entails the summary of Deschutes dataset and the data quality. It also includes counter-intuitive topics such as config. Ini file, stream data, and Dataview. It is recommended to look into the dataset document before exploring the learning modules.

<a id="section_2a">

![Dataset Document Notebook](https://academichub.blob.core.windows.net/images/Nav_markdown_dataset.PNG)

</a>

---

### Part 2b. [Pandas Guide](./Tutorial_AS/PandasGuide_0528_AS_rev2.ipynb):

Pandas is a popular data analysis library that simplistically written for data manipulation and data store in the dataframe structure. For these uses, Pandas is frequently used in the learning modules. The Pandas guide look into the concept of Pandas, and simple Pandas operation used in the learning modules.

<a id="section_2b">

![Pandas Guide](https://academichub.blob.core.windows.net/images/Nav_markdown_pandas_guide.PNG)

</a>

---

### Part 2c. [Dataview tutorial](./2019-07-15_Dataviews_demo_tutorial_ver0.48.ipynb):

Dataview is a data display tool that map and group the data into the desired table format. Likewise, Dataview is used to select the process parameters or any desired variables which are easily retrieved upon executing the Dataview function. Also, Dataview allows to group multiple fermenters and easily request their data with the selected parameters. This Dataview tutorial inform about the concept of Dataview and about the instruction on using the essential dataview functions.


<a id="section_2c">


![Dataview tutorial](https://academichub.blob.core.windows.net/images/Nav_markdown_dataview_tutorial.PNG)
                  
</a>

---

