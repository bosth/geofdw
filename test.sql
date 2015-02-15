DROP SERVER geojson CASCADE;
DROP SERVER geocode CASCADE;
DROP SERVER geocode_reverse CASCADE;

--GeoJSON
CREATE SERVER geojson foreign data wrapper multicorn options ( wrapper 'geofdw.GeoJSON' );
CREATE FOREIGN TABLE geojson_simple ( geom GEOMETRY, name TEXT, year TEXT ) SERVER geojson OPTIONS ( url 'https://raw.githubusercontent.com/MaptimeSEA/geojson/master/Dara.geojson', srid '900913' );
SELECT *, ST_AsText(geom) FROM geojson_simple;
CREATE FOREIGN TABLE geojson_countries ( geom GEOMETRY, name TEXT, id TEXT ) SERVER geojson OPTIONS ( url 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json' );
SELECT name, ST_NumGeometries(geom) AS polygons, ST_SRID(geom) AS srid FROM geojson_countries ORDER BY polygons DESC LIMIT 10;

--Forward Geocoding
CREATE SERVER geocode FOREIGN DATA WRAPPER multicorn OPTIONS ( wrapper 'geofdw.FGeocode' );
CREATE FOREIGN TABLE gc_google ( query TEXT, rank INTEGER, address TEXT, geom GEOMETRY ) SERVER geocode;
SELECT query, rank, address, ST_AsText(geom), ST_SRID(geom) FROM gc_google WHERE query = 'canada house' AND geom && ST_GeomFromEWKT('SRID=4326;POLYGON((50 2, 55 2, 55 -2, 50 -2, 50 2))');
SELECT query, rank, address, ST_AsText(geom), ST_SRID(geom) FROM gc_google WHERE query = 'canada house' AND ST_GeomFromEWKT('SRID=4326;POLYGON((50 2, 55 2, 55 -2, 50 -2, 50 2))') && geom;
SELECT query, rank, address, ST_AsText(geom), ST_SRID(geom) FROM gc_google WHERE query = 'canada house' AND ST_GeomFromEWKT('SRID=4326;POLYGON((50 2, 55 2, 55 -2, 50 -2, 50 2))') ~ geom;
CREATE FOREIGN TABLE gc_nominatim ( query TEXT, rank INTEGER, address TEXT, geom GEOMETRY ) SERVER geocode OPTIONS ( service 'nominatim');
SELECT query, rank, address, ST_AsText(geom), ST_SRID(geom) FROM gc_nominatim WHERE query = 'canada house' AND geom && ST_GeomFromEWKT('SRID=4326;POLYGON((50 2, 55 2, 55 -2, 50 -2, 50 2))');
CREATE FOREIGN TABLE gc_arcgis ( query TEXT, rank INTEGER, address TEXT, geom GEOMETRY ) SERVER geocode OPTIONS ( service 'arcgis');
SELECT query, rank, address, ST_AsText(geom), ST_SRID(geom) FROM gc_arcgis WHERE query = 'canada house';

--Reverse geocoding
CREATE SERVER geocode_reverse FOREIGN DATA WRAPPER multicorn OPTIONS ( wrapper 'geofdw.RGeocode' );
CREATE FOREIGN TABLE gc_google_reverse ( query GEOMETRY, rank INTEGER, address TEXT, geom GEOMETRY ) SERVER geocode_reverse;
SELECT ST_AsText(query), rank, address, ST_AsText(geom), ST_SRID(geom) FROM gc_google_reverse WHERE query = ST_SetSRID(ST_MakePoint(52, -110), 4326);
