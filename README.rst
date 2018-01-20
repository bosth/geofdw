geofdw
======

``geofdw`` is a collection of `PostGIS <http://postgis.net>`__-related
`foreign data
wrappers <https://wiki.postgresql.org/wiki/Foreign_data_wrappers>`__ for
`PostgreSQL <http://postgresql.org>`__ written in Python using the
`multicorn <http://multicorn.org>`__ extension. By using a FDW, you can
access spatial data through Postgres tables without having to import the
data first, which can be useful for dynamic or non-tabular data
available through web services.

Currently implemented forward data wrappers are:

-  FGeocode: forward geocoding
-  RGeocode: reverse geocoding
-  GeoJSON: online GeoJSON
-  RandomPoint: random point in a bounding box

``geofdw`` uses `plpygis <https://github.com/bosth/plpygis>`__ to
manipulate PostGIS geometries.

Examples
--------

FGeocode
~~~~~~~~

Create a single server for all forward geocoding tables:

::

    # CREATE SERVER fwd_geocode FOREIGN DATA WRAPPER multicorn OPTIONS ( wrapper 'geofdw.FGeocode' );

Create two tables, one using the GoogleV3 geocoder and one using
Nominatim:

::

    # CREATE FOREIGN TABLE fgc_google ( query TEXT, rank INTEGER, address TEXT, geom GEOMETRY ) SERVER fwd_geocode;
    # CREATE FOREIGN TABLE fgc_nominatim ( query TEXT, rank INTEGER, address TEXT, geom GEOMETRY ) SERVER fwd_geocode OPTIONS ( service 'nominatim');

Select results from the geocoder matching our query string:

::

    SELECT address, ST_AsText(geom) AS geom FROM fgc_google WHERE query = 'canada house' LIMIT 5;
                                             address                                         |             geom              
     ----------------------------------------------------------------------------------------+------------------------------------
      Canada House, London, UK                                                               | POINT Z (-0.1291 51.5077 0)
      Canada House, Temple Road, Blackrock, Co. Dublin, Ireland                              | POINT Z (-6.1756563 53.2994401 0)
      Canada House, Saint Stephen's Green, Dublin 2, Ireland                                 | POINT Z (-6.2576992 53.335963 0)
      Canada House, 29 Hampton Road, Twickenham, Greater London TW2 5QE, UK                  | POINT Z (-0.3443802 51.441739 0)
      Canada House, 272 Field End Road, Ruislip, Greater London HA4 9NA, UK                  | POINT Z (-0.3973435 51.5752994 0)

Perform the same query but using the Nominatim geocoder:

::

    # SELECT address, ST_AsText(geom) AS geom FROM fgc_nominatim WHERE query = 'canada house' LIMIT 5;
                                                                        address                                                                    |                    geom                    
    -----------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------
     High Commission of Canada, 5, Trafalgar Square, Covent Garden, City of Westminster, London, Greater London, England, SW1Y 5BJ, United Kingdom | POINT Z (-0.129104703393283 51.50782475 0)
     Canada House, West 54th Street, Diamond District, Manhattan, New York, NYC, New York, 10019, United States of America                         | POINT Z (-73.9758789212845 40.7609797 0)
     Canada House, Kololo Road, Governments Cantonment, Juba, Central Equatoria, South Sudan                                                       | POINT Z (31.5901769 4.8615639 0)
     Canada House, Justine Close, Nalumunye, Kazinga, Wakiso, Central 2, Central Region, Uganda                                                    | POINT Z (32.4868336484328 0.25676655 0)
     בית קנדה, 1, שבי ציון, רובע א', אשדוד, מחוז הדרום, 77452, מדינת ישראל                                                                         | POINT Z (34.64463585 31.8086878 0)

Influence the geocoder by restricting the query to a certain bounding
box (in this case, without the hint, Google will only return results in
the USA):

::

    # SELECT address, ST_AsText(geom) AS geom FROM fgc_google WHERE query = 'Water St' AND geom && ST_GeomFromEWKT('SRID=4326;POLYGON((50 2, 55 2, 55 -2, 50 -2, 50 2))');
                                    address                                 |               geom                
    ------------------------------------------------------------------------+-----------------------------------
     Water Street, Lavenham, Sudbury, Suffolk CO10 9RW, UK                  | POINT Z (0.7982752 52.1071416 0)
     Water Street, Stamford, Lincolnshire PE9 2NJ, UK                       | POINT Z (-0.4752917 52.649958 0)
     Water Street, Cambridge, Cambridgeshire CB4 1PA, UK                    | POINT Z (0.1474321 52.2184911 0)
     Water Street, Hampstead Norreys, Thatcham, West Berkshire RG18 0RU, UK | POINT Z (-1.2408465 51.4854726 0)
     Water Street, Burntwood, Staffordshire WS7 1AW, UK                     | POINT Z (-1.9355616 52.6839693 0)
     Water Street, Kettering, Northamptonshire NN16, UK                     | POINT Z (-0.7173979 52.4008413 0)
     Water Street, Birmingham, West Midlands B3 1HP, UK                     | POINT Z (-1.9028035 52.4854385 0)
     Water Street, London WC2R 3LA, UK                                      | POINT Z (-0.1136366 51.5118691 0)
