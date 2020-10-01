cp ../../../../jhub-content/osisoft-academic/Learning_Modules/NB* .
cp ../../../../jhub-content/osisoft-academic/Learning_Modules/DESCHUTES_GUIDE.ipynb .
cp ../../../../jhub-content/osisoft-academic/Learning_Modules/Brewery_Dataset_Doc.ipynb .
cp ../../../../jhub-content/osisoft-academic/Learning_Modules/PandasGuide.ipynb .
cp ../../../../jhub-content/osisoft-academic/Learning_Modules/Hub_Library_Quickstart.* .
cp *.py *.ipynb ..
rm NB*SOLUTION*
zip -r -9 deschutes-learning-modules.zip *.ipynb *.py 
echo
echo "=====> upload zip and quickstart notebook+py to hub blob"
