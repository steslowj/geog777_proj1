from pathlib import Path
import os

# Import modules for modeling and display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import json
from pysal.model import spreg
from spreg import OLS
import ipyleaflet
import ipywidgets
from branca.colormap import linear

# Import modules for shiny framework
from shiny import reactive
from shiny.express import ui, input, render, expressify
from shinywidgets import render_widget

# Import custom Python Functions from local file
from compare import compare

# app

# script to display LaTeX
ui.tags.script(
    src="https://mathjax.rstudio.com/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"
)
ui.tags.script("if (window.MathJax) MathJax.Hub.Queue(['Typeset', MathJax.Hub]);")

# globally setting geopandas to use pyogrio as engine for reading files
gpd.options.io_engine = "pyogrio"

@reactive.Calc
def model():
    cancerfilepath = Path(__file__).resolve().parent / "initialdata\cancer_tracts.shp"
    geocancer = gpd.read_file(str(cancerfilepath))
    data = []
    data.append(geocancer)
    compareResults = [compare(df, power=input.p()) for df in data]
    compareResults = gpd.GeoDataFrame(pd.concat(compareResults, ignore_index=True))
    return compareResults

with ui.div(class_="col-md-10 col-lg-8 py-1 mx-auto pt-4 small text-left"):
    ui.markdown(
        """
        Author: Jessica Steslow, UW-Mad Geog 777 Project 1
        <br>With inspiration from the Shiny App <a href='https://shinylive.io/py/app/#regularization'>Regulation Strength</a>
        """
)
with ui.div(class_="col-md-10 col-lg-8 py-5 mx-auto text-lg-center text-left"):
    ui.h1("Exploring the Influence of Well Nitrate Levels on Cancer Rates in WI, USA")

with ui.div(class_="col-lg-6 py-5 mx-auto"):
    ui.markdown(
        """
        ### Initial data

        The initial data is presented below. Cancer rate is displayed per Census Tract and is normalized by the population in each tract. Nitrate levels taken from discrete well locations. 
        
        The data will take a few moments to load.
        """
    )
#Row for initial data
with ui.div(class_="row py-3 mx-auto"):
    
    with ui.div(class_="col-lg-6 col-sm-11"):
      @render.plot()
      def plot_initialc(): # Geopandas / Matplotlib
          cancerfilepath = Path(__file__).resolve().parent / "initialdata\cancer_tracts.shp"
          geocancer = gpd.read_file(str(cancerfilepath))
          nitratefilepath = Path(__file__).resolve().parent / "initialdata\well_nitrate.shp"
          geonitrate = gpd.read_file(str(nitratefilepath))
          ax = geocancer.plot(column='canrate', 
                              linewidth=0.2, 
                              edgecolor='#777',
                              cmap='Blues', 
                              legend=True, 
                              legend_kwds={'label':'Cancer Rate in Census Tract'})
          # geonitrate.plot(ax=ax, marker='*', markersize=2, column='nitr_ran', cmap='YlOrRd')
          # geonitrate.plot(ax=ax, marker='o', markersize=2, color='grey')
          ax.set_axis_off()
          return ax
    
    with ui.div(class_="col-lg-6 col-sm-11"):
      @render.plot()
      def plot_initialn():
          cancerfilepath = Path(__file__).resolve().parent / "initialdata\cancer_tracts.shp"
          geocancer = gpd.read_file(str(cancerfilepath))
          nitratefilepath = Path(__file__).resolve().parent / "initialdata\well_nitrate.shp"
          geonitrate = gpd.read_file(str(nitratefilepath))
          ax = geocancer.plot(color='#aaa',
                              edgecolor='#555', 
                              linewidth=0.2, 
                              zorder=1)
          geonitrate.plot(ax=ax, 
                          marker='*', 
                          markersize=2, 
                          column='nitr_ran', 
                          cmap='YlOrRd',
                          zorder=2,
                          legend=True,
                          legend_kwds={'label':'Nitrate Level at Well Site'})
          ax.set_axis_off()
          return ax

with ui.div(class_="col-lg-6 py-5 mx-auto"):
    ui.markdown(
        """
        ### Analysis Process

        In order to compare these two different types of data, we must convert them to be in the same type. This app will run the following analysis:
          - Create surface of Nitrate values
          - Distribute Nitrate values to Cancer Polygons
          - Run linear regression on Cancer and Nitrate values per Census Tract Polygon 
        """
    )
with ui.div(class_="col-lg-6 py-5 mx-auto"):
    ui.markdown(
        """
        ### How are the Nitrate Well Sites Distributed?

        In order to compare the Nitrate data to the Cancer data, we must look at the spatial distribution of the well sites. The first step to this is checking how the Nitrate values are distributed within their dataset - we can do this by creating a histogram. Check the histograms below by selecting the number of values per bin.
        """
    )

with ui.div(class_="col-md-78 col-lg-6 py-4 mx-auto"):  
    ui.input_slider("nn", "Number of bins for Nitrate histograms", 1, 100, 20, width="100%")

with ui.div(class_="col-lg-10 row py-3 mx-auto"):

    with ui.div(class_="col-lg-6 col-sm-11 mx-auto"):
        @render.plot(alt="A histogram of nitrate values in WI well sites.")  
        def plot_nitratehist():
            nitratefilepath = Path(__file__).resolve().parent / "initialdata\well_nitrate.shp"
            geonitrate = gpd.read_file(str(nitratefilepath))
            ax = sns.histplot(data=geonitrate, x="nitr_ran", bins=input.nn(), color="orange")  
            ax.set_title("Nitrate values in WI well sites")
            ax.set_xlabel("Nitrate value")
            ax.set_ylabel("Count")
            return ax  
        
    with ui.div(class_="col-lg-6 col-sm-11 mx-auto"):    
        @render.plot(alt="A histogram of the log of nitrate values in WI well sites.")  
        def plot_lognitratehist():
            nitratefilepath = Path(__file__).resolve().parent / "initialdata\well_nitrate.shp"
            geonitrate = gpd.read_file(str(nitratefilepath))
            geonitrate['lognitrate']=np.log(geonitrate['nitr_ran'])
            ax = sns.histplot(data=geonitrate, x="lognitrate", bins=input.nn(), color="orange")  
            ax.set_title("Log of Nitrate values in WI well sites")
            ax.set_xlabel("Log of Nitrate value")
            ax.set_ylabel("Count")
            return ax
         
with ui.div(class_="col-lg-6 py-5 mx-auto"):
    ui.markdown(
        """
        ### Choosing a Power value for IDW

        We can see that neither the Nitrate nor Log of Nitrate distributions are quite normal... But the first is closer. We can try to apply a spatial calculation on the nitrate data to convert distinct points into a surface with averaged nitrate values. 
        
        This analysis will use an Inverse Distance Weighted (IDW) technique, where values are averaged between nitrate points. We can choose to weight points that are close together with a high P value (P>3), or weight all points equally (P=0). P cannot be less than 0.
        """
    )
    # LaTeX
    "$$w = \\frac{1}{{r}^{p}}$$"
    ui.input_slider(
        "p",
        "Select a P value for IDW",
        min=0,
        max=4,
        value=1,
        step=0.5,
        width="100%",
    )
    ui.p(
        {"class": "pt-4 small"},
        "(Each time you change the slider input, the data comparison will take some time to run.)",
    )

with ui.div(class_="col-lg-6 mx-auto"):
    ui.h3("Results")    

with ui.div(class_="col-lg-7 py-5 mx-auto"):
    
    @render.plot()
    def plotRegPlot():
        cancerCompareDF = model()
        # this seaborn plot does a linreg calc to generate the line
        ax = sns.regplot(data=cancerCompareDF,
                          x='mean',
                          y='canrate',
                          line_kws=dict(color='orangered'),
                          scatter_kws={'s':10},
                          ci=None)
        ax.set_title("Scatter Plot and Regression Line")
        ax.set_xlabel("Mean of Nitrate")
        ax.set_ylabel("Cancer Rate")
        return ax
    
    @render.plot() # seaborn scatter plot with residuals on y axix and line at y=0
    def plotSDResiduals():
        cancerCompareDF = model()
        # this seaborn plot does a linreg calc to generate residuals
        ax = sns.residplot(data=cancerCompareDF,
                          x='mean',
                          y='canrate',
                          scatter_kws={'s':10})
        ax.set_title("Residual Plot")
        ax.set_xlabel("Mean of Nitrate")
        ax.set_ylabel("Residual of Cancer Rate")
        return ax
    
    # @render_widget #ipyleaflet map with geodataframe
    # def map():
    #     cancerCompareDF = model()

    #     dffilepath = Path(__file__).resolve().parent / "createddata\well_nitrate.shp"
    #     m = Map(center=(-90, 45), zoom=6)

    #     geo_data = GeoData(geo_dataframe = cancerCompareDF,
    #                        style={'color':'black','opacity':0.4,'weight':1,'fillColor':'red','fillOpacity':0.2},
    #                        name='CancerRate')
    #     m.add(geo_data)
    #     m.add(LayersControl())
    #     return m


    # @render_widget # ipyleaflet attempt to map data with info on hover. difficult to implement correctly
    # def map():
    #     cancerCompareDF = model()

    #     here = Path(__file__)
    #     with open(here.parent / "createddata\geocancerstats.geojson", "r") as f:
    #         geo_json_data = json.load(f)
    #         for d in geo_json_data["features"]:
    #           d["name"] = d["properties"]["GEOID10"]

    #     min_val = min(cancerCompareDF['SDresiduals'].values)
    #     max_val = max(cancerCompareDF['SDresiduals'].values)
    #     diff = max_val-min_val

    #     normalized_vals = (cancerCompareDF['SDresiduals'].values - min_val)/diff

    #     mapping = dict(zip(cancerCompareDF['GEOID10'].values, normalized_vals))

    #     def feature_color(feature):
    #         feature_name = feature['properties']['GEOID10']
    #         return{
    #             'color':'black',
    #             'fillColor':linear.YlOrRd_04(mapping[feature_name]),
    #         }

    #     geo_json = ipyleaflet.GeoJSON(
    #         data = geo_json_data,
    #         style = {
    #             'opacity':1, 'fillOpacity':1.0, 'weight':1
    #         },
    #         hover_style = {
    #             'color': 'white', 'fillOpacity': 0.2, "text":"test"
    #         },
    #         style_callback = feature_color
    #     )

    #     geo_data = ipyleaflet.GeoData(
    #         geo_dataframe = cancerCompareDF,
    #         style = {
    #             'color':'black',
    #             'fillColor':'white',
    #             'opacity':0.0,
    #             'weight':1.0,
    #             'fillOpacity':0.0,
    #         },
    #         name="Data",
    #     )

    #     m = ipyleaflet.Map(center = (-90,45), zoom = 5)
    #     m.add_layer(geo_json)
     
    #     label = ipywidgets.Label(layout=ipywidgets.Layout(width='100%'))  
    #     def hover_handler(event=None, feature=None, id=None, properties=None):
    #       label.value = properties["GEOID10"]

    #     geo_data.on_hover(hover_handler)
    #     m.add_layer(geo_data)
    #     v = ipywidgets.VBox([m,label])

    #     return m

    @render.plot()
    def plotResMap(): # Geopandas / Matplotlib
        cancerCompareDF = model()
        ax = cancerCompareDF.plot(column='SDresiduals', 
                            linewidth=0.2, 
                            edgecolor='#777',
                            cmap='PRGn',
                            scheme='std_mean',
                            legend=True)
        ax.set_title("Standard Deviation of Residuals of Cancer Rate")
        ax.set_frame_on(True)
        ax.set_aspect(1.4)
        ax.set_axis_off()
        return ax


with ui.div(class_="col-lg-8 py-3 mx-auto"):

    @render.express
    def resultstext():
      # get nitrate and cancer dataframe from model function
      cancerCompareDF = model()

      # reformate data for spreg OLS calculation
      gcanrate = np.array(cancerCompareDF["canrate"].values)
      gcanrate.shape = (len(gcanrate),1)
      gmean = np.array(cancerCompareDF["mean"].values)
      gmean.shape = (len(gmean),1)

      # run spreg OLS calculation
      ols = OLS(gcanrate, gmean)
      olsResults = ols.summary
      with ui.div(class_="p-2"):
        ui.h3('Regression Results from OLS Model')
        ui.pre(olsResults)