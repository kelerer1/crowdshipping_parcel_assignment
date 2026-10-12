import osmnx as ox
import pandas as pd
from networkx.classes.multidigraph import MultiDiGraph
from dataclasses import dataclass, field
import geopandas as gpd


@dataclass
class AreaClass:
    """
    The class that contains the main statistics for a given area.
    """

    name: str
    G: MultiDiGraph = field(init=False)
    gdf: gpd.GeoDataFrame = field(init=False)
    area: float = field(init=False)
    stats: pd.Series = field(init=False)

    def __post_init__(self):
        self._get_graph()
        self._get_stats()

    def _get_graph(self):
        """
        Queries the Graph for a given area.
        """
        self.G = ox.graph.graph_from_place(self.name, network_type="drive")

    def _get_stats(self):
        """
        Queries the main statistics for a given area.
        """
        self.gdf = ox.geocoder.geocode_to_gdf(self.name)
        self.area = ox.projection.project_gdf(self.gdf).union_all().area
        self.stats = pd.Series(ox.stats.basic_stats(self.G, area=self.area), name=self.name)

    def save_gpkg_file(self):
        """
        Saves the info as a gpkg file.
        """
        ox.io.save_graph_geopackage(self.G, filepath=f'./{self.name[:4]}_graph.gpkg')
