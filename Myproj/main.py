# In[1]:

import pysal as ps
import geopandas as gpd
import pandas as pd
import numpy as np
import seaborn as sns


# In[2]:

shp = ps.open('us_income/us48.shp')


# In[3]:

us48 = gpd.read_file("us_income/us48.shp")
us48_income = pd.read_csv("us_income/usjoin.csv")
us48_income.columns = ['y_' + col for col in us48_income.columns]
us48_income.rename(columns={'y_Name':'Name'}, inplace=True)
us48_income.rename(columns={'y_STATE_FIPS':'STATE_FIPS'}, inplace=True)
us48["STATE_FIPS"] = pd.to_numeric(us48["STATE_FIPS"])
us48 = us48.merge(us48_income, on='STATE_FIPS')


# In[4]:

#get_ipython().magic(u'matplotlib inline')
us48.plot(color='blue')


# In[5]:

import bokeh as bk
from collections import OrderedDict
from bokeh.charts import Scatter, output_file, show
from bokeh.io import curdoc
from bokeh.models import HoverTool, LogColorMapper,CustomJS,Label,Span,LinearColorMapper
from bokeh.plotting import figure, show, output_file, ColumnDataSource
from bokeh.palettes import Viridis6 as palette
from bokeh.layouts import row,widgetbox,gridplot,layout
from bokeh.models.widgets import Button, RadioButtonGroup, Select, Slider


# In[6]:

def gpd_bokeh(df):
    """Convert geometries from geopandas to bokeh format"""
    nan = float('nan')
    lons = []
    lats = []
    for i,shape in enumerate(df.geometry.values):
        if shape.geom_type == 'MultiPolygon':
            gx = []
            gy = []
            ng = len(shape.geoms) - 1
            for j,member in enumerate(shape.geoms):
                xy = np.array(list(member.exterior.coords))
                xs = xy[:,0].tolist()
                ys = xy[:,1].tolist()
                gx.extend(xs)
                gy.extend(ys)
                if j < ng:
                    gx.append(nan)
                    gy.append(nan)
            lons.append(gx)
            lats.append(gy)

        else:     
            xy = np.array(list(shape.exterior.coords))
            xs = xy[:,0].tolist()
            ys = xy[:,1].tolist()
            lons.append(xs)
            lats.append(ys) 

    return lons,lats


# In[7]:

lons, lats = gpd_bokeh(us48)
palette.reverse()
color_mapper = LogColorMapper(palette=palette)
color1 = np.array(sns.color_palette("RdBu_r",48,).as_hex())
color2 = sns.color_palette("Blues",48,).as_hex()


# In[8]:

sources = {}
colors = {}
years = np.arange(1929,2010)
for year in years:
    array = us48['y_'+str(year)]
    temp = array.argsort()
    ranks = np.empty(len(array), int)
    ranks[temp] = np.arange(len(array))
    colors[year] = color1[ranks] #Rank colors
    sources[year] = ColumnDataSource(data=dict(
    	x=lons, 
    	y=lats, 
    	color = colors[year], 
    	name=us48.STATE_NAME, 
    	income = us48['y_'+str(year)]))

    #print sources[year]['income']

TOOLS = "pan,wheel_zoom,box_zoom,reset,hover,save,tap"

map = figure(title="US48", toolbar_location='above',tools=TOOLS,
          plot_width=600, plot_height=400,webgl=True)
mapP = map.patches('x', 'y', source=sources[years[0]],
          fill_color='color', fill_alpha=0.7, line_color="white", line_width=0.5)
yearLabel = Label(x=50, y=50, x_units='screen', y_units='screen',
                 text=str(1929), render_mode='css',text_font_size='35pt', text_color='#eeeeee')

map.add_layout(yearLabel)

hover = map.select_one(HoverTool)
hover.point_policy = "follow_mouse"
hover.tooltips = [
    ("Name", "@name"),
    ("Income", "@income"),
    ("(Long, Lat)", "($x, $y)"),
]


# In[9]:

#Get the rank
for year in xrange(1929,2010):
	array = us48['y_'+str(year)]
	temp = array.argsort()
	ranks = np.empty(len(array), int)
	ranks[temp] = np.arange(len(array))
	us48['r_'+str(year)] = ranks


# In[10]:

''' Line Plots
us48RankSorted = us48.sort_values(by = 'r_1929', ascending=True)
print list(us48RankSorted['Name'])


lines = figure(plot_width=600, plot_height=500, toolbar_location='above', y_range = list(us48RankSorted['Name']))


for i in xrange(0,48):
	rank = list(us48RankSorted.iloc[i,91:172])
	lines.line(years,rank,color = "grey",line_width=1)

#lines.multi_line(yearList,rankList,color = "red",line_width=1)
yearLine = Span(location=1929, dimension='height', line_color='red', line_width=2)
lines.add_layout(yearLine)

'''


# In[11]:

from math import pi
colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
mapper = LinearColorMapper(palette=colors)
years = np.arange(1929,2010)
years = [str(y )for y in years]
states = sorted(list(us48['Name']))
incomeDataForGrid = []
yearGrid = []
stateGrid = []
for y in years:
    for state in states:
        stateGrid.append(state)
        yearGrid.append(y)
        stateYear = int(us48[us48.Name == state]["r_"+str(y)])
        incomeDataForGrid.append(stateYear)
                        
sourceGrid = ColumnDataSource(
    data=dict(state=stateGrid, year=yearGrid, rate=incomeDataForGrid)
)
TOOLS = "hover,save,pan,box_zoom,wheel_zoom,tap"

g = figure(title="US Income per Household Rank (1929 - 2009)",
           x_range=years, y_range=list(reversed(states)),
           x_axis_location="above", plot_width=1100, plot_height=600,
           tools=TOOLS)
g.grid.grid_line_color = None
g.axis.axis_line_color = None
g.axis.major_tick_line_color = None
g.axis.major_label_text_font_size = "8pt"
g.axis.major_label_standoff = 0
g.xaxis.major_label_orientation = pi / 2

g.rect(x="year", y="state", width=1, height=1,
       source=sourceGrid,
       fill_color={'field': 'rate', 'transform': mapper},
       line_color=None)
       
g.select_one(HoverTool).tooltips = [
    ('date', '@state @year'),
    ('rate', '@rate'),
]
#show(g)  


# In[12]:

def slider_update(attrname, old, new):
    year = yearSlider.value
    yearLabel.text = str(year)
    mapP.data_source.data['income'] = list(sources[year].data['income'])
    mapP.data_source.data['color'] = list(sources[year].data['color'])
    push_notebook() 
    #yearLine.location = year

yearSlider = Slider(start=1929, end=2009, value=1929, step=1, title="Year")
yearSlider.on_change('value', slider_update)


# In[13]:

def animate_update():
    year = yearSlider.value + 1
    if year > 2009:
        year = 1929
    yearSlider.value = year
def animate():
    if button.label == '► Play':
        button.label = '❚❚ Pause'
        curdoc().add_periodic_callback(animate_update, 200)
    else:
        button.label = '► Play'
        curdoc().remove_periodic_callback(animate_update)

button = Button(label='► Play', width=60)
button.on_click(animate)


# In[ ]:




# In[14]:

l = layout([
  [map],
  [yearSlider,button],
])


# In[17]:

curdoc().add_root(l)


# In[18]:

show(l)


# In[ ]:



