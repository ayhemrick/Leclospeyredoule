"""Demo content for Clos Peyredoule.

The house itself is fictional. Everything about the region — the Vauban
citadel and its UNESCO listing, the estuary, the appellations, the museums —
is real, so the demo reads like a property that actually sits above Blaye.

Distances are road distances from the (imaginary) gate, rounded to the nearest
half kilometre, and travel times are by car unless the text says otherwise.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TypedDict

from app.models.content import AttractionCategory, GuideCategory, Visibility


class AttractionSeed(TypedDict):
    """One seeded attraction row."""

    slug: str
    category: AttractionCategory
    position: int
    name_fr: str
    name_en: str
    summary_fr: str
    summary_en: str
    description_fr: str
    description_en: str
    distance_km: Decimal | None
    travel_time_min: int | None
    website_url: str | None
    image_path: str | None
    image_credit: str | None


class GuideSeed(TypedDict):
    """One seeded guide section."""

    slug: str
    category: GuideCategory
    visibility: Visibility
    position: int
    icon: str | None
    title_fr: str
    title_en: str
    body_fr: str
    body_en: str


ATTRACTIONS: list[AttractionSeed] = [
    {
        "slug": "citadelle-de-blaye",
        "category": AttractionCategory.HERITAGE,
        "position": 10,
        "name_fr": "Citadelle de Blaye",
        "name_en": "Blaye Citadel",
        "summary_fr": (
            "La citadelle construite par Vauban à la fin du XVIIe siècle, inscrite au "
            "patrimoine mondial de l'UNESCO depuis 2008."
        ),
        "summary_en": (
            "The citadel Vauban built at the end of the 17th century, inscribed on the "
            "UNESCO World Heritage list since 2008."
        ),
        "description_fr": (
            "Sébastien Le Prestre de Vauban fortifie Blaye à partir de 1685 pour interdire "
            "l'accès de l'estuaire aux flottes ennemies. La citadelle occupe une falaise "
            "au-dessus de la Gironde : on y entre librement à pied, on longe les remparts, "
            "on traverse la place forte avec ses ateliers d'artisans, sa poudrière et son "
            "couvent des Minimes en ruines.\n\n"
            "Le panorama depuis la terrasse est la meilleure introduction possible à la "
            "région : en face, le Médoc ; en contrebas, les carrelets ; au loin, l'île "
            "Nouvelle. Comptez une bonne heure de promenade, deux si vous visitez les "
            "souterrains."
        ),
        "description_en": (
            "Sébastien Le Prestre de Vauban fortified Blaye from 1685 onwards to close the "
            "estuary to enemy fleets. The citadel sits on a cliff above the Gironde. Entry "
            "on foot is free: you can walk the ramparts, cross the fortified town with its "
            "craft workshops, powder magazine and the ruins of the Minimes convent.\n\n"
            "The view from the terrace is the best possible introduction to the region: the "
            "Médoc opposite, fishing huts below, the Île Nouvelle in the distance. Allow an "
            "hour for a walk, two if you visit the underground passages."
        ),
        "distance_km": Decimal("1.5"),
        "travel_time_min": 5,
        "website_url": "https://www.tourisme-blaye.com/",
        "image_path": "/images/citadelle-de-blaye.jpg",
        "image_credit": None,
    },
    {
        "slug": "verrou-vauban",
        "category": AttractionCategory.HERITAGE,
        "position": 20,
        "name_fr": "Le verrou Vauban",
        "name_en": "The Vauban estuary lock",
        "summary_fr": (
            "Trois ouvrages, une seule idée : la citadelle, le fort Pâté sur son île et le "
            "fort Médoc sur l'autre rive verrouillaient ensemble l'estuaire."
        ),
        "summary_en": (
            "Three forts, one idea: the citadel, Fort Pâté on its island and Fort Médoc on "
            "the far bank once sealed the estuary between them."
        ),
        "description_fr": (
            "Aucun canon de l'époque ne portait assez loin pour couvrir seul les trois "
            "kilomètres de fleuve. Vauban a donc croisé les feux de trois positions. "
            "L'ensemble est classé au patrimoine mondial avec les autres fortifications de "
            "Vauban.\n\n"
            "Le fort Pâté, bâti sur un banc de vase au milieu de la Gironde, ne se visite "
            "qu'en bateau lors de sorties saisonnières ; le fort Médoc, à Cussac, se "
            "rejoint en voiture par le bac ou par le pont d'Aquitaine."
        ),
        "description_en": (
            "No cannon of the period could cover three kilometres of river on its own, so "
            "Vauban crossed the fire of three positions instead. The ensemble is listed by "
            "UNESCO together with Vauban's other fortifications.\n\n"
            "Fort Pâté, built on a mud bank mid-river, can only be reached by boat on "
            "seasonal outings; Fort Médoc, at Cussac, is reached by the ferry or the long "
            "way round via Bordeaux."
        ),
        "distance_km": Decimal("3"),
        "travel_time_min": 10,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "estuaire-de-la-gironde",
        "category": AttractionCategory.NATURE,
        "position": 30,
        "name_fr": "L'estuaire de la Gironde",
        "name_en": "The Gironde estuary",
        "summary_fr": (
            "Le plus vaste estuaire d'Europe occidentale, ses carrelets sur pilotis, ses "
            "îles et ses croisières au fil de l'eau."
        ),
        "summary_en": (
            "The largest estuary in Western Europe, with its stilted fishing huts, its "
            "islands and its river cruises."
        ),
        "description_fr": (
            "La Garonne et la Dordogne se rejoignent au bec d'Ambès et forment un fleuve "
            "large de plusieurs kilomètres, couleur café au lait à cause des sédiments "
            "qu'il charrie. Des croisières partent du ponton de Blaye vers l'île Nouvelle "
            "ou vers le fort Pâté selon les marées.\n\n"
            "À pied, le plus simple est de suivre la rive au nord de la citadelle à la "
            "tombée du jour : les carrelets, ces cabanes de pêche sur pilotis munies d'un "
            "grand filet carré, s'alignent jusqu'à l'horizon."
        ),
        "description_en": (
            "The Garonne and the Dordogne meet at the Bec d'Ambès and form a river several "
            "kilometres wide, the colour of milky coffee from the sediment it carries. "
            "Cruises leave the Blaye pontoon for the Île Nouvelle or Fort Pâté depending on "
            "the tide.\n\n"
            "On foot, the simplest outing is the bank north of the citadel at dusk, where "
            "the carrelets — stilted fishing huts with a big square net — line up towards "
            "the horizon."
        ),
        "distance_km": Decimal("2"),
        "travel_time_min": 6,
        "website_url": None,
        "image_path": "/images/estuaire-gironde.jpg",
        "image_credit": None,
    },
    {
        "slug": "vignoble-blaye-cotes-de-bordeaux",
        "category": AttractionCategory.WINE,
        "position": 40,
        "name_fr": "Vignoble de Blaye Côtes de Bordeaux",
        "name_en": "Blaye Côtes de Bordeaux vineyards",
        "summary_fr": (
            "L'appellation qui entoure la maison : merlot dominant, châteaux familiaux et "
            "caveaux ouverts à la dégustation."
        ),
        "summary_en": (
            "The appellation that surrounds the house: merlot-led reds, family estates and "
            "cellars open for tastings."
        ),
        "description_fr": (
            "Le vignoble de la rive droite de l'estuaire est l'un des plus anciens du "
            "Bordelais. Les rouges, largement dominés par le merlot, se boivent plus jeunes "
            "que ceux du Médoc ; on trouve aussi des blancs secs de sauvignon.\n\n"
            "La plupart des propriétés accueillent sans rendez-vous en été et sur appel le "
            "reste de l'année. La Maison du Vin de Blaye, en ville, présente les cuvées de "
            "dizaines de châteaux au même endroit si vous préférez commencer par là."
        ),
        "description_en": (
            "The right-bank vineyard is among the oldest in the Bordeaux region. The reds, "
            "largely merlot, drink younger than Médoc wines; there are dry sauvignon whites "
            "too.\n\n"
            "Most estates welcome visitors without an appointment in summer and by phone "
            "the rest of the year. The Maison du Vin in Blaye pours wines from dozens of "
            "estates under one roof if you would rather start there."
        ),
        "distance_km": Decimal("2.5"),
        "travel_time_min": 8,
        "website_url": None,
        "image_path": "/images/vignoble-blaye.jpg",
        "image_credit": None,
    },
    {
        "slug": "route-de-la-corniche",
        "category": AttractionCategory.NATURE,
        "position": 50,
        "name_fr": "La corniche fleurie",
        "name_en": "The flowered corniche road",
        "summary_fr": (
            "La petite route entre Blaye et Bourg, taillée dans la falaise calcaire, avec "
            "ses maisons troglodytes et ses vues sur l'estuaire."
        ),
        "summary_en": (
            "The small road between Blaye and Bourg, cut into the limestone cliff, past "
            "troglodyte houses and estuary views."
        ),
        "description_fr": (
            "Une quinzaine de kilomètres de virages entre le fleuve et la roche, à faire "
            "lentement, en voiture ou à vélo. Les villages de Plassac, Villeneuve et "
            "Gauriac s'y succèdent, avec des habitations creusées directement dans le "
            "calcaire et des jardins en terrasses.\n\n"
            "Plusieurs haltes offrent un banc et une vue : c'est l'itinéraire à prendre au "
            "coucher du soleil plutôt que la départementale."
        ),
        "description_en": (
            "Fifteen kilometres of bends between the river and the rock, best taken slowly, "
            "by car or by bike. The villages of Plassac, Villeneuve and Gauriac follow one "
            "another, with homes dug straight into the limestone and terraced gardens.\n\n"
            "Several pull-ins offer a bench and a view: take this road at sunset rather "
            "than the main one."
        ),
        "distance_km": Decimal("4"),
        "travel_time_min": 10,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "villa-gallo-romaine-de-plassac",
        "category": AttractionCategory.HERITAGE,
        "position": 60,
        "name_fr": "Villa gallo-romaine de Plassac",
        "name_en": "Gallo-Roman villa at Plassac",
        "summary_fr": (
            "Les vestiges de trois villas successives, du Ier au Ve siècle, avec leurs "
            "mosaïques et un petit musée de site."
        ),
        "summary_en": (
            "The remains of three successive villas, first to fifth century, with their "
            "mosaics and a small site museum."
        ),
        "description_fr": (
            "Le site, fouillé depuis les années 1960, montre l'emprise au sol des bâtiments "
            "et de belles mosaïques géométriques conservées sous abri. Le musée expose les "
            "objets trouvés sur place et explique la vie d'un domaine viticole romain au "
            "bord de l'estuaire — la vigne était déjà là.\n\n"
            "Visite courte et bien adaptée aux enfants, souvent combinée avec un arrêt sur "
            "la corniche."
        ),
        "description_en": (
            "Excavated since the 1960s, the site shows the footprint of the buildings and "
            "fine geometric mosaics kept under cover. The museum displays finds from the "
            "site and explains life on a Roman wine estate beside the estuary — the vines "
            "were already here.\n\n"
            "A short visit that suits children, often combined with a stop on the corniche."
        ),
        "distance_km": Decimal("6"),
        "travel_time_min": 12,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "grotte-de-pair-non-pair",
        "category": AttractionCategory.HERITAGE,
        "position": 70,
        "name_fr": "Grotte de Pair-non-Pair",
        "name_en": "Pair-non-Pair cave",
        "summary_fr": (
            "L'une des premières grottes ornées découvertes en France, avec des gravures "
            "pariétales vieilles de dizaines de milliers d'années."
        ),
        "summary_en": (
            "One of the first decorated caves discovered in France, with wall engravings "
            "tens of thousands of years old."
        ),
        "description_fr": (
            "Découverte en 1881 à Prignac-et-Marcamps, la grotte conserve des gravures de "
            "chevaux, bouquetins, mammouths et cervidés, réalisées au Paléolithique "
            "supérieur. La visite est guidée et le nombre de places par jour est limité "
            "pour protéger les parois : réservez.\n\n"
            "Prévoyez une petite laine, il fait frais à l'intérieur en toute saison."
        ),
        "description_en": (
            "Discovered in 1881 at Prignac-et-Marcamps, the cave preserves engravings of "
            "horses, ibex, mammoths and deer from the Upper Palaeolithic. Visits are guided "
            "and daily numbers are capped to protect the walls, so book ahead.\n\n"
            "Bring a layer: it stays cool inside whatever the season."
        ),
        "distance_km": Decimal("19"),
        "travel_time_min": 25,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "terres-doiseaux",
        "category": AttractionCategory.FAMILY,
        "position": 80,
        "name_fr": "Terres d'Oiseaux",
        "name_en": "Terres d'Oiseaux bird reserve",
        "summary_fr": (
            "Un espace naturel de marais et d'observatoires au bord de l'estuaire, au nord "
            "de Blaye, idéal avec des enfants."
        ),
        "summary_en": (
            "A wetland reserve with hides on the estuary shore north of Blaye, ideal with children."
        ),
        "description_fr": (
            "Des sentiers sur pilotis traversent les marais jusqu'à des observatoires "
            "équipés de longues-vues. Cigognes, spatules, hérons et, en hiver, des milliers "
            "d'oiseaux migrateurs venus du nord.\n\n"
            "Le parcours principal fait environ deux kilomètres, plat et accessible en "
            "poussette."
        ),
        "description_en": (
            "Boardwalks cross the marshes to hides fitted with telescopes. Storks, "
            "spoonbills, herons and, in winter, thousands of migratory birds from the "
            "north.\n\n"
            "The main loop is about two kilometres, flat and pushchair-friendly."
        ),
        "distance_km": Decimal("18"),
        "travel_time_min": 22,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "bourg-sur-gironde",
        "category": AttractionCategory.HERITAGE,
        "position": 90,
        "name_fr": "Bourg-sur-Gironde",
        "name_en": "Bourg-sur-Gironde",
        "summary_fr": (
            "Une petite cité médiévale perchée au-dessus du confluent, ville haute et ville "
            "basse reliées par des escaliers."
        ),
        "summary_en": (
            "A small medieval town perched above the confluence, upper and lower town "
            "linked by stairways."
        ),
        "description_fr": (
            "Bourg garde ses remparts, sa porte de la Mer et un lavoir monumental. La "
            "terrasse du district offre une vue plongeante sur la Dordogne et le bec "
            "d'Ambès.\n\n"
            "Le marché et les cafés de la ville basse en font une halte facile avant ou "
            "après la corniche."
        ),
        "description_en": (
            "Bourg keeps its ramparts, its sea gate and a monumental wash-house. The "
            "terrace looks straight down on the Dordogne and the Bec d'Ambès.\n\n"
            "The market and the cafés of the lower town make it an easy stop before or "
            "after the corniche road."
        ),
        "distance_km": Decimal("16"),
        "travel_time_min": 20,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "bac-blaye-lamarque",
        "category": AttractionCategory.FAMILY,
        "position": 100,
        "name_fr": "Le bac Blaye-Lamarque",
        "name_en": "The Blaye-Lamarque ferry",
        "summary_fr": (
            "La traversée de l'estuaire en bac, seul raccourci vers le Médoc et ses grands crus."
        ),
        "summary_en": (
            "The car ferry across the estuary, the only shortcut to the Médoc and its "
            "great growths."
        ),
        "description_fr": (
            "Une vingtaine de minutes de traversée, à pied, à vélo ou en voiture, entre le "
            "ponton de Blaye et Lamarque, sur la rive du Médoc. C'est le moyen le plus "
            "simple d'aller déjeuner à Margaux ou de rejoindre le fort Médoc.\n\n"
            "Les rotations dépendent de la marée et de la saison : consultez les horaires "
            "du jour avant de partir, et présentez-vous une vingtaine de minutes à l'avance "
            "en été."
        ),
        "description_en": (
            "A twenty-minute crossing on foot, by bike or by car, between the Blaye pontoon "
            "and Lamarque on the Médoc bank. It is the simplest way to have lunch in "
            "Margaux or to reach Fort Médoc.\n\n"
            "Sailings depend on the tide and the season: check the day's timetable before "
            "leaving, and arrive twenty minutes early in summer."
        ),
        "distance_km": Decimal("2"),
        "travel_time_min": 7,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "marche-de-blaye",
        "category": AttractionCategory.GASTRONOMY,
        "position": 110,
        "name_fr": "Le marché de Blaye",
        "name_en": "Blaye market",
        "summary_fr": (
            "Le marché du centre-ville : maraîchers du coin, fromages, huîtres du bassin et "
            "poissons de l'estuaire."
        ),
        "summary_en": (
            "The town-centre market: local growers, cheeses, oysters from the bay and fish "
            "from the estuary."
        ),
        "description_fr": (
            "Le marché se tient en matinée sur la place du centre ; les jours varient selon "
            "la saison, la liste à jour est affichée dans l'entrée de la maison.\n\n"
            "À rapporter : des huîtres, un chèvre fermier, et si la saison s'y prête, de la "
            "lamproie ou de l'anguille préparées par les poissonniers du fleuve."
        ),
        "description_en": (
            "The market runs in the morning on the central square; the days shift with the "
            "season and the current list is posted in the entrance hall.\n\n"
            "Worth taking home: oysters, a farm goat's cheese and, in season, lamprey or "
            "eel prepared by the river fishmongers."
        ),
        "distance_km": Decimal("1.5"),
        "travel_time_min": 5,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "caviar-et-lamproie",
        "category": AttractionCategory.GASTRONOMY,
        "position": 120,
        "name_fr": "Caviar de Gironde et lamproie",
        "name_en": "Gironde caviar and lamprey",
        "summary_fr": (
            "Les deux spécialités de l'estuaire : le caviar d'esturgeon d'élevage et la "
            "lamproie à la bordelaise."
        ),
        "summary_en": (
            "The estuary's two specialities: farmed sturgeon caviar and lamprey cooked "
            "Bordeaux-style."
        ),
        "description_fr": (
            "L'esturgeon sauvage de la Gironde est protégé depuis des décennies, mais des "
            "fermes aquacoles de la région produisent aujourd'hui un caviar réputé ; "
            "plusieurs proposent visite et dégustation.\n\n"
            "La lamproie à la bordelaise, mijotée au vin rouge et aux poireaux, se sert "
            "surtout au printemps. C'est un plat franc : demandez une demi-portion la "
            "première fois."
        ),
        "description_en": (
            "Wild Gironde sturgeon has been protected for decades, but fish farms in the "
            "region now produce a well-regarded caviar, and several offer tours and "
            "tastings.\n\n"
            "Lamprey Bordeaux-style, stewed in red wine with leeks, is mostly a spring "
            "dish. It is an assertive one: ask for a half portion the first time."
        ),
        "distance_km": None,
        "travel_time_min": None,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "bordeaux",
        "category": AttractionCategory.HERITAGE,
        "position": 130,
        "name_fr": "Bordeaux",
        "name_en": "Bordeaux",
        "summary_fr": (
            "Le Port de la Lune, classé au patrimoine mondial, à une heure de route : "
            "miroir d'eau, quais et Cité du Vin."
        ),
        "summary_en": (
            "The Port of the Moon, a World Heritage site, an hour away: the water mirror, "
            "the quays and the Cité du Vin."
        ),
        "description_fr": (
            "L'ensemble urbain du XVIIIe siècle est inscrit à l'UNESCO depuis 2007. Une "
            "journée suffit pour l'essentiel : place de la Bourse et son miroir d'eau, rue "
            "Sainte-Catherine, quartier des Chartrons, puis la Cité du Vin au nord.\n\n"
            "En voiture, le plus simple est de se garer à un parking relais en périphérie "
            "et de finir en tramway."
        ),
        "description_en": (
            "The 18th-century urban ensemble has been UNESCO-listed since 2007. A day "
            "covers the essentials: Place de la Bourse and its water mirror, Rue "
            "Sainte-Catherine, the Chartrons district, then the Cité du Vin to the north.\n\n"
            "By car, the easiest approach is a park-and-ride on the edge of town, then the "
            "tram."
        ),
        "distance_km": Decimal("52"),
        "travel_time_min": 60,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
    {
        "slug": "saint-emilion",
        "category": AttractionCategory.WINE,
        "position": 140,
        "name_fr": "Saint-Émilion",
        "name_en": "Saint-Émilion",
        "summary_fr": (
            "La juridiction viticole classée à l'UNESCO, son église monolithe et ses "
            "macarons, à une heure de la maison."
        ),
        "summary_en": (
            "The UNESCO-listed wine jurisdiction, its monolithic church and its macarons, "
            "an hour from the house."
        ),
        "description_fr": (
            "La juridiction de Saint-Émilion est inscrite au patrimoine mondial depuis 1999 "
            "en tant que paysage culturel viticole. Le village lui-même se parcourt à pied, "
            "en descendant les pavés jusqu'à l'église monolithe creusée dans la roche.\n\n"
            "Les visites de châteaux se réservent à l'avance, surtout en septembre pendant "
            "les vendanges."
        ),
        "description_en": (
            "The Saint-Émilion jurisdiction has been World Heritage-listed since 1999 as a "
            "cultural wine landscape. The village itself is walkable, down cobbles to the "
            "monolithic church carved out of the rock.\n\n"
            "Château visits need booking, especially in September during the harvest."
        ),
        "distance_km": Decimal("62"),
        "travel_time_min": 70,
        "website_url": None,
        "image_path": None,
        "image_credit": None,
    },
]


GUIDE_SECTIONS: list[GuideSeed] = [
    # --- Public: what anyone browsing the flyer can read --------------------
    {
        "slug": "histoire-du-clos",
        "category": GuideCategory.HOUSE,
        "visibility": Visibility.PUBLIC,
        "position": 10,
        "icon": "history",
        "title_fr": "L'histoire du Clos",
        "title_en": "The story of the Clos",
        "body_fr": (
            "Le Clos Peyredoule est une chartreuse girondine bâtie en 1782 pour un "
            "négociant en vin qui expédiait ses barriques depuis le port de Blaye. La "
            "maison a gardé son plan d'origine : un long corps de logis d'un seul niveau, "
            "tourné plein sud vers l'estuaire, prolongé par un chai et un pigeonnier.\n\n"
            "Après un siècle de vigne, deux guerres et une longue période d'abandon, la "
            "demeure a été restaurée pièce par pièce : tomettes d'origine reposées à la "
            "main, cheminées de pierre rouvertes, charpente traitée et toiture refaite en "
            "tuiles canal de récupération."
        ),
        "body_en": (
            "Clos Peyredoule is a *chartreuse girondine* built in 1782 for a wine merchant "
            "who shipped his barrels from the port of Blaye. The house keeps its original "
            "plan: a long single-storey range facing due south towards the estuary, "
            "extended by a barrel cellar and a dovecote.\n\n"
            "After a century of vines, two wars and a long spell of neglect, the house was "
            "restored room by room: original terracotta tiles relaid by hand, stone "
            "fireplaces reopened, the roof frame treated and re-covered with reclaimed "
            "canal tiles."
        ),
    },
    {
        "slug": "la-demeure",
        "category": GuideCategory.HOUSE,
        "visibility": Visibility.PUBLIC,
        "position": 20,
        "icon": "home",
        "title_fr": "La demeure",
        "title_en": "The house",
        "body_fr": (
            "Cinq chambres, quatre salles de bains, une cuisine d'été sous la treille et un "
            "salon de trente mètres carrés avec sa cheminée d'origine. La maison accueille "
            "confortablement dix personnes.\n\n"
            "Le chai attenant sert de salle commune les jours de pluie : longue table, "
            "billard, bibliothèque. Le pigeonnier, restauré en 2019, abrite une chambre "
            "ronde accessible par un escalier étroit — la préférée des enfants."
        ),
        "body_en": (
            "Five bedrooms, four bathrooms, a summer kitchen under the vine arbour and a "
            "thirty-square-metre sitting room with its original fireplace. The house "
            "sleeps ten comfortably.\n\n"
            "The adjoining cellar doubles as the wet-weather room: long table, billiards, "
            "library. The dovecote, restored in 2019, holds a round bedroom up a narrow "
            "stair — the children's favourite."
        ),
    },
    {
        "slug": "le-parc",
        "category": GuideCategory.HOUSE,
        "visibility": Visibility.PUBLIC,
        "position": 30,
        "icon": "tree",
        "title_fr": "Le parc et le jardin clos",
        "title_en": "The grounds and walled garden",
        "body_fr": (
            "Deux hectares plantés de cèdres et de chênes verts, un potager clos de murs "
            "toujours en culture, et une allée de tilleuls qui descend vers la vigne "
            "voisine.\n\n"
            "La piscine, chauffée d'avril à octobre, est masquée par une haie de lauriers "
            "pour ne pas troubler la façade. Depuis le fond du parc, on aperçoit les tours "
            "de la citadelle au-dessus des arbres."
        ),
        "body_en": (
            "Two hectares planted with cedars and holm oaks, a walled kitchen garden still "
            "in production, and a lime avenue running down to the neighbouring vines.\n\n"
            "The pool, heated from April to October, is screened by a laurel hedge so as "
            "not to disturb the façade. From the far end of the grounds you can see the "
            "citadel towers above the trees."
        ),
    },
    {
        "slug": "sejourner",
        "category": GuideCategory.PRACTICAL,
        "visibility": Visibility.PUBLIC,
        "position": 40,
        "icon": "calendar",
        "title_fr": "Séjourner au Clos",
        "title_en": "Staying at the Clos",
        "body_fr": (
            "La maison se loue entière, du samedi au samedi en haute saison et à partir de "
            "trois nuits le reste de l'année. Arrivée à partir de 16 h, départ avant 10 h.\n\n"
            "Le ménage de fin de séjour, le linge de maison et le bois pour la cheminée "
            "sont compris. Les animaux sont acceptés dans les pièces du rez-de-chaussée."
        ),
        "body_en": (
            "The house is let whole, Saturday to Saturday in high season and from three "
            "nights the rest of the year. Arrival from 4 pm, departure before 10 am.\n\n"
            "End-of-stay cleaning, household linen and firewood are included. Pets are "
            "welcome in the ground-floor rooms."
        ),
    },
    # --- Guest-only: unlocked by scanning the QR code -----------------------
    {
        "slug": "arrivee-et-cles",
        "category": GuideCategory.ARRIVAL,
        "visibility": Visibility.GUEST,
        "position": 100,
        "icon": "key",
        "title_fr": "Arrivée, portail et clés",
        "title_en": "Arrival, gate and keys",
        "body_fr": (
            "**Portail** — le code du portail vous est envoyé la veille de votre arrivée et "
            "change à chaque séjour. Le battant de gauche s'ouvre seul si vous arrivez à "
            "pied.\n\n"
            "**Clés** — la boîte à clés est fixée au mur sous le porche, à droite de la "
            "porte d'entrée. Elle contient deux trousseaux : maison et chai.\n\n"
            "**Stationnement** — sous les tilleuls, à gauche en entrant. Évitez la pelouse "
            "après la pluie, le terrain est argileux."
        ),
        "body_en": (
            "**Gate** — the gate code is sent the day before you arrive and changes for "
            "every stay. The left-hand leaf opens on its own if you arrive on foot.\n\n"
            "**Keys** — the key safe is fixed to the wall under the porch, right of the "
            "front door. It holds two sets: house and cellar.\n\n"
            "**Parking** — under the lime trees, to the left as you come in. Avoid the "
            "lawn after rain, the ground is clay."
        ),
    },
    {
        "slug": "wifi-et-connexion",
        "category": GuideCategory.PRACTICAL,
        "visibility": Visibility.GUEST,
        "position": 110,
        "icon": "wifi",
        "title_fr": "Wi-Fi et connexion",
        "title_en": "Wi-Fi and connectivity",
        "body_fr": (
            "**Réseau** : `ClosPeyredoule` — **mot de passe** : `cedre-1782-estuaire`\n\n"
            "La box se trouve dans le placard de l'entrée. Un répéteur couvre le chai et la "
            "terrasse ; le pigeonnier capte mal, c'est assumé.\n\n"
            "La 4G passe correctement sur la terrasse sud, moins bien à l'intérieur à cause "
            "de l'épaisseur des murs."
        ),
        "body_en": (
            "**Network**: `ClosPeyredoule` — **password**: `cedre-1782-estuaire`\n\n"
            "The router is in the hall cupboard. A repeater covers the cellar and the "
            "terrace; the dovecote has poor coverage, deliberately so.\n\n"
            "Mobile data works well on the south terrace, less well indoors because of the "
            "wall thickness."
        ),
    },
    {
        "slug": "chauffage-et-eau",
        "category": GuideCategory.HOUSE,
        "visibility": Visibility.GUEST,
        "position": 120,
        "icon": "thermometer",
        "title_fr": "Chauffage, eau chaude et cheminée",
        "title_en": "Heating, hot water and the fireplace",
        "body_fr": (
            "**Chauffage** — pompe à chaleur, thermostat dans le couloir. Réglé sur 19 °C ; "
            "merci de ne pas dépasser 21 °C, les murs de pierre mettent longtemps à "
            "revenir.\n\n"
            "**Eau chaude** — ballon de 300 litres, suffisant pour dix douches d'affilée. "
            "Si l'eau tiédit, laissez-lui deux heures.\n\n"
            "**Cheminée** — bois sec sous le porche, allume-feu dans le seau en zinc. "
            "Ouvrez la clé de tirage (levier à gauche du foyer) avant d'allumer, et ne "
            "fermez jamais le pare-étincelles sur des braises vives."
        ),
        "body_en": (
            "**Heating** — heat pump, thermostat in the corridor. Set to 19 °C; please do "
            "not go above 21 °C, stone walls take a long time to recover.\n\n"
            "**Hot water** — a 300-litre tank, enough for ten showers in a row. If the "
            "water cools, give it two hours.\n\n"
            "**Fireplace** — dry wood under the porch, firelighters in the zinc bucket. "
            "Open the flue lever to the left of the hearth before lighting, and never close "
            "the spark guard over live embers."
        ),
    },
    {
        "slug": "cuisine-et-electromenager",
        "category": GuideCategory.HOUSE,
        "visibility": Visibility.GUEST,
        "position": 130,
        "icon": "kitchen",
        "title_fr": "Cuisine et électroménager",
        "title_en": "Kitchen and appliances",
        "body_fr": (
            "Piano de cuisson à gaz (bouteille de rechange dans le local technique), four "
            "électrique, lave-vaisselle, deux réfrigérateurs dont un au chai pour les "
            "boissons.\n\n"
            "La cuisine d'été sous la treille dispose d'une plancha et d'un évier ; le "
            "barbecue au charbon est rangé derrière le pigeonnier. Charbon fourni, "
            "allume-feu liquide interdit."
        ),
        "body_en": (
            "Gas range (spare bottle in the plant room), electric oven, dishwasher, two "
            "fridges — one in the cellar for drinks.\n\n"
            "The summer kitchen under the arbour has a plancha and a sink; the charcoal "
            "barbecue is stored behind the dovecote. Charcoal provided, liquid firelighter "
            "not allowed."
        ),
    },
    {
        "slug": "dechets-et-recyclage",
        "category": GuideCategory.PRACTICAL,
        "visibility": Visibility.GUEST,
        "position": 140,
        "icon": "recycle",
        "title_fr": "Déchets et recyclage",
        "title_en": "Waste and recycling",
        "body_fr": (
            "Bac vert (ordures ménagères) et bac jaune (emballages, papier) dans l'appentis "
            "près du portail. Le verre se dépose au conteneur du parking communal, à "
            "cinq cents mètres sur la droite.\n\n"
            "Sortez les bacs la veille du ramassage, dont le jour est affiché à "
            "l'intérieur de la porte de l'appentis. Le compost, au fond du potager, accepte "
            "épluchures et marc de café, pas de restes cuits."
        ),
        "body_en": (
            "Green bin (general waste) and yellow bin (packaging, paper) in the lean-to by "
            "the gate. Glass goes to the container in the village car park, five hundred "
            "metres to the right.\n\n"
            "Put the bins out the evening before collection; the day is posted inside the "
            "lean-to door. The compost heap at the end of the kitchen garden takes peelings "
            "and coffee grounds, but no cooked food."
        ),
    },
    {
        "slug": "reglement-de-la-maison",
        "category": GuideCategory.RULES,
        "visibility": Visibility.GUEST,
        "position": 150,
        "icon": "rules",
        "title_fr": "Règlement de la maison",
        "title_en": "House rules",
        "body_fr": (
            "- Maison **non-fumeur**. La terrasse et le parc le sont, cendriers sous le porche.\n"
            "- **Silence** entre 22 h et 8 h : les voisins sont vignerons et se lèvent tôt.\n"
            "- **Piscine** non surveillée, interdite aux enfants sans adulte ; la bâche doit "
            "être remise le soir.\n"
            "- **Fêtes et événements** uniquement avec accord écrit préalable.\n"
            "- Les **animaux** restent au rez-de-chaussée et jamais seuls dans la maison.\n"
            "- Merci de laisser la **cave à vin** fermée : elle appartient au propriétaire."
        ),
        "body_en": (
            "- The house is **non-smoking**. So are the terrace and grounds; ashtrays under "
            "the porch.\n"
            "- **Quiet** between 10 pm and 8 am: the neighbours are wine growers and start "
            "early.\n"
            "- The **pool** is unsupervised and off limits to children without an adult; "
            "the cover goes back on at night.\n"
            "- **Parties and events** only by prior written agreement.\n"
            "- **Pets** stay on the ground floor and are never left alone in the house.\n"
            "- Please leave the **wine cellar** closed: it belongs to the owner."
        ),
    },
    {
        "slug": "urgences-et-contacts",
        "category": GuideCategory.PRACTICAL,
        "visibility": Visibility.GUEST,
        "position": 160,
        "icon": "alert",
        "title_fr": "Urgences et contacts",
        "title_en": "Emergencies and contacts",
        "body_fr": (
            "- **112** — numéro d'urgence européen (fonctionne partout, depuis tout "
            "téléphone)\n"
            "- **15** SAMU · **18** pompiers · **17** police\n"
            "- **Gardien** — Michel, joignable de 8 h à 20 h, numéro affiché dans l'entrée\n"
            "- **Médecin de garde et pharmacie** — la liste de garde est affichée sur la "
            "porte de la pharmacie du centre de Blaye\n\n"
            "**Coupure de courant** : le tableau électrique est dans le placard de "
            "l'entrée, différentiel en haut à gauche. **Coupure d'eau** : la vanne "
            "générale se trouve dans le regard près du portail."
        ),
        "body_en": (
            "- **112** — European emergency number (works anywhere, from any phone)\n"
            "- **15** ambulance · **18** fire · **17** police\n"
            "- **Caretaker** — Michel, reachable 8 am to 8 pm, number posted in the "
            "entrance hall\n"
            "- **Out-of-hours doctor and pharmacy** — the duty list is posted on the door "
            "of the pharmacy in central Blaye\n\n"
            "**Power cut**: the consumer unit is in the hall cupboard, RCD top left. "
            "**Water cut**: the main stopcock is in the inspection chamber near the gate."
        ),
    },
    {
        "slug": "nos-adresses",
        "category": GuideCategory.LOCAL_TIPS,
        "visibility": Visibility.GUEST,
        "position": 170,
        "icon": "compass",
        "title_fr": "Nos adresses",
        "title_en": "Our addresses",
        "body_fr": (
            "**Le matin** — la boulangerie de la place, à Blaye, cuit encore au bois le "
            "week-end ; demandez le pain de campagne, il tient trois jours.\n\n"
            "**Déjeuner sur le pouce** — les cafés du port, face au ponton du bac, servent "
            "des assiettes simples avec vue sur l'estuaire.\n\n"
            "**Dîner** — deux tables sérieuses en ville, une seule ouvre le dimanche soir : "
            "réservez la veille, surtout en août.\n\n"
            "**Vin** — trois châteaux voisins acceptent les visiteurs sans rendez-vous ; "
            "leurs cartes sont dans le tiroir de la console de l'entrée. Dites que vous "
            "logez au Clos, ils comprendront."
        ),
        "body_en": (
            "**Mornings** — the bakery on the square in Blaye still bakes in a wood oven at "
            "weekends; ask for the *pain de campagne*, it keeps three days.\n\n"
            "**Quick lunch** — the harbour cafés opposite the ferry pontoon serve simple "
            "plates with an estuary view.\n\n"
            "**Dinner** — two serious tables in town, only one of which opens on Sunday "
            "evening: book the day before, especially in August.\n\n"
            "**Wine** — three neighbouring estates take visitors without an appointment; "
            "their cards are in the console drawer in the hall. Say you are staying at the "
            "Clos and they will know."
        ),
    },
]
