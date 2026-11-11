# README REPLICATION PACKAGE - INPUT-OUTPUT ANALYSIS - DATA

This folder contains all data to replicate the input-output analysis

CBS
	Contains the aggregated expenditures per CBS product category according to the CBS budget survey in 2015
	The expenditures are extrapolated to reflect household expenditures of all households in the Netherlands

EXIOBASE
	emissions:		Contains the carbon emissions calculated by using different methodologies - only for referencing/comparing
	IOT_yyyy_pxp:		Contains all EXIOBASE tables from 2013 to 2019 as downloaded from https://doi.org/10.5281/zenodo.5589597
	y_NL_comparisons:	Contains a comparison of product-wise EXIOBASE expenditures of the Netherlands across different years (calculated by "code/01_create_Y_NL.R")

Mapping_csv
	Contains different tables mapping CBS to EXIOBASE as a result of e.g. "code/02_createMapping.R" and "code/03_RAS_final.R"
	These tables are also presented in "CorrespondenceTables_CBS-EXIOBASE_final.xlsx"

Mapping_examples
	Contains mapping tables of other studies as references

EXIOBASE_footprints_sum_2015.csv
	Contains the carbon emissions of EXIOBASE products in 2015. The EXCEL version contains the same data but has a different delimiter that is easier to read by EXCEL
