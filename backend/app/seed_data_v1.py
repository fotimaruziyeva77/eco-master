"""Version 1 content (TZ 9.1), drafted for the team's review (TZ 9.3).

Loaded with `python -m app.seed --content` in the "In review" status: nothing here goes live
until the content team has checked the facts, safety and translations and published it in
the admin panel. Projects also need the "tested by / when" mark before publishing.

Limits of TZ 9.2: question up to 150 characters, answer option up to 60, explanation up to
250, daily task up to 120, project steps 3–7 of up to 120 characters each.
"""


def tr(uz: str, ru: str, en: str) -> dict[str, str]:
    return {"uz": uz, "ru": ru, "en": en}


def trl(uz: list[str], ru: list[str], en: list[str]) -> dict[str, list[str]]:
    return {"uz": uz, "ru": ru, "en": en}


# ------------------------------------------------------------------- projects
# Video lessons: the steps are also the shot list for the video team (TZ 9.2).

V1_PROJECTS = [
    {
        "slug": "plastic-bottle-bird-feeder",
        "category": "plastic",
        "difficulty": "medium",
        "safety_level": "yellow",
        "duration_min": 30,
        "title": tr(
            "Plastik butilkadan qushlar uchun oxur",
            "Кормушка для птиц из пластиковой бутылки",
            "Bird feeder from a plastic bottle",
        ),
        "materials": trl(
            [
                "Bo'sh plastik butilka (1,5 litr)",
                "2 ta yog'och qoshiq yoki tayoqcha",
                "Ip yoki shnur",
                "Qaychi yoki pichoq (kattalar ishlatadi)",
                "Don yoki tuzsiz, qovurilmagan kungaboqar urug'i",
            ],
            [
                "Пустая пластиковая бутылка (1,5 л)",
                "2 деревянные ложки или палочки",
                "Верёвка или шнур",
                "Ножницы или нож (работает взрослый)",
                "Зерно или несолёные необжаренные семечки",
            ],
            [
                "Empty plastic bottle (1.5 L)",
                "2 wooden spoons or sticks",
                "String or cord",
                "Scissors or a knife (used by an adult)",
                "Grain or unsalted, unroasted sunflower seeds",
            ],
        ),
        "steps": trl(
            [
                "Butilkani yuvib, quriting va yorlig'ini olib tashlang.",
                "Kattalar butilkaning ikki yonida bir-biriga qarama-qarshi teshik ochadi.",
                "Teshiklardan yog'och qoshiqni o'tkazing — qushlar unga qo'nib o'tiradi.",
                "Qoshiq kosasi tomonidagi teshikni kattalar biroz kengaytiradi: don shu yerdan qoshiqqa to'kiladi.",
                "Butilkaga don soling va qopqog'ini yoping.",
                "Qopqoqqa ip bog'lab, oxurni daraxt shoxiga osib qo'ying.",
            ],
            [
                "Вымойте и высушите бутылку, снимите этикетку.",
                "Взрослый делает по бокам бутылки два отверстия друг напротив друга.",
                "Проденьте в отверстия деревянную ложку — на неё будут садиться птицы.",
                "Взрослый чуть расширяет отверстие со стороны черпака: через него корм будет сыпаться на ложку.",
                "Насыпьте в бутылку корм и закройте крышку.",
                "Привяжите к крышке верёвку и повесьте кормушку на ветку.",
            ],
            [
                "Wash and dry the bottle and remove the label.",
                "An adult makes two holes opposite each other in the sides of the bottle.",
                "Push a wooden spoon through the holes — birds will perch on it.",
                "An adult widens the hole on the spoon's bowl side a little so seed spills onto the spoon.",
                "Fill the bottle with seed and close the cap.",
                "Tie string to the cap and hang the feeder from a branch.",
            ],
        ),
        "safety_text": tr(
            "Teshiklarni faqat kattalar ochadi: pichoq va kesilgan plastik qirrasi o'tkir. Oxurni mushuklar yeta olmaydigan baland joyga osing.",
            "Отверстия делает только взрослый: нож и края разрезанного пластика острые. Повесьте кормушку повыше, где до неё не доберутся кошки.",
            "Only an adult makes the holes: the knife and cut plastic edges are sharp. Hang the feeder high up, out of reach of cats.",
        ),
    },
    {
        "slug": "glass-jar-mini-garden",
        "category": "glass",
        "difficulty": "easy",
        "safety_level": "yellow",
        "duration_min": 30,
        "title": tr(
            "Shisha bankada mini-bog'",
            "Мини-сад в стеклянной банке",
            "Mini garden in a glass jar",
        ),
        "materials": trl(
            [
                "Keng og'izli toza shisha banka",
                "Mayda toshlar yoki keramzit",
                "Tuproq",
                "Kichik o'simlik (masalan, sukkulent)",
                "Qoshiq va suv purkagich",
            ],
            [
                "Чистая стеклянная банка с широким горлом",
                "Мелкие камешки или керамзит",
                "Земля",
                "Небольшое растение (например, суккулент)",
                "Ложка и пульверизатор",
            ],
            [
                "A clean wide-mouthed glass jar",
                "Small pebbles or clay pebbles",
                "Soil",
                "A small plant (for example, a succulent)",
                "A spoon and a spray bottle",
            ],
        ),
        "steps": trl(
            [
                "Bankani yuvib, quriting. Kattalar tekshirsin: darz yoki o'tkir qirra bo'lmasin.",
                "Tubiga 2–3 sm mayda tosh soling — ortiqcha suv shu yerda to'planadi.",
                "Ustiga qoshiq bilan tuproq soling.",
                "Tuproqda chuqurcha qilib, o'simlikni eking va atrofini bosib qo'ying.",
                "Tuproqni suv purkagich bilan namlang — ko'p suv quymang.",
                "Bankani yorug', lekin to'g'ridan-to'g'ri quyosh tushmaydigan joyga qo'ying.",
            ],
            [
                "Вымойте и высушите банку. Пусть взрослый проверит, нет ли трещин и острых краёв.",
                "Насыпьте на дно 2–3 см камешков — там будет собираться лишняя вода.",
                "Ложкой насыпьте сверху землю.",
                "Сделайте в земле ямку, посадите растение и прижмите землю вокруг.",
                "Увлажните землю из пульверизатора — не лейте много воды.",
                "Поставьте банку в светлое место без прямого солнца.",
            ],
            [
                "Wash and dry the jar. Ask an adult to check it for cracks or sharp edges.",
                "Put 2–3 cm of pebbles on the bottom — extra water collects there.",
                "Spoon soil on top.",
                "Make a small hole in the soil, plant the plant and press the soil around it.",
                "Moisten the soil with the spray bottle — don't pour in much water.",
                "Put the jar somewhere bright but out of direct sunlight.",
            ],
        ),
        "safety_text": tr(
            "Shisha sinishi mumkin: bankani kattalar ko'chiradi, darz ketgan bankani ishlatmang. Banka sinsa, siniqlarni qo'l bilan yig'mang — kattalarni chaqiring.",
            "Стекло может разбиться: банку переносит взрослый, банку с трещинами не используйте. Если банка разбилась, не собирайте осколки руками — позовите взрослых.",
            "Glass can break: an adult carries the jar, and don't use a cracked one. If it breaks, don't pick up the pieces by hand — call an adult.",
        ),
    },
    {
        "slug": "recycled-paper-at-home",
        "category": "paper",
        "difficulty": "medium",
        "safety_level": "yellow",
        "duration_min": 45,
        "title": tr(
            "Eski qog'ozdan yangi qog'oz",
            "Новая бумага из старой",
            "New paper from old paper",
        ),
        "materials": trl(
            [
                "Eski qog'oz (gazeta, daftar varaqlari)",
                "Iliq suv va tog'ora",
                "Blender (kattalar ishlatadi)",
                "Mayda to'r yoki elak",
                "Eski sochiq yoki mato",
            ],
            [
                "Старая бумага (газеты, тетрадные листы)",
                "Тёплая вода и таз",
                "Блендер (работает взрослый)",
                "Мелкая сетка или сито",
                "Старое полотенце или ткань",
            ],
            [
                "Old paper (newspaper, notebook pages)",
                "Warm water and a basin",
                "A blender (used by an adult)",
                "A fine mesh or sieve",
                "An old towel or cloth",
            ],
        ),
        "steps": trl(
            [
                "Qog'ozni mayda bo'laklarga yirting va iliq suvda bir necha soat ivitib qo'ying.",
                "Kattalar ivigan qog'ozni suv bilan blenderda bo'tqa holiga keltiradi.",
                "Bo'tqani suvli tog'oraga soling va aralashtiring.",
                "To'rni tog'oraga botirib, ko'taring — ustida yupqa qog'oz qatlami qoladi.",
                "Qatlamni sochiqqa ag'daring va ustidan bosib, suvini siqib chiqaring.",
                "Bir kun quriting — yangi qog'ozingiz tayyor!",
            ],
            [
                "Порвите бумагу на мелкие кусочки и замочите в тёплой воде на несколько часов.",
                "Взрослый измельчает размокшую бумагу с водой в блендере до кашицы.",
                "Вылейте кашицу в таз с водой и перемешайте.",
                "Опустите сетку в таз и поднимите — на ней останется тонкий слой бумаги.",
                "Переверните слой на полотенце и прижмите, чтобы отжать воду.",
                "Сушите сутки — ваша новая бумага готова!",
            ],
            [
                "Tear the paper into small pieces and soak them in warm water for a few hours.",
                "An adult blends the soaked paper with water into pulp.",
                "Pour the pulp into a basin of water and stir.",
                "Dip the mesh into the basin and lift it out — a thin layer of paper stays on it.",
                "Turn the layer onto a towel and press it to squeeze out the water.",
                "Let it dry for a day — your new paper is ready!",
            ],
        ),
        "safety_text": tr(
            "Blenderni faqat kattalar ishlatadi: pichoqlari juda o'tkir, ishlayotganda ichiga qo'l solmang. Elektr asboblarini ho'l qo'l bilan ushlamang.",
            "Блендером пользуется только взрослый: ножи очень острые, не опускайте в него руки во время работы. Не трогайте электроприборы мокрыми руками.",
            "Only an adult uses the blender: the blades are very sharp, so never put your hand in it while it's running. Don't touch electrical appliances with wet hands.",
        ),
    },
    {
        "slug": "t-shirt-tote-bag",
        "category": "textile",
        "difficulty": "easy",
        "safety_level": "green",
        "duration_min": 20,
        "title": tr(
            "Eski futbolkadan tikuvsiz sumka",
            "Сумка из старой футболки без шитья",
            "No-sew bag from an old T-shirt",
        ),
        "materials": trl(
            ["Eski futbolka", "Qaychi", "Chizg'ich va bo'r yoki marker"],
            ["Старая футболка", "Ножницы", "Линейка и мелок или маркер"],
            ["An old T-shirt", "Scissors", "A ruler and chalk or a marker"],
        ),
        "steps": trl(
            [
                "Futbolkaning yenglarini chok bo'ylab kesib oling.",
                "Bo'yin qismini kengroq qilib kesing — bu sumkaning og'zi bo'ladi.",
                "Pastki qismida 2–3 sm oraliqda 8–10 sm uzunlikdagi chiziqlar chizib, ular bo'ylab kesing.",
                "Old va orqa tasmalarni juft-juft qilib, ikki marta tugun bog'lang.",
                "Sumkani ag'daring — tugunlar ichida qoladi. Sumka tayyor!",
            ],
            [
                "Отрежьте рукава футболки по швам.",
                "Вырежьте горловину пошире — это будет вход в сумку.",
                "Внизу начертите полоски длиной 8–10 см через каждые 2–3 см и разрежьте по ним.",
                "Свяжите переднюю и заднюю полоски попарно двойным узлом.",
                "Выверните сумку — узлы окажутся внутри. Сумка готова!",
            ],
            [
                "Cut the sleeves off the T-shirt along the seams.",
                "Cut the neckline wider — this will be the bag's opening.",
                "At the bottom, draw strips 8–10 cm long, 2–3 cm apart, and cut along them.",
                "Tie the front and back strips together in pairs with double knots.",
                "Turn the bag inside out — the knots stay inside. Your bag is ready!",
            ],
        ),
        "safety_text": tr(
            "Qaychini uchi pastga qaratib ushlang va kesayotganda barmoqlaringizni ehtiyot qiling.",
            "Держите ножницы остриём вниз и берегите пальцы, когда режете.",
            "Hold the scissors pointing down and mind your fingers while cutting.",
        ),
    },
    {
        "slug": "eggshell-seedlings",
        "category": "organic",
        "difficulty": "easy",
        "safety_level": "green",
        "duration_min": 20,
        "title": tr(
            "Tuxum po'chog'ida ko'chat",
            "Рассада в яичной скорлупе",
            "Seedlings in eggshells",
        ),
        "materials": trl(
            [
                "Tuxum po'chog'i yarimlari",
                "Karton tuxum qutisi",
                "Tuproq",
                "Urug'lar (masalan, rayhon yoki shivit)",
                "Qoshiq va suv",
            ],
            [
                "Половинки яичной скорлупы",
                "Картонная коробка для яиц",
                "Земля",
                "Семена (например, базилик или укроп)",
                "Ложка и вода",
            ],
            [
                "Eggshell halves",
                "A cardboard egg box",
                "Soil",
                "Seeds (for example, basil or dill)",
                "A spoon and water",
            ],
        ),
        "steps": trl(
            [
                "Po'choqlarni yuvib, tubida tish kavlagich bilan kichik teshik oching.",
                "Po'choqlarni tuxum qutisiga tik qilib joylang.",
                "Har biriga qoshiq bilan tuproq soling.",
                "Har bir po'choqqa 2–3 ta urug' ekib, ustini yupqa tuproq bilan yoping.",
                "Tuproqni nam saqlang va qutini yorug' deraza tokchasiga qo'ying.",
                "Ko'chat o'sgach, uni po'chog'i bilan birga tuvakka eking — po'choq o'g'itga aylanadi.",
            ],
            [
                "Вымойте скорлупки и проделайте зубочисткой маленькое отверстие в дне.",
                "Поставьте скорлупки в коробку для яиц.",
                "Насыпьте в каждую ложкой землю.",
                "Посадите в каждую 2–3 семени и присыпьте тонким слоем земли.",
                "Поддерживайте землю влажной и поставьте коробку на светлый подоконник.",
                "Когда рассада подрастёт, посадите её в горшок прямо со скорлупой — она станет удобрением.",
            ],
            [
                "Wash the shells and poke a small hole in the bottom with a toothpick.",
                "Stand the shells up in the egg box.",
                "Spoon soil into each one.",
                "Plant 2–3 seeds in each shell and cover them with a thin layer of soil.",
                "Keep the soil moist and put the box on a bright windowsill.",
                "When the seedlings grow, plant them in a pot shell and all — the shell turns into fertiliser.",
            ],
        ),
        "safety_text": tr(
            "Xom tuxum bilan ishlagandan keyin qo'lingizni sovunlab yuving.",
            "После работы с сырыми яйцами вымойте руки с мылом.",
            "Wash your hands with soap after handling raw eggs.",
        ),
    },
    # Projects for the short videos the team collected in October 2026; each video is
    # uploaded to its project in the admin panel.
    {
        "slug": "bubble-wrap-butterfly",
        "category": "plastic",
        "difficulty": "medium",
        "safety_level": "yellow",
        "duration_min": 30,
        "title": tr(
            "Pufakchali plyonkadan kapalak",
            "Бабочка из пузырчатой плёнки",
            "Butterfly from bubble wrap",
        ),
        "materials": trl(
            [
                "Qadoqlashdan qolgan pufakchali plyonka",
                "Qog'oz va qalam (shablon uchun)",
                "Marker",
                "Qaychi",
                "Issiq yelim to'pponchasi (kattalar bilan)",
                "Mo'ylovlar uchun ingichka sim",
            ],
            [
                "Пузырчатая плёнка от упаковки",
                "Бумага и карандаш (для шаблона)",
                "Маркер",
                "Ножницы",
                "Клеевой пистолет (со взрослым)",
                "Тонкая проволока для усиков",
            ],
            [
                "Bubble wrap left over from a parcel",
                "Paper and a pencil (for the template)",
                "A marker",
                "Scissors",
                "A hot glue gun (with an adult)",
                "Thin wire for the antennae",
            ],
        ),
        "steps": trl(
            [
                "Qog'ozga kapalak qanotlarini chizib, qirqib oling — bu shablon.",
                "Shablonni plyonkaga qo'yib, marker bilan aylantirib chizing.",
                "Ikki juft qanotni qaychi bilan qirqib oling.",
                "Kattalar yordamida qanotlarni o'rtasidan issiq yelim bilan yopishtiring.",
                "Plyonka bo'lagini o'rab tanacha yasang va o'rtaga yopishtiring.",
                "Simdan mo'ylov qo'shing va kapalakni gul tuvagiga qo'ying.",
            ],
            [
                "Нарисуйте на бумаге крылья бабочки и вырежьте их — это шаблон.",
                "Положите шаблон на плёнку и обведите его маркером.",
                "Вырежьте ножницами две пары крыльев.",
                "Вместе со взрослым склейте крылья посередине клеевым пистолетом.",
                "Сверните полоску плёнки в тельце и приклейте его посередине.",
                "Добавьте усики из проволоки и посадите бабочку на цветочный горшок.",
            ],
            [
                "Draw butterfly wings on paper and cut them out — this is your template.",
                "Lay the template on the bubble wrap and trace around it with a marker.",
                "Cut out two pairs of wings with scissors.",
                "With an adult, glue the wings together in the middle with the glue gun.",
                "Roll a strip of bubble wrap into a body and glue it in the middle.",
                "Add wire antennae and sit the butterfly on a flower pot.",
            ],
        ),
        "safety_text": tr(
            "Issiq yelim to'pponchasini faqat kattalar bilan ishlating: yelim va uchi kuydiradi. "
            "Simning o'tkir uchini bukib qo'ying.",
            "Клеевым пистолетом работайте только со взрослым: клей и носик обжигают. "
            "Загните острый кончик проволоки.",
            "Use the hot glue gun only with an adult: the glue and the tip can burn. "
            "Bend over the sharp end of the wire.",
        ),
    },
    {
        "slug": "plastic-bag-pompom-flowers",
        "category": "plastic",
        "difficulty": "easy",
        "safety_level": "green",
        "duration_min": 15,
        "title": tr(
            "Paketdan pompon gullar",
            "Цветы-помпоны из пакетов",
            "Pom-pom flowers from plastic bags",
        ),
        "materials": trl(
            [
                "Rangli plastik paketlar",
                "Qaychi",
                "Ip yoki ingichka sim",
                "Tayoqchalar yoki ichimlik naychalari",
                "Vaza yoki bo'sh butilka",
            ],
            [
                "Цветные пластиковые пакеты",
                "Ножницы",
                "Нитка или тонкая проволока",
                "Палочки или трубочки для напитков",
                "Ваза или пустая бутылка",
            ],
            [
                "Coloured plastic bags",
                "Scissors",
                "Thread or thin wire",
                "Sticks or drinking straws",
                "A vase or an empty bottle",
            ],
        ),
        "steps": trl(
            [
                "Paketni tekislab, undan to'rtburchak bo'lak qirqib oling.",
                "Bo'lakni garmoshkadek buklang.",
                "O'rtasidan ip yoki sim bilan mahkam bog'lang.",
                "Ikki uchini aylana qilib qirqing va qatlamlarini ochib, pompon yasang.",
                "Pomponni tayoqchaga bog'lang va guldastani vazaga qo'ying.",
            ],
            [
                "Расправьте пакет и вырежьте из него прямоугольник.",
                "Сложите его гармошкой.",
                "Крепко перевяжите посередине ниткой или проволокой.",
                "Закруглите концы ножницами и расправьте слои в помпон.",
                "Привяжите помпон к палочке и поставьте букет в вазу.",
            ],
            [
                "Smooth out a bag and cut a rectangle from it.",
                "Fold it back and forth like a fan.",
                "Tie it tightly in the middle with thread or wire.",
                "Round off both ends with scissors and fluff the layers into a pom-pom.",
                "Tie the pom-pom to a stick and put the bouquet in a vase.",
            ],
        ),
    },
    {
        "slug": "plastic-bag-blossom-tree",
        "category": "plastic",
        "difficulty": "medium",
        "safety_level": "green",
        "duration_min": 40,
        "title": tr(
            "Paketlardan gullagan daraxt",
            "Цветущее деревце из пакетов",
            "Blossom tree from plastic bags",
        ),
        "materials": trl(
            [
                "Rangli axlat paketlari (1 o'ram)",
                "Ingichka sim",
                "Qaychi",
                "Yashil yoki jigarrang lenta",
                "Gul tuvagi yoki stakan",
            ],
            [
                "Цветные мусорные пакеты (1 рулон)",
                "Тонкая проволока",
                "Ножницы",
                "Зелёная или коричневая изолента",
                "Цветочный горшок или стакан",
            ],
            [
                "Coloured bin bags (1 roll)",
                "Thin wire",
                "Scissors",
                "Green or brown tape",
                "A flower pot or a cup",
            ],
        ),
        "steps": trl(
            [
                "Paketlarni 4–5 sm enli uzun tasmalarga qirqing.",
                "Tasmani bir necha marta buklab, o'rtasidan sim bilan bog'lang.",
                "Ikki tomonidagi bukilgan joyini qirqib, qatlamlarini ochib gul yasang.",
                "Ko'p gul yasang va simlarini birlashtirib shoxchalar qiling.",
                "Shoxchalarni bitta tanaga birlashtirib, lenta bilan o'rang.",
                "Daraxtni tuvakka o'rnating — xona bezagi tayyor!",
            ],
            [
                "Нарежьте пакеты на длинные полоски шириной 4–5 см.",
                "Сложите полоску несколько раз и перетяните посередине проволокой.",
                "Разрежьте сгибы с обеих сторон и расправьте слои в цветок.",
                "Сделайте много цветов и скрутите их проволочки в веточки.",
                "Соедините веточки в ствол и обмотайте его изолентой.",
                "Поставьте деревце в горшок — украшение для комнаты готово!",
            ],
            [
                "Cut the bags into long strips 4–5 cm wide.",
                "Fold a strip several times and twist wire around the middle.",
                "Cut the folds on both sides and fluff the layers into a flower.",
                "Make lots of flowers and twist their wires together into branches.",
                "Join the branches into one trunk and wrap it with tape.",
                "Stand the tree in a pot — your room decoration is ready!",
            ],
        ),
    },
    {
        "slug": "cardboard-corn-sunflower",
        "category": "paper",
        "difficulty": "easy",
        "safety_level": "yellow",
        "duration_min": 20,
        "title": tr(
            "Karton va makkajo'xoridan kungaboqar",
            "Подсолнух из картона и кукурузы",
            "Sunflower from cardboard and corn",
        ),
        "materials": trl(
            [
                "Quti kartoni",
                "Eski, ovqatga yaramaydigan makkajo'xori donlari",
                "Kungaboqar urug'i yoki qora loviya (o'rtasi uchun)",
                "Stakan (aylana chizish uchun) va qaychi",
                "PVA yelim yoki issiq yelim to'pponchasi (kattalar bilan)",
            ],
            [
                "Картон от коробки",
                "Старые кукурузные зёрна, негодные в пищу",
                "Семечки или чёрная фасоль (для серединки)",
                "Стакан (обвести круг) и ножницы",
                "Клей ПВА или клеевой пистолет (со взрослым)",
            ],
            [
                "Cardboard from a box",
                "Old corn kernels that are no good for eating",
                "Sunflower seeds or black beans (for the middle)",
                "A cup (to draw the circle) and scissors",
                "PVA glue or a hot glue gun (with an adult)",
            ],
        ),
        "steps": trl(
            [
                "Kartonga stakanni qo'yib aylana chizing va qirqib oling.",
                "Aylananing chetiga yelim surting va donlarni uchi tashqariga qaratib yopishtiring.",
                "Ichkariga yana bir-ikki qator don yopishtiring — bular gulbarglar.",
                "O'rtasini kungaboqar urug'i yoki qora loviya bilan to'ldiring.",
                "Orqasiga ip yoki magnit yopishtiring — sovg'a tayyor.",
            ],
            [
                "Обведите стакан на картоне и вырежьте круг.",
                "Нанесите клей по краю круга и приклейте зёрна острым концом наружу.",
                "Приклейте внутри ещё один-два ряда — это лепестки.",
                "Заполните серединку семечками или чёрной фасолью.",
                "Приклейте сзади петельку или магнит — подарок готов.",
            ],
            [
                "Trace a cup on the cardboard and cut out the circle.",
                "Put glue along the edge and stick on the kernels, pointy ends out.",
                "Glue one or two more rows inside — these are the petals.",
                "Fill the middle with sunflower seeds or black beans.",
                "Glue a loop or a magnet on the back — your gift is ready.",
            ],
        ),
        "safety_text": tr(
            "Issiq yelim to'pponchasini kattalar bilan ishlating yoki o'rniga PVA yelim oling. "
            "Donlarni og'izga solmang.",
            "Клеевым пистолетом работайте со взрослым или возьмите клей ПВА. "
            "Не берите зёрна в рот.",
            "Use the hot glue gun with an adult, or use PVA glue instead. "
            "Don't put the kernels in your mouth.",
        ),
    },
    {
        "slug": "twig-and-dried-flower-picture",
        "category": "organic",
        "difficulty": "medium",
        "safety_level": "yellow",
        "duration_min": 45,
        "title": tr(
            "Shoxcha va quruq gullardan rasm",
            "Картина из веточек и сухих цветов",
            "Picture from twigs and dried flowers",
        ),
        "materials": trl(
            [
                "Qalin karton yoki eski rasm ramkasi",
                "Yerga tushgan ingichka quruq shoxchalar",
                "Quritilgan gullar va barglar",
                "Qalam",
                "Issiq yelim to'pponchasi (kattalar bilan)",
            ],
            [
                "Плотный картон или старая рамка",
                "Упавшие тонкие сухие веточки",
                "Сухие цветы и листья",
                "Карандаш",
                "Клеевой пистолет (со взрослым)",
            ],
            [
                "Thick cardboard or an old picture frame",
                "Thin dry twigs that have fallen to the ground",
                "Dried flowers and leaves",
                "A pencil",
                "A hot glue gun (with an adult)",
            ],
        ),
        "steps": trl(
            [
                "Parkda yoki hovlida yerga tushgan quruq shoxcha va gullarni yig'ing.",
                "Kartonga qalam bilan qiz, uy yoki daraxt rasmini chizing.",
                "Shoxchalarni rasm bo'yicha qatorma-qator yopishtiring.",
                "Quruq gullar va barglar bilan bezang.",
                "Rasmni ramkaga soling yoki devorga osib qo'ying.",
            ],
            [
                "Соберите в парке или во дворе упавшие сухие веточки и цветы.",
                "Нарисуйте на картоне карандашом девочку, дом или дерево.",
                "Приклеивайте веточки ряд за рядом по рисунку.",
                "Украсьте картину сухими цветами и листьями.",
                "Вставьте картину в рамку или повесьте на стену.",
            ],
            [
                "Collect fallen dry twigs and flowers in a park or yard.",
                "Draw a girl, a house or a tree on the cardboard in pencil.",
                "Glue the twigs on row by row, following your drawing.",
                "Decorate the picture with dried flowers and leaves.",
                "Put the picture in a frame or hang it on the wall.",
            ],
        ),
        "safety_text": tr(
            "Issiq yelim to'pponchasini kattalar bilan ishlating. Faqat yerga tushgan "
            "shoxchalarni oling — tirik daraxtni sindirmang.",
            "Клеевым пистолетом работайте со взрослым. Берите только упавшие веточки — "
            "не ломайте живые деревья.",
            "Use the hot glue gun with an adult. Only take twigs that have fallen — "
            "never break branches off living trees.",
        ),
    },
]


# ------------------------------------------------------------------ questions
# By waste type and general ecology (TZ 9.1); correct_index is 0-based.


def question(category, correct, text, options, explanation) -> dict:
    return {
        "category": category,
        "correct_index": correct,
        "text": text,
        "options": options,
        "explanation": explanation,
    }


V1_QUESTIONS = [
    # --- plastic
    question(
        "plastic",
        0,
        tr(
            "Plastik butilka tagidagi uchburchak ichidagi raqam nimani bildiradi?",
            "Что означает цифра в треугольнике на дне пластиковой бутылки?",
            "What does the number in the triangle on the bottom of a plastic bottle mean?",
        ),
        trl(
            [
                "Plastik turini",
                "Butilka narxini",
                "Ishlab chiqarilgan yilini",
                "Necha marta ishlatish mumkinligini",
            ],
            ["Вид пластика", "Цену бутылки", "Год выпуска", "Сколько раз её можно использовать"],
            [
                "The type of plastic",
                "The bottle's price",
                "The year it was made",
                "How many times it can be used",
            ],
        ),
        tr(
            "Raqam plastik turini ko'rsatadi: masalan, 1 — PET (ichimlik butilkalari), 2 — HDPE (shampun idishlari). Bu saralashga yordam beradi.",
            "Цифра показывает вид пластика: например, 1 — ПЭТ (бутылки для напитков), 2 — ПНД (флаконы от шампуня). Это помогает сортировке.",
            "The number shows the type of plastic: for example, 1 is PET (drink bottles) and 2 is HDPE (shampoo bottles). It helps with sorting.",
        ),
    ),
    question(
        "plastic",
        1,
        tr("Mikroplastik nima?", "Что такое микропластик?", "What is microplastic?"),
        trl(
            [
                "Juda yengil plastik paket",
                "5 mm dan kichik plastik zarrachalar",
                "Plastikdan yasalgan kichik o'yinchoq",
            ],
            [
                "Очень лёгкий пластиковый пакет",
                "Частицы пластика меньше 5 мм",
                "Маленькая пластиковая игрушка",
            ],
            [
                "A very light plastic bag",
                "Plastic particles smaller than 5 mm",
                "A small plastic toy",
            ],
        ),
        tr(
            "Katta plastik buyumlar quyosh va suv ta'sirida mayda bo'laklarga parchalanadi. Bu zarrachalar suvga, tuproqqa va hatto ovqatga tushadi.",
            "Крупные пластиковые вещи под действием солнца и воды распадаются на мелкие кусочки. Эти частицы попадают в воду, почву и даже в еду.",
            "Big plastic items break into tiny pieces in sunlight and water. These particles end up in water, soil and even food.",
        ),
    ),
    question(
        "plastic",
        2,
        tr(
            "Nega plastik chiqindini yoqib bo'lmaydi?",
            "Почему пластиковые отходы нельзя сжигать?",
            "Why shouldn't plastic waste be burned?",
        ),
        trl(
            ["U umuman yonmaydi", "Yoqish juda qimmatga tushadi", "Yonganda zaharli tutun chiqadi"],
            ["Он вообще не горит", "Сжигать слишком дорого", "При горении выделяется ядовитый дым"],
            [
                "It doesn't burn at all",
                "Burning it is too expensive",
                "Burning releases toxic smoke",
            ],
        ),
        tr(
            "Plastik yonganda havoga zaharli moddalar chiqadi. Ular nafas yo'llariga zarar yetkazadi, shuning uchun plastikni hech qachon yoqmang.",
            "При горении пластика в воздух попадают ядовитые вещества. Они вредят органам дыхания, поэтому никогда не сжигайте пластик.",
            "Burning plastic releases toxic substances into the air. They harm the lungs, so never burn plastic.",
        ),
    ),
    question(
        "plastic",
        0,
        tr(
            "Qaysi odat plastik chiqindini eng ko'p kamaytiradi?",
            "Какая привычка сильнее всего сокращает пластиковый мусор?",
            "Which habit cuts plastic waste the most?",
        ),
        trl(
            [
                "O'z suv idishingizdan foydalanish",
                "Har kuni yangi butilkada suv sotib olish",
                "Plastik idishlarni yerga ko'mish",
            ],
            [
                "Пользоваться своей бутылкой для воды",
                "Каждый день покупать воду в новой бутылке",
                "Закапывать пластиковую посуду в землю",
            ],
            [
                "Using your own water bottle",
                "Buying water in a new bottle every day",
                "Burying plastic dishes in the ground",
            ],
        ),
        tr(
            "Ko'p marta ishlatiladigan suv idishi yuzlab bir martalik butilkalar o'rnini bosadi.",
            "Многоразовая бутылка для воды заменяет сотни одноразовых.",
            "A reusable water bottle replaces hundreds of single-use ones.",
        ),
    ),
    question(
        "plastic",
        1,
        tr(
            "Dengizga tushgan plastik paket qaysi hayvon uchun ayniqsa xavfli?",
            "Для какого животного особенно опасен пластиковый пакет в море?",
            "Which animal is especially at risk from a plastic bag in the sea?",
        ),
        trl(
            ["Tuya", "Dengiz toshbaqasi", "Chumoli"],
            ["Верблюд", "Морская черепаха", "Муравей"],
            ["A camel", "A sea turtle", "An ant"],
        ),
        tr(
            "Dengiz toshbaqalari suvdagi paketni meduza deb o'ylab yutib yuboradi. Bu ular uchun halokatli bo'lishi mumkin.",
            "Морские черепахи принимают пакет в воде за медузу и проглатывают его. Это может их погубить.",
            "Sea turtles mistake bags in the water for jellyfish and swallow them. This can kill them.",
        ),
    ),
    question(
        "plastic",
        2,
        tr(
            "Bir martalik plastik qoshiq o'rniga nima ishlatish mumkin?",
            "Что можно взять вместо одноразовой пластиковой ложки?",
            "What can you use instead of a single-use plastic spoon?",
        ),
        trl(
            ["Yangi plastik qoshiq", "Qog'oz salfetka", "Uydan olib kelingan qoshiq"],
            ["Новую пластиковую ложку", "Бумажную салфетку", "Ложку, взятую из дома"],
            ["A new plastic spoon", "A paper napkin", "A spoon brought from home"],
        ),
        tr(
            "Uydagi qoshiq yuzlab marta ishlatiladi, bir martalik qoshiq esa bir necha daqiqadan keyin chiqindiga aylanadi.",
            "Домашняя ложка служит сотни раз, а одноразовая становится мусором через несколько минут.",
            "A spoon from home is used hundreds of times; a single-use one becomes waste within minutes.",
        ),
    ),
    # --- glass
    question(
        "glass",
        2,
        tr(
            "Shisha qanday xomashyodan tayyorlanadi?",
            "Из какого сырья делают стекло?",
            "What raw material is glass made from?",
        ),
        trl(
            ["Yog'och", "Neft", "Qum"],
            ["Из дерева", "Из нефти", "Из песка"],
            ["Wood", "Oil", "Sand"],
        ),
        tr(
            "Shisha asosan qumni juda yuqori haroratda eritib tayyorlanadi. Eski shishani qayta ishlash qum va energiyani tejaydi.",
            "Стекло делают в основном из песка, расплавляя его при очень высокой температуре. Переработка старого стекла экономит песок и энергию.",
            "Glass is made mostly from sand melted at very high temperatures. Recycling old glass saves sand and energy.",
        ),
    ),
    question(
        "glass",
        1,
        tr(
            "Singan shisha bilan nima qilish kerak?",
            "Что делать с разбитым стеклом?",
            "What should you do with broken glass?",
        ),
        trl(
            [
                "Qo'l bilan yig'ib, paketga solish",
                "Kattalarga aytish: ular qalin qog'ozga o'raydi",
                "Hovliga tashlab yuborish",
            ],
            [
                "Собрать руками в пакет",
                "Сказать взрослым: они завернут его в плотную бумагу",
                "Выбросить во двор",
            ],
            [
                "Pick it up by hand into a bag",
                "Tell an adult: they'll wrap it in thick paper",
                "Throw it out into the yard",
            ],
        ),
        tr(
            "Siniqlar qo'lni kesib yuborishi mumkin. Kattalar ularni supurgi bilan yig'ib, qalin qog'ozga o'raydi va «Ehtiyot: shisha» deb yozib qo'yadi.",
            "Осколки могут порезать руки. Взрослые сметут их веником, завернут в плотную бумагу и подпишут «Осторожно: стекло».",
            "Shards can cut your hands. An adult sweeps them up, wraps them in thick paper and labels it «Careful: glass».",
        ),
    ),
    question(
        "glass",
        2,
        tr(
            "Qaysi shisha buyumni oddiy butilkalar bilan birga topshirib bo'lmaydi?",
            "Какую стеклянную вещь нельзя сдавать вместе с обычными бутылками?",
            "Which glass item can't be recycled together with ordinary bottles?",
        ),
        trl(
            ["Murabbo bankasi", "Sharbat butilkasi", "Ko'zgu (oyna)"],
            ["Банку из-под варенья", "Бутылку из-под сока", "Зеркало"],
            ["A jam jar", "A juice bottle", "A mirror"],
        ),
        tr(
            "Ko'zgu, deraza oynasi va idish-tovoq shishasining tarkibi boshqacha. Ular butilka shishasi bilan aralashsa, qayta ishlash buziladi.",
            "У зеркал, оконного стекла и стеклянной посуды другой состав. Если смешать их с бутылочным стеклом, переработка испортится.",
            "Mirrors, window glass and glass dishes are made differently. Mixed with bottle glass, they spoil the recycling.",
        ),
    ),
    question(
        "glass",
        0,
        tr(
            "Shisha butilkalarni topshirishdan oldin nima qilinadi?",
            "Что делают со стеклянными бутылками перед сдачей?",
            "What do you do with glass bottles before recycling them?",
        ),
        trl(
            ["Qopqog'i olinib, chayib qo'yiladi", "Maydalab sindiriladi", "Ichiga qum solinadi"],
            ["Снимают крышку и ополаскивают", "Разбивают на куски", "Насыпают внутрь песок"],
            ["Remove the cap and rinse them", "Smash them to pieces", "Fill them with sand"],
        ),
        tr(
            "Toza va qopqoqsiz butilkani qayta ishlash oson. Butilkani sindirmang — siniqlar xavfli.",
            "Чистую бутылку без крышки легко переработать. Не разбивайте бутылки — осколки опасны.",
            "A clean bottle without its cap is easy to recycle. Don't break bottles — the shards are dangerous.",
        ),
    ),
    question(
        "glass",
        1,
        tr(
            "Nega tabiatda tashlab ketilgan shisha butilka xavfli?",
            "Почему брошенная на природе стеклянная бутылка опасна?",
            "Why is a glass bottle left in nature dangerous?",
        ),
        trl(
            [
                "Uni hayvonlar yeb qo'yadi",
                "Siniqlari jarohatlaydi, quyoshda yong'in chiqarishi mumkin",
                "U zaharli gaz chiqaradi",
            ],
            [
                "Её съедают животные",
                "Осколки ранят, а на солнце она может вызвать пожар",
                "Она выделяет ядовитый газ",
            ],
            [
                "Animals eat it",
                "Its shards hurt, and in the sun it can start a fire",
                "It gives off poisonous gas",
            ],
        ),
        tr(
            "Shisha siniqlari odam va hayvonlarni jarohatlaydi. Shisha orqali to'plangan quyosh nuri quruq o'tni yondirib yuborishi mumkin.",
            "Осколки стекла ранят людей и животных. Солнечные лучи, собранные стеклом, могут поджечь сухую траву.",
            "Glass shards injure people and animals. Sunlight focused through glass can set dry grass on fire.",
        ),
    ),
    question(
        "glass",
        1,
        tr(
            "Shisha bankani uyda qanday qayta ishlatish mumkin?",
            "Как снова использовать стеклянную банку дома?",
            "How can you reuse a glass jar at home?",
        ),
        trl(
            [
                "Uni faqat tashlab yuborish mumkin",
                "Yorma, ziravor yoki qalam saqlash uchun",
                "Uni hech narsaga ishlatib bo'lmaydi",
            ],
            [
                "Её можно только выбросить",
                "Для круп, специй или карандашей",
                "Её ни для чего не использовать",
            ],
            [
                "It can only be thrown away",
                "For storing grains, spices or pencils",
                "It's no use for anything",
            ],
        ),
        tr(
            "Yuvilgan shisha banka yillar davomida xizmat qiladi. Qayta ishlatish — chiqindini kamaytirishning eng oson yo'li.",
            "Вымытая стеклянная банка служит годами. Повторное использование — самый простой способ сократить мусор.",
            "A washed glass jar lasts for years. Reusing things is the easiest way to cut waste.",
        ),
    ),
    # --- paper
    question(
        "paper",
        0,
        tr(
            "Qog'oz qanday xomashyodan tayyorlanadi?",
            "Из какого сырья делают бумагу?",
            "What raw material is paper made from?",
        ),
        trl(
            ["Yog'och", "Qum", "Neft"],
            ["Из древесины", "Из песка", "Из нефти"],
            ["Wood", "Sand", "Oil"],
        ),
        tr(
            "Qog'oz asosan yog'och tolalaridan tayyorlanadi. Qog'ozni tejash va qayta ishlash daraxtlarni asraydi.",
            "Бумагу делают в основном из волокон древесины. Экономия и переработка бумаги сохраняют деревья.",
            "Paper is made mostly from wood fibres. Saving and recycling paper protects trees.",
        ),
    ),
    question(
        "paper",
        1,
        tr(
            "Qog'ozni necha marta qayta ishlash mumkin?",
            "Сколько раз можно перерабатывать бумагу?",
            "How many times can paper be recycled?",
        ),
        trl(
            ["Faqat bir marta", "Taxminan 5–7 marta", "Cheksiz marta"],
            ["Только один раз", "Примерно 5–7 раз", "Бесконечно"],
            ["Only once", "About 5–7 times", "Endlessly"],
        ),
        tr(
            "Har safar qayta ishlanganda qog'oz tolalari qisqaradi. Shuning uchun qog'ozni taxminan 5–7 marta qayta ishlash mumkin.",
            "При каждой переработке волокна бумаги становятся короче. Поэтому бумагу можно перерабатывать примерно 5–7 раз.",
            "Paper fibres get shorter each time they're recycled. That's why paper can be recycled about 5–7 times.",
        ),
    ),
    question(
        "paper",
        2,
        tr(
            "Karton qutini topshirishdan oldin nima qilgan ma'qul?",
            "Что лучше сделать с картонной коробкой перед сдачей?",
            "What should you do with a cardboard box before recycling it?",
        ),
        trl(
            [
                "Suvga ivitib qo'yish",
                "Ichini boshqa chiqindiga to'ldirish",
                "Yassilab, taxlab qo'yish",
            ],
            ["Замочить в воде", "Набить другим мусором", "Сложить её плоско"],
            ["Soak it in water", "Fill it with other rubbish", "Flatten it"],
        ),
        tr(
            "Yassilangan karton kam joy egallaydi. Uni quruq va toza saqlang — ho'l karton yaxshi qayta ishlanmaydi.",
            "Сложенный картон занимает мало места. Храните его сухим и чистым — мокрый картон плохо перерабатывается.",
            "Flattened cardboard takes up little space. Keep it dry and clean — wet cardboard doesn't recycle well.",
        ),
    ),
    question(
        "paper",
        0,
        tr(
            "Qaysi odat qog'ozni tejaydi?",
            "Какая привычка экономит бумагу?",
            "Which habit saves paper?",
        ),
        trl(
            [
                "Varaqning ikkala tomoniga yozish",
                "Har bir yozuv uchun yangi varaq olish",
                "Eski daftarlarni yoqib yuborish",
            ],
            [
                "Писать на обеих сторонах листа",
                "Брать новый лист для каждой записи",
                "Сжигать старые тетради",
            ],
            [
                "Writing on both sides of the sheet",
                "Taking a new sheet for every note",
                "Burning old notebooks",
            ],
        ),
        tr(
            "Ikkala tomonidan foydalansangiz, qog'oz ikki barobar kam sarflanadi. Eski daftarlarni yoqmang — makulaturaga topshiring.",
            "Если использовать обе стороны, бумаги уходит вдвое меньше. Не сжигайте старые тетради — сдайте их в макулатуру.",
            "Using both sides halves the paper you need. Don't burn old notebooks — hand them in as waste paper.",
        ),
    ),
    question(
        "paper",
        1,
        tr("«Makulatura» nima?", "Что такое «макулатура»?", "What is waste paper collection?"),
        trl(
            [
                "Yangi daftar turi",
                "Qayta ishlashga yig'ilgan eski qog'oz va karton",
                "Qog'oz fabrikasining nomi",
            ],
            [
                "Новый вид тетрадей",
                "Старая бумага и картон, собранные для переработки",
                "Название бумажной фабрики",
            ],
            [
                "A new kind of notebook",
                "Old paper and cardboard collected for recycling",
                "The name of a paper mill",
            ],
        ),
        tr(
            "Makulaturadan yangi qog'oz, karton va qog'oz sochiqlar tayyorlanadi. Uni yig'ib, qabul punktiga topshirish mumkin.",
            "Из макулатуры делают новую бумагу, картон и бумажные полотенца. Её можно собрать и сдать в пункт приёма.",
            "Waste paper is turned into new paper, cardboard and paper towels. You can collect it and take it to a collection point.",
        ),
    ),
    question(
        "paper",
        1,
        tr(
            "Do'kon cheki qaysi qutiga tashlanadi?",
            "Куда выбросить кассовый чек?",
            "Where does a shop receipt go?",
        ),
        trl(
            ["Qog'oz qutisiga", "Oddiy chiqindiga", "Kompostga"],
            ["В контейнер для бумаги", "В обычный мусор", "В компост"],
            ["The paper bin", "General waste", "The compost"],
        ),
        tr(
            "Kassa cheklari issiqlikka sezgir maxsus qog'ozdan bo'ladi, unda kimyoviy moddalar bor. Shuning uchun ular odatda qayta ishlanmaydi.",
            "Кассовые чеки печатают на особой термобумаге с химическими веществами. Поэтому их обычно не перерабатывают.",
            "Receipts are printed on special heat-sensitive paper with chemicals in it. That's why they usually aren't recycled.",
        ),
    ),
    # --- textile
    question(
        "textile",
        2,
        tr(
            "Bitta paxta futbolka tayyorlash uchun qancha suv kerak?",
            "Сколько воды нужно, чтобы сделать одну хлопковую футболку?",
            "How much water does it take to make one cotton T-shirt?",
        ),
        trl(
            ["Bir stakan", "Bir chelak", "Minglab litr"],
            ["Один стакан", "Одно ведро", "Тысячи литров"],
            ["One glass", "One bucket", "Thousands of litres"],
        ),
        tr(
            "Paxtani sug'orish uchun juda ko'p suv sarflanadi. Shuning uchun kiyimni uzoq kiyish va qayta ishlatish suvni ham tejaydi.",
            "На полив хлопка уходит очень много воды. Поэтому, нося вещи дольше и используя их снова, мы экономим и воду.",
            "Growing cotton takes a lot of water. So wearing clothes longer and reusing them saves water too.",
        ),
    ),
    question(
        "textile",
        0,
        tr(
            "Yirtilgan, lekin toza kiyimni nima qilgan ma'qul?",
            "Что лучше сделать с порванной, но чистой одеждой?",
            "What's best to do with torn but clean clothes?",
        ),
        trl(
            ["Undan latta yoki sumka yasash", "Yoqib yuborish", "Ko'chaga tashlab yuborish"],
            ["Сделать из неё тряпку или сумку", "Сжечь", "Выбросить на улицу"],
            ["Make a rag or a bag from them", "Burn them", "Throw them out in the street"],
        ),
        tr(
            "Eski matodan uy tozalash uchun latta, sumka yoki yostiqcha yasash mumkin. Shunda kiyim ikkinchi hayot oladi.",
            "Из старой ткани можно сделать тряпку для уборки, сумку или подушку. Так одежда получает вторую жизнь.",
            "Old fabric can become a cleaning rag, a bag or a cushion. That gives clothes a second life.",
        ),
    ),
    question(
        "textile",
        2,
        tr(
            "Kiyimni uzoqroq kiyish uchun nima yordam beradi?",
            "Что помогает носить одежду дольше?",
            "What helps clothes last longer?",
        ),
        trl(
            [
                "Har kuni juda issiq suvda yuvish",
                "Kichik teshik chiqsa, darhol tashlash",
                "Yorliqdagi yuvish qoidalariga amal qilish",
            ],
            [
                "Каждый день стирать в очень горячей воде",
                "Сразу выбрасывать при маленькой дырке",
                "Соблюдать правила стирки на ярлыке",
            ],
            [
                "Washing them in very hot water every day",
                "Throwing them away at the first small hole",
                "Following the washing instructions on the label",
            ],
        ),
        tr(
            "Yorliqda kiyimni qanday yuvish va dazmollash yozilgan. To'g'ri parvarish qilingan va o'z vaqtida tikilgan kiyim uzoq xizmat qiladi.",
            "На ярлыке написано, как стирать и гладить вещь. Одежда, за которой правильно ухаживают и вовремя зашивают, служит долго.",
            "The label says how to wash and iron the garment. Clothes that are cared for and mended in time last a long time.",
        ),
    ),
    question(
        "textile",
        1,
        tr(
            "Qaysi biri tekstil chiqindisi?",
            "Что из этого — текстильные отходы?",
            "Which of these is textile waste?",
        ),
        trl(
            ["Banan po'chog'i", "Eski paypoq", "Shisha banka"],
            ["Банановая кожура", "Старый носок", "Стеклянная банка"],
            ["A banana peel", "An old sock", "A glass jar"],
        ),
        tr(
            "Tekstil — matodan yasalgan buyumlar: kiyim, paypoq, choyshab, sochiq. Ularni boshqa chiqindidan alohida yig'gan ma'qul.",
            "Текстиль — это вещи из ткани: одежда, носки, постельное бельё, полотенца. Их лучше собирать отдельно от остального мусора.",
            "Textiles are things made of fabric: clothes, socks, bedding, towels. It's best to collect them separately from other waste.",
        ),
    ),
    question(
        "textile",
        0,
        tr(
            "Kiyim almashinuvi (svop) nima?",
            "Что такое обмен одеждой (своп)?",
            "What is a clothes swap?",
        ),
        trl(
            [
                "Do'stlar keraksiz kiyimlarini bir-biriga almashtirishi",
                "Kiyimni do'konga qaytarish",
                "Eski kiyimni yoqish",
            ],
            [
                "Друзья меняются ненужной одеждой",
                "Возврат одежды в магазин",
                "Сжигание старой одежды",
            ],
            [
                "Friends trading clothes they no longer need",
                "Returning clothes to a shop",
                "Burning old clothes",
            ],
        ),
        tr(
            "Svopda har kim o'ziga kichik bo'lgan yoki yoqmay qolgan kiyimni olib kelib, boshqasiniki bilan almashtiradi. Bu pul va tabiatni tejaydi.",
            "На своп каждый приносит вещи, которые стали малы или разонравились, и меняет их на чужие. Это экономит деньги и бережёт природу.",
            "At a swap everyone brings clothes they've outgrown or stopped liking and trades them. It saves money and protects nature.",
        ),
    ),
    # --- organic
    question(
        "organic",
        2,
        tr("Kompost nima?", "Что такое компост?", "What is compost?"),
        trl(
            [
                "Plastik idishning bir turi",
                "Chiqindi yoqiladigan joy",
                "Organik chiqindidan bo'lgan tabiiy o'g'it",
            ],
            [
                "Вид пластиковой посуды",
                "Место, где сжигают мусор",
                "Природное удобрение из органических отходов",
            ],
            [
                "A kind of plastic container",
                "A place where waste is burned",
                "Natural fertiliser made from organic waste",
            ],
        ),
        tr(
            "Po'choqlar, barglar va o'simlik qoldiqlari bir necha oyda chirib, unumdor tuproqqa aylanadi. Bu kompost deyiladi.",
            "Очистки, листья и остатки растений за несколько месяцев перегнивают и превращаются в плодородную землю. Это и есть компост.",
            "Peels, leaves and plant scraps rot over a few months into rich soil. That's compost.",
        ),
    ),
    question(
        "organic",
        0,
        tr(
            "Chiqindixonaga tushgan ovqat qoldiqlari nima chiqaradi?",
            "Что выделяют пищевые отходы на свалке?",
            "What do food scraps give off in a landfill?",
        ),
        trl(
            ["Metan gazini", "Toza kislorodni", "Hech narsa chiqarmaydi"],
            ["Газ метан", "Чистый кислород", "Ничего не выделяют"],
            ["Methane gas", "Pure oxygen", "Nothing at all"],
        ),
        tr(
            "Havosiz joyda chirigan ovqat qoldiqlari metan chiqaradi. Bu gaz iqlim isishini kuchaytiradi. Kompost qilish bu muammoni kamaytiradi.",
            "Без доступа воздуха пищевые отходы гниют и выделяют метан. Этот газ усиливает потепление климата. Компостирование уменьшает эту проблему.",
            "Without air, rotting food scraps release methane, a gas that speeds up global warming. Composting reduces this problem.",
        ),
    ),
    question(
        "organic",
        1,
        tr(
            "Qaysi biri kompostga solinadi?",
            "Что можно положить в компост?",
            "What can go into compost?",
        ),
        trl(
            ["Plastik paket", "Sabzavot po'chog'i", "Batareya"],
            ["Пластиковый пакет", "Очистки от овощей", "Батарейку"],
            ["A plastic bag", "Vegetable peels", "A battery"],
        ),
        tr(
            "Kompostga faqat chiriydigan narsalar solinadi: meva va sabzavot qoldiqlari, barglar, o't. Plastik va batareya chirimaydi.",
            "В компост кладут только то, что гниёт: остатки фруктов и овощей, листья, траву. Пластик и батарейки не перегнивают.",
            "Only things that rot go into compost: fruit and vegetable scraps, leaves, grass. Plastic and batteries don't rot.",
        ),
    ),
    question(
        "organic",
        0,
        tr(
            "Ovqat isrofini kamaytirish uchun nima qilish kerak?",
            "Как сократить пищевые отходы?",
            "How can you waste less food?",
        ),
        trl(
            [
                "Kerakli miqdorda tayyorlash va qoldiqni keyin yeyish",
                "Ovqatni har doim ko'p pishirish",
                "Qolgan ovqatni darhol tashlash",
            ],
            [
                "Готовить сколько нужно и доедать остатки позже",
                "Всегда готовить побольше",
                "Сразу выбрасывать остатки еды",
            ],
            [
                "Cook what you need and eat leftovers later",
                "Always cook extra",
                "Throw leftovers away at once",
            ],
        ),
        tr(
            "Tashlab yuborilgan ovqat bilan birga uni yetishtirishga ketgan suv, yer va mehnat ham isrof bo'ladi.",
            "Вместе с выброшенной едой пропадают вода, земля и труд, потраченные на её выращивание.",
            "When food is thrown away, the water, land and work used to grow it are wasted too.",
        ),
    ),
    question(
        "organic",
        1,
        tr(
            "Kompost tayyor bo'lganini qanday bilish mumkin?",
            "Как понять, что компост готов?",
            "How do you know compost is ready?",
        ),
        trl(
            [
                "Muzdek qotib qoladi",
                "To'q rangli, mayin, o'rmon tuprog'i hidi keladi",
                "Ustidan oq tutun chiqadi",
            ],
            [
                "Он замерзает и твердеет",
                "Он тёмный, рыхлый и пахнет лесной землёй",
                "Над ним идёт белый дым",
            ],
            [
                "It freezes solid",
                "It's dark, crumbly and smells like forest soil",
                "White smoke rises from it",
            ],
        ),
        tr(
            "Tayyor kompost to'q jigarrang va mayin bo'ladi, yoqimsiz hid bermaydi. Uni gul va ko'chatlarga o'g'it sifatida ishlatish mumkin.",
            "Готовый компост тёмно-коричневый и рассыпчатый, без неприятного запаха. Его можно использовать как удобрение для цветов и рассады.",
            "Ready compost is dark brown and crumbly, with no bad smell. You can use it as fertiliser for flowers and seedlings.",
        ),
    ),
    question(
        "organic",
        0,
        tr(
            "Qotib qolgan nonni nima qilish mumkin?",
            "Что можно сделать с зачерствевшим хлебом?",
            "What can you do with stale bread?",
        ),
        trl(
            ["Quritib, suxari qilish", "Ko'chaga tashlab yuborish", "Plastik bilan birga tashlash"],
            ["Высушить и сделать сухари", "Выбросить на улицу", "Выбросить вместе с пластиком"],
            ["Dry it into rusks", "Throw it out in the street", "Throw it out with the plastic"],
        ),
        tr(
            "Qotgan nondan suxari yoki taom tayyorlash mumkin. Nonni isrof qilmaslik ham chiqindini kamaytiradi.",
            "Из чёрствого хлеба можно сделать сухари или приготовить блюдо. Не выбрасывать хлеб — тоже способ сократить отходы.",
            "Stale bread can become rusks or part of a meal. Not wasting bread also cuts waste.",
        ),
    ),
    # --- metal
    question(
        "metal",
        0,
        tr(
            "Banka po'latdanmi yoki alyuminiydanmi, qanday bilish mumkin?",
            "Как узнать, из стали или алюминия банка?",
            "How can you tell if a can is steel or aluminium?",
        ),
        trl(
            ["Magnit yaqinlashtirib ko'rish", "Hidlab ko'rish", "Suvga tashlab ko'rish"],
            ["Приложить магнит", "Понюхать её", "Бросить в воду"],
            ["Hold a magnet to it", "Smell it", "Drop it in water"],
        ),
        tr(
            "Magnit po'lat bankaga yopishadi, alyuminiyga esa yopishmaydi. Qayta ishlash zavodlarida ham metallar shu yo'l bilan ajratiladi.",
            "Магнит притягивается к стальной банке, а к алюминиевой — нет. На заводах переработки металлы тоже разделяют магнитами.",
            "A magnet sticks to a steel can but not to an aluminium one. Recycling plants use magnets to separate metals too.",
        ),
    ),
    question(
        "metal",
        2,
        tr(
            "Alyuminiyni qayta ishlash yangisini olishga nisbatan qancha energiya tejaydi?",
            "Сколько энергии экономит переработка алюминия по сравнению с получением нового?",
            "How much energy does recycling aluminium save compared with making new aluminium?",
        ),
        trl(
            ["Juda oz", "Deyarli yarmini", "Taxminan 95 foizini"],
            ["Совсем немного", "Почти половину", "Около 95 %"],
            ["Very little", "Almost half", "About 95%"],
        ),
        tr(
            "Eski bankadan yangisini yasash rudadan alyuminiy olishga qaraganda taxminan 95% kam energiya talab qiladi.",
            "Чтобы сделать новую банку из старой, нужно примерно на 95 % меньше энергии, чем чтобы получить алюминий из руды.",
            "Making a new can from an old one takes about 95% less energy than producing aluminium from ore.",
        ),
    ),
    question(
        "metal",
        2,
        tr(
            "Qaysi biri metall chiqindi?",
            "Что из этого — металлические отходы?",
            "Which of these is metal waste?",
        ),
        trl(
            ["Gazeta", "Olma qoldig'i", "Konserva qopqog'i"],
            ["Газета", "Огрызок яблока", "Крышка от консервов"],
            ["A newspaper", "An apple core", "A tin lid"],
        ),
        tr(
            "Konserva qopqoqlari, bankalar, mix va eski kalitlar — metall. Ularni topshirsa, eritib yangi buyumlar yasaladi.",
            "Крышки от консервов, банки, гвозди и старые ключи — это металл. Если их сдать, их переплавят и сделают новые вещи.",
            "Tin lids, cans, nails and old keys are metal. Once recycled, they're melted down into new things.",
        ),
    ),
    question(
        "metal",
        0,
        tr(
            "Nega metallni qayta ishlash muhim?",
            "Почему важно перерабатывать металл?",
            "Why is recycling metal important?",
        ),
        trl(
            [
                "Yer ostidan kamroq ruda qaziladi",
                "Metall chirib, tuproqqa aylanadi",
                "Metall tezda yo'qolib ketadi",
            ],
            [
                "Меньше приходится добывать руду",
                "Металл сгниёт и станет землёй",
                "Металл быстро исчезает",
            ],
            ["Less ore needs to be mined", "Metal rots into soil", "Metal disappears quickly"],
        ),
        tr(
            "Ruda qazib olish tabiatni buzadi va ko'p energiya talab qiladi. Metallni qayta ishlash buni kamaytiradi, metall esa sifatini yo'qotmaydi.",
            "Добыча руды разрушает природу и требует много энергии. Переработка металла это сокращает, а металл не теряет своих свойств.",
            "Mining ore damages nature and uses lots of energy. Recycling metal reduces this, and the metal keeps its quality.",
        ),
    ),
    question(
        "metal",
        0,
        tr(
            "Ochilgan konserva bankasining o'tkir qirrasi bilan nima qilish kerak?",
            "Как обезопасить острый край открытой консервной банки?",
            "How do you make the sharp edge of an open can safe?",
        ),
        trl(
            [
                "Qopqog'ini ichiga bosib qo'yish, kattalardan yordam so'rash",
                "Ichini barmoq bilan tozalash",
                "Qopqog'ini qo'l bilan yirtib olish",
            ],
            [
                "Вдавить крышку внутрь, попросить помощи взрослых",
                "Почистить банку изнутри пальцем",
                "Оторвать крышку руками",
            ],
            [
                "Push the lid inside, ask an adult to help",
                "Clean the inside with your finger",
                "Tear the lid off by hand",
            ],
        ),
        tr(
            "Konserva bankasining qirrasi pichoqdek o'tkir. Qopqog'ini ichiga bosib qo'ysangiz, hech kim — chiqindini olib ketuvchilar ham — jarohat olmaydi.",
            "Край консервной банки острый, как нож. Если вдавить крышку внутрь, никто не порежется — даже те, кто вывозит мусор.",
            "The edge of a can is as sharp as a knife. Pushing the lid inside keeps everyone safe — even the people who collect the rubbish.",
        ),
    ),
    # --- hazardous
    question(
        "hazardous",
        1,
        tr(
            "Nega batareyani oddiy chiqindiga tashlab bo'lmaydi?",
            "Почему батарейку нельзя выбрасывать в обычный мусор?",
            "Why can't a battery go in the ordinary rubbish?",
        ),
        trl(
            [
                "U juda og'ir",
                "Unda tuproq va suvni zaharlaydigan moddalar bor",
                "U o'z-o'zidan zaryadlanib qoladi",
            ],
            [
                "Она слишком тяжёлая",
                "В ней есть вещества, отравляющие почву и воду",
                "Она сама снова зарядится",
            ],
            [
                "It's too heavy",
                "It contains substances that poison soil and water",
                "It will recharge itself",
            ],
        ),
        tr(
            "Ba'zi batareyalarda simob, kadmiy, qo'rg'oshin kabi zaharli moddalar bor. Ular chiqindixonada tuproq va suvga o'tadi.",
            "В некоторых батарейках есть ядовитые ртуть, кадмий и свинец. На свалке они попадают в почву и воду.",
            "Some batteries contain poisonous mercury, cadmium or lead. In a landfill they leak into soil and water.",
        ),
    ),
    question(
        "hazardous",
        2,
        tr(
            "Simobli termometr sinib qolsa, nima qilish kerak?",
            "Что делать, если разбился ртутный градусник?",
            "What should you do if a mercury thermometer breaks?",
        ),
        trl(
            [
                "Simob tomchilarini qo'l bilan yig'ish",
                "Changyutgich bilan tozalab tashlash",
                "Xonadan chiqib, darhol kattalarga aytish",
            ],
            [
                "Собрать капли ртути руками",
                "Убрать всё пылесосом",
                "Выйти из комнаты и сразу сказать взрослым",
            ],
            [
                "Pick up the mercury drops by hand",
                "Clean it all up with a vacuum cleaner",
                "Leave the room and tell an adult at once",
            ],
        ),
        tr(
            "Simob bug'i juda zaharli. Unga tegmang va changyutgich ishlatmang. Kattalar xonani shamollatib, mutaxassislarni chaqiradi.",
            "Пары ртути очень ядовиты. Не трогайте её и не пользуйтесь пылесосом. Взрослые проветрят комнату и вызовут специалистов.",
            "Mercury vapour is very poisonous. Don't touch it or use a vacuum cleaner. Adults will air the room and call specialists.",
        ),
    ),
    question(
        "hazardous",
        0,
        tr(
            "Energiya tejovchi (lyuminessent) lampada qanday xavfli modda bor?",
            "Какое опасное вещество есть в энергосберегающей (люминесцентной) лампе?",
            "What dangerous substance is in an energy-saving (fluorescent) lamp?",
        ),
        trl(["Simob", "Shakar", "Tuz"], ["Ртуть", "Сахар", "Соль"], ["Mercury", "Sugar", "Salt"]),
        tr(
            "Bunday lampalarda oz miqdorda simob bor. Ularni sindirmang va oddiy chiqindiga tashlamang — maxsus qabul punktiga topshiring.",
            "В таких лампах есть немного ртути. Не разбивайте их и не выбрасывайте в обычный мусор — сдавайте в специальный пункт приёма.",
            "These lamps contain a little mercury. Don't break them or put them in ordinary rubbish — take them to a special collection point.",
        ),
    ),
    question(
        "hazardous",
        0,
        tr(
            "Yaqin atrofda batareya qabul qilinadigan joy bo'lmasa, nima qilish kerak?",
            "Что делать, если рядом нет пункта приёма батареек?",
            "What should you do if there's no battery collection point nearby?",
        ),
        trl(
            [
                "Yopiq quti yoki bankada, quruq joyda yig'ib borish",
                "Hovliga ko'mib qo'yish",
                "Gulxanga tashlash",
            ],
            [
                "Собирать в закрытой коробке или банке в сухом месте",
                "Закопать во дворе",
                "Бросить в костёр",
            ],
            [
                "Keep them in a closed box or jar in a dry place",
                "Bury them in the yard",
                "Throw them on a bonfire",
            ],
        ),
        tr(
            "Batareyalarni bolalar yeta olmaydigan quruq joyda, kontaktlarini skotch bilan yopib saqlang. Qabul punkti topilganda hammasini birdaniga topshiring.",
            "Храните батарейки в сухом месте, недоступном детям, заклеив контакты скотчем. Когда найдётся пункт приёма, сдайте их все сразу.",
            "Keep batteries somewhere dry and out of children's reach, with the contacts taped over. When you find a collection point, hand them all in at once.",
        ),
    ),
    question(
        "hazardous",
        1,
        tr(
            "Muddati o'tgan dorilarni nima qilish kerak?",
            "Что делать с просроченными лекарствами?",
            "What should you do with out-of-date medicines?",
        ),
        trl(
            [
                "Hojatxonaga oqizib yuborish",
                "Kattalarga berish: ular xavfsiz yo'q qiladi",
                "Ko'chaga tashlash",
            ],
            ["Смыть в унитаз", "Отдать взрослым: они безопасно утилизируют", "Выбросить на улице"],
            [
                "Flush them down the toilet",
                "Give them to an adult to dispose of safely",
                "Throw them away in the street",
            ],
        ),
        tr(
            "Dorilar suvga tushsa, baliq va boshqa jonzotlarga zarar qiladi. Ularni o'zingiz ichmang — kattalarga bering.",
            "Попав в воду, лекарства вредят рыбам и другим живым существам. Не принимайте их сами — отдайте взрослым.",
            "Medicines that get into water harm fish and other living things. Don't take them yourself — give them to an adult.",
        ),
    ),
    question(
        "hazardous",
        2,
        tr(
            "Qaysi biri xavfli chiqindi?",
            "Что из этого — опасные отходы?",
            "Which of these is hazardous waste?",
        ),
        trl(
            ["Karton quti", "Olma po'chog'i", "Bo'yoq qoldig'i bor banka"],
            ["Картонная коробка", "Яблочная кожура", "Банка с остатками краски"],
            ["A cardboard box", "An apple peel", "A tin with leftover paint"],
        ),
        tr(
            "Bo'yoq, erituvchi, batareya, lampa va dorilar — xavfli chiqindi. Ular alohida yig'iladi va maxsus usulda yo'q qilinadi.",
            "Краски, растворители, батарейки, лампы и лекарства — опасные отходы. Их собирают отдельно и утилизируют особым способом.",
            "Paint, solvents, batteries, lamps and medicines are hazardous waste. They're collected separately and disposed of in a special way.",
        ),
    ),
    question(
        "hazardous",
        0,
        tr(
            "Eski telefon yoki zaryadlovchi qaysi chiqindiga kiradi?",
            "К каким отходам относится старый телефон или зарядка?",
            "What kind of waste is an old phone or charger?",
        ),
        trl(
            ["Elektron chiqindi — alohida topshiriladi", "Oddiy plastik", "Organik chiqindi"],
            ["Электронные отходы — их сдают отдельно", "Обычный пластик", "Органические отходы"],
            ["E-waste — handed in separately", "Ordinary plastic", "Organic waste"],
        ),
        tr(
            "Elektron qurilmalarda qimmatbaho metallar va zaharli moddalar bor. Ularni alohida topshirsangiz, metallar qayta ishlatiladi.",
            "В электронике есть ценные металлы и ядовитые вещества. Если сдать её отдельно, металлы используют снова.",
            "Electronics contain valuable metals and toxic substances. Handed in separately, the metals can be used again.",
        ),
    ),
    # --- general ecology
    question(
        None,
        0,
        tr(
            "Daraxtlar havoga nima beradi?",
            "Что деревья дают воздуху?",
            "What do trees give to the air?",
        ),
        trl(
            ["Kislorod", "Tutun", "Chang"], ["Кислород", "Дым", "Пыль"], ["Oxygen", "Smoke", "Dust"]
        ),
        tr(
            "Daraxtlar karbonat angidridni yutib, kislorod chiqaradi. Ular shahar havosini changdan ham tozalaydi.",
            "Деревья поглощают углекислый газ и выделяют кислород. Они также очищают городской воздух от пыли.",
            "Trees take in carbon dioxide and release oxygen. They also catch dust and clean city air.",
        ),
    ),
    question(
        None,
        1,
        tr(
            "Orol dengizi nega qurib qoldi?",
            "Почему высохло Аральское море?",
            "Why did the Aral Sea dry up?",
        ),
        trl(
            [
                "Juda ko'p yomg'ir yoqqani uchun",
                "Daryolar suvi sug'orishga ko'p olingani uchun",
                "Dengiz suvi muzlab qolgani uchun",
            ],
            [
                "Шло слишком много дождей",
                "Воду рек забирали на полив полей",
                "Вода в море замёрзла",
            ],
            [
                "There was too much rain",
                "River water was taken to irrigate fields",
                "The sea water froze",
            ],
        ),
        tr(
            "Amudaryo va Sirdaryo suvi yillar davomida dalalarni sug'orishga olindi. Dengizga suv yetib bormay, u qurib qoldi.",
            "Много лет воду Амударьи и Сырдарьи забирали на полив полей. Вода перестала доходить до моря, и оно высохло.",
            "For years the water of the Amu Darya and Syr Darya was taken to irrigate fields. It stopped reaching the sea, and the sea dried up.",
        ),
    ),
    question(
        None,
        0,
        tr(
            "Elektrni tejash tabiatga qanday yordam beradi?",
            "Как экономия электроэнергии помогает природе?",
            "How does saving electricity help nature?",
        ),
        trl(
            [
                "Elektr olish uchun kamroq yoqilg'i yoqiladi",
                "Hech qanday yordam bermaydi",
                "Ko'proq daraxt kesiladi",
            ],
            [
                "Для её выработки сжигают меньше топлива",
                "Никак не помогает",
                "Вырубают больше деревьев",
            ],
            [
                "Less fuel is burned to produce it",
                "It doesn't help at all",
                "More trees are cut down",
            ],
        ),
        tr(
            "O'zbekistonda elektrning katta qismi tabiiy gaz yoqib olinadi. Elektrni tejasak, kamroq gaz yoqiladi va havo tozaroq bo'ladi.",
            "В Узбекистане большую часть электричества получают, сжигая природный газ. Экономя электричество, мы сжигаем меньше газа, и воздух чище.",
            "In Uzbekistan most electricity comes from burning natural gas. Saving electricity means less gas is burned and the air is cleaner.",
        ),
    ),
    question(
        None,
        2,
        tr(
            "Qaysi chiqindi tabiatda eng tez parchalanadi?",
            "Какой мусор быстрее всего разлагается в природе?",
            "Which waste breaks down fastest in nature?",
        ),
        trl(
            ["Shisha butilka", "Plastik paket", "Olma qoldig'i"],
            ["Стеклянная бутылка", "Пластиковый пакет", "Огрызок яблока"],
            ["A glass bottle", "A plastic bag", "An apple core"],
        ),
        tr(
            "Olma qoldig'i bir necha haftada chiriydi. Plastik va shisha esa yuzlab, hatto minglab yillar saqlanib qoladi.",
            "Огрызок яблока перегнивает за несколько недель. А пластик и стекло сохраняются сотни и даже тысячи лет.",
            "An apple core rots in a few weeks. Plastic and glass last hundreds or even thousands of years.",
        ),
    ),
    question(
        None,
        0,
        tr("Chiqindini saralash nima uchun kerak?", "Зачем сортировать мусор?", "Why sort waste?"),
        trl(
            [
                "Foydali xomashyoni qayta ishlatish uchun",
                "Chiqindini ko'paytirish uchun",
                "Hech narsa uchun",
            ],
            ["Чтобы снова использовать полезное сырьё", "Чтобы мусора стало больше", "Ни для чего"],
            ["To reuse valuable raw materials", "To make more waste", "For no reason"],
        ),
        tr(
            "Saralangan qog'oz, plastik, shisha va metall qayta ishlanib, yangi buyumlarga aylanadi. Chiqindixonaga esa kamroq chiqindi boradi.",
            "Рассортированные бумага, пластик, стекло и металл перерабатываются в новые вещи. А на свалку попадает меньше мусора.",
            "Sorted paper, plastic, glass and metal are recycled into new things, and less waste goes to landfill.",
        ),
    ),
    question(
        None,
        0,
        tr(
            "Hududingizda alohida konteynerlar bo'lmasa, nima qilish mumkin?",
            "Что делать, если рядом нет отдельных контейнеров?",
            "What can you do if there are no separate bins in your area?",
        ),
        trl(
            [
                "Uyda saralab, qabul punktiga topshirish",
                "Hammasini aralash tashlash",
                "Chiqindini yoqib yuborish",
            ],
            [
                "Сортировать дома и сдавать в пункт приёма",
                "Выбрасывать всё вместе",
                "Сжигать мусор",
            ],
            [
                "Sort at home and take it to a collection point",
                "Throw everything out together",
                "Burn the rubbish",
            ],
        ),
        tr(
            "Qog'oz, plastik butilka va metallni uyda alohida yig'ing. Ularni qabul punktlari yoki makulatura yig'imlarida topshirish mumkin.",
            "Собирайте дома отдельно бумагу, пластиковые бутылки и металл. Их можно сдать в пункты приёма или на сборе макулатуры.",
            "Collect paper, plastic bottles and metal separately at home. You can hand them in at collection points or waste-paper drives.",
        ),
    ),
    question(
        None,
        1,
        tr(
            "Avtomobil o'rniga piyoda yurish yoki velosiped nima beradi?",
            "Что даёт ходьба пешком или велосипед вместо машины?",
            "What does walking or cycling instead of driving do?",
        ),
        trl(
            [
                "Havo ko'proq ifloslanadi",
                "Havo tozaroq bo'ladi, sog'liq mustahkamlanadi",
                "Hech narsa o'zgarmaydi",
            ],
            ["Воздух загрязняется сильнее", "Воздух чище, а здоровье крепче", "Ничего не меняется"],
            ["The air gets dirtier", "Cleaner air and better health", "Nothing changes"],
        ),
        tr(
            "Avtomobillar havoga tutun chiqaradi. Yaqin joyga piyoda yoki velosipedda borsangiz, havo toza bo'ladi, o'zingiz ham sog'lom bo'lasiz.",
            "Автомобили выбрасывают в воздух выхлопные газы. Если ходить на короткие расстояния пешком или ездить на велосипеде, воздух будет чище, а вы — здоровее.",
            "Cars release exhaust fumes into the air. Walking or cycling short distances keeps the air cleaner and you healthier.",
        ),
    ),
]


# ----------------------------------------------------------------- game items
# Evenly over the six bins of the sorting game (TZ 9.1); emoji until photos arrive.


def item(bin_code: str, icon: str, name: dict, explanation: dict) -> dict:
    return {"bin": bin_code, "icon": icon, "name": name, "explanation": explanation}


V1_GAME_ITEMS = [
    # plastic
    item(
        "plastic",
        "🛍️",
        tr("Plastik paket", "Пластиковый пакет", "Plastic bag"),
        tr(
            "Plastik paket plastik qutisiga tashlanadi. Undan ham yaxshisi — mato sumka bilan yuring.",
            "Пластиковый пакет — в контейнер для пластика. А ещё лучше — ходите с тканевой сумкой.",
            "A plastic bag goes into the plastic bin. Even better — carry a cloth bag.",
        ),
    ),
    item(
        "plastic",
        "🧴",
        tr("Suyuq sovun idishi", "Флакон от жидкого мыла", "Liquid soap bottle"),
        tr(
            "Idishni chayib, plastik qutisiga tashlang.",
            "Ополосните флакон и выбросьте в контейнер для пластика.",
            "Rinse the bottle and put it into the plastic bin.",
        ),
    ),
    item(
        "plastic",
        "🪥",
        tr("Eski tish cho'tkasi", "Старая зубная щётка", "Old toothbrush"),
        tr(
            "Tish cho'tkasi plastikdan yasalgan, shuning uchun plastik qutisiga tushadi.",
            "Зубная щётка сделана из пластика, поэтому она отправляется в контейнер для пластика.",
            "A toothbrush is made of plastic, so it goes into the plastic bin.",
        ),
    ),
    item(
        "plastic",
        "🥡",
        tr("Plastik ovqat qutisi", "Пластиковый контейнер для еды", "Plastic food container"),
        tr(
            "Ovqat qoldiqlarini tozalab, plastik qutisiga tashlang.",
            "Очистите от остатков еды и выбросьте в контейнер для пластика.",
            "Clean out the food and put it into the plastic bin.",
        ),
    ),
    # glass
    item(
        "glass",
        "🥛",
        tr("Sut shishasi", "Стеклянная бутылка из-под молока", "Glass milk bottle"),
        tr(
            "Shisha butilkani chayib, shisha qutisiga tashlang.",
            "Ополосните стеклянную бутылку и выбросьте в контейнер для стекла.",
            "Rinse the glass bottle and put it into the glass bin.",
        ),
    ),
    item(
        "glass",
        "🫙",
        tr("Murabbo bankasi", "Банка из-под варенья", "Jam jar"),
        tr(
            "Shisha banka shisha qutisiga tushadi, metall qopqog'ini esa metallga ajrating.",
            "Стеклянная банка — в контейнер для стекла, а металлическую крышку — к металлу.",
            "The glass jar goes into the glass bin; put the metal lid with the metal.",
        ),
    ),
    item(
        "glass",
        "🫙",
        tr(
            "Shisha limonad butilkasi",
            "Стеклянная бутылка из-под лимонада",
            "Glass lemonade bottle",
        ),
        tr(
            "Shisha butilkalar cheksiz marta qayta ishlanadi — ularni shisha qutisiga tashlang.",
            "Стеклянные бутылки можно перерабатывать бесконечно — выбросьте их в контейнер для стекла.",
            "Glass bottles can be recycled endlessly — put them into the glass bin.",
        ),
    ),
    item(
        "glass",
        "🥒",
        tr("Bodring bankasi", "Банка из-под огурцов", "Pickle jar"),
        tr(
            "Tuzlama bankasini yuvib, shisha qutisiga tashlang.",
            "Банку из-под солений вымойте и выбросьте в контейнер для стекла.",
            "Wash the pickle jar and put it into the glass bin.",
        ),
    ),
    item(
        "glass",
        "🍅",
        tr("Shisha ketchup idishi", "Стеклянная бутылка из-под кетчупа", "Glass ketchup bottle"),
        tr(
            "Ichini chayib, shisha qutisiga tashlang. Plastik ketchup idishi esa plastik qutisiga.",
            "Ополосните и выбросьте в контейнер для стекла. А пластиковая бутылка от кетчупа — в контейнер для пластика.",
            "Rinse it and put it into the glass bin. A plastic ketchup bottle goes into the plastic bin.",
        ),
    ),
    # paper
    item(
        "paper",
        "📄",
        tr("Yozilgan qog'oz varag'i", "Исписанный лист бумаги", "Used sheet of paper"),
        tr(
            "Qog'oz varaqlari qog'oz qutisiga tushadi va qayta ishlanadi.",
            "Листы бумаги — в контейнер для бумаги, их переработают.",
            "Sheets of paper go into the paper bin to be recycled.",
        ),
    ),
    item(
        "paper",
        "📖",
        tr("Eski jurnal", "Старый журнал", "Old magazine"),
        tr(
            "Eski jurnallar qog'oz qutisiga tashlanadi — yoki ularni kimgadir sovg'a qiling.",
            "Старые журналы — в контейнер для бумаги. Или подарите их кому-нибудь.",
            "Old magazines go into the paper bin — or give them to someone.",
        ),
    ),
    item(
        "paper",
        "✉️",
        tr("Konvert", "Конверт", "Envelope"),
        tr(
            "Qog'oz konvertlar qog'oz qutisiga tushadi.",
            "Бумажные конверты — в контейнер для бумаги.",
            "Paper envelopes go into the paper bin.",
        ),
    ),
    item(
        "paper",
        "✂️",
        tr("Rangli qog'oz qirqimlari", "Обрезки цветной бумаги", "Coloured paper scraps"),
        tr(
            "Qirqimlarni yig'ib, qog'oz qutisiga tashlang.",
            "Соберите обрезки и выбросьте в контейнер для бумаги.",
            "Collect the scraps and put them into the paper bin.",
        ),
    ),
    # organic
    item(
        "organic",
        "🥔",
        tr("Kartoshka po'chog'i", "Картофельные очистки", "Potato peels"),
        tr(
            "Sabzavot po'choqlari organik qutisiga — ulardan kompost bo'ladi.",
            "Овощные очистки — в контейнер для органики, из них получится компост.",
            "Vegetable peels go into the organic bin — they make compost.",
        ),
    ),
    item(
        "organic",
        "🍉",
        tr("Tarvuz po'sti", "Арбузная корка", "Watermelon rind"),
        tr(
            "Tarvuz po'sti tez chiriydi va kompostga aylanadi.",
            "Арбузная корка быстро перегнивает и становится компостом.",
            "Watermelon rind rots quickly and turns into compost.",
        ),
    ),
    item(
        "organic",
        "🥚",
        tr("Tuxum po'chog'i", "Яичная скорлупа", "Eggshells"),
        tr(
            "Maydalangan tuxum po'chog'i kompostni boyitadi.",
            "Измельчённая яичная скорлупа обогащает компост.",
            "Crushed eggshells enrich compost.",
        ),
    ),
    item(
        "organic",
        "🌿",
        tr("Qirqilgan o't", "Скошенная трава", "Cut grass"),
        tr(
            "O't va barglarni yoqmang — ular kompost uchun juda yaxshi.",
            "Траву и листья не сжигайте — они отлично подходят для компоста.",
            "Don't burn grass and leaves — they're great for compost.",
        ),
    ),
    # metal
    item(
        "metal",
        "🥫",
        tr("Alyuminiy ichimlik bankasi", "Алюминиевая банка из-под напитка", "Aluminium drink can"),
        tr(
            "Bankani ezib, metall qutisiga tashlang — alyuminiy cheksiz marta qayta ishlanadi.",
            "Сомните банку и выбросьте в контейнер для металла — алюминий можно перерабатывать бесконечно.",
            "Crush the can and put it into the metal bin — aluminium can be recycled endlessly.",
        ),
    ),
    item(
        "metal",
        "📎",
        tr("Qog'oz qisqichlari", "Скрепки", "Paper clips"),
        tr(
            "Mayda metall buyumlar ham metall qutisiga tushadi.",
            "Мелкие металлические предметы тоже отправляются в контейнер для металла.",
            "Small metal things go into the metal bin too.",
        ),
    ),
    item(
        "metal",
        "🥄",
        tr("Eski metall qoshiq", "Старая металлическая ложка", "Old metal spoon"),
        tr(
            "Ishlatib bo'lmaydigan metall idish-tovoq metall qutisiga tashlanadi.",
            "Металлическую посуду, которой уже не пользуются, выбрасывают в контейнер для металла.",
            "Metal cutlery you can't use any more goes into the metal bin.",
        ),
    ),
    item(
        "metal",
        "🔧",
        tr("Eski gayka kaliti", "Старый гаечный ключ", "Old spanner"),
        tr(
            "Metall asboblar eritilib, yangi buyumlarga aylanadi.",
            "Металлические инструменты переплавляют и делают из них новые вещи.",
            "Metal tools are melted down and made into new things.",
        ),
    ),
    # hazardous
    item(
        "hazardous",
        "🌡️",
        tr("Simobli termometr", "Ртутный градусник", "Mercury thermometer"),
        tr(
            "Simob juda zaharli. Termometrni sindirmang va kattalarga bering.",
            "Ртуть очень ядовита. Не разбивайте градусник и отдайте его взрослым.",
            "Mercury is very poisonous. Don't break the thermometer — give it to an adult.",
        ),
    ),
    item(
        "hazardous",
        "📱",
        tr("Telefon akkumulyatori", "Аккумулятор от телефона", "Phone battery"),
        tr(
            "Akkumulyator yonib ketishi va zaharli moddalar chiqarishi mumkin — u alohida topshiriladi.",
            "Аккумулятор может загореться и выделить ядовитые вещества — его сдают отдельно.",
            "A battery can catch fire and leak toxic substances — it's handed in separately.",
        ),
    ),
    item(
        "hazardous",
        "🎨",
        tr("Bo'yoq qoldig'i bor banka", "Банка с остатками краски", "Tin with leftover paint"),
        tr(
            "Bo'yoq va erituvchilar xavfli chiqindi — ularni to'kib yubormang.",
            "Краски и растворители — опасные отходы, их нельзя выливать.",
            "Paint and solvents are hazardous waste — never pour them away.",
        ),
    ),
    item(
        "hazardous",
        "🔌",
        tr("Eski zaryadlovchi", "Старое зарядное устройство", "Old charger"),
        tr(
            "Elektron chiqindi alohida topshiriladi: undagi metallar qayta ishlatiladi.",
            "Электронные отходы сдают отдельно: металлы из них используют снова.",
            "E-waste is handed in separately so its metals can be used again.",
        ),
    ),
]


# ---------------------------------------------------------------- daily tasks
# Up to 120 characters, safe, about 10 minutes at home (TZ 9.2).

V1_DAILY_TASKS = [
    tr(
        "Uyingizdagi plastik butilkalarni sanab, sonini yozib qo'ying.",
        "Посчитайте пластиковые бутылки у себя дома и запишите число.",
        "Count the plastic bottles in your home and write the number down.",
    ),
    tr(
        "Bugun do'konga o'z sumkangiz bilan boring yoki kattalarga eslating.",
        "Сегодня идите в магазин со своей сумкой или напомните об этом взрослым.",
        "Take your own bag to the shop today, or remind an adult to.",
    ),
    tr(
        "Eski futbolka yoki matodan uy tozalash uchun latta tayyorlang.",
        "Сделайте тряпку для уборки из старой футболки или ткани.",
        "Make a cleaning rag from an old T-shirt or piece of fabric.",
    ),
    tr(
        "Uydagi jo'mraklardan suv tomib turmaganini tekshiring va kattalarga ayting.",
        "Проверьте, не капает ли вода из кранов дома, и скажите взрослым.",
        "Check whether any taps at home are dripping and tell an adult.",
    ),
    tr(
        "Karton qutilarni yassilab, bir joyga taxlab qo'ying.",
        "Сложите картонные коробки плоско и уберите в одно место.",
        "Flatten the cardboard boxes and stack them in one place.",
    ),
    tr(
        "Ishlatilmayotgan zaryadlovchilarni rozetkadan quruq qo'l bilan sug'urib qo'ying.",
        "Выньте из розеток неиспользуемые зарядки — сухими руками.",
        "Unplug chargers you're not using — with dry hands.",
    ),
    tr(
        "Uydagi gullarga suv quying yoki bitta urug' eking.",
        "Полейте домашние цветы или посадите одно семечко.",
        "Water the houseplants or plant one seed.",
    ),
    tr(
        "Bugun likopchangizga olgan ovqatni oxirigacha yeng.",
        "Сегодня доешьте всё, что положили себе на тарелку.",
        "Today, finish everything you put on your plate.",
    ),
    tr(
        "Eski o'yinchoq yoki kitobni kimgadir sovg'a qilish uchun ajratib qo'ying.",
        "Отложите старую игрушку или книгу, чтобы подарить её кому-нибудь.",
        "Set aside an old toy or book to give to someone.",
    ),
    tr(
        "Varaqning ikkala tomoniga yozing — bugun kamida bitta varaqni tejang.",
        "Пишите на обеих сторонах листа — сэкономьте сегодня хотя бы один лист.",
        "Write on both sides of the paper — save at least one sheet today.",
    ),
    tr(
        "Uydagi chiqindini kuzating: qaysi turi eng ko'p? Oilangizga aytib bering.",
        "Посмотрите, какого мусора дома больше всего, и расскажите семье.",
        "Look at your household rubbish: which kind is there most of? Tell your family.",
    ),
    tr(
        "Bugun dushda 2 daqiqa kamroq turing.",
        "Сегодня проведите в душе на 2 минуты меньше.",
        "Spend 2 minutes less in the shower today.",
    ),
    tr(
        "Qushlar uchun idishda toza suv qo'yib qo'ying (balkonda yoki hovlida).",
        "Поставьте для птиц миску с чистой водой (на балконе или во дворе).",
        "Put out a bowl of clean water for birds (on a balcony or in the yard).",
    ),
    tr(
        "Kattalar bilan birga eng yaqin chiqindi qabul punkti qayerdaligini aniqlang.",
        "Вместе со взрослыми узнайте, где ближайший пункт приёма вторсырья.",
        "With an adult, find out where the nearest recycling collection point is.",
    ),
    tr(
        "Kunduzi chiroq yoqmang: pardani oching va quyosh nuridan foydalaning.",
        "Днём не включайте свет: откройте шторы и пользуйтесь солнечным светом.",
        "Don't switch the lights on in the daytime: open the curtains and use sunlight.",
    ),
    tr(
        "Kiyimlaringizni ko'rib chiqing: kichik bo'lganlarini sovg'a uchun ajrating.",
        "Переберите одежду и отложите ту, что стала мала, чтобы отдать её.",
        "Go through your clothes and set aside the ones that are too small to give away.",
    ),
    tr(
        "Do'stingizga ilovadagi bitta eko-maslahatni aytib bering.",
        "Расскажите другу один эко-совет из приложения.",
        "Tell a friend one eco tip from the app.",
    ),
    tr(
        "Qotgan nonni tashlamang: undan suxari tayyorlashga yordam bering.",
        "Не выбрасывайте чёрствый хлеб: помогите сделать из него сухари.",
        "Don't throw away stale bread: help make rusks from it.",
    ),
    tr(
        "Bugun bir martalik qoshiq, sanchqi va trubochka ishlatmang.",
        "Сегодня не пользуйтесь одноразовыми ложками, вилками и трубочками.",
        "Today, don't use any single-use spoons, forks or straws.",
    ),
    tr(
        "Qog'oz qirqimlaridan kitob uchun xatcho'p yasang.",
        "Сделайте закладку для книги из бумажных обрезков.",
        "Make a bookmark from paper scraps.",
    ),
]


# ----------------------------------------------------------------------- tips
# One or two sentences, practical where separate containers are rare (TZ 9.3).

V1_TIPS = [
    tr(
        "Suv idishingizni o'zingiz bilan olib yuring: bitta idish yuzlab bir martalik butilkani tejaydi.",
        "Носите с собой свою бутылку для воды: одна бутылка заменяет сотни одноразовых.",
        "Carry your own water bottle: one bottle replaces hundreds of single-use ones.",
    ),
    tr(
        "Hududingizda alohida konteyner bo'lmasa, qog'oz va butilkalarni uyda yig'ib, qabul punktiga topshiring.",
        "Если рядом нет отдельных контейнеров, собирайте бумагу и бутылки дома и сдавайте в пункт приёма.",
        "If there are no separate bins nearby, collect paper and bottles at home and take them to a collection point.",
    ),
    tr(
        "Plastik butilkani topshirishdan oldin ezib qo'ying — u ancha kam joy egallaydi.",
        "Перед сдачей сомните пластиковую бутылку — она займёт гораздо меньше места.",
        "Crush plastic bottles before recycling them — they take up much less space.",
    ),
    tr(
        "Meva va sabzavot po'choqlaridan kompost qiling — gullaringiz uchun bepul o'g'it bo'ladi.",
        "Делайте компост из очистков фруктов и овощей — это бесплатное удобрение для цветов.",
        "Make compost from fruit and vegetable peels — free fertiliser for your plants.",
    ),
    tr(
        "Kichik bo'lib qolgan kiyimlarni uka-singillaringiz yoki qo'shnilarga sovg'a qiling.",
        "Одежду, которая стала мала, подарите младшим братьям, сёстрам или соседям.",
        "Give clothes that no longer fit to younger brothers, sisters or neighbours.",
    ),
    tr(
        "Tishingizni yuvayotganda jo'mrakni yoping — har daqiqada bir necha litr suv tejaladi.",
        "Закрывайте кран, когда чистите зубы, — так вы сэкономите несколько литров воды в минуту.",
        "Turn off the tap while brushing your teeth — it saves several litres of water a minute.",
    ),
    tr(
        "Xonadan chiqayotganda chiroqni o'chiring. Kunduzi pardani ochib, quyosh nuridan foydalaning.",
        "Уходя из комнаты, выключайте свет. Днём открывайте шторы и пользуйтесь солнечным светом.",
        "Switch off the light when you leave a room. In the daytime, open the curtains and use sunlight.",
    ),
    tr(
        "Ishlatilmayotgan zaryadlovchini rozetkadan sug'uring — u bo'sh turganda ham ozgina elektr sarflaydi.",
        "Вынимайте неиспользуемую зарядку из розетки — даже без телефона она потребляет немного электричества.",
        "Unplug chargers you're not using — they use a little electricity even with nothing attached.",
    ),
    tr(
        "Daraxt eking yoki unga g'amxo'rlik qiling: bitta daraxt yozda atrofni salqinlatadi va changni ushlab qoladi.",
        "Посадите дерево или ухаживайте за ним: одно дерево летом даёт прохладу и задерживает пыль.",
        "Plant a tree or look after one: a single tree cools its surroundings in summer and traps dust.",
    ),
    tr(
        "Do'konda ortiqcha qadoqlangan mahsulot o'rniga vaznga sotiladiganini tanlang.",
        "В магазине выбирайте товары на развес вместо товаров в лишней упаковке.",
        "At the shop, choose loose products instead of over-packaged ones.",
    ),
    tr(
        "Eski daftarlarning toza varaqlarini birlashtirib, qoralama daftar qiling.",
        "Соберите чистые листы из старых тетрадей и сделайте из них черновик.",
        "Gather the blank pages from old notebooks to make a scrap notebook.",
    ),
    tr(
        "Bir martalik batareya o'rniga qayta zaryadlanadigan akkumulyator ishlating — u yuzlab marta xizmat qiladi.",
        "Пользуйтесь аккумуляторами вместо одноразовых батареек — они служат сотни раз.",
        "Use rechargeable batteries instead of disposable ones — they can be recharged hundreds of times.",
    ),
    tr(
        "Simobli termometr sinsa, unga tegmang va changyutgich ishlatmang — darhol kattalarga ayting.",
        "Если разбился ртутный градусник, не трогайте ртуть и не пылесосьте — сразу скажите взрослым.",
        "If a mercury thermometer breaks, don't touch it or vacuum — tell an adult straight away.",
    ),
    tr(
        "Shisha va metallni cheksiz marta qayta ishlash mumkin, shuning uchun ularni tashlamang — topshiring.",
        "Стекло и металл можно перерабатывать бесконечно, поэтому не выбрасывайте их — сдавайте.",
        "Glass and metal can be recycled endlessly, so don't throw them away — recycle them.",
    ),
    tr(
        "Non — ne'mat. Ortiqcha non sotib olmang, qotganidan esa suxari yoki taom tayyorlang.",
        "Хлеб — это ценность. Не покупайте лишнего, а из чёрствого делайте сухари или блюда.",
        "Bread is precious. Don't buy more than you need, and turn stale bread into rusks or meals.",
    ),
    tr(
        "Konserva bankasini topshirishdan oldin chayib, qopqog'ini ichiga bosib qo'ying — hech kim jarohat olmaydi.",
        "Перед сдачей ополосните консервную банку и вдавите крышку внутрь — никто не порежется.",
        "Rinse tins before recycling them and push the lid inside so no one gets cut.",
    ),
    tr(
        "Yaqin joyga piyoda yoki velosipedda boring: avtomobilsiz qatnov havoni toza saqlaydi.",
        "На короткие расстояния ходите пешком или ездите на велосипеде: поездки без машины берегут чистоту воздуха.",
        "Walk or cycle for short trips: travelling without a car keeps the air clean.",
    ),
    tr(
        "Yozda gullarni ertalab yoki kechqurun sug'oring — kunduzi suv tez bug'lanib ketadi.",
        "Летом поливайте растения утром или вечером — днём вода быстро испаряется.",
        "In summer, water plants in the morning or evening — in the daytime the water evaporates quickly.",
    ),
    tr(
        "Sovg'ani gazeta yoki eski matoga o'rang — chiroyli va chiqindisiz.",
        "Заворачивайте подарки в газету или старую ткань — красиво и без мусора.",
        "Wrap presents in newspaper or old fabric — pretty and waste-free.",
    ),
    tr(
        "Muddati o'tgan dorilarni hojatxonaga oqizmang — ular suvni ifloslantiradi. Kattalarga bering.",
        "Не смывайте просроченные лекарства в унитаз — они загрязняют воду. Отдайте их взрослым.",
        "Don't flush expired medicines down the toilet — they pollute water. Give them to an adult.",
    ),
    tr(
        "Buzilgan buyumni darhol tashlamang: uni tuzatib ko'ring yoki kattalardan yordam so'rang.",
        "Не выбрасывайте сломанную вещь сразу: попробуйте её починить или попросите помощи у взрослых.",
        "Don't throw a broken thing away at once: try to fix it or ask an adult to help.",
    ),
    tr(
        "Kir yuvish mashinasini to'liq yuklab ishlating — bu suv va elektrni tejaydi.",
        "Включайте стиральную машину только с полной загрузкой — это экономит воду и электричество.",
        "Run the washing machine only with a full load — it saves water and electricity.",
    ),
    tr(
        "Plastik trubochka o'rniga to'g'ridan-to'g'ri stakandan iching yoki ko'p martalik trubochka oling.",
        "Пейте прямо из стакана вместо пластиковой трубочки или купите многоразовую.",
        "Drink straight from the glass instead of using a plastic straw, or get a reusable one.",
    ),
    tr(
        "Ko'chada chiqindi qutisi topilmasa, axlatni uyga olib keting — yerga tashlamang.",
        "Если на улице нет урны, донесите мусор до дома — не бросайте его на землю.",
        "If there's no bin on the street, take your rubbish home — don't drop it.",
    ),
    tr(
        "Maktabingizda makulatura yig'imi bo'lsa, eski gazeta va kartonlaringizni olib boring.",
        "Если в школе собирают макулатуру, принесите свои старые газеты и картон.",
        "If your school collects waste paper, bring your old newspapers and cardboard.",
    ),
]


# ------------------------------------------------------------ knowledge cards
# Problem → cause → effect → solution → what I can do (TZ 8.10). Each sentence of
# "action" becomes one checkbox in the app.

V1_CARDS = [
    {
        "slug": "batteries",
        "title": tr(
            "Batareyalar nega xavfli?", "Чем опасны батарейки?", "Why are batteries dangerous?"
        ),
        "sections": {
            "uz": {
                "problem": "Odamlar har yili millionlab batareya ishlatadi. Ularning ko'pchiligi oddiy chiqindi bilan birga chiqindixonaga tushadi.",
                "cause": "Ko'pchilik batareyani qayerga topshirishni bilmaydi. Ba'zi hududlarda qabul punktlari kam.",
                "effect": "Vaqt o'tib batareya qobig'i yemiriladi va ba'zi batareyalardagi simob, kadmiy, qo'rg'oshin tuproq va suvga o'tadi. Litiy akkumulyatorlar chiqindi mashinasida yonib ketishi mumkin.",
                "solution": "Batareyalarni alohida yig'ib, maxsus qabul punktlariga topshirish kerak. Qayta zaryadlanadigan akkumulyatorlar tashlanadigan batareyalarni ancha kamaytiradi.",
                "action": "Uyda batareyalar uchun alohida quti tayyorlang. Ularning kontaktlarini skotch bilan yopib qo'ying. Qabul punktini topib, yig'ilganlarini kattalar bilan birga topshiring.",
            },
            "ru": {
                "problem": "Люди каждый год используют миллионы батареек. Большинство из них вместе с обычным мусором попадает на свалку.",
                "cause": "Многие не знают, куда сдавать батарейки. В некоторых районах мало пунктов приёма.",
                "effect": "Со временем корпус батарейки разрушается, и ртуть, кадмий и свинец из некоторых батареек попадают в почву и воду. Литиевые аккумуляторы могут загореться в мусоровозе.",
                "solution": "Батарейки нужно собирать отдельно и сдавать в специальные пункты приёма. Аккумуляторы, которые можно заряжать, сильно сокращают число выброшенных батареек.",
                "action": "Заведите дома отдельную коробку для батареек. Заклейте их контакты скотчем. Найдите пункт приёма и сдайте собранное вместе со взрослыми.",
            },
            "en": {
                "problem": "People use millions of batteries every year. Most of them end up in landfill with ordinary rubbish.",
                "cause": "Many people don't know where to hand in batteries. Some areas have few collection points.",
                "effect": "Over time a battery's casing breaks down, and the mercury, cadmium and lead in some batteries leak into soil and water. Lithium batteries can catch fire in rubbish trucks.",
                "solution": "Batteries should be collected separately and taken to special collection points. Rechargeable batteries mean far fewer batteries are thrown away.",
                "action": "Keep a separate box for batteries at home. Tape over their contacts. Find a collection point and hand them in together with an adult.",
            },
        },
    },
    {
        "slug": "burning-leaves",
        "title": tr(
            "Barglarni yoqish: kuzgi tutun",
            "Сжигание листьев: осенний дым",
            "Burning leaves: autumn smoke",
        ),
        "sections": {
            "uz": {
                "problem": "Kuzda ko'p joylarda to'kilgan barglar va o'tlar yoqiladi. Shahar va qishloqlar ustida achchiq tutun paydo bo'ladi.",
                "cause": "Barglarni yoqish tez va oson tuyuladi. Ko'pchilik ulardan kompost qilish mumkinligini bilmaydi.",
                "effect": "Tutunda mayda zarrachalar va is gazi bor. Ular nafas yo'llariga zarar yetkazadi, ayniqsa bolalar va astmasi borlar uchun xavfli. Olov tarqalib, yong'in chiqishi ham mumkin.",
                "solution": "Barglarni kompostga yig'ish yoki daraxtlar tagiga mulcha qilib yoyish mumkin. Ular chirib, tuproqni boyitadi.",
                "action": "Barglarni yoqmang va yoqayotganlarga xavfini tushuntiring. Kattalar bilan birga barglardan kompost uyumi tayyorlang.",
            },
            "ru": {
                "problem": "Осенью во многих местах сжигают опавшие листья и траву. Над городами и сёлами появляется едкий дым.",
                "cause": "Сжигать листья кажется быстро и просто. Многие не знают, что из них можно сделать компост.",
                "effect": "В дыме есть мелкие частицы и угарный газ. Они вредят органам дыхания и особенно опасны для детей и людей с астмой. Огонь может перекинуться дальше и вызвать пожар.",
                "solution": "Листья можно собрать в компост или разложить под деревьями как мульчу. Перегнивая, они обогащают почву.",
                "action": "Не сжигайте листья и объясните другим, чем это опасно. Вместе со взрослыми сделайте из листьев компостную кучу.",
            },
            "en": {
                "problem": "In autumn, fallen leaves and grass are burned in many places. Acrid smoke hangs over towns and villages.",
                "cause": "Burning leaves seems quick and easy. Many people don't know leaves can be made into compost.",
                "effect": "The smoke contains tiny particles and carbon monoxide. They harm the lungs and are especially dangerous for children and people with asthma. The fire can also spread.",
                "solution": "Leaves can be composted or spread under trees as mulch. As they rot, they enrich the soil.",
                "action": "Don't burn leaves, and explain the danger to people who do. Make a compost heap from leaves together with an adult.",
            },
        },
    },
]
