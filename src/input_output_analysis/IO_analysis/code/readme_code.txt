# README REPLICATION PACKAGE - INPUT-OUTPUT ANALYSIS - CODE

This folder contains all code to replicate the input-output analysis.


requirements.txt
	Python environment for running "04_calc_EXIOBASE_footprints.ipynb"


01_create_Y_NL.R
	Creates the Y-table of EXIOBASE for all transactions that relate to the Netherlands (inputs and outputs)

02_createMapping.R
	Automatically creates a mapping table of EXIOBASE variables to CBS variables (via official COICOP concordance tables)

The following step is to create a manual mapping table based on the automatically created one. The result can be found in the excel document "CorrespondenceTables_CBS-EXIOBASE_final.xlsx" on the sheet "Mapping_manual"

03_RAS_final.R
	Performs the RAS to create a weighted mapping table of EXIOBASE to CBS variables on the basis of the manual mapping table.

04_calc_EXIOBASE_footprints.ipynb
	Performs the input-output analysis to get the carbon emissions per EXIOBASE variable/product
	The result of this step was imported into the excel document "CorrespondenceTables_CBS-EXIOBASE_final.xlsx" on the sheet "CarbonIntensity_EXIOBASE"

	04_calc_EXIOBASE_footprints_Jiamin.m & 04_calc_EXIOBASE_footprints_sum_Jiamin.ipynb
		Provided the basis to create "04_calc_EXIOBASE_footprints.ipynb" - Currently not in use

The following step in the analysis is performed within the excel document "CorrespondenceTables_CBS-EXIOBASE_final.xlsx" (see readme sheet from CarbonIntensity_EXIOBASE upward).
This completes the calculation of the carbon intensities of the 156 product categories according to CBS in the Netherlands.


The following 2 steps compare different methodologies and provide insights on the intensities across products and years:

05_compare_EXIOBASEyears.Rmd
	Creates plots to compare the expenditures and emissions of all products according to EXIOBASE in 2013-2016

06_compare_CBSintensities.Rmd
	Creates plots to compare the carbon emissions and intensities across the different methods (pre-RAS and post-RAS) across 2014-2016