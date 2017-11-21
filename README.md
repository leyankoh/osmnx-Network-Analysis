# Exploring network analysis using osmnx

So far I have only managed to get a basic formatted network map up.

The first: 4km buffer around Singapore's Raffles Place MRT. If I wanted to visualise the urban form of Singapore better however,
it would be make more sense to zoom in more on the map - but this is a good first attempt at styling the network!

![RP](https://i.imgur.com/ikTgp6j.png)

Next would be an isochrone map of Central London - more specifically, around Trafalgar Square (the central node that I took) - 1km (default) buffer.
The scales are 5, 10, 15, 20, 25 minute walk distances calculated along edges to nodes. Walking speed is taken as a standard 4.5km/h.

![traf_isochrone](https://i.imgur.com/taQJnGw.png)

This is the normalised polygonised map. Of course, ArcGIS might have a stronger package that allows for isochrones to be accurately plotted along networks (instead of crow's flies distance in this case).
Alternatively, QGIS offers some sort of network isochrone mapping support - though I believe that you'd have to use some combination of postGIS and pgRouting.

![traf_polygon](https://i.imgur.com/q7ISLNC.png)

# Accessibility Analysis: Central London

For this analysis, I only used POIs of amenities that included schools, doctors, pharmacies and restaurants
The following map was produced from the code (accessibilityAnalysis.py)
One way to improve the visualisation is not to make it seem like the yellow areas are more accessibile.
The fact is that it's actually quite the opposite - the yellow areas indicate that walking distance to the nearest amenity is higher.
So it seems accessibility to our arbitrary amenities in Central London is quite high

This could be pushed further if I used the point data loaded directly from the shapefiles I pulled from geofabrik. 
(although I'd have to do more work to bound the points to my bbox)

![Access_clondon](https://i.imgur.com/waEo0bI.png)

