import dash_core_components as dcc
import dash_html_components as html





bargraph_about = html.Div([
    html.Div("This chart ranks all (available) countries of the world for the selected dataset in a given year, in descending order."),
    html.Br(),
    html.Div("It will preselect the dataset selected in the underlying main map. Switch between the available years and change datasets at any time using the dropdown (clearing the dropdowns will cause the chart to default to its presets based on the main map and select the most current year)."),
    html.Br(),
    html.Div("Note the graph doesn't quite fit in 200+ countries along the horizontal axis, so you may need to zoom in to see a country name. To view the full width graph in all its glory download the chart to your local computer using the download button on the right.")
])

bargraph_instructions = html.Div([
    html.Div("1. Select or remove countries to highlight using the dropdown (type directly into the dropdowns to search faster)"),
    html.Br(),
    html.Div("2. Change datasets and year using the dropdown (country highlights are remembered) "),
    html.Br(),
    html.Div("3. Hover mouse on chart for tooltip data "),
    html.Br(),
    html.Div("4. Zoom-in with lasso-select (left-click-drag on a section of the chart). To reset the chart, double-click on it. "),
    html.Br(),
    html.Div("5. Download button can be used to download the chart or export data for all available countries in the selected dataset and year (if you want all years use the download button from the main map)"),
])

linegraph_about = html.Div([
    html.Div("This chart provides a facility to look at trends over time for a given dataset and sample of countries."),
    html.Br(),
    html.Div("Select as many countries as you wish and the graph will autoupdate and autoscale. Flick between datasets and your selected countries are remembered."),
    html.Br(),
    html.Div("Note that USA, China, India and UK have been preselected as defaults for illustrative purposes.")
])


linegraph_instructions = html.Div([
    html.Div("1. Select/remove countries using the dropdown (type directly into the dropdowns to search faster)"),
    html.Br(),
    html.Div("2. Change datasets using the dropdown (country selections are remembered)"),
    html.Br(),
    html.Div("3. Hover mouse on chart for tooltip data "),
    html.Br(),
    html.Div("4. Zoom-in with lasso-select (left-click-drag on a section of the chart). To reset the chart, double-click on it."),
    html.Br(),
    html.Div("5. Toggle selected countries on/off by clicking on the legend (far right)"),
    html.Br(),
    html.Div("6. Download button will export all countries and available years for the selected dataset"),
])

bubblegraph_about = html.Div([
    html.Div("This chart allows for a comparison of up to three datasets in a given year."),
    html.Br(),
    html.Div("Here's how it works: each data point (bubble) on the chart represents a country, and each axis (x, y, bubble size) represents the value for that country in the respective dataset. So this chart is effectively a typical scatter plot with an optional 3rd dimension as bubble size."), 
    html.Br(),
    html.Div("Mix and match dataset combinations and axes to find the interesting relationships between datasets. The plot comes preselected to a useful dataset combination to show how it would be typically used (hit the EXAMPLE button to reset it to this default). You can look at any combination of three datasets, provided that data is available for that combination. As you select/de-select datasets, the available years are re-queried in real-time, and will autoselect the most recent year that data is available for all sets."), 
    html.Br(),
    html.Div("If you just want to look at two datasets in a typical scatter plot, simply remove the dataset for the bubble dropdown.\n\nBubbles (country data points) are coloured based on their continent, and you can toggle continents on/off by clicking on the continent legend (far right)."),
])

bubblegraph_instructions = html.Div([
    html.Div("1. Don't panic"),
    html.Br(),
    html.Div("2. Select each dataset you want (the graph will attempt to build each time it detects a change)"),
    html.Br(),
    html.Div("3. Select a year from the available list (default is most recent)"),
    html.Br(),
    html.Div("4. Toggle logarithmic scale on/off for each axis"),
    html.Br(),
    html.Div("5. Toggle continents on/off using legend (far right)"),
    html.Br(),
    html.Div("6. Zoom-in with lasso-select (left-click-drag on a section of the chart). To reset the chart, double-click on it"),
    html.Br(),
    html.Div("7. Reset chart to a nice example with the button"),
    html.Br(),
    html.Div("8. Download your custom dataset combination and year for all countries using the download button"),
    html.Br(),
    html.Div("9. Clear all values by clicking the CLEAR button (or do it manually with the dropdowns)"),
    html.Br(),
])

sunburst_about = html.Div([
    html.Div("This alien looking pizza graph is actually called a sunburst chart. They allow you to make comparisons between quantitative datasets (i.e. stuff that adds up to a total number, like population or wealth) and contrast this with another dataset that paints each region a color based on it's value."),
    html.Br(),
    html.Div("The quantitative data set controls the size of the pizza slices, and the color dataset (pizza toppings) controls how they are coloured. Sunburst charts can do a lot of other cool stuff too, this is just one example."),
    html.Br(),
    html.Div("In this case each country is a slice of the pizza, with the size of the slice based on its value in proportion to the total."),
    html.Br(),
    html.Div("I've set the default to a well known combination, with population as the quantitative data, and life expectancy as the color. This allows you to see an nice proportional breakdown of population by contintent and region, and draw insights from the secondary dataset that colours the regions (in this case, life expectancy)."),
    html.Br(),
    html.Div("You are free to switch between datasets and I've done my best to keep the graph robust, although it doesn't always work. "),
    html.Br(),
    html.Div("Take special note that, like all the charts on this site, this graph is interactive. If you click on the continent it will animate and zoom in on that section and you can hover the mouse for tooltip data. Finally, note the color scheme will match that of the main map, which you can change in the settings area from the control panel on the main page."),
])

sunburst_instructions = html.Div([
    html.Div("1. Select quantitative dataset (default is population, and is recommended for most comparisons)"),
    html.Br(),
    html.Div("2. Select the color dataset"),
    html.Br(),
    html.Div("3. Choose from available years (year will default to the most recent intersection of both datasets)"),
    html.Br(),
    html.Div("4. Hit the example button to reset the chart to it's default"),
    html.Br(),
    html.Div("5. Download the currently displayed datasets for all countries and available years using the download button."),
])


jigsaw_about = html.Div([
    html.Div("This strange jigsaw puzzle map is a special 3d version of the main map."),
    html.Br(),
    html.Div("It's like a bar graph where every country is a bar! Each country (bar) extrudes upward into the sky to represent it's value; the higher the country stretches up, the higher it's value for the particular dataset in comparison to other countries."),
    html.Br(),
    html.Div("The chart is based on the underlying main map, inheriting the colour scheme and dataset chosen. You can hover the mouse over each country for tooltip data."),
    html.Br(),
    html.Div("The coolest thing about this is this is a true 3d rendered map, so you can zoom in and fly around like the world's worst flight simulator. The underlying technology is WebGL based on pyDeck and deck.gl, implemented through dash-deck. Note that Antarctica is not rendered in this map owing to a bug. "),
    html.Br(),
    html.Div("If you wish to change colours, go to settings from the control panel (bottom left) on the main map page."),
    html.Br(),
])


jigsaw_instructions = html.Div([
    html.Div("1. Zoom in/out with the mouse wheel"),
    html.Br(),
    html.Div("2. Change viewing angle by holding CTRL + left click hold-drag (or hold right mouse button and pan around)"),
    html.Br(),
    html.Div("3. Move around the map by left click-drag or the keyboard arrow keys"),
    html.Br(),
    html.Div("4. To change dataset, you will need to return to the main map and select another from the navigation menu. Then hit the jigsaw button again."),
    html.Br(),
    html.Div("5. Change colour scheme in the settings menu from the control panel (main map page)"),
    html.Br(),
    html.Div("6. Randomise colours of all countries with the 'jellybean' button"),
    html.Br(),    
])

globe_about = html.Div([
    html.Div("Imagine if the main map was a proper 3d Globe!"),
    html.Br(),
    html.Div("Welcome to 'Preparation H', the nerdiest part of this project. What you see before you is a fully interactive 3d representation of the underlying main map! "),
    html.Br(),
    html.Div("You can zoom in/out and pan the globe around. Hovering the mouse over a country will show it's value for the current dataset and year."),
    html.Br(),    
    html.Div("The globe inherits the colour and series from the underlying map. To change datasets go to the main map and choose another datset from the navigation menu. To change colour scheme (which is nice) go to settings in control panel, and then re-run the globe. More to come on this visualisation and I'll be adding knobs and dials etc."),
    html.Br(),
    html.Div("What ever happens never EVER press the JELLYBEAN MODE. My servers will catch fire."),
    html.Br(),
    html.Div("If you are interested in the underlying technology used to make this globe, it is based on DeckGL and implemented by "),
    html.A("Dash Deck", href='https://dash.gallery/dash-deck-explorer/globe-view', target="_blank")
    
])

globe_instructions = html.Div([
    html.Div("1. Be amazed at this crazy but kind-of-cool visualisation"),
    html.Br(),
    html.Div("2. Zoom in, zoom out with the mouse wheel. Turn the globe using left mouse button click-hold-drag. Keyboard arrow keys also work."),
    html.Br(),
    html.Div("3. Hover over a country to view the datapoint for the current dataset"),
    html.Br(),
    html.Div("4. To change dataset, go back to main page and select another, and hit globe again."),
    html.Br(),
    html.Div("5. Never... EVER push the jellybean mode button. It will break everything!"),    
])





