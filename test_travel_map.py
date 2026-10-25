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


class MapOptionTests(unittest.TestCase):
    def test_country_card_renders_each_map_option_as_a_link(self):
        page = travel_map.build_selection_page(
            [
                {
                    "data": {
                        "trip": {
                            "country": "Norway",
                            "overview": {
                                "rank": 4,
                                "cost": {"relative_costs": "low_to_moderate"},
                            },
                        }
                    },
                    "map_path": "Norway/map-option-1.html",
                    "map_options": [
                        {
                            "label": "Bekijk kaart (optie 1)",
                            "map_path": "Norway/map-option-1.html",
                        },
                        {
                            "label": "Bekijk kaart (optie 2)",
                            "map_path": "Norway/map.html",
                        },
                    ],
                    "center": None,
                }
            ]
        )

        self.assertIn('href="Norway/map-option-1.html"', page)
        self.assertIn('href="Norway/map.html"', page)
        self.assertIn("Bekijk kaart (optie 1)", page)
        self.assertIn("Bekijk kaart (optie 2)", page)
        self.assertIn('onclick="event.stopPropagation()"', page)
        self.assertIn('data-cost="1.5"', page)
        self.assertIn("cost-low-to-moderate", page)

    def test_country_card_without_options_keeps_single_map_cta(self):
        page = travel_map.build_selection_page(
            [
                {
                    "data": {"trip": {"country": "Iceland", "overview": {}}},
                    "map_path": "Iceland/map.html",
                    "center": None,
                }
            ]
        )

        self.assertIn('<div class="cta">Bekijk kaart →</div>', page)


class TransferStopTests(unittest.TestCase):
    def test_map_renders_stops_from_the_option_one_yaml_schema(self):
        fmap = travel_map.build_map(
            {
                "trip": {
                    "country": "Norway",
                    "lodging_locations": [],
                    "transfer_routes": [
                        {
                            "from": "base_1",
                            "to": "base_2",
                            "description": "Geilo naar Aurland",
                            "en_route_stops": [
                                {
                                    "name": "Stegastein",
                                    "type": "viewpoint",
                                    "duration_minutes": 45,
                                    "notes": "Uitzicht over de fjord.",
                                    "coordinates": {"lat": 60.9085, "lon": 7.2137},
                                }
                            ],
                        }
                    ],
                }
            }
        )
        transfer_layer = next(
            child
            for child in fmap._children.values()
            if isinstance(child, folium.FeatureGroup)
            and child.layer_name == "◇ Tussenstops"
        )
        markers = [
            child
            for child in transfer_layer._children.values()
            if isinstance(child, folium.CircleMarker)
        ]

        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0].location, [60.9085, 7.2137])
        rendered_map = fmap.get_root().render()
        self.assertIn("Stegastein", rendered_map)
        self.assertIn("0.75 h", rendered_map)
        self.assertIn("Uitzicht over de fjord.", rendered_map)


class RoutePlannerTests(unittest.TestCase):
    def test_map_includes_route_planner_for_lodging_locations(self):
        fmap = travel_map.build_map(
            {
                "trip": {
                    "country": "Norway",
                    "lodging_locations": [
                        {
                            "id": "base_1",
                            "name": "Geilo",
                            "coordinates": {"lat": 60.5333, "lon": 8.2},
                        },
                        {
                            "id": "base_2",
                            "name": "Kalvåtn",
                            "coordinates": {"lat": 61.948, "lon": 6.525},
                        },
                    ],
                }
            }
        )
        rendered_map = fmap.get_root().render()

        self.assertIn("Routeplanner", rendered_map)
        self.assertIn("Verblijf \" + (index + 1) + \": \" + start.name", rendered_map)
        self.assertIn('"name": "Geilo"', rendered_map)
        self.assertIn(travel_map.OSRM_ROUTING_URL, rendered_map)
        self.assertIn('step.mode === "ferry"', rendered_map)
        self.assertIn("Routebeschrijving", rendered_map)
        self.assertIn("Land:", rendered_map)
        self.assertIn("Verblijfplaatsen", rendered_map)
        self.assertLess(rendered_map.index("Geilo"), rendered_map.index("Kalvåtn"))
        self.assertNotIn("Prioriteit (markergrootte)", rendered_map)
        self.assertNotIn("Terug naar landenselectie", rendered_map)


if __name__ == "__main__":
    unittest.main()
