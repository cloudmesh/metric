Retrieval/Analysis for Microsoft Academic Knowledge API
=======================================================

Introduction
^^^^^^^^^^^^

The intent of this script is to retrieve the entire Microsoft Knowledge API database, then place it into MongoDB for analysis against XSEDE publications.

Usage
^^^^^

To retrieve database (by year)::

    ak_api.py evaluate <year> [--count=<count> --offset=<offset> --skip=<skip>]
    
This currently takes ~2 mins per 100,000 entries. MongoDB should be installed and running before attempting evaluate. Count is the number of entries per retrieval, offset is the index to begin at and skip is the number of calls to skip from the beginning (count * offset).

To retrieve parent information for each field of study::

    ak_api.py parents
    
This requires the presence of FieldsOfStudy.txt and FieldOfStudyHierarchy.txt.
    
To retrieve average citation count by fos (after evaluate and parents)::

    ak_api.py citations
