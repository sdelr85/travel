import unittest
import json
import re
from html import escape

import folium
import yaml

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

    def test_norway_option_one_yaml_renders_all_transfer_stops(self):
        option_path = travel_map.HERE / "Norway" / "info-option-1.yaml"
        with option_path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
        transfers = data["trip"]["transfer_routes"]
        stops = [
            stop
            for transfer in transfers
            for stop in transfer.get("en_route_stops", [])
        ]
        fmap = travel_map.build_map(data)
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

        self.assertTrue(all("coordinates" in stop for stop in stops))
        self.assertEqual(len(markers), len(stops))


class RoutePlannerTests(unittest.TestCase):
    def test_numbered_locations_are_only_added_while_planner_is_enabled(self):
        planner = travel_map._route_planner_html(
            "test_map",
            [{"name": "Geilo", "coordinates": {"lat": 60.5333, "lon": 8.2}}],
        )

        self.assertIn("const numberedLocations = L.layerGroup();", planner)
        self.assertIn('const label = (index + 1) + ". " + location.name;', planner)
        self.assertIn('className: "route-planner-number"', planner)
        self.assertIn("html: String(index + 1)", planner)
        self.assertIn("map.removeLayer(numberedLocations);", planner)
        self.assertIn("numberedLocations.addTo(map);", planner)

    def test_explicit_route_order_must_include_each_location_once(self):
        for order in (["base_1", "base_1"], ["unknown"], [], "base_1"):
            with self.subTest(order=order):
                with self.assertRaisesRegex(ValueError, "exactly once"):
                    travel_map.build_map({"trip": {
                        "lodging_locations": [{
                            "id": "base_1",
                            "name": "Geilo",
                            "coordinates": {"lat": 60.5333, "lon": 8.2},
                        }],
                        "route_planner_order": order,
                    }})

    def test_norway_numbering_follows_chronological_stay_order(self):
        with (travel_map.HERE / "Norway" / "info-option-1.yaml").open(
            encoding="utf-8"
        ) as file:
            data = yaml.safe_load(file)
        rendered = travel_map.build_map(data).get_root().render()
        locations = json.loads(
            re.search(r"const routeLocations = (.*);", rendered)[1]
        )
        self.assertEqual(
            [location["name"] for location in locations],
            ["Hirtshals", "Geilo / Hardangervidda",
             "Hornindal / Haugen / Kalvåtn", "Sykkylven / Stranda",
             "Bergen (Fridalen)"],
        )

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
        self.assertIn("route-planner-start", rendered_map)
        self.assertIn("routeLocations.forEach", rendered_map)
        self.assertIn("Kies een bestemming als startpunt", rendered_map)
        self.assertIn("map.on(\"click\"", rendered_map)
        self.assertNotIn("route-planner-end", rendered_map)
        self.assertIn('"name": "Geilo"', rendered_map)
        self.assertIn(travel_map.OSRM_ROUTING_URL, rendered_map)
        self.assertIn('step.mode === "ferry"', rendered_map)
        self.assertIn("Routebeschrijving", rendered_map)
        self.assertIn('id="route-planner-enabled"', rendered_map)
        self.assertIn(
            '<input type="checkbox" id="route-planner-enabled" ',
            rendered_map,
        )
        self.assertIn("let routePlannerEnabled = false;", rendered_map)
        self.assertIn('routeToggle.addEventListener("change"', rendered_map)
        self.assertIn("if (routePlannerEnabled && destination)", rendered_map)
        self.assertGreaterEqual(
            rendered_map.count("if (!routePlannerEnabled) return;"),
            2,
        )
        self.assertIn("Land:", rendered_map)
        self.assertIn("Verblijfplaatsen", rendered_map)
        self.assertLess(rendered_map.index("Geilo"), rendered_map.index("Kalvåtn"))
        self.assertNotIn("Prioriteit (markergrootte)", rendered_map)
        self.assertNotIn("Terug naar landenselectie", rendered_map)

    def test_planner_starts_collapsed_and_only_shows_body_when_enabled(self):
        planner = travel_map._route_planner_html(
            "test_map",
            [{"name": "Geilo", "coordinates": {"lat": 60.5333, "lon": 8.2}}],
        )

        self.assertIn('id="route-planner-body" hidden>', planner)
        self.assertIn('aria-controls="route-planner-body" aria-expanded="false"', planner)
        self.assertLess(
            planner.index('id="route-planner-enabled"'),
            planner.index('id="route-planner-body"'),
        )
        self.assertIn("plannerBody.hidden = !routePlannerEnabled;", planner)
        self.assertIn(
            'routeToggle.setAttribute("aria-expanded", String(routePlannerEnabled));',
            planner,
        )
        self.assertIn("max-height: min(360px, 50vh); overflow-y: auto;", planner)
        self.assertIn(".route-planner-body { max-height: 35vh; }", planner)
        self.assertIn(".route-planner-body { max-height: 20vh; }", planner)
        self.assertIn(
            ".leaflet-left .route-planner-control {\n            clear: none;",
            planner,
        )
        self.assertIn("width: min(220px, calc(100vw - 120px));", planner)

    def test_layer_list_is_responsive_even_without_route_locations(self):
        rendered_map = travel_map.build_map(
            {"trip": {"country": "Iceland"}}
        ).get_root().render()

        self.assertIn(
            'window.matchMedia("(max-width: 600px), (max-height: 500px)")',
            rendered_map,
        )
        self.assertIn("if (mobile.matches) layers.collapse();", rendered_map)
        self.assertIn("else layers.expand();", rendered_map)
        self.assertIn('mobile.addEventListener("change", updateLayerControl);', rendered_map)

    def test_norway_option_one_includes_bergen_and_hirtshals_as_route_points(self):
        option_path = travel_map.HERE / "Norway" / "info-option-1.yaml"
        with option_path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
        fmap = travel_map.build_map(data)
        rendered_map = fmap.get_root().render()
        route_points_layer = next(
            child
            for child in fmap._children.values()
            if isinstance(child, folium.FeatureGroup)
            and child.layer_name == "⚓ Start- en eindpunten"
        )
        route_point_markers = [
            child
            for child in route_points_layer._children.values()
            if isinstance(child, folium.Marker)
        ]
        final_layer = next(
            child
            for child in fmap._children.values()
            if isinstance(child, folium.FeatureGroup)
            and child.layer_name == "🏠 Bergen (Fridalen)"
        )
        final_markers = [
            child
            for child in final_layer._children.values()
            if isinstance(child, folium.Marker)
        ]
        bounds = fmap.get_bounds()

        self.assertIn('"name": "Bergen (Fridalen)"', rendered_map)
        self.assertIn('"name": "Hirtshals"', rendered_map)
        self.assertIn("Eindbestemming · ook startpunt routeplanner", rendered_map)
        self.assertEqual(len(route_point_markers), 1)
        self.assertEqual(route_point_markers[0].location, [57.5884, 9.97])
        self.assertEqual(route_point_markers[0].icon.options["icon"], "home")
        self.assertEqual(len(final_markers), 1)
        self.assertEqual(final_markers[0].location, [60.3695, 5.3582])
        self.assertEqual(final_markers[0].icon.options["icon"], "home")
        self.assertLessEqual(bounds[0][0], 57.5884)
        self.assertGreaterEqual(bounds[1][0], 57.5884)
        self.assertLessEqual(bounds[0][1], 9.97)
        self.assertGreaterEqual(bounds[1][1], 9.97)
        self.assertIn("Start- en eindpunt voor de routeplanner", rendered_map)
        self.assertNotIn("route-planner-end", rendered_map)

    def test_norway_option_one_accommodation_urls_are_clickable(self):
        option_path = travel_map.HERE / "Norway" / "info-option-1.yaml"
        with option_path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
        trip = data["trip"]
        locations = [
            *trip["lodging_locations"],
            trip["final_stop"],
            *trip["route_planner_locations"],
        ]
        urls = [location["accommodation_url"] for location in locations]
        rendered_map = travel_map.build_map(data).get_root().render()

        for url in urls:
            self.assertIn(escape(url, quote=True), rendered_map)
        self.assertEqual(
            rendered_map.count('target="_blank" rel="noopener noreferrer"'),
            len(urls),
        )
        self.assertIn("Airbnb: Soltun Geilo", rendered_map)
        self.assertIn("Booking.com: Central 4 room, Bergen", rendered_map)

    def test_accommodation_url_must_use_http_or_https(self):
        with self.assertRaisesRegex(ValueError, "absolute HTTP\\(S\\) URL"):
            travel_map.build_map(
                {
                    "trip": {
                        "lodging_locations": [
                            {
                                "name": "Unsafe listing",
                                "coordinates": {"lat": 60, "lon": 5},
                                "accommodation_url": "javascript:alert(1)",
                            }
                        ]
                    }
                }
            )


if __name__ == "__main__":
    unittest.main()
