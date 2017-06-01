Retrieval/Analysis for Microsoft Academic Knowledge API
=======================================================

Introduction
^^^^^^^^^^^^

The intent of this script is to retrieve the entire Microsoft Knowledge API database, then place it into MongoDB for analysis against XSEDE publications.

Usage
^^^^^

To retrieve publications (by year)::

    ak_api.py evaluate <year> [--count=<count> --start=<start>]
    
MongoDB should be installed and running before attempting evaluate. Count is the number of results per call (default is 100000). Use start to begin at a certain month (by index, so January = 0).

To retrieve parent information for each field of study::

    ak_api.py parents
    
This requires the presence of FieldsOfStudy.txt and FieldOfStudyHierarchy.txt.
    
To retrieve average citation count by fos (after evaluate and parents)::

    ak_api.py citations
