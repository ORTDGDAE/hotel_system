from __future__ import annotations

from pathlib import Path
from pptx import Presentation
from pptx.util import Pt

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "Aurelia_Collection_Hotel_Management_Project_Short_Deck.pptx"
OUT = ROOT / "Aurelia_Collection_Hotel_Management_Project_Short_Deck_KH.pptx"
prs = Presentation(str(BASE))

# Natural, presentation-ready Khmer. Technical names remain in Latin script
# where hotel teams are more likely to recognize them quickly.
T = {
    # Cover and shared footer
    "AURELIA COLLECTION": "AURELIA COLLECTION",
    "Hotel Management\nProject": "គម្រោងគ្រប់គ្រង\nសណ្ឋាគារ",
    "A short, meaningful view of the complete guest journey,\nPMS operations, role access, pricing and deployment path.": "ទិដ្ឋភាពសង្ខេប និងមានខ្លឹមសារ អំពីដំណើររបស់ភ្ញៀវទាំងមូល, ប្រតិបត្តិការ PMS, សិទ្ធិតាមតួនាទី, តម្លៃ និងផ្លូវដាក់ឱ្យប្រើ។",
    "properties": "សណ្ឋាគារ",
    "room types": "ប្រភេទបន្ទប់",
    "lowest rate": "តម្លៃចាប់ផ្តើម",
    "Direct booking · front desk · housekeeping · finance · analytics": "ការកក់ផ្ទាល់ · Front Desk · Housekeeping · ហិរញ្ញវត្ថុ · Analytics",
    "LATEST PROJECT SUMMARY · 29 SEP 2026": "សង្ខេបគម្រោងកំណែចុងក្រោយ · ២៩ កញ្ញា ២០២៦",
    "Aurelia Collection · Hotel management project · 29 September 2026": "Aurelia Collection · គម្រោងគ្រប់គ្រងសណ្ឋាគារ · ២៩ កញ្ញា ២០២៦",
    "Aurelia Collection · short project deck": "Aurelia Collection · បទបង្ហាញសង្ខេបអំពីគម្រោង",

    # 2 — executive view
    "EXECUTIVE VIEW": "ទិដ្ឋភាពសម្រាប់អ្នកគ្រប់គ្រង",
    "What the project delivers": "អ្វីដែលគម្រោងនេះផ្តល់ជូន",
    "One operating system connects guest demand to room readiness, financial control and management insight.": "ប្រព័ន្ធប្រតិបត្តិការតែមួយ ភ្ជាប់តម្រូវការរបស់ភ្ញៀវ ជាមួយការរៀបចំបន្ទប់, ការគ្រប់គ្រងហិរញ្ញវត្ថុ និងព័ត៌មានសម្រាប់អ្នកគ្រប់គ្រង។",
    "The problem": "បញ្ហាដែលត្រូវដោះស្រាយ",
    "Hotel teams work across disconnected channels, spreadsheets and manual handoffs. That creates slow response, unclear ownership and risk of inventory or billing errors.": "ក្រុមសណ្ឋាគារត្រូវធ្វើការតាម Channel ផ្សេងៗ, Spreadsheet និងការប្រគល់ការងារដោយដៃ។ វាធ្វើឱ្យការឆ្លើយតបយឺត, មិនច្បាស់ថាអ្នកណាទទួលខុសត្រូវ និងអាចបង្កកំហុសផ្នែកស្តុក ឬវិក្កយបត្រ។",
    "The answer": "ដំណោះស្រាយ",
    "Aurelia Collection combines a guest website and a role-based PMS with one reservation record, one room state and one financial snapshot.": "Aurelia Collection ភ្ជាប់គេហទំព័រសម្រាប់ភ្ញៀវ ជាមួយ PMS ដែលកំណត់សិទ្ធិតាមតួនាទី ដោយមានកំណត់ត្រាកក់តែមួយ, ស្ថានភាពបន្ទប់តែមួយ និង Financial Snapshot តែមួយ។",
    "The result": "លទ្ធផល",
    "A clear operating rhythm: discover, book, prepare, arrive, stay, check out, reconcile and improve.": "លំហូរប្រតិបត្តិការដែលច្បាស់: ស្វែងរក, កក់, រៀបចំ, មកដល់, ស្នាក់នៅ, Check-out, ផ្ទៀងផ្ទាត់ និងកែលម្អ។",
    "The project is deliberately simple for users and disciplined underneath.": "គម្រោងនេះរចនាឱ្យសាមញ្ញសម្រាប់អ្នកប្រើ ប៉ុន្តែមានវិន័យខ្ពស់នៅខាងក្រោយ។",
    "minimum catalog rate": "តម្លៃអប្បបរមាក្នុង Catalog",
    "tax only": "ពន្ធតែប៉ុណ្ណោះ",
    "service charge": "Service Charge",
    "operating source of truth": "ប្រភពទិន្នន័យប្រតិបត្តិការតែមួយ",

    # 3 — channels
    "DEMAND TO STAY": "ពីតម្រូវការទៅការស្នាក់នៅ",
    "One journey, three booking channels": "ដំណើរតែមួយ តាមបណ្តាញកក់ ៣ ប្រភេទ",
    "Every channel ends in the same controlled reservation, inventory check and folio workflow.": "គ្រប់ Channel បញ្ចប់នៅកន្លែងតែមួយ: ការកក់ដែលបានគ្រប់គ្រង, ការត្រួតពិនិត្យស្តុក និងលំហូរ Folio។",
    "Website": "គេហទំព័រ",
    "Guest searches dates, rooms and live totals, then confirms online.": "ភ្ញៀវស្វែងរកកាលបរិច្ឆេទ, បន្ទប់ និងតម្លៃសរុបបច្ចុប្បន្ន បន្ទាប់មកបញ្ជាក់តាមអនឡាញ។",
    "Walk-in / phone": "Walk-in / ទូរស័ព្ទ",
    "Reception creates the stay for the guest using the same rules.": "Reception បង្កើតការស្នាក់នៅជំនួសភ្ញៀវ ដោយប្រើច្បាប់ដូចគ្នា។",
    "OTA / agency": "OTA / Agency",
    "Source is recorded manually today; external reference stays visible.": "បច្ចុប្បន្ន ប្រភពត្រូវបានកត់ត្រាដោយដៃ ហើយលេខយោងខាងក្រៅនៅតែអាចមើលឃើញ។",
    "One reservation": "ការកក់តែមួយ",
    "Availability, price, folio, status and history remain consistent.": "Availability, តម្លៃ, Folio, ស្ថានភាព និងប្រវត្តិ នៅតែស៊ីសង្វាក់គ្នា។",
    "Guest service": "សេវាសម្រាប់ភ្ញៀវ",
    "Property discovery, room details, live availability, registered-user welcome offer, confirmation and My Stays self-service.": "ស្វែងរកសណ្ឋាគារ, ព័ត៌មានបន្ទប់, Availability បច្ចុប្បន្ន, Welcome Offer សម្រាប់អ្នកចុះឈ្មោះ, ការបញ្ជាក់ និងការគ្រប់គ្រងតាម My Stays។",
    "Future channel layer": "ស្រទាប់ Channel នាពេលអនាគត",
    "A channel-manager integration can later add automatic OTA availability, rate, booking-import and overbooking protection.": "ការភ្ជាប់ Channel Manager នៅពេលក្រោយ អាចធ្វើឱ្យ Availability និង Rate ជាមួយ OTA, ការនាំចូលការកក់ និងការការពារ Overbooking ដំណើរការដោយស្វ័យប្រវត្តិ។",
    "Current boundary: OTA / agency handling is manual but controlled; automatic synchronization is future scope.": "ព្រំដែនបច្ចុប្បន្ន: OTA / Agency ត្រូវបានគ្រប់គ្រងដោយដៃ ប៉ុន្តែមានការត្រួតពិនិត្យ; ការធ្វើសមកាលកម្មស្វ័យប្រវត្តិ ជាវិសាលភាពបន្ទាប់។",

    # 4 — roles
    "PEOPLE AND ACCESS": "មនុស្ស និងសិទ្ធិប្រើប្រាស់",
    "Five roles keep the hotel moving": "តួនាទី ៥ ធ្វើឱ្យសណ្ឋាគារដំណើរការ",
    "Each role sees the work it owns while the platform protects shared inventory and financial records.": "តួនាទីនីមួយៗឃើញការងារដែលខ្លួនទទួលខុសត្រូវ ខណៈ Platform ការពារស្តុករួម និងកំណត់ត្រាហិរញ្ញវត្ថុ។",
    "Guest": "ភ្ញៀវ",
    "Search, book, manage a personal stay": "ស្វែងរក, កក់ និងគ្រប់គ្រងការស្នាក់នៅផ្ទាល់ខ្លួន",
    "Reception": "Reception",
    "Reservations, arrivals, departures and payments": "ការកក់, ការមកដល់, ការចាកចេញ និងការទូទាត់",
    "Housekeeping": "Housekeeping",
    "Room status, tasks and maintenance handoff": "ស្ថានភាពបន្ទប់, កិច្ចការ និងការប្រគល់ការងារ Maintenance",
    "Manager": "Manager",
    "Rates, finance, analytics and property scope": "Rate, ហិរញ្ញវត្ថុ, Analytics និងវិសាលភាពសណ្ឋាគារ",
    "Administrator": "Administrator",
    "Users, configuration and full system control": "អ្នកប្រើ, ការកំណត់រចនា និងការគ្រប់គ្រងប្រព័ន្ធពេញលេញ",
    "Access principle": "គោលការណ៍សិទ្ធិ",
    "Guests see their own journey · staff operate the hotel · managers control the business · administrators control the system.": "ភ្ញៀវឃើញដំណើររបស់ខ្លួន · Staff ប្រតិបត្តិការសណ្ឋាគារ · Manager គ្រប់គ្រងអាជីវកម្ម · Administrator គ្រប់គ្រងប្រព័ន្ធ។",

    # 5 — operations
    "OPERATIONS": "ប្រតិបត្តិការ",
    "From booking to checkout": "ពីការកក់ ដល់ Check-out",
    "The PMS turns a reservation into a visible operational handoff instead of a hidden manual task.": "PMS បម្លែងការកក់មួយ ទៅជាការប្រគល់ការងារដែលអាចមើលឃើញ ជំនួសឱ្យកិច្ចការដោយដៃដែលលាក់នៅខាងក្រោយ។",
    "Reservation": "ការកក់",
    "Dates, guests, source and total are captured.": "កាលបរិច្ឆេទ, ព័ត៌មានភ្ញៀវ, ប្រភព និងចំនួនសរុប ត្រូវបានកត់ត្រា។",
    "Validation": "ការផ្ទៀងផ្ទាត់",
    "Availability and pricing are checked atomically.": "Availability និងតម្លៃ ត្រូវបានត្រួតពិនិត្យជាប្រព័ន្ធ Atomic។",
    "Prepare": "រៀបចំ",
    "Housekeeping and room status make the room sellable.": "Housekeeping និងស្ថានភាពបន្ទប់ ធានាថាបន្ទប់អាចដាក់លក់បាន។",
    "Arrive": "មកដល់",
    "Reception checks in only to a ready room.": "Reception Check-in បានតែបន្ទប់ដែលបានរៀបចំរួចរាល់។",
    "Stay": "ស្នាក់នៅ",
    "Tasks, service issues and room condition remain visible.": "កិច្ចការ, បញ្ហាសេវា និងស្ថានភាពបន្ទប់ នៅតែអាចមើលឃើញ។",
    "Checkout": "Check-out",
    "Folio, payment, status and audit trail are closed.": "Folio, ការទូទាត់, ស្ថានភាព និង Audit Trail ត្រូវបានបិទបញ្ចប់។",
    "Operational value: reception, housekeeping and management see the same truth at the same time.": "តម្លៃប្រតិបត្តិការ: Reception, Housekeeping និង Management ឃើញទិន្នន័យពិតដូចគ្នា ក្នុងពេលតែមួយ។",

    # 6 — pricing
    "COMMERCIAL MODEL": "គំរូពាណិជ្ជកម្ម",
    "Simple pricing that is easy to trust": "តម្លៃសាមញ្ញ ដែលងាយយល់ និងអាចទុកចិត្តបាន",
    "The current Cambodia pricing revision starts at $30/night and applies 5% tax only.": "កំណែតម្លៃបច្ចុប្បន្នសម្រាប់កម្ពុជា ចាប់ពី $30 ក្នុងមួយយប់ ហើយគិតពន្ធតែ 5% ប៉ុណ្ណោះ។",
    "Example stay": "ឧទាហរណ៍ការស្នាក់នៅ",
    "per night": "ក្នុងមួយយប់",
    "2 nights": "២ យប់",
    "Welcome offer 10%": "Welcome Offer 10%",
    "Taxable subtotal": "Subtotal សម្រាប់គិតពន្ធ",
    "Tax 5%": "ពន្ធ 5%",
    "Guest total": "សរុបសម្រាប់ភ្ញៀវ",
    "Current catalog": "Catalog បច្ចុប្បន្ន",
    "•  Entry rooms: $30–$58\n•  Suites and city rooms: $64–$172\n•  Villas and premium stays: $216–$356\n•  Highest current catalog rate: $460\n•  Historical bookings keep original snapshots": "•  បន្ទប់ចាប់ផ្តើម: $30–$58\n•  Suite និងបន្ទប់ទីក្រុង: $64–$172\n•  វីឡា និងការស្នាក់នៅ Premium: $216–$356\n•  តម្លៃខ្ពស់បំផុតក្នុង Catalog: $460\n•  ការកក់ចាស់ៗ រក្សា Snapshot ដើម",
    "Service charge: 0% · Tax: 5%": "Service Charge: 0% · Tax: 5%",

    # 7 — platform
    "PLATFORM": "Platform",
    "The PMS is modular and deployment-ready": "PMS មានម៉ូឌុលច្បាស់ និងត្រៀមដាក់ឱ្យប្រើ",
    "Start simply for a demo or small property, then connect a larger database when operational scale requires it.": "ចាប់ផ្តើមយ៉ាងសាមញ្ញសម្រាប់ Demo ឬសណ្ឋាគារតូច បន្ទាប់មកភ្ជាប់ Database ធំជាង នៅពេលប្រតិបត្តិការត្រូវការពង្រីក។",
    "Guest site": "គេហទំព័រភ្ញៀវ",
    "Properties, rooms, search, booking and My Stays": "សណ្ឋាគារ, បន្ទប់, ស្វែងរក, ការកក់ និង My Stays",
    "Front office": "Front Office",
    "Dashboard, reservations, calendar and folios": "Dashboard, ការកក់, ប្រតិទិន និង Folio",
    "Operations": "ប្រតិបត្តិការ",
    "Room Board, housekeeping and maintenance": "Room Board, Housekeeping និង Maintenance",
    "Business": "អាជីវកម្ម",
    "Rates, payments, invoices, reports and analytics": "Rate, ការទូទាត់, Invoice, របាយការណ៍ និង Analytics",
    "DEPLOYMENT PATH": "ផ្លូវដាក់ឱ្យប្រើ",
    "•  SQLite-first startup\n•  Windows install and start scripts\n•  Optional MySQL / MariaDB\n•  Navicat-ready database path\n•  Static assets and role-aware routes": "•  ចាប់ផ្តើមដោយ SQLite ជាមុន\n•  Install និង Start Script សម្រាប់ Windows\n•  ជម្រើស MySQL / MariaDB\n•  ផ្លូវ Database ដែលត្រៀមសម្រាប់ Navicat\n•  Static Asset និង Route ដែលស្គាល់តួនាទី",
    "The default path is fast; the upgrade path is clear.": "ផ្លូវលំនាំដើមលឿន; ផ្លូវពង្រីកប្រព័ន្ធក៏ច្បាស់លាស់។",
    "Technical handoff: preserve the same models and workflows when moving from SQLite to MySQL/MariaDB.": "ការប្រគល់ផ្នែកបច្ចេកទេស: រក្សា Model និង Workflow ដដែល នៅពេលផ្លាស់ពី SQLite ទៅ MySQL/MariaDB។",

    # 8 — safeguards
    "TRUST LAYER": "ស្រទាប់ទំនុកចិត្ត",
    "Simple screens, disciplined controls": "ផ្ទាំងសាមញ្ញ ជាមួយការគ្រប់គ្រងមានវិន័យ",
    "The system is designed to make the safe path the easiest path for hotel teams.": "ប្រព័ន្ធត្រូវបានរចនា ដើម្បីឱ្យវិធីធ្វើការដែលមានសុវត្ថិភាព ក្លាយជាវិធីងាយបំផុតសម្រាប់ក្រុមសណ្ឋាគារ។",
    "Inventory": "ស្តុកបន្ទប់",
    "Every night is checked before a booking is created.": "រាល់យប់ត្រូវបានពិនិត្យ មុនពេលបង្កើតការកក់។",
    "Pricing": "តម្លៃ",
    "Rate, discount, tax and total are stored with the stay.": "Rate, បញ្ចុះតម្លៃ, Tax និងចំនួនសរុប ត្រូវបានរក្សាទុកជាមួយការស្នាក់នៅ។",
    "Room readiness": "ភាពរួចរាល់របស់បន្ទប់",
    "Only vacant-clean rooms can be assigned at arrival.": "នៅពេលភ្ញៀវមកដល់ អាចចាត់បានតែបន្ទប់ Vacant-Clean ប៉ុណ្ណោះ។",
    "Cancellation": "ការលុបចោល",
    "Policy and refund records are applied consistently.": "គោលការណ៍ និងកំណត់ត្រា Refund ត្រូវបានអនុវត្តដោយស្មើគ្នា។",
    "Access": "សិទ្ធិ",
    "Role scope separates guest, operations, manager and admin work.": "សិទ្ធិតាមតួនាទី បែងចែកការងារ Guest, Operations, Manager និង Admin ឱ្យច្បាស់។",
    "Audit": "Audit",
    "Ledger, inventory and financial invariants are checked.": "Ledger, ស្តុក និង Financial Invariant ត្រូវបានត្រួតពិនិត្យ។",
    "Release confidence": "ទំនុកចិត្តលើកំណែចេញផ្សាយ",
    "23/23 tests passed · 2,160 ledger invariants passed · 10 properties and 24 room types updated": "តេស្ត ២៣/២៣ បានជោគជ័យ · Ledger Invariant ២,១៦០ បានជោគជ័យ · បានធ្វើបច្ចុប្បន្នភាពសណ្ឋាគារ ១០ និងប្រភេទបន្ទប់ ២៤",

    # 9 — outcomes
    "OWNER OUTCOMES": "លទ្ធផលសម្រាប់ម្ចាស់សណ្ឋាគារ",
    "What the hotel team gains": "អ្វីដែលក្រុមសណ្ឋាគារទទួលបាន",
    "The project is measured by operational clarity, not by the number of screens it contains.": "គម្រោងនេះវាស់តម្លៃតាមភាពច្បាស់លាស់នៃប្រតិបត្តិការ មិនមែនតាមចំនួនផ្ទាំងដែលមានឡើយ។",
    "For the owner": "សម្រាប់ម្ចាស់សណ្ឋាគារ",
    "A chain-level view of demand, occupancy, ADR, revenue, payments and open folio balances.": "ទិដ្ឋភាពកម្រិត Chain អំពីតម្រូវការ, Occupancy, ADR, ចំណូល, ការទូទាត់ និងសមតុល្យ Folio ដែលនៅបើក។",
    "For the guest": "សម្រាប់ភ្ញៀវ",
    "Clear room choices, transparent total pricing, direct booking convenience and self-service stay management.": "ជម្រើសបន្ទប់ច្បាស់, តម្លៃសរុបថ្លា, ភាពងាយស្រួលក្នុងការកក់ផ្ទាល់ និងការគ្រប់គ្រងការស្នាក់នៅដោយខ្លួនឯង។",
    "For the front desk": "សម្រាប់ Front Desk",
    "One reservation workflow for web, walk-in, phone and agency demand with fewer handoff errors.": "Workflow កក់តែមួយ សម្រាប់ Web, Walk-in, ទូរស័ព្ទ និង Agency ដោយកាត់បន្ថយកំហុសពេលប្រគល់ការងារ។",
    "The meaningful change": "ការផ្លាស់ប្តូរដែលមានន័យ",
    "•  The hotel can see what is happening now.\n•  The team knows who owns the next action.\n•  The owner can trust how totals were calculated.\n•  The technology can grow without changing the hotel’s operating language.": "•  សណ្ឋាគារអាចឃើញអ្វីដែលកំពុងកើតឡើងភ្លាមៗ។\n•  ក្រុមការងារដឹងថា អ្នកណាទទួលខុសត្រូវលើសកម្មភាពបន្ទាប់។\n•  ម្ចាស់សណ្ឋាគារអាចទុកចិត្តលើរបៀបគណនាចំនួនសរុប។\n•  បច្ចេកវិទ្យាអាចពង្រីកបាន ដោយមិនប្តូរភាសាប្រតិបត្តិការរបស់សណ្ឋាគារ។",

    # 10 — demo
    "DEMONSTRATION": "លំដាប់ Demo",
    "The shortest meaningful walkthrough": "លំដាប់បង្ហាញដែលខ្លី ប៉ុន្តែមានខ្លឹមសារ",
    "Use this sequence to show the project end to end in a few minutes.": "ប្រើលំដាប់នេះ ដើម្បីបង្ហាញគម្រោងពីដើមដល់ចប់ ក្នុងពេលប៉ុន្មាននាទី។",
    "Open the website": "បើកគេហទំព័រ",
    "Show the public guest experience.": "បង្ហាញបទពិសោធន៍សម្រាប់ភ្ញៀវសាធារណៈ។",
    "Search a $30 room": "ស្វែងរកបន្ទប់ $30",
    "Show dates, inventory and tax-only total.": "បង្ហាញកាលបរិច្ឆេទ, ស្តុក និងសរុបដែលគិតពន្ធតែប៉ុណ្ណោះ។",
    "Confirm a stay": "បញ្ជាក់ការស្នាក់នៅ",
    "Show offer, confirmation and My Stays.": "បង្ហាញ Offer, ការបញ្ជាក់ និង My Stays។",
    "Open the PMS": "បើក PMS",
    "Show dashboard and reservation record.": "បង្ហាញ Dashboard និងកំណត់ត្រាកក់។",
    "Create a walk-in": "បង្កើត Walk-in",
    "Show controlled manual booking.": "បង្ហាញការកក់ដោយដៃ ដែលមានការគ្រប់គ្រង។",
    "Operate the room": "ប្រតិបត្តិការបន្ទប់",
    "Show check-in, Room Board and tasks.": "បង្ហាញ Check-in, Room Board និងកិច្ចការ។",
    "Close the stay": "បិទការស្នាក់នៅ",
    "Show checkout, folio and payment.": "បង្ហាញ Check-out, Folio និងការទូទាត់។",
    "Show the next step": "បង្ហាញជំហានបន្ទាប់",
    "Explain MySQL and future OTA connection.": "ពន្យល់អំពី MySQL និងការភ្ជាប់ OTA នាពេលអនាគត។",
    "Next handoff: verify the owner’s MySQL/Navicat connection, then add live OTA synchronization when ready.": "ការប្រគល់ការងារបន្ទាប់: ផ្ទៀងផ្ទាត់ការភ្ជាប់ MySQL/Navicat របស់ម្ចាស់ប្រព័ន្ធ បន្ទាប់មកបន្ថែមការធ្វើសមកាលកម្ម OTA ផ្ទាល់ នៅពេលត្រៀមរួច។",
}


def replace_shape_text(shape, value):
    tf = shape.text_frame
    old_run = None
    old_align = None
    if tf.paragraphs:
        old_align = tf.paragraphs[0].alignment
        if tf.paragraphs[0].runs:
            old_run = tf.paragraphs[0].runs[0]
    size = old_run.font.size.pt if old_run and old_run.font.size else 11
    bold = bool(old_run.font.bold) if old_run else False
    italic = bool(old_run.font.italic) if old_run else False
    color = None
    if old_run:
        try:
            color = old_run.font.color.rgb
        except Exception:
            color = None
    # Khmer glyphs are visually wider; reduce only long copy while preserving
    # the existing slide hierarchy for titles and metrics.
    n = len(value)
    if n > 180:
        size = min(size, 8.5)
    elif n > 125:
        size = min(size, 9.0)
    elif n > 82:
        size = min(size, 9.8)
    elif n > 50:
        size = min(size, 11.5 if size >= 13 else size)
    elif n > 30 and size >= 24:
        size = min(size, 22)
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    if old_align is not None:
        p.alignment = old_align
    run = p.add_run()
    run.text = value
    run.font.name = "Noto Sans Khmer"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


untranslated = []
for slide in prs.slides:
    for shape in slide.shapes:
        if not hasattr(shape, "text_frame") or not shape.text.strip():
            continue
        original = shape.text
        translated = T.get(original)
        if translated is None:
            translated = original
            # Numbers, currency, A monogram and technical abbreviations may stay.
            if any(c.isalpha() for c in original) and original not in {"A", "PMS", "OTA", "ADR", "MySQL", "Navicat"}:
                untranslated.append(original)
        replace_shape_text(shape, translated)

prs.core_properties.title = "Aurelia Collection — គម្រោងគ្រប់គ្រងសណ្ឋាគារ · បទបង្ហាញសង្ខេប"
prs.core_properties.subject = "បទបង្ហាញសង្ខេបជាភាសាខ្មែរ អំពី Website, PMS, តួនាទី, ប្រតិបត្តិការ, តម្លៃ និង Deployment"
prs.core_properties.author = "Aurelia Collection"
prs.core_properties.keywords = "Khmer, hotel management, PMS, roles, website, walk-in, OTA, pricing, deployment"
prs.core_properties.comments = "Humanized Khmer translation of the validated short project deck."
prs.save(OUT)

print(OUT)
if untranslated:
    print("UNTRANSLATED_TEXT:")
    for value in sorted(set(untranslated)):
        print(value)
