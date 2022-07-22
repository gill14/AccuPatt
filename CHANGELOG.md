# Changelog
All notable changes to this project will be documented in this file.
## [Unreleased]
### Added
- Thrush 510P2, 510P2+ to available aircraft ([#1](https://github.com/gill14/AccuPatt/issues/1))
- CP09A (Australian) nozzle to non-modeled nozzles ([#1](https://github.com/gill14/AccuPatt/issues/1))
### Changed
- Overwrites and Deletes now simply move file to Trash (MacOS) or Recycle Bin (Windows)
### Fixed
- Conversion of xlsx to db hangup ([#2](https://github.com/gill14/AccuPatt/issues/2))
- On open file, flyin date being replaced with current date in Application Info widget
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
## [2.0.13] - 16 June 2022
### Added
- Meaningfully handle missing pass observables, showing as dashes on the report and excluding from series-wise averages
- Show boom width as percentage on report if both wingspan and boom-width are provided
- Button to fill in only business info from a previous file
- Button to fill in pass observables from all passes in one screen, essentially a slimmed-down Pass Manager
- Series info units retain persistent user-defined defaults
- Export SAFE Log from chosen files or from chosen directory, recursively searching for all datafiles within that directory
### Changed
- Defined Set Manager, create set from regular spacing, add all card process options and spread factors
- Pass Manager, changed to column-based
### Fixed
- Series info units not saving to datafile if not explicitly selected
## [2.0.12] - 8 June 2022
### Added
- Option to flip input image vertically/horizontally in multi mode
- Option to add a logo to PDF SAFE report
### Changed
- Plot rendering on/after PDF generation
- Move fly-in header info to single line header in PDF SAFE report
### Fixed
- New Series not enabling main tab widget
- Clearing plots on New Series
## [2.0.11] - 30 May 2022
### Added
- Pass Manager - Shift Pass location in list
- Prompt to delete original scan image file after saving cropped ROIs to the datafile
- Add (alembic) DB compatibility layer, supporting 2.0.10+ datafile versions moving forward
- User (Non-Deterministic) Config Options moved to Menu Items
	- String Plot Options 
		- Swath Box - Enable/Disable showing of swath box
		- Simulation View - Show One Swath or All Passes for overlap simulations
	- Card Plot Options
		- Swath Box - Enable/Disable showing of swath box
		- Simulation View - Show One Swath or All Passes for overlap simulations
		- Colorize by DSC - Show DSC calculated color fill for Individual, Average and/or Simulation Plots
		- Interpolate DSC - Switch between linear spline ar piecewise interpolation for DSC colorized fill.
### Changed
- Improve Plot visibility and coloring
### Fixed
- Passes added from Pass Manager cause plots to misbehave
- Plots need resized after PDF generation
- Card Plot Average shade by DSC interpolation algorithm
## [2.0.10] - 22 May 2022
### Added
- Auto-commit wingspan on aircraft model selection
- Save file trigger after each string pass accepted
- Auto-populate pass-heading, temp, humidity for other passes
- Card simulation plots and cv calculations
### Changed
- Sort new series file aircraft in current directory list
- Enforce single series id per db file to prevent accidental overwrites
### Fixed
- Simulation plots not clearing
- Back and forth odd passes plotting incorrectly
- Blank loading window on new series
- Multi-image uploader roi finder minimum detection size
- Auto increment series numbering
- Numeric series info fields unable to clear
- Setting target ex/em wavelengths
- Report values outside USDA Model range
## [2.0.9] - 16 May 2022
### Added
- Card Manager: visibility/eding of all card processing parameters
- Card Manager: original/outline/processed image viewer
- Card Process Options: option to band-pass or band-reject for each HSB range
- Card Process Options: calculated autothreshold indicator for Grayscale threshold
- Ability to add/remove ROIs for multi-card-in-single-image uploads
- Card image pre-processor with progress popup to improve UI responsiveness
- Card stain approximation method to data file
- WRK String Spectrometer Manual to help menu
### Changed
- Redesigned Card Analysis tab in main window
	- controls for centering, colorizing by DSC and setting adjusted swath width
	- Individual Passes tab including deposition plot and stat table
	- Composite tab including overlay and average plots
	- Distributions tab including series-, pass- and card-wise computations
### Fixed
- String drive overrun (timer) issue
- Card Process Options: Hue range upper limit for HSB threshold
## [2.0.8] - 24 March 2022
### Added
- Rebuild Pass Manager for pass observables
- Set default number of passes in Pass Manager
- Impose units for series-wise observable means
- Impose units for retrieving pass observables
- Add cards-include-in-composite to Pass for series-wise calculations
- String Drive - Direct Command Line
- User-defined defaults for string advanced options
- User-defined defaults for spray card processing and spread factors
- *.tif *.tiff support for loading spray cards
### Fixed
- Droplet stat table inadvertently defaulting to persistent dpi
- Import AccuPatt 1 cards inadvertently defaulting to persistent dpi
## [2.0.7] - 16 March 2022
### Added
- SprayCard individual images/statistics pages to SAFE Report
- Menu Items:
    - Report: Include SprayCard images
    - Report: SprayCard image type
    - Report: SprayCard images per page
    - Options: Reset all user-defined defaults
### Changed
- Fully adjustable (editable) DPI, in addition to suggested list
### Fixed
- Spectrometer disconnect on subsequent calls to capture string
- Atomization model pressure/airspeed unit prechecks
- Duplicate labels on Card Manager table item delegates
## [2.0.6] - 14 March 2022
### Added
- String Advanced Options dialog for pass/series smoothing and centering params
- String simulation view option: one-pass/all-passes
### Fixed
- Capture String window string data/option migrations
- Serial port handoffs between dialogs
## [2.0.5] - 11 March 2022
### Added
- String pattern rebase (allows adjustment of x-domain post-processing)
- Auto-open report PDF upon generation
### Changed
- Multiple plot and table reformats
- String pattern x-mods now apply directly rather than using nearest point shift
- String pattern centering boolean and center-method replaces standalone method
- String pattern smoothing window/order moved to persistent settings
- String pattern smoothing window now x-domain-based rather than point-based
- String pattern smooth/rebase now affects individual trim plot
### Fixed
- Replaced implicit dtypes on persistent settings with explicit dtypes for Windows
## [2.0.4] - 25 February 2022
### Added
- SAFE Report: spray card page(s)
- Locally Defined Card Sets, Batch Creator
- Batch Image Upload functionality
- Set image dpi by default from queried exif data
- Image Processing stain shape approximation
- Persistence to Pass and Spray-Card options
- Several non-model nozzles for convenience
- Fly-in worksheets to help menu for convenience
- Version number to datafile, window title and about popup
### Changed
- Duplicate Pass observables from Capture String Pass to Card Manager
### Fixed
- String Simulation mean deposition line
- Multiple plot legend fixes
## [2.0.3] - 2 February 2022
### Added
- Centering/Smoothing on per-pass basis
- Average Centering/Smoothing and Integral Equalization on series-basis
- Centering options: Centroid, Center of Distribution (Dr. Fritz)
- Spray Card min particle size, watershed segmentation options
- Windows Installer
### Changed
- Remove SS/Def Atomization Model redundancies from Nozzle Selection
- String plot spatial units now follow target swath units, regardless of collection units
- Card plot spatial units now follow target swath units, regardless of collection units (override incl.)
- Excitation/Emission wavelengths and integration time saved to datafile
- Spray Card image processed colors seperated for edge (incl in cov) vs undersized stains (excl in cov)
- Fold importing of AccuPatt 1 files into standard open menu, with optional to view-only or create db copy
### Fixed
- Atomization Model Prechecks for airspeed, orifice, deflection and pressure
## [2.0.2] - 28 January 2022
### Added
- Measure string speed
### Fixed
- Save trigger before opening Card Manager
## [2.0.1] - 27 January 2022
### Fixed
- Handling of blank spray cards
- Parsing new string data to pass object
## [2.0.0] - 26 January 2022
- Initial rewrite of AccuPatt using Python/Qt. Based on prior (1.xx) version using Java/JavaFX. Final release of the legacy version is 1.06+.


[Unreleased]: https://github.com/gill14/accupatt/compare/v2.0.14...HEAD
[2.0.14]: https://github.com/gill14/accupatt/compare/v2.0.13...v2.0.14
[2.0.13]: https://github.com/gill14/accupatt/compare/v2.0.12...v2.0.13
[2.0.12]: https://github.com/gill14/accupatt/compare/v2.0.11...v2.0.12
[2.0.11]: https://github.com/gill14/accupatt/compare/v2.0.10...v2.0.11
[2.0.10]: https://github.com/gill14/accupatt/compare/v2.0.9...v2.0.10
[2.0.9]: https://github.com/gill14/accupatt/compare/v2.0.8...v2.0.9
[2.0.8]: https://github.com/gill14/accupatt/compare/v2.0.7...v2.0.8
[2.0.7]: https://github.com/gill14/accupatt/compare/v2.0.6...v2.0.7
[2.0.6]: https://github.com/gill14/accupatt/compare/v2.0.5...v2.0.6
[2.0.5]: https://github.com/gill14/accupatt/compare/v2.0.4...v2.0.5
[2.0.4]: https://github.com/gill14/accupatt/compare/v2.0.3...v2.0.4
[2.0.3]: https://github.com/gill14/accupatt/compare/v2.0.2...v2.0.3
[2.0.2]: https://github.com/gill14/accupatt/compare/v2.0.1...v2.0.2
[2.0.0]: https://github.com/gill14/accupatt/compare/initial_commit...v2.0.0