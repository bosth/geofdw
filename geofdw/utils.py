from geofdw.exception import CRSError


def crs_to_srid(crs):
    if crs is None:
        return None
    srid = crs.lower().replace("epsg:", "")
    try:
        return int(srid)
    except ValueError as e:
        raise CRSError(crs)
