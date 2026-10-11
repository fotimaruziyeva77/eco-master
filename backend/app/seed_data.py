"""Reference data and demo content.

CATEGORIES and BANNED_WORDS are real reference data. DEMO_* is sample content for
development and demos only; the real content set is prepared in phase 7 and reviewed
by the content team (TZ 9.3).
"""

# TZ 8.3: one list of waste types for the whole app.
CATEGORIES = [
    {
        "code": "plastic",
        "examples": {
            "uz": "Butilka, idish, stakan",
            "ru": "Бутылки, флаконы, стаканчики",
            "en": "Bottles, containers, cups",
        },
        "icon": "🥤",
        "color": "#0284C7",
        "has_projects": True,
        "is_game_bin": True,
        "name": {"uz": "Plastik", "ru": "Пластик", "en": "Plastic"},
    },
    {
        "code": "glass",
        "examples": {
            "uz": "Butilka va bankalar",
            "ru": "Бутылки и банки",
            "en": "Bottles and jars",
        },
        "icon": "🫙",
        "color": "#10B981",
        "has_projects": True,
        "is_game_bin": True,
        "name": {"uz": "Shisha", "ru": "Стекло", "en": "Glass"},
    },
    {
        "code": "paper",
        "examples": {
            "uz": "Karton, gazeta, daftar",
            "ru": "Картон, газеты, тетради",
            "en": "Cardboard, newspapers, notebooks",
        },
        "icon": "📦",
        "color": "#D97706",
        "has_projects": True,
        "is_game_bin": True,
        "name": {"uz": "Qog'oz va karton", "ru": "Бумага и картон", "en": "Paper and cardboard"},
    },
    {
        "code": "textile",
        "examples": {
            "uz": "Eski kiyim, mato",
            "ru": "Старая одежда, ткань",
            "en": "Old clothes, fabric",
        },
        "icon": "👕",
        "color": "#8B5CF6",
        "has_projects": True,
        "is_game_bin": False,
        "name": {
            "uz": "Tekstil (eski kiyim)",
            "ru": "Текстиль (старая одежда)",
            "en": "Textiles (old clothes)",
        },
    },
    {
        "code": "organic",
        "examples": {
            "uz": "Po'choq, barg, ovqat qoldig'i",
            "ru": "Очистки, листья, остатки еды",
            "en": "Peels, leaves, food scraps",
        },
        "icon": "🍂",
        "color": "#84CC16",
        "has_projects": True,
        "is_game_bin": True,
        "name": {"uz": "Organik", "ru": "Органика", "en": "Organic"},
    },
    {
        "code": "metal",
        "examples": {
            "uz": "Banka, mix, kalit",
            "ru": "Банки, гвозди, ключи",
            "en": "Cans, nails, keys",
        },
        "icon": "🥫",
        "color": "#64748B",
        "has_projects": False,
        "is_game_bin": True,
        "name": {"uz": "Metall", "ru": "Металл", "en": "Metal"},
    },
    {
        "code": "hazardous",
        "examples": {
            "uz": "Batareya, lampa, dori",
            "ru": "Батарейки, лампы, лекарства",
            "en": "Batteries, lamps, medicines",
        },
        "icon": "🔋",
        "color": "#DC2626",
        "has_projects": False,
        "is_game_bin": True,
        "name": {"uz": "Xavfli chiqindi", "ru": "Опасные отходы", "en": "Hazardous waste"},
    },
]

# Reserved names match at the start or end of a nickname; profanity anywhere in it.
# Starter list only — the content team extends it in the admin panel (TZ 8.12).
RESERVED_WORDS = [
    "admin",
    "administrator",
    "moderator",
    "ekoustoz",
    "ecomaster",
    "support",
    "telegram",
    "official",
    "админ",
    "администратор",
    "модератор",
    "экоустоз",
    "экомастер",
    "поддержка",
]
PROFANITY = [
    # en
    "fuck",
    "shit",
    "bitch",
    "cunt",
    "whore",
    "slut",
    "porn",
    "nigger",
    "nigga",
    "faggot",
    "asshole",
    "dick",
    "penis",
    # ru (Cyrillic)
    "хуй",
    "хуе",
    "хуё",
    "хуя",
    "пизд",
    "ебан",
    "ебат",
    "ебал",
    "блять",
    "блядь",
    "бляд",
    "сука",
    "мудак",
    "мудил",
    "пидор",
    "пидар",
    "гандон",
    "шлюх",
    "залуп",
    "дроч",
    # ru (Latin transliteration)
    "huy",
    "pizd",
    "blyat",
    "blyad",
    "suka",
    "mudak",
    "pidor",
    "pidar",
    "gandon",
    "eban",
    "ebat",
    "zalup",
    # uz
    "jalab",
    "qotaq",
    "dalbayob",
    "dalbaeb",
    "sikaman",
    "sikay",
    "onangni",
    "жалаб",
    "қотақ",
    "далбаёб",
    "сикаман",
]

# ------------------------------------------------------------------------ demo

DEMO_PROJECTS = [
    {
        "slug": "plastic-bottle-flower-pot",
        "category": "plastic",
        "difficulty": "easy",
        "safety_level": "yellow",
        "duration_min": 20,
        "sort_order": 1,
        "title": {
            "uz": "Plastik butilkadan gul tuvagi",
            "ru": "Цветочный горшок из пластиковой бутылки",
            "en": "Flower pot from a plastic bottle",
        },
        "materials": {
            "uz": [
                "Bo'sh plastik butilka (1,5–2 litr)",
                "Qaychi (kattalar ishlatadi)",
                "Tuproq",
                "Urug' yoki ko'chat",
                "Bo'yoq va cho'tka (ixtiyoriy)",
            ],
            "ru": [
                "Пустая пластиковая бутылка (1,5–2 л)",
                "Ножницы (работает взрослый)",
                "Земля",
                "Семена или рассада",
                "Краски и кисточка (по желанию)",
            ],
            "en": [
                "Empty plastic bottle (1.5–2 L)",
                "Scissors (used by an adult)",
                "Soil",
                "Seeds or a seedling",
                "Paint and a brush (optional)",
            ],
        },
        "steps": {
            "uz": [
                "Butilkani yuvib, yorlig'ini olib tashlang.",
                "Kattalar butilkani o'rtasidan kesib beradi.",
                "Kattalar tubida suv chiqib ketishi uchun 3–4 ta kichik teshik ochadi.",
                "Xohlasangiz, tuvakni bo'yab bezating.",
                "Tuproq soling, urug' yoki ko'chat eking va suv quying.",
            ],
            "ru": [
                "Вымойте бутылку и снимите этикетку.",
                "Взрослый разрезает бутылку посередине.",
                "Взрослый делает в дне 3–4 небольших отверстия для стока воды.",
                "По желанию раскрасьте горшок.",
                "Насыпьте землю, посадите семена или рассаду и полейте.",
            ],
            "en": [
                "Wash the bottle and remove the label.",
                "An adult cuts the bottle in half.",
                "An adult makes 3–4 small drainage holes in the bottom.",
                "Paint and decorate the pot if you like.",
                "Fill it with soil, plant the seeds or seedling and water it.",
            ],
        },
        "safety_text": {
            "uz": (
                "Butilkani kesish va teshik ochishni faqat kattalar bajaradi. "
                "Kesilgan plastik qirrasi o'tkir bo'lishi mumkin — ehtiyot bo'ling."
            ),
            "ru": (
                "Резать бутылку и делать отверстия должен только взрослый. "
                "Край разрезанного пластика может быть острым — будьте осторожны."
            ),
            "en": (
                "Only an adult cuts the bottle and makes the holes. "
                "The cut plastic edge can be sharp — be careful."
            ),
        },
    },
    {
        "slug": "cardboard-pencil-holder",
        "category": "paper",
        "difficulty": "easy",
        "safety_level": "green",
        "duration_min": 15,
        "sort_order": 1,
        "title": {
            "uz": "Kartondan qalamdon",
            "ru": "Подставка для карандашей из картона",
            "en": "Cardboard pencil holder",
        },
        "materials": {
            "uz": [
                "Tualet qog'ozining 3–4 ta karton naychasi",
                "Qalin karton bo'lagi (taglik uchun)",
                "Yelim",
                "Rangli qog'oz yoki eski jurnal varaqlari",
                "Uchi to'mtoq bolalar qaychisi",
            ],
            "ru": [
                "3–4 картонные втулки от туалетной бумаги",
                "Кусок плотного картона (для основания)",
                "Клей",
                "Цветная бумага или страницы старого журнала",
                "Детские ножницы с закруглёнными концами",
            ],
            "en": [
                "3–4 cardboard toilet paper tubes",
                "A piece of thick cardboard (for the base)",
                "Glue",
                "Coloured paper or old magazine pages",
                "Children's scissors with rounded tips",
            ],
        },
        "steps": {
            "uz": [
                "Naychalarni rangli qog'oz bilan o'rab, yelimlang.",
                "Kartondan taglik kesib oling.",
                "Naychalarni turli balandlikda kesing.",
                "Naychalarni taglikka tik qilib yelimlang.",
                "Yelim 15–20 daqiqa qurisin, keyin qalamlarni joylang.",
            ],
            "ru": [
                "Обклейте втулки цветной бумагой.",
                "Вырежьте из картона основание.",
                "Обрежьте втулки на разную высоту.",
                "Приклейте втулки к основанию вертикально.",
                "Дайте клею высохнуть 15–20 минут и поставьте карандаши.",
            ],
            "en": [
                "Wrap the tubes in coloured paper and glue it down.",
                "Cut a base out of the cardboard.",
                "Trim the tubes to different heights.",
                "Glue the tubes upright onto the base.",
                "Let the glue dry for 15–20 minutes, then add your pencils.",
            ],
        },
        "safety_text": None,
    },
    {
        "slug": "dry-leaves-compost",
        "category": "organic",
        "difficulty": "medium",
        "safety_level": "green",
        "duration_min": 30,
        "sort_order": 1,
        "title": {
            "uz": "Quruq barglardan kompost",
            "ru": "Компост из сухих листьев",
            "en": "Compost from dry leaves",
        },
        "materials": {
            "uz": [
                "Teshikli quti yoki chelak",
                "Quruq barglar",
                "Sabzavot va meva po'choqlari",
                "Bir necha hovuch tuproq",
                "Suv",
                "Qo'lqop",
            ],
            "ru": [
                "Ящик или ведро с отверстиями",
                "Сухие листья",
                "Очистки овощей и фруктов",
                "Несколько горстей земли",
                "Вода",
                "Перчатки",
            ],
            "en": [
                "A box or bucket with holes",
                "Dry leaves",
                "Vegetable and fruit peels",
                "A few handfuls of soil",
                "Water",
                "Gloves",
            ],
        },
        "steps": {
            "uz": [
                "Qutining tubiga quruq barglar qatlamini yoying.",
                "Ustiga sabzavot va meva po'choqlarini soling (go'sht va sut mahsulotlarini solmang).",
                "Bir hovuch tuproq sepib, qatlamlarni takrorlang.",
                "Aralashma siqilgan shimgichdek nam turishi uchun ozgina suv sepib turing.",
                "Har hafta aralashtiring. 2–3 oydan keyin kompostni gul va daraxtlar tagiga soling.",
            ],
            "ru": [
                "Выложите на дно ящика слой сухих листьев.",
                "Сверху положите очистки овощей и фруктов (без мяса и молочных продуктов).",
                "Присыпьте горстью земли и повторите слои.",
                "Слегка поливайте, чтобы смесь была влажной, как отжатая губка.",
                "Перемешивайте раз в неделю. Через 2–3 месяца внесите компост под цветы и деревья.",
            ],
            "en": [
                "Spread a layer of dry leaves on the bottom of the box.",
                "Add vegetable and fruit peels on top (no meat or dairy).",
                "Sprinkle a handful of soil and repeat the layers.",
                "Add a little water so the mix stays as damp as a wrung-out sponge.",
                "Stir it every week. After 2–3 months, spread the compost around plants and trees.",
            ],
        },
        "safety_text": {
            "uz": "Qo'lqop kiyib ishlang va ishdan keyin qo'lingizni sovunlab yuving.",
            "ru": "Работайте в перчатках и после работы вымойте руки с мылом.",
            "en": "Wear gloves and wash your hands with soap afterwards.",
        },
    },
]

DEMO_TIPS = [
    {
        "uz": "Do'konga o'z sumkangiz bilan boring: bitta mato sumka ko'plab plastik paketlar o'rnini bosadi.",
        "ru": "Ходите в магазин со своей сумкой: одна тканевая сумка заменяет множество пакетов.",
        "en": "Take your own bag to the shop: one cloth bag replaces lots of plastic bags.",
    },
    {
        "uz": "Quruq barglarni yoqmang — tutun havoni ifloslantiradi. Ulardan kompost qiling.",
        "ru": "Не сжигайте сухие листья — дым загрязняет воздух. Сделайте из них компост.",
        "en": "Don't burn dry leaves — the smoke pollutes the air. Turn them into compost.",
    },
    {
        "uz": "Ishlatilgan batareyalarni oddiy chiqindiga tashlamang: alohida yig'ib, qabul punktiga topshiring.",
        "ru": "Не выбрасывайте батарейки с обычным мусором: собирайте их отдельно и сдавайте в пункт приёма.",
        "en": "Don't throw used batteries in the bin: collect them separately and take them to a drop-off point.",
    },
    {
        "uz": "Shisha bankalarni yuvib, qayta ishlating — ziravor, yorma yoki mayda buyumlar uchun juda qulay.",
        "ru": "Мойте стеклянные банки и используйте снова — для специй, круп или мелочей.",
        "en": "Wash glass jars and reuse them for spices, grains or small things.",
    },
    {
        "uz": "Qog'ozning ikkala tomoniga yozing: qog'oz tejaladi, demak daraxtlar ham.",
        "ru": "Пишите на обеих сторонах листа: так экономится бумага, а значит и деревья.",
        "en": "Write on both sides of the paper: you save paper, and so you save trees.",
    },
]

DEMO_CARDS = [
    {
        "slug": "plastic-pollution",
        "sort_order": 1,
        "title": {
            "uz": "Plastik ifloslanish",
            "ru": "Пластиковое загрязнение",
            "en": "Plastic pollution",
        },
        "sections": {
            "uz": {
                "problem": (
                    "Plastik tabiatda juda sekin — yuzlab yillar davomida parchalanadi, "
                    "shuning uchun tuproqda, daryo va dengizlarda to'planib boradi."
                ),
                "cause": (
                    "Bir marta ishlatiladigan paket, butilka va idishlar juda ko'p ishlab "
                    "chiqariladi, ularning faqat kichik qismi qayta ishlanadi."
                ),
                "effect": (
                    "Hayvonlar plastikni ovqat deb yutib yuboradi yoki unga o'ralib qoladi. "
                    "Mayda zarrachalari (mikroplastik) suv va ovqat orqali odam organizmiga ham tushadi."
                ),
                "solution": (
                    "Plastikni kamroq ishlatish, qayta foydalanish, saralab qayta ishlashga topshirish."
                ),
                "action": (
                    "O'z suv idishing va mato sumkangdan foydalan. Plastik butilkalarni alohida yig'. "
                    "Eski butilkadan foydali buyum yasa."
                ),
            },
            "ru": {
                "problem": (
                    "Пластик разлагается в природе очень медленно — сотни лет, поэтому "
                    "накапливается в почве, реках и морях."
                ),
                "cause": (
                    "Одноразовых пакетов, бутылок и посуды производят очень много, а "
                    "перерабатывается лишь малая часть."
                ),
                "effect": (
                    "Животные принимают пластик за еду или запутываются в нём. Мелкие частицы "
                    "(микропластик) с водой и едой попадают и в организм человека."
                ),
                "solution": (
                    "Меньше использовать пластик, использовать вещи повторно, сортировать и сдавать "
                    "на переработку."
                ),
                "action": (
                    "Пользуйся своей бутылкой для воды и тканевой сумкой. Собирай пластиковые "
                    "бутылки отдельно. Сделай из старой бутылки полезную вещь."
                ),
            },
            "en": {
                "problem": (
                    "Plastic breaks down in nature very slowly — over hundreds of years — so it "
                    "builds up in soil, rivers and seas."
                ),
                "cause": (
                    "Huge amounts of single-use bags, bottles and dishes are made, and only a "
                    "small share is recycled."
                ),
                "effect": (
                    "Animals mistake plastic for food or get tangled in it. Tiny pieces "
                    "(microplastics) reach people through water and food."
                ),
                "solution": "Use less plastic, reuse things, and sort plastic for recycling.",
                "action": (
                    "Use your own water bottle and cloth bag. Collect plastic bottles separately. "
                    "Turn an old bottle into something useful."
                ),
            },
        },
    },
    {
        "slug": "aral-sea",
        "sort_order": 2,
        "title": {
            "uz": "Orol dengizi fojiasi",
            "ru": "Трагедия Аральского моря",
            "en": "The Aral Sea disaster",
        },
        "sections": {
            "uz": {
                "problem": (
                    "Orol dengizi bir paytlar dunyodagi eng katta ko'llardan biri edi. "
                    "1960-yillardan boshlab u tez qurib, suvining katta qismini yo'qotdi."
                ),
                "cause": (
                    "Amudaryo va Sirdaryo suvining katta qismi dalalarni sug'orish uchun olindi, "
                    "dengizga yetib boradigan suv keskin kamaydi."
                ),
                "effect": (
                    "Qurigan tubdan tuz va chang bo'ronlari ko'tariladi, bu odamlar sog'lig'iga va "
                    "dalalarga zarar yetkazadi. Baliqchilik deyarli yo'qoldi, iqlim qattiqroq bo'ldi."
                ),
                "solution": (
                    "Suvni tejaydigan sug'orish (masalan, tomchilatib sug'orish) va dengizning "
                    "qurigan tubiga saksovul kabi cho'l o'simliklarini ekish."
                ),
                "action": (
                    "Uyda suvni teja: tishingni yuvayotganda jo'mrakni yop. Orol haqida "
                    "bilganlaringni do'stlaringga aytib ber."
                ),
            },
            "ru": {
                "problem": (
                    "Аральское море когда-то было одним из крупнейших озёр мира. С 1960-х годов "
                    "оно быстро высыхало и потеряло большую часть воды."
                ),
                "cause": (
                    "Большую часть воды Амударьи и Сырдарьи забирали на орошение полей, и до моря "
                    "стало доходить гораздо меньше воды."
                ),
                "effect": (
                    "С высохшего дна поднимаются солевые и пыльные бури, которые вредят здоровью "
                    "людей и полям. Рыболовство почти исчезло, климат стал суровее."
                ),
                "solution": (
                    "Водосберегающее орошение (например, капельное) и посадка пустынных растений, "
                    "таких как саксаул, на высохшем дне моря."
                ),
                "action": (
                    "Береги воду дома: закрывай кран, когда чистишь зубы. Расскажи друзьям о том, "
                    "что узнал об Арале."
                ),
            },
            "en": {
                "problem": (
                    "The Aral Sea was once one of the largest lakes in the world. Since the 1960s "
                    "it has dried up fast and lost most of its water."
                ),
                "cause": (
                    "Most of the water of the Amu Darya and Syr Darya rivers was taken to irrigate "
                    "fields, so far less water reached the sea."
                ),
                "effect": (
                    "Salt and dust storms rise from the dry seabed and harm people's health and "
                    "farmland. Fishing almost disappeared and the climate became harsher."
                ),
                "solution": (
                    "Water-saving irrigation (such as drip irrigation) and planting desert plants "
                    "like saxaul on the dry seabed."
                ),
                "action": (
                    "Save water at home: turn off the tap while brushing your teeth. Tell your "
                    "friends what you learned about the Aral Sea."
                ),
            },
        },
    },
]

# TZ 8.5: one shared task per day. Demo set; the full 30 are prepared in phase 7.
DEMO_DAILY_TASKS = [
    {
        "uz": "Uyda 5 ta plastik chiqindini topib, alohida qutiga yig'ing.",
        "ru": "Найдите дома 5 пластиковых отходов и сложите их в отдельную коробку.",
        "en": "Find 5 pieces of plastic waste at home and put them in a separate box.",
    },
    {
        "uz": "Tishingizni yuvayotganda jo'mrakni yopib qo'ying.",
        "ru": "Закрывайте кран, пока чистите зубы.",
        "en": "Turn off the tap while you brush your teeth.",
    },
    {
        "uz": "Xonadan chiqayotganda chiroqni o'chirishni unutmang.",
        "ru": "Выходя из комнаты, не забудьте выключить свет.",
        "en": "Remember to switch off the light when you leave a room.",
    },
    {
        "uz": "Bitta eski shisha bankani yuvib, undan qalam yoki mayda buyumlar idishi qiling.",
        "ru": "Вымойте старую стеклянную банку и сделайте из неё подставку для карандашей или мелочей.",
        "en": "Wash an old glass jar and turn it into a pencil or odds-and-ends holder.",
    },
    {
        "uz": "Uyda ishlatilgan batareyalar uchun alohida quti tayyorlang.",
        "ru": "Подготовьте дома отдельную коробку для использованных батареек.",
        "en": "Set up a separate box at home for used batteries.",
    },
    {
        "uz": "Uydagi karton va gazetalarni alohida yig'ing.",
        "ru": "Соберите дома картон и газеты отдельно.",
        "en": "Collect the cardboard and newspapers at home separately.",
    },
    {
        "uz": "Oilangizga chiqindini saralash haqida bitta qiziq faktni aytib bering.",
        "ru": "Расскажите семье один интересный факт о сортировке отходов.",
        "en": "Tell your family one interesting fact about sorting waste.",
    },
    {
        "uz": "Bugun bir martalik plastik stakan yoki idish ishlatmang.",
        "ru": "Сегодня не пользуйтесь одноразовыми пластиковыми стаканчиками и посудой.",
        "en": "Don't use single-use plastic cups or dishes today.",
    },
    {
        "uz": "Kattalar bilan birga hovlidagi 5 ta axlatni qo'lqopda yig'ib, qutiga tashlang.",
        "ru": "Вместе со взрослыми соберите в перчатках 5 штук мусора во дворе и выбросьте в урну.",
        "en": "Together with an adult, wear gloves and pick up 5 pieces of litter in your yard.",
    },
    {
        "uz": "Meva va sabzavot po'choqlarini oddiy chiqindidan alohida yig'ing.",
        "ru": "Собирайте очистки фруктов и овощей отдельно от обычного мусора.",
        "en": "Keep fruit and vegetable peels separate from the rest of the rubbish.",
    },
]
