RETAIL DATA CLEANING PROJECT
============================

Dataset: UCI Online Retail II
Size: 1,067,371 transaction rows
Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
DOI: 10.24432/C5CG6D
License: CC BY 4.0

FILES
-----
retail_data_cleaning_1m.ipynb
    Complete notebook with before/after profiling, cleaning, feature engineering,
    validation and CSV export.

HOW TO RUN
----------
1. Install Python, Jupyter Notebook and the required packages:
   pip install pandas numpy openpyxl ucimlrepo
2. Open the notebook.
3. Run all cells from top to bottom.
4. The notebook attempts to fetch the dataset from UCI automatically.
   If that fails, download online_retail_II.xlsx from the official UCI page and
   put it in the same folder as the notebook.
5. The final cell creates clean_dataset.csv.

IMPORTANT
---------
The original dataset has no product-cost column, so true profit margin cannot be
calculated honestly from the available fields. The notebook calculates sales_revenue
and computes profit_margin_pct only if a cost field is present. It does not invent
costs. Outliers are flagged rather than automatically deleted because large
wholesale orders may be legitimate.
