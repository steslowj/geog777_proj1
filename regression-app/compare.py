from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from osgeo import gdalconst
from rasterstats import zonal_stats
from pysal.model import spreg
from spreg import OLS

# globally setting geopandas to use pyogrio as engine for reading files
gpd.options.io_engine = "pyogrio"

# define functions

def testingslider(power=1):
    slidervalue = power
    return slidervalue


def compare(df, power=6):
    # run calculation of:
    # 1.1 Use GDAL.grid to create IDW tiff with well shp and input power value
    try:
      dsIn = Path(__file__).resolve().parent / "initialdata\well_nitrate.shp"
      dsOut = Path(__file__).resolve().parent / "createddata\invdist.tif"
      idwPower = "invdist:power=" + str(power)
      idw = gdal.Grid(dsOut, dsIn, zfield="nitr_ran", algorithm = idwPower)
      print("step 1: IDW calculated with gdal.grid")
    except:
       print("step 1 failed to complete")

    # 1.2 set data sources to none
    dsIn = dsOut = idw = None

    # 1.3 Use GDAL.translate to create png of idw tif for display (optional)
    # scaleParams are min and max value of nitr_ran, needed to stretch png pixel range of white-black appropriately
    '''
    dsIn = str( Path(__file__).resolve().parent / "createddata\invdist.tif" )
    try:
        dsOut = gdal.Translate("invdistPNG.png", dsIn, scaleParams=[[-1.89477, 17.0655]])
        print("\ngdal_translate ran")
        print(gdal.Info(dsOut))
        stats = dsOut.GetRasterBand(1).GetStatistics(True, True)
        print(stats)
    except:
        print("\ngdal_translate didn't work")
    dsIn = dsOut = None
    '''
    
    # 2. Use rasterstats to create a zonal statistics of IDW tif and cancer rate shp
    try:
      cancerstats = zonal_stats("regression-app\initialdata\cancer_tracts.shp", "regression-app\createddata\invdist.tif",
                            stats="mean",
                            copy_properties=True,
                            geojson_out=True,
                            all_touched=True)
      print("step 2: zonal stats calculated")
    except:
       print("step 2 failed to complete")
    
    # 3. Place the zonal stats geojson into a pandas geodataframe
    # This geodataframe contains 'GEOID10', 'canrate', 'mean', and 'geometry' columns
    try:
      geocancerstats = gpd.GeoDataFrame.from_features(cancerstats)
      print("step 3: converted to geopandas dataframe")
    except:
       print("step 3 failed to complete")
      
    # 4. Prepare data for linear regression
    try:
      gcanrate = np.array(geocancerstats["canrate"].values)
      gcanrate.shape = (len(gcanrate),1)

      gmean = np.array(geocancerstats["mean"].values)
      gmean.shape = (len(gmean),1)
      print("step 4: data prepared for regression")
    except:
       print("step 4 failed to complete")

    # 5. Calculate linear regression with PYSAL spreg Ordinary Least Squares
    try:
       ols = OLS(gcanrate, gmean)
       print("step 5: regression calculated")
    except:
       print("step 5 failed to complete")

    # 6. Add array of residuals of regression into geodataframe, in the same order it was calculated
    try:
      geocancerstats['residuals']=ols.u
      geocancerstats['SDresiduals']=geocancerstats['residuals']/(ols.std_y)
      #print(geocancerstats)
      print("step 6: residuals added to geodataframe")
    except:
       print("step 6 failed to complete")

    # 6.2 Create geojson with processed geodataframe (optional)
    # geocancerstats.to_file("regression-app\createddata\geocancerstats.geojson", driver='GeoJSON')
       
    # 7. Return df and regression results
    results = []
    results.append(geocancerstats)

    return geocancerstats
