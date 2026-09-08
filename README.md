![logo image](./resources/accupatt_logo.png "AccuPatt Logo")
# What is it?
AccuPatt is a software tool for agricultural aircraft spray pattern testing. This includes measuring tracer dye deposition on string collectors and measuring droplet deposition from spray cards. It is built as a desktop GUI application with Python and Qt.
# What Equipment is needed?
Minimum system requirements:
- Windows 10 (x86-64 only if using compiled installer)
- macOS 11 (ARM only if using compiled installer)
## For String Analysis
Currently, AccuPatt is configured to interoperate only with the WRK String Spectrometer System, available for purchase from WRK of Oklahoma. While the timeframe is unknown, interoperability is also planned for the USDA-ARS Aerial Application Technology Research Unit's Spectrometer System.
## For Spray Card Analysis
A flatbed scanner (and spray cards, of course!). You will use the scanning software that came with the scanner (or any other software of your choice) to scan the cards. AccuPatt can then be used to process those images and perform stain/droplet analyses.
# How much does it cost?
If you are satisfied with the application and it provides value for your operation, consider supporting the National Aerial Application Research and Education Foundation (NAAREF). NAAREF is a 501(c)(3) non-profit organization that seeks to promote and foster research, technology transfer and advanced education among aerial applicators, allied industries, government agencies and academic institutions.
# How can I contribute or make my own changes?
Outside of the much appreciated bug finding and reporting, feel free to clone this repository and do your own thing. Poetry is used for dependency and virtual environment management. Once you've cloned the repository, use Poetry to create a virtual environment and install the needed dependencies from the *pyproject.toml* file and run the project using:
```shell
poetry install
poetry run python -m accupatt
```
## Spectrometer support (OceanDirect SDK)
AccuPatt talks to Ocean Optics spectrometers through the OceanDirect SDK. That SDK is proprietary and is **not** included in this repository — the OceanDirect API Terms only permit distributing it as part of a built application, so it is staged locally instead of committed.

If you want string analysis to work from a source checkout, install the SDK yourself and stage it:

1. Download and install the OceanDirect SDK from [Ocean Optics](https://www.oceanoptics.com/software/oceandirect/). You accept Ocean Optics' API Terms when you install it — that acceptance is yours to give and cannot be made on your behalf.
2. Stage the Python bindings into the working tree:
   ```shell
   poetry run python tools/sync_oceandirect.py
   ```
   Set `OCEANDIRECT_HOME` first if you installed it somewhere non-standard. Run it once per platform you build on; it leaves other platforms' libraries alone.

Everything else in AccuPatt — spray card analysis, reporting, the database tools — works without the SDK. Spectrometer features report "OceanDirect Driver Not Installed" and stay disabled.

To confirm a spectrometer is working, plug one in and run:
```shell
poetry run python tools/check_spectrometer.py
```
It reports the SDK version, the device's capabilities, and a few live frames — which distinguishes "no SDK" from "no device" from "device misbehaving" without going through the GUI.

Released installers bundle the SDK, so end users do not need to do any of this. They accept the [AccuPatt EULA](resources/documents/AccuPatt_EULA.txt) instead, which carries the restrictions Ocean Optics requires be passed through.
# What if I just want to use it?
You can access a compiled installer as well as the user manual using the links below:
- [macOS and Windows Installers](https://github.com/gill14/AccuPatt/releases)
- [User Manual](https://github.com/gill14/AccuPatt/blob/master/user_manual/accupatt_2_user_manual.pdf)

