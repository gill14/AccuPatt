# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
...
## [2.0.14] - 15 July 2022
### Added
- Defined Dye Manager allowing for selecting pre-defined dyes or configuring fully custom ones, all with local persistance.
- Test Spectrometer screen providing a live readout of the entire spectrum from the device, including colorized markers for the target excitation and emission wavelengths for the selected dye.
- Card Plot Options window, including new options:
	- Y-Axis: Coverage (%) or Deposition (GPA, l/ha)
	- Average Plot Dash-Overlay: Inner-Swath-Half-Average (swath box) or Average (all points)
### Changed
- Improved segmentation algorithm for separating adjoining stains; now enabled by default
- Multiple pop-ups added to card manager for clarity and transparency
- User-defined limiters for maximum stain counts to prevent crashes from improper thresholding
- Capture/Edit Pass String screen facelift
### Fixed
- Droplet volume calculation error using pre-spread-factored stain diameter
- Blank (but included) cards were being fully interpolated over instead of treated as zero deposition with only shading interpolated
- Card Average plot incorrectly interpolating edges where not all passes contained deposition data
- Composite Card droplet histogram by coverage. Was mistakenly using volume instead of area
- Reduced height of Card Process Options window so it appears correctly on smaller screens