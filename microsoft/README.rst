Retrieval/Analysis for Microsoft Knowledge API
==============================================

Introduction
^^^^^^^^^^^^

The intent of this script is to retrieve the entire Microsoft Knowledge API database, then place it into MongoDB for analysis against XSEDE publications.

Usage
^^^^^

to retrieve database (by year)::

    ak_api.py evaluate <year>
    
This currently takes ~2 mins per 100,000 entries.
    
to retrieve average citation count by fos (after evaluate)::

    ak_api.py citations
    
Issues
^^^^^^

- Many entries are missing information
- Fields of Science are inconsistent



