import read_info, star_functions
import csv
import numpy as np
import os
import pandas as pd

if __name__ == "__main__":
    # Main program of my spotty-PSG connection code

    # 1) Read in all of the user-defined config parameters into a class, called Params.
    Params = read_info.ParamModel()

    # 2) Check that all directories used in the program are created
    if not os.path.isdir('./%s/' % Params.starName):
        os.mkdir('./%s/' % Params.starName)
        os.mkdir('./%s/Data/' % Params.starName)
        os.mkdir('./%s/Data/AllModelSpectraValues/' % Params.starName)
        os.mkdir('./%s/Data/HemiMapArrays/' % Params.starName)
        os.mkdir('./%s/Data/PSGCombinedSpectra/' % Params.starName)
        os.mkdir('./%s/Data/PSGThermalSpectra/' % Params.starName)
        os.mkdir('./%s/Data/SumfluxArraysTowardsObserver/' % Params.starName)
        os.mkdir('./%s/Data/SumfluxArraysTowardsPlanet/' % Params.starName)
        os.mkdir('./%s/Data/SurfaceCoveragePercentage/' % Params.starName)
        os.mkdir('./%s/Data/VariablePlanetFlux/' % Params.starName)
        os.mkdir('./%s/Figures/' % Params.starName)
        os.mkdir('./%s/Figures/VariabilityGraphs/' % Params.starName)
        os.mkdir('./%s/Figures/Hemi+LightCurve/' % Params.starName)
        os.mkdir('./%s/Figures/HemiMapImages/' % Params.starName)
        os.mkdir('./%s/Figures/IntegralPhasePlot/' % Params.starName)
        os.mkdir('./%s/Figures/LightCurves/' % Params.starName)
        os.mkdir('./%s/Figures/PlanetPlots/' % Params.starName)
        os.mkdir('./%s/Figures/PlanetPlots/PlanetPhase0Contrast/' % Params.starName)
        os.mkdir('./%s/Figures/PlanetPlots/VariableAndPSGContrast/' % Params.starName)
        os.mkdir('./%s/Figures/StellarPlots/' % Params.starName)
        os.mkdir('./%s/Figures/StellarPlots/MaxSumfluxChanges/' % Params.starName)
        os.mkdir('./%s/Figures/StellarPlots/StarFlux/' % Params.starName)

    # 3) If not already created, create the 2D Spot map of the star's surface
    #    that plots the locations of the spots and faculae. Used later to create
    #    the 3D hemisphere models
    if not os.path.isfile('./%s/Figures/FlatMap.png' % Params.starName):
        # Create a 2D spotmmodel from the star_flatmap.py file
        StarModel2D = star_functions.StarModel2D(
            Params.spotCoverage,
            Params.spotNumber,
            Params.facCoverage,
            Params.facNumber,
            Params.starName,
        )

                    # Generate the spots on the star
        surface_map = StarModel2D.generate_spots()

        # Convert the 1's and 0's in the ndarray, which store the spot locations, to a smaller data type
        surface_map = surface_map.astype(np.int8)

        # Saves the numpy array version of the flat surface map to be loaded while creating the hemisphere views
        np.save('./%s/Data/flatMap.npy' % Params.starName, surface_map)

    # 4) This section "Bins" the stellar models to be a uniform resolving power and wavelength range.

    # If the stellar data was previously binned, simply load in the saved binned stellar model.
    ###### Does saving these as .npy arrays save storage space/loading time rather than .txt files?
    if Params.loadData:
        allModels = read_info.ReadStarModels(Params.starName)

        allModels.photModel = pd.read_csv('./NextGenModels/BinnedData/binned%dStellarModel.txt' % Params.teffStar,
                                  names=['wavelength', 'flux'], delimiter=' ', skiprows=1)

        allModels.spotModel = pd.read_csv('./NextGenModels/BinnedData/binned%dStellarModel.txt' % Params.teffSpot,
                                   names=['wavelength', 'flux'], delimiter=' ', skiprows=1)
        
        allModels.facModel = pd.read_csv('./NextGenModels/BinnedData/binned%dStellarModel.txt' % Params.teffFac,
                                      names=['wavelength', 'flux'], delimiter=' ', skiprows=1)
        
        if not np.all(allModels.photModel.wavelength == allModels.spotModel.wavelength) or not np.all(allModels.photModel.wavelength == allModels.facModel.wavelength):
            raise ValueError("The star, spot, and faculae spectra should be on the same wavelength scale and currently are not. Have you binned the date yet? Check 'binData' in your config file.")
        data = {'wavelength': allModels.photModel.wavelength, 'photflux': allModels.photModel.flux, 'spotflux': allModels.spotModel.flux, 'facflux': allModels.facModel.flux}
        allModels.mainDataFrame = pd.DataFrame(data)
    else:
        topValues = []
        cwValues = []
        CW = Params.binnedWavelengthMin
        # Calculate the center wavelenghts (CW) and upper values (top) of each bin
        while CW < Params.binnedWavelengthMax:
            deltaLambda = CW / Params.resolvingPower
            topValue = CW + (deltaLambda / 2)
            topValues.append(topValue)
            cwValues.append(CW)
            CW += deltaLambda

        allModels = read_info.ReadStarModels(Params.starName, Params.binnedWavelengthMin, Params.binnedWavelengthMax,
                                             Params.imageResolution, Params.resolvingPower, Params.phot_model_file,
                                             Params.spot_model_file, Params.fac_model_file, topValues, cwValues)
        allModels.read_model(Params.teffStar, Params.teffSpot, Params.teffFac)
        print("Done")

    # 5) This section generates the hemispheres of the star, based on the 2D surface map.
         
    # Name of the .npy array which contains the flat surface map
    # This array is used to create the hemisphere maps
    surface_map = np.load('./%s/Data/flatMap.npy' % Params.starName)

    # If the generate hemispheres boolean set by the user-defined config is true, the program will generate
    # (or re-generate with different inclination for example) the star hemispheres.
    if Params.generateHemispheres:

        # Can be made high res by user-specified config. 3000x3000 array
        if Params.highResHemispheres:
            Params.imageResolution = 3000

        HM = star_functions.HemiModel(
            Params.teffStar,
            Params.rotstar,
            surface_map,
            Params.inclination,
            Params.imageResolution,
            Params.starName,
        )

        # Tyler's Suggestion
        # create array of phases
        phases = [i * Params.deltaPhase for i in range(Params.num_exposures)]

        # Begin at phase = 0
        # Count keeps track of which hemisphere map image is being looked at currently
        phase = 0
        count = 0
        print("\nGENERATING HEMISPHERES")
        print("----------------------")
        for phase in phases:
            # EDIT: Am I able to compute the surface area percentages for the current stellar phase here? And save them for later?
            #       This would keep me from having to re-load the .npy arrays later on.

            # IMPORTANT
            # I want to add in the functionality to save the surface area coverage percentage during this for-loop
            # will save time. Look into adding it inside the generate_hemisphere_map method.
            hemi_map = HM.generate_hemisphere_map(phase, count)
            print("Percent Complete = %.1f" % (phase * 100), "%")
            count += 1
        
        deltaStellarPhase = Params.deltaPhase * 360

        w = csv.writer(open("./%s/Data/SurfaceCoveragePercentage/surfaceCoveragePercentageDict.csv" % Params.starName, "w"))
        for key, val in HM.surfaceCoverageDictionary.items():
            w.writerow([key, val])

    # GCM file type should be a net cdf file typ
    # Most common gcf file type

    print("done")

