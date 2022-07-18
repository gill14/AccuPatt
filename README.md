![logo image](./resources/accupatt_logo.png "Title is optional")
# What is it?
AccuPatt is a software tool for agricultural aircraft spray pattern testing. This includes measuring tracer dye deposition on string collectors and measuring droplet deposition from spray cards. It is built as a desktop GUI application with Python and Qt.
# What Equipment is needed?
Minimum system requirements:
- Windows 10
- MacOS 11
## For String Analysis
Currently, AccuPatt is configured to interoperate only with the WRK String Spectrometer System, available for purchase from WRK of Oklahoma. While the timeframe is unknown, interoperability is also planned for the USDA-ARS Aerial Application Technology Research Unit's Spectrometer System.
## For Spray Card Analysis
A flatbed scanner (and spray cards, of course!). You will use the scanning software that came with the scanner (or any other software of your choice) to scan the cards. AccuPatt can then be used to process those images and perform stain/droplet analyses.
# How much does it cost?
If you are satisfied with the application and it provides value for your operation, consider supporting the National Aerial Application Research and Education Foundation (NAAREF). NAAREF is a 501(c)(3) non-profit organization that seeks to promote and foster research, technology transfer and advanced education among aerial applicators, allied industries, government agencies and academic institutions.
# How can I contribute or make my own changes?
Outside of the much appreciated bug finding and reporting, feel free to clone this repository and do your own thing. Poetry is used for dependency and virtual environment management. Once you've cloned the repository, use Poetry to create a virtual environment and install the needed dependencies from the *pyproject.toml* file and run the project using:
> poetry run python -m accupatt
# Where can I find an Installer?
https://sites.google.com/illinois.edu/accupatt/download
