DROP SERVER geojson CASCADE;
DROP SERVER geocode CASCADE;
DROP SERVER geocode_reverse CASCADE;
DROP SERVER random_point CASCADE;

------Random point
CREATE SERVER random_point FOREIGN DATA WRAPPER multicorn OPTIONS (wrapper 'geofdw.RandomPoint');
CREATE FOREIGN TABLE random_points(geom geometry(point)) SERVER random_point OPTIONS (min_x '-180', min_y '-90', max_x '180', max_y '90', num '10');
SELECT ST_AsText(geom) FROM random_points;

--GeoJSON
CREATE SERVER geojson foreign data wrapper multicorn options ( wrapper 'geofdw.fdw.GeoJSON' );
CREATE FOREIGN TABLE geojson_simple    (geom geometry, name TEXT, year TEXT) SERVER geojson OPTIONS (url 'https://raw.githubusercontent.com/MaptimeSEA/geojson/master/Dara.geojson', srid '900913');
CREATE FOREIGN TABLE geojson_countries (geom geometry, name TEXT, id TEXT)   SERVER geojson OPTIONS (url 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json');
SELECT *, ST_AsText(geom) FROM geojson_simple;
SELECT name, ST_NumGeometries(geom) AS polygons FROM geojson_countries ORDER BY polygons DESC LIMIT 10;

--Forward Geocoding
CREATE SERVER geocode FOREIGN DATA WRAPPER multicorn OPTIONS ( wrapper 'geofdw.FGeocode' );
CREATE FOREIGN TABLE gc_google    (query TEXT, rank INTEGER, address TEXT, geom geometry) SERVER geocode;
CREATE FOREIGN TABLE gc_arcgis    (query TEXT, rank INTEGER, address TEXT, geom geometry) SERVER geocode OPTIONS ( service 'arcgis');
CREATE FOREIGN TABLE gc_nominatim (query TEXT, rank INTEGER, address TEXT, geom geometry) SERVER geocode OPTIONS ( service 'nominatim');
SELECT rank, address, ST_AsText(geom) FROM gc_nominatim WHERE query = 'canada house' AND geom && ST_GeomFromEWKT('SRID=4326;POLYGON((2 50, 2 55, -2 55, -2 50, 2 50))');
SELECT rank, address, ST_AsText(geom) FROM gc_nominatim WHERE query = 'canada house' AND ST_GeomFromEWKT('SRID=4326;POLYGON((2 50, 2 55, -2 55, -2 50, 2 50))') && geom;
SELECT rank, address, ST_AsText(geom) FROM gc_nominatim WHERE query = 'canada house' AND ST_GeomFromEWKT('SRID=4326;POLYGON((2 50, 2 55, -2 55, -2 50, 2 50))') ~ geom;
SELECT rank, address, ST_AsText(geom) FROM gc_nominatim WHERE query = 'canada house';
SELECT rank, address, ST_AsText(geom) FROM gc_google WHERE query = 'canada house';
SELECT rank, address, ST_AsText(geom) FROM gc_arcgis WHERE query = 'canada house';

--Reverse geocoding
CREATE SERVER geocode_reverse FOREIGN DATA WRAPPER multicorn OPTIONS (wrapper 'geofdw.RGeocode');
CREATE FOREIGN TABLE gc_google_reverse (query geometry, rank INTEGER, address TEXT, geom geometry) SERVER geocode_reverse;
SELECT rank, address, ST_AsText(geom) FROM gc_google_reverse WHERE query = ST_SetSRID(ST_MakePoint(52, -110), 4326);
