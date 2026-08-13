"""Interactive travel maps: country selection screen + per-country Folium maps."""

import pathlib
import statistics

import folium
import yaml

# ── paths ─────────────────────────────────────────────────────────────────────
HERE = pathlib.Path(__file__).parent
OUTPUT_SELECTION = HERE / "index.html"

# ISO 3166-1 alpha-2 codes used with the flag-icons CSS library
COUNTRY_ISO = {
    "Iceland": "is",
    "Norway": "no",
    "Scotland": "gb-sct",
    "Faroe Islands": "fo",
    "Azores": "pt",
    "Canada": "ca",
    "Montenegro": "me",
    "New Zealand": "nz",
    "Patagonia": "ar",  # Argentina
    "South Africa": "za",
    "Namibia": "na",
    "Georgia": "ge",
    "Costa Rica": "cr",
    "Italy (Dolomites)": "it",
    "Switzerland": "ch",
    "Alaska": "us",
    "Reunion Island": "re",
    "Japan": "jp",
}

FLAG_ICONS_CDN = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">'

COUNTRY_NL = {
    "Iceland": "IJsland",
    "Norway": "Noorwegen",
    "Scotland": "Schotland",
    "Faroe Islands": "Faeröer",
    "Azores": "Azoren",
    "Montenegro": "Montenegro",
    "New Zealand": "Nieuw-Zeeland",
    "Patagonia": "Patagonë",
    "South Africa": "Zuid-Afrika",
    "Namibia": "Namibië",
    "Georgia": "Georgië",
    "Italy (Dolomites)": "Italië (Dolomieten)",
    "Switzerland": "Zwitserland",
    "Reunion Island": "Réunion",
}

# ── colour palette (one per base + final stop) ───────────────────────────────
BASE_COLORS = [
    {"hex": "#e74c3c", "folium": "red"},
    {"hex": "#2980b9", "folium": "blue"},
    {"hex": "#27ae60", "folium": "green"},
    {"hex": "#8e44ad", "folium": "purple"},
    {"hex": "#2c3e50", "folium": "darkblue"},
    {"hex": "#16a085", "folium": "darkgreen"},
    {"hex": "#d35400", "folium": "darkred"},
    {"hex": "#f39c12", "folium": "orange"},
]
FINAL_STOP_COLOR = {"hex": "#e67e22", "folium": "orange"}

# ── priority → display info ───────────────────────────────────────────────────
PRIORITY_META = {
    "must_do": {"stars": "★★★★", "label": "Absoluut doen", "radius": 11},
    "highly_recommended": {"stars": "★★★☆", "label": "Sterk aanbevolen", "radius": 9},
    "if_time": {"stars": "★★☆☆", "label": "Als er tijd is", "radius": 7},
    "optional_paid_activity": {
        "stars": "★☆☆☆",
        "label": "Optionele betaalde activiteit",
        "radius": 6,
    },
}
DEFAULT_PRIORITY = {"stars": "☆☆☆☆", "label": "Geen beoordeling", "radius": 6}


def _priority(p: str) -> dict:
    return PRIORITY_META.get(p, DEFAULT_PRIORITY)


# Dutch labels for attraction/stop types
TYPE_NL = {
    "adventure": "avontuur",
    "adventure_activity": "avontuurlijke activiteit",
    "alpine_hike": "alpine wandeling",
    "alpine_hiking": "alpine wandeling",
    "alpine_lake": "alpenmeer",
    "alpine_meadow": "alpenweiland",
    "alpine_route": "alpenroute",
    "alpine_valley": "alpenvallei",
    "architecture": "architectuur",
    "arrival_point": "aankomstpunt",
    "backup_viewpoint": "alternatief uitkijkpunt",
    "basalt_formations": "basaltformaties",
    "beach": "strand",
    "beach_hike": "strandwandeling",
    "black_sand_beach": "zwart zandstrand",
    "boat_trip": "boottocht",
    "boat_trip_lake": "boottocht meer",
    "boat_trip_sea_cliffs": "boottocht zeekliffen",
    "boat_trip_short": "korte boottocht",
    "cable_car_hike": "kabelbaan en wandeling",
    "cable_car_viewpoint": "kabelbaan uitkijkpunt",
    "canyon": "canyon",
    "canyon_hiking": "canyon wandeling",
    "canyon_scenic_drive": "canyon schilderachtige rit",
    "canyon_viewpoint": "canyon uitkijkpunt",
    "canyon_walk": "canyon wandeling",
    "canyon_waterfall": "canyon waterval",
    "castle": "kasteel",
    "castle_ruin": "kasteelruïne",
    "cave": "grot",
    "church_viewpoint": "kerk uitkijkpunt",
    "city": "stad",
    "city_experience": "stadsbeleving",
    "city_or_meal_stop": "stadsstop of maaltijdstop",
    "city_overnight_stop": "stad overnachting",
    "city_stop": "stadsstop",
    "city_stop_or_overnight": "stadsstop of overnachting",
    "city_walk": "stadswandeling",
    "cliffs": "kliffen",
    "cloud_forest": "wolkenbos",
    "coastal_landscape": "kustlandschap",
    "coastal_scenic": "schilderachtige kust",
    "coastal_town": "kuststad",
    "coastal_viewpoint": "kust uitkijkpunt",
    "coastal_village": "kustdorp",
    "coastal_walk": "kustwandeling",
    "coastal_waterfalls": "kustwatervallen",
    "crater": "krater",
    "crater_hike": "kraterwandeling",
    "crater_lake": "kratermeer",
    "cultural_landmark": "cultureel monument",
    "cultural_site": "culturele bezienswaardighed",
    "desert_landscape": "woestijnlandschap",
    "desert_stop": "woestijnstop",
    "dune_excursion": "duinexcursie",
    "dune_hike": "duinwandeling",
    "dunes": "duinen",
    "engineering_landmark": "ingenieursbouwwerk",
    "family_activity": "gezinsactiviteit",
    "family_cultural_activity": "culturele gezinsactiviteit",
    "ferry_hike_viewpoint": "veerboot wandeling uitkijkpunt",
    "film_location": "filmlocatie",
    "fishing_town": "visserstadje",
    "fishing_village": "vissersdorp",
    "fjord": "fjord",
    "fjord_cruise": "fjordcruise",
    "fjord_village": "fjorddorp",
    "fjord_village_lunch_stop": "fjorddorp lunchtussenstop",
    "forest_walk": "boswandeling",
    "fortress": "vesting",
    "geological_site": "geologische locatie",
    "geology": "geologie",
    "geology_hike": "geologische wandeling",
    "geothermal": "geothermisch",
    "geothermal_area": "geothermisch gebied",
    "geothermal_bath": "geothermisch bad",
    "geothermal_beach": "geothermisch strand",
    "geothermal_hike": "geothermische wandeling",
    "geothermal_park": "geothermisch park",
    "geothermal_pool": "geothermisch bad",
    "glacial_lake": "gletsjermeer",
    "glacier": "gletsjer",
    "glacier_hike": "gletsjerwandeling",
    "glacier_lagoon": "gletsjerlaguune",
    "glacier_lake_hike": "gletsjermeer wandeling",
    "glacier_viewpoint": "gletsjer uitkijkpunt",
    "glacier_walk": "gletsjerwandeling",
    "gondola": "gondel",
    "gorge": "kloof",
    "granite_mountains": "granieten bergen",
    "guided_hike_or_boat_tour": "begeleide wandeling of boottocht",
    "harry_potter_highlight": "Harry Potter locatie",
    "hike": "wandeling",
    "hike_hot_spring": "wandeling hete bron",
    "hike_viewpoint": "wandeling uitkijkpunt",
    "hiking": "wandelen",
    "hiking_viewpoint": "wandelen uitkijkpunt",
    "hill_town": "heuvelstadje",
    "historic_loch": "historisch loch",
    "historic_site": "historische locatie",
    "historic_town": "historische stad",
    "historic_village": "historisch dorp",
    "hot_spring": "hete bron",
    "iconic_hike": "iconische wandeling",
    "iconic_viewpoint": "iconisch uitkijkpunt",
    "immersive_experience": "meeslepende beleving",
    "island_day_trip": "eiland dagtocht",
    "island_drive_villages_beaches": "eilandrit dorpen en stranden",
    "island_ferry_hike_puffins": "veerboot wandeling papegaaiduikers",
    "lagoon": "lagune",
    "lake": "meer",
    "lake_scenic_drive": "meer schilderachtige rit",
    "lake_scenic_drive_walk": "meer schilderachtige rit en wandeling",
    "lake_walk": "meerwandeling",
    "landmark": "bezienswaardigheid",
    "landscape": "landschap",
    "lava_field": "lavaveld",
    "lava_formations": "lavaformaties",
    "monastery": "klooster",
    "monument": "monument",
    "mountain": "berg",
    "mountain_area": "berggebied",
    "mountain_hike": "bergwandeling",
    "mountain_hike_viewpoint": "bergwandeling uitkijkpunt",
    "mountain_landscape": "berglandschap",
    "mountain_national_park": "nationaal park (berg)",
    "mountain_pass": "bergpas",
    "mountain_railway": "bergspoorweg",
    "mountain_railway_viewpoint": "bergspoorweg uitkijkpunt",
    "mountain_resort": "bergresort",
    "mountain_scenery": "bergscenerie",
    "mountain_town": "bergstadje",
    "mountain_viewpoint": "berg uitkijkpunt",
    "mountain_village": "bergdorp",
    "mountains": "bergen",
    "museum": "museum",
    "museum_history": "historisch museum",
    "national_park": "nationaal park",
    "nature": "natuur",
    "nature_history": "natuur en geschiedenis",
    "old_town": "historische binnenstad",
    "own_car_from_belgium": "eigen auto vanuit België",
    "paid_activity": "betaalde activiteit",
    "plateau_hike": "plateauwandeling",
    "plateau_hiking": "plateauwandeling",
    "plateau_scenic_drive_hike": "plateau schilderachtige rit en wandeling",
    "practical_overnight_stop": "praktische overnachting",
    "rainforest": "regenwoud",
    "rainforest_beach": "regenwoud strand",
    "rainforest_hike": "regenwoudwandeling",
    "rainforest_walk": "regenwoudwandeling",
    "relaxation": "ontspanning",
    "rock_art": "rotstekeningen",
    "route_choice": "routekeuze",
    "ruins_historic_site": "ruïnes historische locatie",
    "safari": "safari",
    "scenic_cable_car": "schilderachtige kabelbaan",
    "scenic_drive": "schilderachtige rit",
    "scenic_drive_plateau": "schilderachtige rit plateau",
    "scenic_flight": "schilderachtige vlucht",
    "scenic_hiking_area": "schilderachtig wandelgebied",
    "scenic_lake": "schilderachtig meer",
    "scenic_loch": "schilderachtig loch",
    "scenic_mountain_road": "schilderachtige bergweg",
    "scenic_pass": "schilderachtige bergpas",
    "scenic_town": "schilderachtig stadje",
    "scenic_train": "schilderachtige treinrit",
    "scenic_valley": "schilderachtige vallei",
    "scenic_viewpoint": "schilderachtig uitkijkpunt",
    "scenic_village": "schilderachtig dorp",
    "scenic_walk": "schilderachtige wandeling",
    "sea_stack_viewpoint": "zeestapel uitkijkpunt",
    "seal_colony": "zeehondenkolonie",
    "short_hike": "korte wandeling",
    "short_hike_viewpoint": "korte wandeling uitkijkpunt",
    "short_island_ferry_walk": "korte eiland veerboot wandeling",
    "small_hot_spring": "kleine hete bron",
    "snorkeling": "snorkelen",
    "snorkeling_wildlife": "snorkelen wildlife",
    "strenuous_hike": "zware wandeling",
    "thermal_pool": "thermaal bad",
    "town": "stadje",
    "town_mountain_valley": "stad bergvallei",
    "town_outdoor_activities": "stad buitenactiviteiten",
    "town_stop": "stadstussenstop",
    "town_walk": "stadswandeling",
    "town_walk_culture": "stadswandeling cultuur",
    "tramway": "tram",
    "tunnel_route_feature": "tunnelroute",
    "unesco_landscape": "UNESCO landschap",
    "urban_hike": "stedelijke wandeling",
    "urban_park": "stadspark",
    "valley": "vallei",
    "valley_hike": "valleiwandeling",
    "valley_walk": "valleiwandeling",
    "viewpoint": "uitkijkpunt",
    "viewpoint_hike": "uitkijkpunt wandeling",
    "viewpoint_paid_activity": "uitkijkpunt betaalde activiteit",
    "village": "dorp",
    "village_beach_viewpoint": "dorp strand uitkijkpunt",
    "village_coast": "kustdorp",
    "village_drive": "dorpsrit",
    "village_fjord_view": "dorp fjorduitzicht",
    "village_gorge_walk": "dorp kloofwandeling",
    "village_lagoon_landscape": "dorp laguunlandschap",
    "village_lake_walk": "dorp meerwandeling",
    "village_mountain_viewpoint": "dorp berg uitkijkpunt",
    "village_river_gorge": "dorp rivierkloof",
    "village_short_walk": "dorp korte wandeling",
    "village_viewpoint": "dorp uitkijkpunt",
    "volcanic_area": "vulkanisch gebied",
    "volcanic_caldera": "vulkanische caldera",
    "volcanic_coastline": "vulkanische kustlijn",
    "volcanic_hike": "vulkanische wandeling",
    "volcanic_lake": "vulkanisch meer",
    "volcanic_landscape": "vulkanisch landschap",
    "volcano": "vulkaan",
    "volcano_center": "vulkaancentrum",
    "volcano_hike": "vulkaanwandeling",
    "volcano_scenery": "vulkaanscenerie",
    "walk": "wandeling",
    "water_activity": "wateractiviteit",
    "waterfall": "waterval",
    "waterfall_geology": "waterval geologie",
    "waterfall_hike": "watervalwandeling",
    "waterfall_park": "watervalpark",
    "waterfall_viewpoint": "waterval uitkijkpunt",
    "waterfall_village_viewpoint": "waterval dorp uitkijkpunt",
    "waterfall_walk": "watervalwandeling",
    "wildlife": "wildlife",
    "wildlife_boat_trip": "wildlife boottocht",
    "wildlife_walk": "wildlife wandeling",
    "bridge_crossing": "brugoverstapping",
    "canal_landscape": "kanallandschap",
}


def _type_label(t: str) -> str:
    return TYPE_NL.get(t, t.replace("_", " ").title()) if t else "—"


TRANSFER_ROLE_NL = {
    "route_segment": "routegedeelte",
    "scenic_detour": "schilderachtige omweg",
    "overnight_stop": "overnachtingsstop",
}


def _transfer_role_label(role: str) -> str:
    return TRANSFER_ROLE_NL.get(role, role.replace("_", " ").title()) if role else ""


TOOLTIP_STYLE = (
    "font-family:sans-serif;font-size:14px;"
    "width:min(320px,calc(100vw - 32px));max-width:calc(100vw - 32px);"
    "min-width:0;white-space:normal;overflow-wrap:anywhere;"
)


def _lodging_tooltip(loc: dict, color: str) -> str:
    nights = loc.get("stay_nights", "?")
    region = loc.get("region", "")
    note = loc.get("planning_note", "")
    note_html = f'<br><i style="color:#666;font-size:14px">{note}</i>' if note else ""
    return (
        f'<div style="{TOOLTIP_STYLE}">'
        f'<b style="color:{color};font-size:16px">🏨 {loc["name"]}</b><br>'
        f'<span style="color:#555">{region}</span><br>'
        f'<hr style="margin:4px 0">'
        f"<b>Nachten:</b> {nights}"
        f"{note_html}"
        f"</div>"
    )


def _attraction_tooltip(attr: dict, base_name: str, color: str) -> str:
    pm = _priority(attr.get("priority", ""))
    hours = attr.get("visit_duration_hours", "?")
    drive = attr.get("drive_time_minutes")
    drive_str = f"{drive} min rijden" if drive else ""
    atype = _type_label(attr.get("type", ""))
    strategy = attr.get("visit_strategy", {})
    note = strategy.get("notes", "")
    evening = strategy.get("good_for_evening_visit")
    lines = [
        f'<div style="{TOOLTIP_STYLE}">',
        f'<b style="font-size:15px">{attr["name"]}</b><br>',
        f'<span style="color:{color};font-weight:bold">{pm["stars"]} {pm["label"]}</span><br>',
        '<hr style="margin:4px 0">',
        f"<b>Type:</b> {atype}<br>",
        f"<b>Duur:</b> {hours} h",
    ]
    if drive_str:
        lines.append(f"<br><b>Vanaf basis:</b> {drive_str}")
    if evening is True:
        lines.append(
            '<br><span style="color:#e67e22">🌅 Geschikt voor avondbezoek</span>'
        )
    lines.append(f'<br><b>Basis:</b> <span style="color:{color}">{base_name}</span>')
    if note:
        lines.append(f'<br><i style="color:#666;font-size:13px">{note}</i>')
    lines.append("</div>")
    return "".join(lines)


def _transfer_stop_tooltip(stop: dict, route_desc: str, color: str) -> str:
    pm = _priority(stop.get("priority", ""))
    hours = stop.get("stop_duration_hours", "?")
    atype = _type_label(stop.get("type", ""))
    role = _transfer_role_label(stop.get("transfer_role", ""))
    note = stop.get("planning_note", "")
    role_html = f"<br><b>Rol:</b> {role}" if role else ""
    note_html = f'<br><i style="color:#666;font-size:13px">{note}</i>' if note else ""
    return (
        f'<div style="{TOOLTIP_STYLE}">'
        f'<b style="font-size:15px">🔷 {stop["name"]}</b><br>'
        f'<span style="color:{color};font-weight:bold">{pm["stars"]} {pm["label"]}</span><br>'
        f'<hr style="margin:4px 0">'
        f"<b>Type:</b> {atype}<br>"
        f"<b>Stopduur:</b> {hours} h"
        f"{role_html}"
        f'<br><b>Onderweg:</b> <span style="color:{color}">{route_desc}</span>'
        f"{note_html}"
        f"</div>"
    )


def _final_stop_tooltip(stop: dict) -> str:
    color = FINAL_STOP_COLOR["hex"]
    attractions = stop.get("attractions", [])
    # attractions are now full objects; fall back to plain strings for safety
    items = "".join(
        f"<li>{a['name'] if isinstance(a, dict) else a}</li>" for a in attractions
    )
    note = stop.get("planning_note", "")
    note_html = f'<br><i style="color:#666;font-size:13px">{note}</i>' if note else ""
    return (
        f'<div style="{TOOLTIP_STYLE}">'
        f'<b style="color:{color};font-size:16px">🏙️ {stop["name"]}</b><br>'
        f'<span style="color:#555">Eindbestemming</span>'
        f'<hr style="margin:4px 0">'
        f"<ul style='margin:4px 0 0 14px;padding:0'>{items}</ul>"
        f"{note_html}"
        f"</div>"
    )


def build_map(data: dict) -> folium.Map:
    trip = data["trip"]
    bases = trip.get("lodging_locations", [])
    final = trip.get("final_stop")
    final_name = final["name"] if final else "Eindbestemming"
    country = trip.get("country", "")
    iso = COUNTRY_ISO.get(country, "")
    display_country = COUNTRY_NL.get(country, country)
    flag_html = (
        f'<span class="fi fi-{iso}" style="border-radius:3px;margin-right:5px"></span>'
        if iso
        else ""
    )

    # compute center from lodging locations and let fit_bounds set the zoom
    base_coords = [
        [loc["coordinates"]["lat"], loc["coordinates"]["lon"]]
        for loc in bases
        if "coordinates" in loc
    ]
    center = (
        [
            statistics.mean(c[0] for c in base_coords),
            statistics.mean(c[1] for c in base_coords),
        ]
        if base_coords
        else [0.0, 0.0]
    )

    fmap = folium.Map(location=center, zoom_start=6, tiles="CartoDB positron")
    if len(base_coords) >= 2:
        fmap.fit_bounds(base_coords)

    # ── legend ────────────────────────────────────────────────────────────────
    bases = trip.get("lodging_locations", [])
    legend_rows = ""
    for i, loc in enumerate(bases):
        c = BASE_COLORS[i % len(BASE_COLORS)]["hex"]
        legend_rows += (
            f'<tr><td><span style="color:{c};font-size:18px">■</span></td>'
            f'<td style="padding-left:6px">{loc["name"]}</td></tr>'
        )
    if final:
        legend_rows += (
            f'<tr><td><span style="color:{FINAL_STOP_COLOR["hex"]};font-size:18px">■</span></td>'
            f'<td style="padding-left:6px">{final_name} (eindbestemming)</td></tr>'
        )
    priority_rows = "".join(
        f'<tr><td>{v["stars"]}</td><td style="padding-left:6px">{v["label"]}</td></tr>'
        for v in PRIORITY_META.values()
    )
    legend_html = f"""
    <style>
        @media (max-width: 600px) {{
            .travel-legend {{
                bottom: 8px !important;
                left: 8px !important;
                right: 8px !important;
                max-height: 38vh;
                overflow-y: auto;
                font-size: 11px !important;
                padding: 8px 10px !important;
            }}
        }}
    </style>
    <div class="travel-legend" style="
        position: fixed; bottom: 30px; left: 30px; z-index: 1000;
        background: white; padding: 12px 16px; border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,.25); font-family: sans-serif; font-size: 13px;
    ">
        <b style="font-size:15px">{flag_html}{display_country}</b>
        <hr style="margin:6px 0 4px">
        <b style="font-size:14px">Verblijfplaatsen</b>
        <table style="border-collapse:collapse;margin-top:4px">{legend_rows}</table>
        <hr style="margin:8px 0">
        <b style="font-size:14px">Prioriteit (markergrootte)</b>
        <table style="border-collapse:collapse;margin-top:4px">{priority_rows}</table>
        <hr style="margin:8px 0">
        <span style="font-size:12px;color:#666">
            🏨 = verblijf &nbsp;|&nbsp; ● = attractie &nbsp;|&nbsp; ◇ = tussenstop
        </span>
        <hr style="margin:8px 0">
        <a href="../index.html"
           style="font-size:12px;color:#2980b9;text-decoration:none">← Terug naar landenselectie</a>
    </div>
    """
    fmap.get_root().header.add_child(folium.Element(FLAG_ICONS_CDN))
    fmap.get_root().html.add_child(folium.Element(legend_html))

    # ── feature groups (become toggleable layers) ─────────────────────────────
    fg_lodging = folium.FeatureGroup(name="🏨 Verblijven", show=True)
    fg_attractions = folium.FeatureGroup(name="● Bezienswaardigheden", show=True)
    fg_transfer = folium.FeatureGroup(name="◇ Tussenstops", show=True)
    fg_final = folium.FeatureGroup(name=f"★ {final_name}", show=True)
    fg_airport = folium.FeatureGroup(name="✈ Luchthaven", show=True)

    # ── lodging + attractions ─────────────────────────────────────────────────
    for i, loc in enumerate(bases):
        color = BASE_COLORS[i % len(BASE_COLORS)]
        coords = loc["coordinates"]

        folium.Marker(
            location=[coords["lat"], coords["lon"]],
            tooltip=folium.Tooltip(
                _lodging_tooltip(loc, color["hex"]),
                sticky=True,
            ),
            icon=folium.Icon(color=color["folium"], icon="home", prefix="fa"),
            z_index_offset=1000,
        ).add_to(fg_lodging)

        for attr in loc.get("base_attractions", []):
            if "coordinates" not in attr:
                continue
            acoords = attr["coordinates"]
            pm = _priority(attr.get("priority", ""))
            folium.CircleMarker(
                location=[acoords["lat"], acoords["lon"]],
                radius=pm["radius"],
                color=color["hex"],
                fill=True,
                fill_color=color["hex"],
                fill_opacity=0.75,
                weight=2,
                tooltip=folium.Tooltip(
                    _attraction_tooltip(attr, loc["name"], color["hex"]),
                    sticky=True,
                ),
            ).add_to(fg_attractions)

    # ── transfer stops ────────────────────────────────────────────────────────
    base_id_to_color = {
        loc["id"]: BASE_COLORS[i % len(BASE_COLORS)] for i, loc in enumerate(bases)
    }
    attr_by_id = {
        attr["id"]: attr
        for loc in bases
        for attr in loc.get("base_attractions", [])
        if "id" in attr
    }

    for transfer in trip.get("transfer_routes", []):
        from_id = transfer.get("from", "")
        route_desc = transfer.get(
            "description", f"{from_id} → {transfer.get('to', '')}"
        )
        color = base_id_to_color.get(from_id, FINAL_STOP_COLOR)

        for candidate in transfer.get("en_route_candidates", []):
            ref = candidate.get("attraction_ref")
            if ref:
                base_attr = attr_by_id.get(ref, {})
                coords = base_attr.get("coordinates")
                name = base_attr.get("name", ref)
            else:
                coords = candidate.get("coordinates")
                name = candidate.get("name", "")
            if not coords:
                continue
            merged = {
                **(attr_by_id.get(ref, {}) if ref else {}),
                **candidate,
                "name": name,
            }
            pm = _priority(merged.get("priority", ""))
            folium.CircleMarker(
                location=[coords["lat"], coords["lon"]],
                radius=pm["radius"] + 4,
                color=color["hex"],
                fill=True,
                fill_color="white",
                fill_opacity=0.0,
                weight=2.5,
                dash_array="6 4",
                tooltip=folium.Tooltip(
                    _transfer_stop_tooltip(merged, route_desc, color["hex"]),
                    sticky=True,
                ),
            ).add_to(fg_transfer)

    # ── final stop ────────────────────────────────────────────────────────────
    if final and "coordinates" in final:
        fc = final["coordinates"]
        folium.Marker(
            location=[fc["lat"], fc["lon"]],
            tooltip=folium.Tooltip(
                _final_stop_tooltip(final),
                sticky=True,
            ),
            icon=folium.Icon(
                color=FINAL_STOP_COLOR["folium"],
                icon="star",
                prefix="fa",
            ),
            z_index_offset=2000,
        ).add_to(fg_final)
        for attr in final.get("attractions", []):
            if not isinstance(attr, dict) or "coordinates" not in attr:
                continue
            ac = attr["coordinates"]
            pm = _priority(attr.get("priority", ""))
            folium.CircleMarker(
                location=[ac["lat"], ac["lon"]],
                radius=pm["radius"],
                color=FINAL_STOP_COLOR["hex"],
                fill=True,
                fill_color=FINAL_STOP_COLOR["hex"],
                fill_opacity=0.75,
                weight=2,
                tooltip=folium.Tooltip(
                    _attraction_tooltip(attr, final["name"], FINAL_STOP_COLOR["hex"]),
                    sticky=True,
                ),
            ).add_to(fg_final)

    # ── airport ───────────────────────────────────────────────────────────────
    airport = trip.get("airport")
    if airport and "coordinates" in airport:
        ac = airport["coordinates"]
        folium.Marker(
            location=[ac["lat"], ac["lon"]],
            tooltip=folium.Tooltip(
                f'<div style="font-family:sans-serif"><b>✈️ {airport["name"]}</b></div>',
                sticky=True,
            ),
            icon=folium.Icon(color="gray", icon="plane", prefix="fa"),
        ).add_to(fg_airport)

    # add all layers, skipping empty optional ones
    layers = [fg_lodging, fg_attractions, fg_transfer]
    if final:
        layers.append(fg_final)
    if airport:
        layers.append(fg_airport)
    for fg in layers:
        fg.add_to(fmap)
    folium.LayerControl(collapsed=False).add_to(fmap)

    return fmap


def build_selection_page(countries: list) -> str:
    """Generate a standalone HTML country-selection page with trip info cards."""
    # sort by rank; unranked countries go last
    sorted_countries = sorted(
        countries,
        key=lambda c: c["data"]["trip"].get("overview", {}).get("rank", 9999),
    )

    # build Leaflet markers data
    import json

    markers_js = ""
    for c in sorted_countries:
        if not c.get("center"):
            continue
        trip = c["data"]["trip"]
        overview = trip.get("overview", {})
        country = trip.get("country", "Unknown")
        iso = COUNTRY_ISO.get(country, "")
        rank = overview.get("rank", "")
        card_id = country.lower().replace(" ", "-").replace("(", "").replace(")", "")
        display_country = COUNTRY_NL.get(country, country)
        lat, lon = c["center"]
        label = f"#{rank}" if rank else "?"
        flag_span = (
            f'<span class="fi fi-{iso}" style="vertical-align:middle"></span> '
            if iso
            else ""
        )
        rank_line = (
            f'<span style="opacity:.7;font-size:11px">#{rank}</span><br>'
            if rank
            else ""
        )
        cost = overview.get("cost") or trip.get("cost", {})
        relative_cost = cost.get("relative_costs", "")
        cost_color = {
            "low": "#27ae60",
            "medium": "#e67e22",
            "high": "#e74c3c",
            "very_high": "#1a1a1a",
        }.get(relative_cost, "#1a2a3a")
        icon_html = (
            f'<div class="map-marker" style="background:{cost_color}">{label}</div>'
        )
        duration = overview.get("duration_days") or trip.get("duration", {}).get(
            "days", ""
        )
        bases_count = len(trip.get("lodging_locations", []))
        couple_range = (cost.get("couple") or {}).get("eur_range", "")
        family_range = (cost.get("family") or {}).get("eur_range", "")
        popup_html = (
            f'<div style="font-family:sans-serif;font-size:13px;min-width:180px;text-align:center">'
            f"{flag_span}<b style='font-size:14px'>{display_country}</b><br>{rank_line}"
            f'<hr style="margin:5px 0">'
            f'<span style="font-size:12px">📅 {duration} dagen &nbsp;·&nbsp; 🏨 {bases_count} verblijven</span><br>'
            f'<span style="font-size:12px">💑 {couple_range or "—"}</span><br>'
            f'<span style="font-size:12px">👨\u200d👩\u200d👧\u200d👦 {family_range or "—"}</span>'
            f'<hr style="margin:5px 0">'
            f'<a href="#{card_id}" style="color:#2c3e50;font-weight:bold;font-size:12px">Naar details ↓</a>'
            f"</div>"
        )
        markers_js += (
            f"allMarkers.push(L.marker([{lat:.4f},{lon:.4f}],{{icon:L.divIcon({{className:'',html:"
            f"{json.dumps(icon_html)},iconSize:[28,28],iconAnchor:[14,14]}})}})."
            f"addTo(worldMap).bindPopup({json.dumps(popup_html)}));\n"
        )

    cards_html = ""
    for c in sorted_countries:
        trip = c["data"]["trip"]
        overview = trip.get("overview", {})
        country = trip.get("country", "Unknown")
        iso = COUNTRY_ISO.get(country, "")
        display_country = COUNTRY_NL.get(country, country)
        rank = overview.get("rank")

        duration = overview.get("duration_days") or trip.get("duration", {}).get(
            "days", "?"
        )
        transport = overview.get("transport", "—")
        bases_count = len(trip.get("lodging_locations", []))
        highlights = overview.get("highlights", [])
        summary = overview.get("summary", "")
        summary_reason = overview.get("summary_reason", "").strip()

        cost = overview.get("cost") or trip.get("cost", {})
        couple_range = (cost.get("couple") or {}).get("eur_range", "")
        family_range = (cost.get("family") or {}).get("eur_range", "")
        relative_cost_order = {"low": 1, "medium": 2, "high": 3, "very_high": 4}
        cost_sort_val = relative_cost_order.get(cost.get("relative_costs", ""), 9)
        highlights_html = "".join(f"<li>{h}</li>" for h in highlights)
        rank_badge = f'<div class="rank-badge">#{rank}</div>' if rank else ""
        rank_sort = rank if rank else 9999
        card_id = country.lower().replace(" ", "-").replace("(", "").replace(")", "")

        cards_html += f"""
        <div class="card" id="{card_id}" onclick="window.location='{c["map_path"]}'" data-rank="{rank_sort}" data-cost="{cost_sort_val}">
            <div class="card-header">
                {rank_badge}
                <span class="fi fi-{iso} card-flag"></span>
                <h2>{display_country}</h2>
            </div>
            <div class="card-body">
                <div class="stats">
                    <div class="stat-row"><span>📅 {duration} dagen</span><span>🏨 {bases_count} verblijven</span></div>
                    <div class="stat-row"><span>{transport}</span></div>
                    <div class="stat-row cost-{cost.get("relative_costs", "medium").replace("_", "-")}"><span>💑 {couple_range or "—"}</span><span>👨‍👩‍👧‍👦 {family_range or "—"}</span></div>
                </div>
                {"<p class='summary'>" + summary + "</p>" if summary else ""}
                {"<p class='reason'>" + summary_reason + "</p>" if summary_reason else ""}
                {"<ul class='highlights'>" + highlights_html + "</ul>" if highlights else ""}
                <div class="cta">Bekijk kaart →</div>
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reisplannen</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(160deg, #1a2a3a 0%, #2c3e50 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .page {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            color: white;
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,.3);
        }}
        .subtitle {{
            text-align: center;
            color: rgba(255,255,255,.75);
            font-size: 1.05rem;
            margin-bottom: 40px;
        }}
        .cards {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        .card {{
            background: white;
            border-radius: 14px;
            box-shadow: 0 6px 24px rgba(0,0,0,.25);
            cursor: pointer;
            transition: transform .2s, box-shadow .2s;
            overflow: hidden;
        }}
        .card:hover {{
            transform: translateY(-6px);
            box-shadow: 0 16px 40px rgba(0,0,0,.25);
        }}
        .card-header {{
            background: linear-gradient(135deg, #2c3e50, #34495e);
            padding: 14px 14px 10px;
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
        }}
        .rank-badge {{
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(255,255,255,.18);
            color: white;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 8px;
            letter-spacing: 0.02em;
        }}
        .flag {{ font-size: 3rem; line-height: 1; }}
        .card-flag {{
            width: 2rem;
            height: 1.5rem;
            border-radius: 4px;
            box-shadow: 0 2px 6px rgba(0,0,0,.35);
            flex-shrink: 0;
            background-size: cover;
        }}
        .card-header h2 {{
            color: white;
            font-size: 1.25rem;
            font-weight: 700;
        }}
        .card-body {{ padding: 12px 14px 14px; }}
        .stats {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-bottom: 10px;
        }}
        .stat-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .stat-row span {{
            background: #f0f2f5;
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 0.82rem;
            color: #444;
        }}
        .cost-low span    {{ background: #d5f0e0; color: #1a6e3a; }}
        .cost-medium span {{ background: #fdebd0; color: #a04000; }}
        .cost-high span   {{ background: #fce8e8; color: #922b21; }}
        .cost-very-high span {{ background: #4a4a4a; color: #f0f0f0; }}
        .summary {{
            color: #555;
            font-size: 0.85rem;
            line-height: 1.45;
            margin-bottom: 6px;
        }}
        .reason {{
            color: #2c3e50;
            font-size: 0.82rem;
            font-style: italic;
            line-height: 1.4;
            margin-bottom: 10px;
        }}
        .highlights {{
            list-style: none;
            margin-bottom: 12px;
        }}
        .highlights li {{
            padding: 2px 0;
            font-size: 0.82rem;
            color: #444;
        }}
        .highlights li::before {{ content: "📍 "; }}
        .cta {{
            display: inline-block;
            background: linear-gradient(135deg, #2c3e50, #1a2a3a);
            color: white;
            padding: 7px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        .sort-bar {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 18px;
            color: rgba(255,255,255,.8);
            font-size: 0.9rem;
        }}
        .sort-btn {{
            background: rgba(255,255,255,.15);
            color: white;
            border: 1px solid rgba(255,255,255,.3);
            border-radius: 20px;
            padding: 5px 14px;
            font-size: 0.85rem;
            cursor: pointer;
        }}
        .sort-btn.active, .sort-btn:hover {{
            background: rgba(255,255,255,.9);
            color: #1a2a3a;
            border-color: transparent;
        }}
        #world-map {{
            width: 100%;
            height: 420px;
            border-radius: 14px;
            box-shadow: 0 6px 24px rgba(0,0,0,.35);
            margin-bottom: 0;
        }}
        .cost-legend {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            z-index: 999;
            background: rgba(255,255,255,.92);
            border-radius: 7px;
            padding: 7px 11px;
            font-family: sans-serif;
            font-size: 12px;
            box-shadow: 0 1px 5px rgba(0,0,0,.25);
            line-height: 1.8;
        }}
        .map-marker {{
            background: #1a2a3a;  /* overridden per-marker by cost colour */
            color: white;
            border: 2px solid rgba(255,255,255,.6);
            border-radius: 50%;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            font-family: sans-serif;
            cursor: pointer;
        }}
        @media (max-width: 1024px) {{
            .cards {{ grid-template-columns: repeat(2, 1fr); }}
            h1 {{ font-size: 2rem; }}
            #world-map {{ height: 320px; }}
        }}
        @media (max-width: 600px) {{
            body {{ padding: 20px 12px; }}
            .cards {{ grid-template-columns: 1fr; gap: 14px; }}
            h1 {{ font-size: 1.6rem; }}
            .subtitle {{ font-size: 0.95rem; margin-bottom: 24px; }}
            #world-map {{ height: 240px; margin-bottom: 0; border-radius: 10px 10px 0 0; }}
            .cost-legend {{
                position: static;
                border-radius: 0 0 10px 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,.2);
                margin-bottom: 20px;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="page">
        <h1>🗺️ Reisplannen</h1>
        <p class="subtitle">Kies een bestemming om de interactieve kaart te verkennen</p>
        <div style="position:relative;margin-bottom:32px">
            <div id="world-map"></div>
            <div class="cost-legend">
                <b style="font-size:12px">Reiskosten</b><br>
                <span style="color:#27ae60">●</span> Laag
                &nbsp;<span style="color:#e67e22">●</span> Gemiddeld
                &nbsp;<span style="color:#e74c3c">●</span> Hoog
                &nbsp;<span style="color:#1a1a1a">●</span> Zeer hoog
            </div>
        </div>
        <div class="sort-bar">
            Sorteren op:
            <button class="sort-btn active" data-sort="rank">⭐ Rangschikking</button>
            <button class="sort-btn" data-sort="cost">💰 Prijs (laag → hoog)</button>
            <button class="sort-btn" data-sort="cost-rank">🏆 Beste prijs-kwaliteit</button>
        </div>
        <div class="cards" id="cards-grid">{cards_html}
        </div>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var worldMap = L.map('world-map', {{scrollWheelZoom: false}});
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
        }}).addTo(worldMap);
        var allMarkers = [];
        {markers_js}
        if (allMarkers.length) {{
            var group = L.featureGroup(allMarkers);
            worldMap.fitBounds(group.getBounds().pad(0.15));
        }}
    </script>
    <script>
        var grid = document.getElementById('cards-grid');
        var btns = document.querySelectorAll('.sort-btn');
        function sortCards(key) {{
            var cards = Array.from(grid.querySelectorAll('.card'));
            cards.sort(function(a, b) {{
                var ar = +a.dataset.rank, br = +b.dataset.rank;
                var ac = +a.dataset.cost, bc = +b.dataset.cost;
                if (key === 'rank') return ar - br;
                if (key === 'cost') return ac - bc || ar - br;
                if (key === 'cost-rank') return (ac * 5 + ar) - (bc * 5 + br);  // one cost tier ≈ 5 rank positions
                return 0;
            }});
            cards.forEach(function(card) {{ grid.appendChild(card); }});
        }}
        btns.forEach(function(btn) {{
            btn.addEventListener('click', function() {{
                btns.forEach(function(b) {{ b.classList.remove('active'); }});
                btn.classList.add('active');
                sortCards(btn.dataset.sort);
            }});
        }});
    </script>
</body>
</html>"""


def main() -> None:
    countries = []
    for country_dir in sorted(HERE.iterdir()):
        if not country_dir.is_dir():
            continue
        yaml_file = country_dir / "info.yaml"
        if not yaml_file.exists():
            continue
        with yaml_file.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Skip empty or invalid yaml files
        if data is None:
            continue

        map_file = country_dir / "map.html"
        fmap = build_map(data)
        fmap.save(str(map_file))
        print(f"Map saved → {map_file}")

        # compute center from lodging locations for the world map marker
        base_coords = [
            [loc["coordinates"]["lat"], loc["coordinates"]["lon"]]
            for loc in data["trip"].get("lodging_locations", [])
            if "coordinates" in loc
        ]
        center = (
            [
                statistics.mean(c[0] for c in base_coords),
                statistics.mean(c[1] for c in base_coords),
            ]
            if base_coords
            else None
        )

        countries.append(
            {
                "data": data,
                "map_path": f"{country_dir.name}/map.html",
                "center": center,
            }
        )

    selection_html = build_selection_page(countries)
    OUTPUT_SELECTION.write_text(selection_html, encoding="utf-8")
    print(f"Selection page saved → {OUTPUT_SELECTION}")


if __name__ == "__main__":
    main()
