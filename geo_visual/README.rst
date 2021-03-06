Visuals for Geographical Data
=============================

* Tim Whitson @whitstd

Project can be viewed live at: https://jsfiddle.net/whitstd/epL60myp

Data
^^^^

Dataset: `data.csv <data.csv>`_ https://sciimp.ccr.xdmod.org/xdportalpub/byorg

Geo data from: National Center for Education Statistics `hd2015.csv <hd2015.csv>`_ https://nces.ed.gov/ipeds/Home/UseTheData

Method
^^^^^^

Step 1: Obtain Geographical Data
--------------------------------

The dataset did not come with any geographical data. I was not able to find an API to add to the data, so I used the data provided from the National Center for Education Statistics.

I wrote `add_location.py <add_location.py>`_ to merge the datasets. Final dataset: `data-coords.csv <data-coords.csv>`_

Step 2: Visualize
-----------------

For now, I chose the Highmaps Javacscript library to display the data. Highmaps is a branch of Highcharts, which is already in use in the project. Using Highmaps, I was able to easily display the data and to modify the visuals dynamically based on user input.

Future
^^^^^^

Currently, the project uses Google Sheets (supported natively by Highcharts). This will need to be replaced with actual data from the database.

Different map types can be added. The dataset now also contains new information, such as state and zip code, which could also be used instead of latitude and longitude.
