# Watches Data Cleaning Project

## Project Overview
This project focuses on cleaning and preprocessing a watches dataset using Python and Pandas. The goal is to improve data quality by handling missing values, removing duplicate records, standardizing text data, and treating outliers.

## Dataset
The dataset contains information about various watches, including:
- Product ID
- Brand
- Rating
- Price
- Discount
- Final Price
- Seller Information
- Product Specifications

## Data Cleaning Steps
1. Loaded the dataset using Pandas.
2. Removed duplicate records.
3. Handled missing values:
   - Numeric columns filled with median values.
   - Text columns filled with "Unknown".
4. Removed unnecessary leading and trailing spaces.
5. Converted columns to appropriate data types.
6. Handled outliers using the IQR method and value capping.

## Technologies Used
- Python
- Pandas
- NumPy
- Jupyter Notebook / VS Code

## Output
The cleaned dataset is saved as:

```text
cleaned_watches.xlsx
