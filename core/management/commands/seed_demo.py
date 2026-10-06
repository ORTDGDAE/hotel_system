"""Seeds the Aurelia Collection: 10 Cambodian properties with inventory, staff,
rate rules, 60 days of booking history, payments, housekeeping & maintenance.

    python manage.py seed_demo [--flush]
"""
import datetime as dt
import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking, RateRule
from bookings.services import available_rooms, price_stay
from finance.models import Invoice, Payment
from finance.services import ensure_invoice
from hotel.models import Amenity, Attraction, Property, Room, RoomType
from operations.models import HousekeepingTask, MaintenanceRequest

random.seed(42)

FIRST = ["Sokha", "Dara", "Chantra", "Piseth", "Sreyleak", "Vichea", "Bopha", "Rith", "Sovann", "Malis",
         "James", "Emma", "Liam", "Olivia", "Noah", "Ava", "Lucas", "Mia", "Hiro", "Yuki", "Wei", "Mei",
         "Pierre", "Claire", "Hans", "Anna", "Carlos", "Sofia", "Ahmed", "Layla"]
LAST = ["Chan", "Keo", "Sam", "Ouch", "Lim", "Vong", "Pich", "Heng", "Sok", "Chea",
        "Smith", "Johnson", "Brown", "Taylor", "Nguyen", "Tanaka", "Wang", "Dupont", "Müller", "Garcia"]

IMG = lambda n: f"/static/img/props/{n}.jpg"
ROOM_IMG = lambda n: f"/static/img/rooms/{n}.jpg"

# Cambodia-friendly tiered catalog demo pricing: the entry room starts at $30
# and premium inventory reaches $460. The pricing engine, rate rules, and
# historical financial snapshots remain separate contracts and are not rewritten by this seed.

# name, slug, city, country, stars, svc%, tax%, image, tagline, room types:
# (name, price, cap, count, sqm, bed, floors, img, amenity keys)
PROPERTIES = [
    ("Aurelia Grand Phnom Penh", "aurelia-grand-phnom-penh", "Phnom Penh", "Cambodia", 5, "0.000", "0.050",
     IMG("phnom-penh"), "Riverside grand hotel on the Tonlé Sap — the flagship of the collection.",
     [("Deluxe River King", "52", 2, 18, 38, "king", "2–4", "deluxe"),
      ("Premier City Twin", "64", 3, 12, 42, "twin", "5–6", "premier"),
      ("Executive Suite", "100", 3, 8, 64, "suite", "7", "executive"),
      ("Royal Mekong Suite", "172", 4, 4, 96, "suite", "8", "royal")]),
    ("Aurelia Angkor Sanctuary", "aurelia-angkor-sanctuary", "Siem Reap", "Cambodia", 5, "0.000", "0.050",
     IMG("siem-reap"), "Temple-gate sanctuary amid frangipani gardens, minutes from Angkor Wat.",
     [("Sanctuary Deluxe", "46", 2, 10, 36, "king", "1–2", "sr-sanctuary"),
      ("Temple View Suite", "86", 3, 6, 58, "suite", "3", "sr-temple")]),
    ("Aurelia Kep Cove Resort", "aurelia-kep-cove", "Kep", "Cambodia", 4, "0.000", "0.050",
     "/static/img/props/kep.webp", "Barefoot cove resort facing Kampot pepper hills and crab-market sunsets.",
     [("Cove Garden Room", "36", 2, 10, 30, "double", "1", "kep-garden"),
      ("Sea View Suite", "66", 3, 6, 48, "king", "2", "kep-sea")]),
    ("Aurelia Koh Rong Overwater", "aurelia-koh-rong-overwater", "Koh Rong", "Cambodia", 5, "0.000", "0.050",
     IMG("koh-rong"), "Overwater villas on a private white-sand spit in the Gulf of Thailand.",
     [("Beach Bungalow", "56", 2, 8, 34, "king", "—", "kr-bungalow"),
      ("Overwater Villa", "128", 3, 6, 62, "king", "—", "overwater")]),
    ("Aurelia Sihanoukville Marina Bay", "aurelia-marina-bay", "Sihanoukville", "Cambodia", 4, "0.000", "0.050",
     "/static/img/props/sihanoukville.webp", "Marina-front towers with yacht-club access and rooftop sea pools.",
     [("Marina Room", "38", 2, 12, 32, "twin", "3–5", "sv-marina"),
      ("Bay Panorama Suite", "74", 3, 6, 52, "king", "6", "sv-panorama")]),
    ("Aurelia Battambang Riverside", "aurelia-battambang-riverside", "Battambang", "Cambodia", 4, "0.000", "0.050",
     IMG("battambang"), "Colonial-era riverside maison in Cambodia's artistic second city.",
     [("Colonial Room", "30", 2, 10, 28, "double", "1–2", "bt-colonial"),
      ("River Maison Suite", "58", 3, 5, 46, "king", "3", "bt-river")]),
    ("Raffles Hotel Le Royal, Phnom Penh", "raffles-hotel-le-royal", "Phnom Penh", "Cambodia", 5, "0.000", "0.050",
     IMG("le-royal"), "The 1929 colonial grande dame — Cambodia's most awarded address.",
     [("Deluxe Room", "128", 2, 60, 40, "king", "2–3", "colonial"),
      ("Premier Balcony Room", "154", 2, 58, 45, "twin", "4–5", "lr-balcony"),
      ("State Suite", "256", 3, 40, 72, "king", "6–8", "lr-state"),
      ("Le Royal Suite", "460", 4, 17, 98, "king", "9", "lr-royal")]),
    ("Rosewood Phnom Penh", "rosewood-phnom-penh", "Phnom Penh", "Cambodia", 5, "0.000", "0.050",
     IMG("rosewood"), "Sky-high ultra-luxury crowning the Vattanac Capital Tower — the capital's glass landmark.",
     [("Premier River King", "136", 2, 26, 45, "king", "30–39", "rw-premier"),
      ("Executive Sky Suite", "264", 3, 12, 78, "king", "40–42", "rw-executive")]),
    ("Sala Lodges", "sala-lodges", "Siem Reap", "Cambodia", 5, "0.000", "0.050",
     IMG("sala-lodges"), "Eleven rescued Khmer heritage houses reassembled amid rice paddies and palms.",
     [("Garden Sala Villa", "86", 2, 6, 55, "king", "1", "sala-garden"),
      ("Heritage Sala House", "146", 4, 5, 85, "king", "2", "sala-heritage")]),
    ("Song Saa Private Island", "song-saa-private-island", "Koh Rong", "Cambodia", 5, "0.000", "0.050",
     IMG("song-saa"), "Cambodia's first private-island reserve — twin islets, one house reef, barefoot villas.",
     [("Ocean View Villa", "216", 2, 10, 60, "king", "1", "ss-oceanview"),
      ("Overwater Reserve Villa", "356", 2, 14, 72, "king", "2", "ss-overwater")]),
]

# Destination categories as rated by travellers on booking.com (Cambodia
# country page, fetched 2026-09) + original OTA-style property descriptions
# grounded in real landmark facts.
VIBES = {
    "aurelia-grand-phnom-penh": "History, Culture, Markets",
    "aurelia-angkor-sanctuary": "Temples, History, Culture",
    "aurelia-kep-cove": "Seafood, Tranquillity, Relaxation",
    "aurelia-koh-rong-overwater": "Sandy Beaches, Relaxation, Beaches",
    "aurelia-marina-bay": "Beaches, Sandy Beaches, Relaxation",
    "aurelia-battambang-riverside": "Countryside, Friendly Locals, Sightseeing",
    "raffles-hotel-le-royal": "Heritage, History, Culture",
}

DESCRIPTIONS = {
    "aurelia-grand-phnom-penh": (
        "On the Tonlé Sap riverfront promenade, the flagship puts the Royal Palace, the National "
        "Museum and the night market inside a ten-minute stroll. Phnom Penh is rated by travellers "
        "for history, culture and markets — and the house answers with a rooftop Mekong terrace, "
        "Khmer-fusion dining and a spa above the river. Palace ferries and Sisowath Quay cafés "
        "leave from the door; Phnom Penh International is 40 minutes away."),
    "aurelia-angkor-sanctuary": (
        "Minutes from the gates of Angkor — the largest religious monument on earth — the sanctuary "
        "sits in frangipani gardens on the temple circuit road. Siem Reap, Cambodia's most-loved "
        "destination for temples, history and culture with 688 places to stay, is at its calmest "
        "here: sunrise departures for Angkor Wat, an afternoon by the pool, Kampot-pepper tasting "
        "menus in the evening, Pub Street and the Old Market a short tuk-tuk ride away."),
    "aurelia-kep-cove": (
        "Kep is Cambodia's quiet coast — a seaside town rated for seafood, tranquillity and "
        "relaxation, famous for its crab market and pepper farms. The cove resort faces the water "
        "below Kep National Park's jungle hills: barefoot lawns, a saltwater pool, bicycles for "
        "the coast road to Kep Beach and the ferry jetty to Koh Tonsay (Rabbit Island). Sunset "
        "at the crab market is five minutes away."),
    "aurelia-koh-rong-overwater": (
        "A boat ride from the Sihanoukville pier, Koh Rong is rated by travellers for sandy "
        "beaches, relaxation and beaches — powder-white sand and warm, glass-clear gulf water. "
        "The resort spans a private spit: overwater villas above a shallow house reef, beach "
        "bungalows under the casuarinas, kayaks and snorkel gear at the jetty, bioluminescent "
        "plankton on night swims. No roads, no cars — only the tide table."),
    "aurelia-marina-bay": (
        "Cambodia's beach capital — rated for beaches, sandy beaches and relaxation — arcs around "
        "a peninsula of bays from Ochheuteal to Sokha and Otres. Marina Bay rises over the yacht "
        "harbour with rooftop sea pools and a marina club, shuttle boats to the island reefs, "
        "Kbal Chhay waterfall and Ream National Park inland, and the Koh Rong ferries leaving "
        "from the pier below the hotel."),
    "raffles-hotel-le-royal": (
        "Opened in 1929 as the Hotel Royal and restored for its century, Le Royal is Phnom Penh's "
        "grande dame: white colonnades, frangipani lawns and the vaulted Elephant Bar where Chaplin "
        "and Jackie Kennedy once drank. Named Cambodia's top city hotel by Travel + Leisure (2026), "
        "a MICHELIN Key holder and No. 2 in Southeast Asia in the Condé Nast Readers' Choice Awards, "
        "it pairs heritage suites with twin pools, a spa and French-Khmer fine dining — five minutes "
        "from the Royal Palace."),
    "aurelia-battambang-riverside": (
        "Cambodia's artistic second city is rated for countryside, friendly locals and sightseeing "
        "— colonial shophouses, art studios and the slow bend of the Sangker River. The riverside "
        "maison is a restored French-era townhouse on the riverfront boulevard: the bamboo train, "
        "hilltop Wat Banan and an evening at the Phare circus are all short rides away; house "
        "bicycles and the river terrace handle the rest."),
}

# Top nearby attractions per property — attraction names and rankings taken
# from Booking.com "Things to do" city pages (fetched 2026-09); blurbs and
# distances are our own editorial copy. Kep & Koh Rong have no Booking
# attractions page — sourced from the country page + neighbouring lists.
VIBES.update({
    "rosewood-phnom-penh": "Skyline, Heritage, Luxury",
    "sala-lodges": "Heritage, Gardens, Quiet",
    "song-saa-private-island": "Island, Eco-Luxury, Romance",
})

DESCRIPTIONS.update({
    "rosewood-phnom-penh": (
        "Floors 30 to 42 of the Vattanac Capital Tower on Monivong Boulevard — Cambodia's tallest "
        "building — hold the Rosewood's glass-walled rooms above the rooftops. The residence-style "
        "interiors layer Khmer silk, lacquer and art-deco references over skyline views from the "
        "Mekong to the palace spires; the rooftop bar and the sky lobby's lantern light are city "
        "institutions. Wat Phnom, the rail-market food stalls and the riverfront are minutes below."),
    "sala-lodges": (
        "Eleven authentic Khmer heritage houses — some fifty years old, dismantled in villages "
        "across the countryside and reassembled beam by beam — stand in a garden of rice paddies, "
        "sugar palms and banana trees on Salakomreuk Road. Each lodge keeps its own character: "
        "hand-made quilts, rusted-wood walls, deep verandas. A twenty-metre sunset pool and a "
        "modern pavilion restaurant anchor the estate; Angkor's temple road is a short tuk-tuk "
        "ride away, Pub Street and the Old Market closer still."),
    "song-saa-private-island": (
        "Two islets — Koh Ouen and Koh Bong — joined by a footbridge over a self-declared marine "
        "reserve in the Koh Rong archipelago: Cambodia's first private-island resort and its "
        "most serious conservation story. Villas of driftwood, thatch and stone step straight "
        "onto the house reef; overwater reserves hang above turquoise shallows where black-tip "
        "sharks patrol. Forty-five minutes by speedboat from Sihanoukville, the island runs on "
        "solar power, reef restoration and barefoot silence."),
})

ATTRACTIONS = {
    "aurelia-grand-phnom-penh": [
        ("ri-sailboat-line", "Mekong & Tonlé Sap sunset cruise", "from the pier", "Boats leave steps from the door; gold light where four rivers meet."),
        ("ri-government-line", "Royal Palace & Silver Pagoda", "1.2 km", "Gilded spires and the Emerald Buddha — the kingdom's ceremonial heart."),
        ("ri-gallery-line", "National Museum of Cambodia", "1.5 km", "The world's finest Khmer sculpture, around a rust-red cloister."),
        ("ri-boxing-line", "Kun Khmer kickboxing night", "2.5 km", "Cambodia's ancient boxing art at the city's evening fight cards."),
        ("ri-candle-line", "Tuol Sleng (S-21) & Choeung Ek", "15 km", "The genocide museum and Killing Fields — the city's essential history."),
        ("ri-shopping-bag-line", "Central Market, Psar Thmei", "2 km", "An art-deco dome of gems, silk, watches and street food."),
    ],
    "aurelia-angkor-sanctuary": [
        ("ri-ancient-gate-line", "Angkor Wat at sunrise", "6 km", "The largest religious monument on earth, mirrored in its moat."),
        ("ri-tree-line", "Ta Prohm & the Bayon", "8 km", "Strangler-fig galleries and 200 smiling stone faces of Angkor Thom."),
        ("ri-ticket-2-line", "Phare, the Cambodian Circus", "3 km", "Acrobats, fire and drums telling Khmer stories — the town's best night."),
        ("ri-music-2-line", "Apsara dance dinner", "2.5 km", "Classical Khmer dance between courses of Kampot-pepper cuisine."),
        ("ri-drop-line", "Phnom Kulen waterfalls", "48 km", "The sacred mountain: river of a thousand lingas and picnic cascades."),
    ],
    "aurelia-kep-cove": [
        ("ri-restaurant-line", "Kep crab market", "1.5 km", "Blue-swimmer crab stalls beneath the famous statue — eat at sunset."),
        ("ri-landscape-line", "Kep National Park", "3 km", "A jungle loop road with viewpoints over the Kampot plain and islands."),
        ("ri-sailboat-line", "Koh Tonsay (Rabbit Island)", "30 min by boat", "Bungalows, a quiet swimming beach and a lighthouse walk."),
        ("ri-plant-line", "Kampot pepper plantations", "12 km", "The world's most praised pepper, grown one valley over."),
    ],
    "aurelia-koh-rong-overwater": [
        ("ri-umbrella-line", "Saracen Bay", "1 km", "A crescent of powder-white sand — the island's postcard view."),
        ("ri-water-flash-line", "House-reef snorkelling", "off the jetty", "Coral gardens and clownfish at slack tide, no boat needed."),
        ("ri-sparkling-2-line", "Bioluminescent night swim", "after dark", "On moonless nights the water glows blue with every stroke."),
        ("ri-footprint-line", "Long Beach jungle trail", "4 km", "Over the headland to the island's longest, emptiest sand."),
    ],
    "aurelia-marina-bay": [
        ("ri-umbrella-line", "Ochheuteal & Otres beaches", "3 km", "Beach clubs and long sand at Ochheuteal; quieter palms at Otres."),
        ("ri-landscape-line", "Bokor National Park", "45 km", "Cloud-forest hills and the ruins of a colonial hill station."),
        ("ri-plant-line", "Kampot pepper & salt farms", "60 km", "Pepper vines, glittering salt pans and cave pagodas on the plain."),
        ("ri-restaurant-2-line", "Kampot cooking class", "60 km", "Market-to-wok Khmer classics with a local family."),
        ("ri-drop-line", "Kbal Chhay waterfall", "18 km", "A wide, swim-friendly cascade in the coastal hills."),
    ],
    "raffles-hotel-le-royal": [
        ("ri-goblet-line", "The Elephant Bar", "in-house", "A vaulted 1929 bar of murals and memoirs — order the Femme Fatale."),
        ("ri-government-line", "Royal Palace & Silver Pagoda", "1 km", "Gilded spires and the Emerald Buddha — the kingdom's ceremonial heart."),
        ("ri-gallery-line", "National Museum of Cambodia", "1.3 km", "The world's finest Khmer sculpture, around a rust-red cloister."),
        ("ri-sailboat-line", "Sisowath Quay riverfront", "1.2 km", "Cafés, night market and sunset walks on the Tonlé Sap esplanade."),
        ("ri-candle-line", "Tuol Sleng (S-21) & Choeung Ek", "3 km & 14 km", "The genocide museum and Killing Fields — essential history."),
        ("ri-shopping-bag-line", "Central Market, Psar Thmei", "1.6 km", "An art-deco dome of gems, silk, watches and street food."),
    ],
    "aurelia-battambang-riverside": [
        ("ri-train-line", "The bamboo train (norry)", "4 km", "The famous flatbed rail ride out through the rice fields."),
        ("ri-moon-line", "Phnom Sampeau bat caves", "12 km", "At dusk, millions of bats stream from the cave in a black ribbon."),
        ("ri-ancient-gate-line", "Wat Banan hilltop temple", "20 km", "358 steps to an Angkor-era sanctuary above the Sangker valley."),
        ("ri-bowl-line", "Psar Nath market & cooking class", "1 km", "A market stroll, then wok time with a Battambang cook."),
        ("ri-palette-line", "Phare Ponleu Selpak arts campus", "2 km", "The Battambang art school whose circus became world-famous."),
    ],
}

ATTRACTIONS.update({
    "rosewood-phnom-penh": [
        ("ri-government-line", "Royal Palace & Silver Pagoda", "1.3 km", "Gilded spires and the Emerald Buddha from the tower's south glass."),
        ("ri-gallery-line", "National Museum of Cambodia", "1.6 km", "The world's finest Khmer sculpture around a rust-red cloister."),
        ("ri-ancient-gate-line", "Wat Phnom", "0.9 km", "The founding hill-temple of the city, four blocks from the tower."),
        ("ri-shopping-bag-line", "Russian Market, Psar Tuol Tom Pong", "3.4 km", "Silk, silver, spices and the city's best street food rows."),
    ],
    "sala-lodges": [
        ("ri-ancient-gate-line", "Angkor Wat at sunrise", "7 km", "The largest religious monument on earth, mirrored in its moat."),
        ("ri-restaurant-2-line", "Pub Street & Psar Chaa", "1.4 km", "Lantern-lit terraces and the old market's smoky grill lanes."),
        ("ri-ticket-2-line", "Phare, the Cambodian Circus", "2.1 km", "Acrobats, fire and drums telling Khmer stories — the town's best night."),
        ("ri-sailboat-line", "Kampong Phluk floating village", "16 km", "Stilted houses and flooded forest on the Tonlé Sap's edge."),
    ],
    "song-saa-private-island": [
        ("ri-water-flash-line", "Koh Ouen house-reef dive", "0.2 km", "Step off the jetty into a restored reef of coral gardens and seahorses."),
        ("ri-sparkling-2-line", "Plankton glow night swim", "0.5 km", "Warm black water that ignites blue with every stroke — no filter needed."),
        ("ri-sailboat-line", "Koh Rong Sanloem day sail", "9 km", "A private boat to Saracen Bay's white arc and lazy reef snorkels."),
        ("ri-tree-line", "Jungle canopy walk, Koh Ouen", "0.3 km", "A ranger-led trail over the island's banyan ridge to the west lookout."),
    ],
})

# WGS-84 coordinates, sourced from Google Maps / operator listings.
PROPERTY_COORDS = {
    "aurelia-grand-phnom-penh": (11.5656, 104.9325),
    "aurelia-angkor-sanctuary": (13.3520, 103.8570),
    "aurelia-kep-cove": (10.5400, 104.3150),
    "aurelia-koh-rong-overwater": (10.6700, 103.2500),
    "aurelia-marina-bay": (10.5700, 103.8100),
    "aurelia-battambang-riverside": (13.0980, 103.2050),
    "raffles-hotel-le-royal": (11.5699, 104.9290),
    "rosewood-phnom-penh": (11.5687, 104.9309),
    "sala-lodges": (13.3454, 103.8605),
    "song-saa-private-island": (10.7555, 103.2621),
}

ATTRACTION_COORDS = {
    "Mekong & Tonlé Sap sunset cruise": (11.5656, 104.9325),
    "Royal Palace & Silver Pagoda": (11.5625, 104.9312),
    "National Museum of Cambodia": (11.5686, 104.9312),
    "Kun Khmer kickboxing night": (11.5400, 104.9350),
    "Tuol Sleng (S-21) & Choeung Ek": (11.5483, 104.9232),
    "Central Market, Psar Thmei": (11.5719, 104.9356),
    "Sisowath Quay riverfront": (11.5656, 104.9325),
    "Angkor Wat at sunrise": (13.4125, 103.8670),
    "Ta Prohm & the Bayon": (13.4355, 103.8890),
    "Phare, the Cambodian Circus": (13.3408, 103.8453),
    "Apsara dance dinner": (13.3535, 103.8563),
    "Phnom Kulen waterfalls": (13.5889, 104.0578),
    "Kep crab market": (10.5364, 104.3098),
    "Kep National Park": (10.5653, 104.2986),
    "Koh Tonsay (Rabbit Island)": (10.4833, 104.3667),
    "Kampot pepper plantations": (10.6167, 104.1833),
    "Saracen Bay": (10.6647, 103.2352),
    "House-reef snorkelling": (10.6600, 103.2400),
    "Bioluminescent night swim": (10.6550, 103.2500),
    "Long Beach jungle trail": (10.6833, 103.2833),
    "Ochheuteal & Otres beaches": (10.5653, 103.8186),
    "Bokor National Park": (10.6631, 104.0569),
    "Kampot pepper & salt farms": (10.6167, 104.1833),
    "Kampot cooking class": (10.6167, 104.1800),
    "Kbal Chhay waterfall": (10.4833, 103.7167),
    "The Elephant Bar": (11.5699, 104.9290),
    "The bamboo train (norry)": (13.0736, 103.2226),
    "Phnom Sampeau bat caves": (13.0236, 103.0586),
    "Wat Banan hilltop temple": (13.0289, 103.1356),
    "Psar Nath market & cooking class": (13.0957, 103.2022),
    "Phare Ponleu Selpak arts campus": (13.0880, 103.1960),
    "Wat Phnom": (11.5761, 104.9292),
    "Russian Market, Psar Tuol Tom Pong": (11.5478, 104.9283),
    "Pub Street & Psar Chaa": (13.3535, 103.8563),
    "Kampong Phluk floating village": (13.2889, 103.9833),
    "Koh Ouen house-reef dive": (10.7560, 103.2610),
    "Plankton glow night swim": (10.7480, 103.2540),
    "Koh Rong Sanloem day sail": (10.6647, 103.2352),
    "Jungle canopy walk, Koh Ouen": (10.7565, 103.2615),
}

AMENITY_SET = ["River view", "Free WiFi 500Mbps", "Rain shower", "Smart TV 55″", "Minibar",
               "Nespresso machine", "King bed", "Bathtub", "Balcony", "Air conditioning",
               "Safe deposit", "Spa access", "Airport transfer", "Breakfast included", "Pool access", "Work desk"]


class Command(BaseCommand):
    help = "Seed the Cambodia-only (10-property) Aurelia Collection demo dataset."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if Property.objects.exists() and not options["flush"]:
            self.stdout.write(self.style.WARNING("Data exists — use --flush to reseed."))
            return
        if options["flush"]:
            for model in (Payment, Invoice, HousekeepingTask, MaintenanceRequest, Booking,
                          RateRule, Room, RoomType, Attraction, Property, Amenity):
                model.objects.all().delete()

        today = timezone.localdate()

        # ---------------- users ----------------
        def mk_user(username, role, first, last, email=None, password="Aurelia2026!", **kw):
            u, _ = User.objects.update_or_create(
                username=username,
                defaults=dict(role=role, first_name=first, last_name=last,
                              email=email or f"{username}@aureliagrand.example", **kw),
            )
            u.set_password(password)
            u.save()
            return u

        admin = mk_user("admin", User.Role.ADMIN, "Aurelia", "Ops", is_superuser=True, is_staff=True)
        manager = mk_user("manager", User.Role.MANAGER, "Sophea", "Rith")          # chain-wide
        reception = mk_user("reception", User.Role.RECEPTIONIST, "Dara", "Keo")    # flagship
        hk1 = mk_user("housekeeping", User.Role.HOUSEKEEPING, "Bopha", "Sam")
        hk2 = mk_user("housekeeping2", User.Role.HOUSEKEEPING, "Malis", "Chea")
        guest = mk_user("guest", User.Role.GUEST, "Sokha", "Chan", email="sokha.chan@example.com")

        amenities = {n: Amenity.objects.create(name=n, icon="ri-vip-diamond-line") for n in AMENITY_SET}
        amenities["River view"].icon = "ri-water-flash-line"; amenities["Free WiFi 500Mbps"].icon = "ri-wifi-line"
        amenities["Rain shower"].icon = "ri-rainy-line"; amenities["Smart TV 55″"].icon = "ri-tv-2-line"
        amenities["Minibar"].icon = "ri-goblet-line"; amenities["Nespresso machine"].icon = "ri-cup-line"
        amenities["King bed"].icon = "ri-hotel-bed-line"; amenities["Bathtub"].icon = "ri-water-flash-line"
        amenities["Balcony"].icon = "ri-sun-line"; amenities["Air conditioning"].icon = "ri-temp-cold-line"
        amenities["Safe deposit"].icon = "ri-lock-2-line"; amenities["Spa access"].icon = "ri-leaf-line"
        amenities["Airport transfer"].icon = "ri-car-line"; amenities["Breakfast included"].icon = "ri-bread-line"
        amenities["Pool access"].icon = "ri-drop-line"; amenities["Work desk"].icon = "ri-briefcase-4-line"

        def ams(*names):
            return [amenities[n] for n in names]

        # ---------------- properties + inventory ----------------
        props = []
        for (name, slug, city, country, stars, svc, tax, image, tagline, types) in PROPERTIES:
            prop = Property.objects.create(
                name=name, slug=slug, city=city, country=country, stars=stars,
                service_rate=Decimal(svc), tax_rate=Decimal(tax), image_url=image, tagline=tagline,
                description=DESCRIPTIONS.get(slug, ""), vibe_tags=VIBES.get(slug, ""),
                latitude=PROPERTY_COORDS.get(slug, (None, None))[0],
                longitude=PROPERTY_COORDS.get(slug, (None, None))[1],
                address=f"1 Aurelia Way, {city}", phone=f"+855 23 900 {random.randint(100,999)}",
                email=f"stay@{slug}.example",
            )
            for ti, (tname, price, cap, count, sqm, bed, floors, img) in enumerate(types):
                rt = RoomType.objects.create(
                    property=prop, name=tname, base_price=Decimal(price), max_guests=cap,
                    total_rooms=count, size_sqm=sqm, bed_type=bed, floor_range=floors,
                    image_url=ROOM_IMG(img),
                    description=f"{tname} at {name}: {sqm} m² of considered comfort with {bed.replace('_', ' ')} configuration.",
                )
                rt.amenities.set(ams(*random.sample(AMENITY_SET, 8)))
                floor_base = int(floors.split("–")[0].split("-")[0]) if floors[0].isdigit() else ti + 1
                for i in range(count):
                    Room.objects.create(number=f"{floor_base}{i + 1:02d}", property=prop,
                                        room_type=rt, floor=floor_base,
                                        status=Room.Status.VACANT_CLEAN)
            for si, (icon, aname, dist, blurb) in enumerate(ATTRACTIONS.get(slug, [])):
                Attraction.objects.create(property=prop, name=aname, blurb=blurb,
                                          icon=icon, distance=dist, sort=si,
                                          latitude=ATTRACTION_COORDS.get(aname, (None, None))[0],
                                          longitude=ATTRACTION_COORDS.get(aname, (None, None))[1])
            props.append(prop)

        # Add one hotel-scoped Reception account for every active property.
        # Keep the original `reception` account below as a backwards-compatible
        # flagship alias used by the one-click demo login and older QA scripts.
        for prop in props:
            front_desk = mk_user(
                f"reception.{prop.slug}",
                User.Role.RECEPTIONIST,
                prop.city,
                "Reception",
            )
            front_desk.home_property = prop
            front_desk.save()

        # Housekeeping team roster (hk1/hk2 are the flagship's first two).
        team = [hk1, hk2]

        # assign home properties to demo staff
        reception.home_property = props[0]; reception.save()
        hk1.home_property = props[0]; hk1.save()
        hk2.home_property = props[0]; hk2.save()
        # Keep three cleaners per hotel in the demo. Existing housekeeping and
        # housekeeping2 are the first two members of the flagship team.
        for prop in props:
            start_index = 3 if prop.pk == props[0].pk else 1
            for index in range(start_index, 4):
                username = f"hk.{prop.slug}-{index}"
                member = mk_user(username, User.Role.HOUSEKEEPING, prop.city, f"Housekeeper {index}")
                member.home_property = prop
                member.save()
                team.append(member)

        sr_mgr = mk_user("manager.sr", User.Role.PROPERTY_MANAGER, "Virak", "Ngy")
        sr_mgr.home_property = props[1]; sr_mgr.save()
        # One property manager per hotel for the demo workflow. The group
        # manager above remains the only chain-wide operational account.
        for prop in props:
            if prop.pk == sr_mgr.home_property_id:
                continue
            username = f"pm.{prop.slug}"
            city_manager = mk_user(username, User.Role.PROPERTY_MANAGER, prop.city, "Manager")
            city_manager.home_property = prop
            city_manager.save()

        # ---------------- rate rules: chain + property ----------------
        RateRule.objects.create(name="High season · Dec–Jan", rule_type="seasonal",
                                start_date=dt.date(today.year, 12, 20), end_date=dt.date(today.year + 1, 1, 5),
                                multiplier=Decimal("1.35"), priority=10)
        RateRule.objects.create(name="Weekend premium", rule_type="weekend",
                                start_date=today - dt.timedelta(days=90), end_date=today + dt.timedelta(days=365),
                                multiplier=Decimal("1.12"), priority=5)
        RateRule.objects.create(name="Green season promo · Phnom Penh", rule_type="promo", property=props[0],
                                room_type=props[0].room_types.first(), start_date=today - dt.timedelta(days=10),
                                end_date=today + dt.timedelta(days=20), multiplier=Decimal("0.9"), priority=15)
        RateRule.objects.create(name="Angkor New Year", rule_type="seasonal", property=props[1],
                                start_date=today - dt.timedelta(days=5), end_date=today + dt.timedelta(days=5),
                                multiplier=Decimal("1.4"), priority=20)
        RateRule.objects.create(name="Bon Om Touk · Phnom Penh", rule_type="seasonal", property=props[0],
                                start_date=dt.date(today.year, 11, 5), end_date=dt.date(today.year, 11, 8),
                                multiplier=Decimal("1.25"), priority=25)
        # Keep the pricing-rule records for the PMS demo, but leave them
        # disabled so date searches stay flat at each room type's tiered rack rate.
        RateRule.objects.update(is_active=False)

        # ---------------- booking history per property ----------------
        sources = [Booking.Source.WEB] * 5 + [Booking.Source.OTA] * 3 + [Booking.Source.PHONE, Booking.Source.WALK_IN]

        def person():
            first, last = random.choice(FIRST), random.choice(LAST)
            return (f"{first} {last}", f"{first.lower()}.{last.lower()}@example.com",
                    f"+855 {random.randint(10,99)} {random.randint(200,999)} {random.randint(1000,9999)}")

        def make_booking(rt, check_in, nights, status, source=None, guest_user=None,
                         created_days_ago=None, need_rooms=True):
            check_out = check_in + dt.timedelta(days=nights)
            rooms = 1 if random.random() > 0.15 else 2
            avail = available_rooms(rt, check_in, check_out)
            if avail <= 0:
                return None
            rooms = min(rooms, avail)
            if need_rooms:
                free = Room.objects.filter(room_type=rt, status=Room.Status.VACANT_CLEAN).count()
                if free < rooms:
                    rooms = free
                    if rooms <= 0:
                        return None
            adults = min(rt.max_guests * rooms, random.choice([1, 2, 2, 2, 3]))
            children = random.choice([0, 0, 0, 1]) if adults < rt.max_guests * rooms else 0
            name, email, phone = person()
            if guest_user is not None:
                name, email, phone = guest_user.get_full_name(), guest_user.email, guest_user.phone
            pricing = price_stay(rt, check_in, check_out, rooms)
            created = timezone.now() - dt.timedelta(days=created_days_ago or random.randint(3, 40),
                                                    hours=random.randint(0, 20))
            b = Booking.objects.create(
                guest=guest_user, guest_name=name, guest_email=email, guest_phone=phone,
                room_type=rt, check_in=check_in, check_out=check_out, rooms_count=rooms,
                adults=adults, children=children, status=status, source=source or random.choice(sources),
                currency="USD", nightly_total=pricing["subtotal"], service_total=pricing["service"],
                tax_total=pricing["tax"], grand_total=pricing["total"], rate_details=pricing["nights"],
                created_by=random.choice([reception, manager]) if source in ("phone", "walk_in", "ota") else None,
                special_requests=random.choice(["", "", "Early check-in if possible", "High floor please",
                                                "Quiet room away from lift", "Airport pickup please"]),
            )
            Booking.objects.filter(pk=b.pk).update(created_at=created)
            b.refresh_from_db()
            ensure_invoice(b)
            return b

        def prepaid(b, at=None):
            inv = ensure_invoice(b)
            Payment.objects.create(invoice=inv, booking=b, amount=b.grand_total, method="card",
                                   status="completed", note="Prepaid at booking", reference=f"SIM-{b.code}",
                                   created_at=at or b.created_at)
            inv.recalc_status()

        total_bookings = 0
        for pi, prop in enumerate(props):
            rts = list(prop.room_types.all())
            scale = 1.0 if pi == 0 else 0.45   # flagship gets fuller history

            def n(base):
                return max(1, int(round(base * scale)))

            # past checked-out stays
            for _ in range(n(14)):
                rt = random.choices(rts, weights=[4, 2, 2, 1][:len(rts)])[0]
                ci = today - dt.timedelta(days=random.randint(2, 55))
                nights = random.choices([1, 2, 3, 4, 5], weights=[2, 4, 3, 2, 1])[0]
                if ci + dt.timedelta(days=nights) > today - dt.timedelta(days=1):
                    continue
                b = make_booking(rt, ci, nights, Booking.Status.CHECKED_OUT, need_rooms=False,
                                 created_days_ago=(today - ci).days + random.randint(3, 25))
                if not b:
                    continue
                total_bookings += 1
                inv = ensure_invoice(b)
                Payment.objects.create(invoice=inv, booking=b, amount=b.grand_total,
                                       method=random.choice(["card", "card", "cash", "bank_transfer"]),
                                       status="completed", note="Settled at check-out", reference=f"SIM-{b.code}",
                                       created_at=timezone.now() - dt.timedelta(days=(today - b.check_out).days))
                inv.recalc_status()

            # cancellations
            for _ in range(n(2)):
                rt = random.choice(rts)
                b = make_booking(rt, today - dt.timedelta(days=random.randint(3, 30)), random.randint(1, 3),
                                 Booking.Status.CANCELLED, need_rooms=False)
                if not b:
                    continue
                b.cancellation_reason = "Plans changed"; b.cancellation_fee = Decimal("0")
                b.save(update_fields=["cancellation_reason", "cancellation_fee"])
                inv = ensure_invoice(b); inv.total = Decimal("0"); inv.subtotal = Decimal("0"); inv.save()
                inv.recalc_status()

            # in-house
            for _ in range(n(4)):
                rt = random.choices(rts, weights=[4, 2, 2, 1][:len(rts)])[0]
                ci = today - dt.timedelta(days=random.randint(0, 3))
                b = make_booking(rt, ci, random.randint(2, 6), Booking.Status.CHECKED_IN,
                                 created_days_ago=random.randint(4, 30))
                if not b:
                    continue
                total_bookings += 1
                free = list(Room.objects.filter(room_type=rt, status=Room.Status.VACANT_CLEAN))
                for _ in range(b.rooms_count):
                    if not free:
                        break
                    room = free.pop(random.randrange(len(free)))
                    room.status = Room.Status.OCCUPIED_CLEAN
                    room.save(update_fields=["status", "updated_at"])
                    b.room_assignments.create(room=room, assigned_by=reception)
                if random.random() < 0.4:
                    assigned = [a.room for a in b.room_assignments.all()]
                    if assigned:
                        assigned[0].status = Room.Status.OCCUPIED_DIRTY
                        assigned[0].save(update_fields=["status", "updated_at"])
                if random.random() < 0.6:
                    prepaid(b)

            # arrivals today
            for _ in range(n(3)):
                rt = random.choices(rts, weights=[4, 2, 2, 1][:len(rts)])[0]
                b = make_booking(rt, today, random.randint(1, 4), Booking.Status.CONFIRMED,
                                 created_days_ago=random.randint(2, 20), need_rooms=False)
                if not b:
                    continue
                total_bookings += 1
                if random.random() < 0.5:
                    prepaid(b)

            # departures today
            for _ in range(n(2)):
                rt = random.choices(rts, weights=[4, 2, 2, 1][:len(rts)])[0]
                ci = today - dt.timedelta(days=random.randint(1, 4))
                b = make_booking(rt, ci, (today - ci).days, Booking.Status.CHECKED_IN,
                                 created_days_ago=random.randint(5, 25))
                if not b:
                    continue
                total_bookings += 1
                free = list(Room.objects.filter(room_type=rt, status=Room.Status.VACANT_CLEAN))
                for _ in range(b.rooms_count):
                    if not free:
                        break
                    room = free.pop(random.randrange(len(free)))
                    room.status = Room.Status.OCCUPIED_CLEAN
                    room.save(update_fields=["status", "updated_at"])
                    b.room_assignments.create(room=room, assigned_by=reception)

            # future window
            for _ in range(n(9)):
                rt = random.choices(rts, weights=[4, 2, 2, 1][:len(rts)])[0]
                b = make_booking(rt, today + dt.timedelta(days=random.randint(1, 30)), random.randint(1, 5),
                                 Booking.Status.CONFIRMED, created_days_ago=random.randint(1, 15),
                                 need_rooms=False)
                if not b:
                    continue
                total_bookings += 1
                if random.random() < 0.45:
                    prepaid(b)

        # demo guest's own stays (flagship)
        make_booking(props[0].room_types.all()[2], today + dt.timedelta(days=12), 3,
                     Booking.Status.CONFIRMED, source=Booking.Source.WEB, guest_user=guest, need_rooms=False)
        make_booking(props[0].room_types.all()[0], today - dt.timedelta(days=40), 2,
                     Booking.Status.CHECKED_OUT, source=Booking.Source.WEB, guest_user=guest,
                     created_days_ago=60, need_rooms=False)

        # ---------------- housekeeping & maintenance ----------------
        vacant = list(Room.objects.filter(status=Room.Status.VACANT_CLEAN))
        for room in random.sample(vacant, min(14, len(vacant))):
            room.status = Room.Status.VACANT_DIRTY
            room.save(update_fields=["status", "updated_at"])
            HousekeepingTask.objects.create(room=room, task_type="checkout_clean",
                                            priority=random.choice(["urgent", "high", "normal"]))
        for room in Room.objects.filter(status=Room.Status.OCCUPIED_DIRTY):
            HousekeepingTask.objects.create(room=room, task_type="daily_service", priority="normal")
        tasks = list(HousekeepingTask.objects.filter(status="pending"))
        if tasks:
            t = tasks[0]; t.status = "in_progress"; t.assigned_to = hk1; t.started_at = timezone.now(); t.save()
        for t in tasks[1:4]:
            t.status = "completed"; t.assigned_to = hk1
            t.completed_at = timezone.now() - dt.timedelta(hours=random.randint(1, 6)); t.save()
            if t.room.status == Room.Status.VACANT_DIRTY:
                t.room.status = Room.Status.VACANT_CLEAN
                t.room.save(update_fields=["status", "updated_at"])

        ooo = Room.objects.filter(status=Room.Status.VACANT_CLEAN, room_type__property=props[3]).first() \
            or Room.objects.filter(status=Room.Status.VACANT_CLEAN).first()
        if ooo:
            ooo.status = Room.Status.MAINTENANCE
            ooo.save(update_fields=["status", "updated_at"])
            MaintenanceRequest.objects.create(room=ooo, title="Air-conditioning compressor failure",
                                              severity="critical", reported_by=reception,
                                              description="Unit not cooling; parts ordered.")
        m2 = Room.objects.exclude(pk=ooo.pk).filter(status=Room.Status.VACANT_CLEAN).first()
        if m2:
            MaintenanceRequest.objects.create(room=m2, title="Bathroom faucet dripping", severity="low",
                                              status="resolved", reported_by=hk1,
                                              resolved_at=timezone.now() - dt.timedelta(days=2))

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Property.objects.count()} properties, {RoomType.objects.count()} room types, "
            f"{Room.objects.count()} rooms, {Booking.objects.count()} bookings, "
            f"{Payment.objects.count()} payments, {HousekeepingTask.objects.count()} tasks, "
            f"{User.objects.count()} users."))
        self.stdout.write("Logins (password Aurelia2026!): manager · reception · reception.<hotel-slug> · "
                          "manager.sr · housekeeping · guest")
