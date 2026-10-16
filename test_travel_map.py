import unittest

import folium

import travel_map


class BasemapTests(unittest.TestCase):
    def test_country_map_uses_key_free_tiles(self):
        fmap = travel_map.build_map({"trip": {"country": "Iceland"}})
        tile_layers = [
            layer
            for layer in fmap._children.values()
            if isinstance(layer, folium.TileLayer)
        ]

        self.assertEqual(len(tile_layers), 1)
        tiles = tile_layers[0]
        self.assertEqual(
            tiles.tiles, "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        )
        self.assertEqual(tiles.options["attribution"], travel_map.BASEMAP_ATTRIBUTION)
        self.assertEqual(tiles.options["max_zoom"], 19)
        self.assertEqual(tiles.layer_name, "OpenStreetMap")
        self.assertIn("openstreetmap.org/copyright", tiles.options["attribution"])
        self.assertNotIn("carto", fmap.get_root().render().lower())

    def test_overview_uses_same_key_free_tiles(self):
        page = travel_map.build_selection_page([])

        self.assertIn(f"L.tileLayer('{travel_map.BASEMAP_TILES}'", page)
        self.assertIn(f"attribution: '{travel_map.BASEMAP_ATTRIBUTION}'", page)
        self.assertIn("maxZoom: 19", page)
        self.assertNotIn("carto", page.lower())


if __name__ == "__main__":
    unittest.main()
