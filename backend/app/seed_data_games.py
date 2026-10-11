"""Badges (reference data) and demo quiz questions / sorting-game items.

Demo content is for development only; the real set (60–80 questions, 40–50 items) is
prepared in phase 7 and reviewed by the content team (TZ 9.3).
"""

# TZ 8.6. Conditions are in app/badges.py.
BADGES = [
    {
        "code": "first_step",
        "icon": "👣",
        "name": {"uz": "Birinchi qadam", "ru": "Первый шаг", "en": "First step"},
        "description": {
            "uz": "Birinchi ballingizni oling",
            "ru": "Получите первые баллы",
            "en": "Earn your first points",
        },
    },
    {
        "code": "streak_7",
        "icon": "🔥",
        "name": {"uz": "7 kun ketma-ket", "ru": "7 дней подряд", "en": "7-day streak"},
        "description": {
            "uz": "Kunlik topshiriqni 7 kun ketma-ket bajaring",
            "ru": "Выполняйте ежедневное задание 7 дней подряд",
            "en": "Complete the daily task 7 days in a row",
        },
    },
    {
        "code": "master_plastic",
        "icon": "🥤",
        "name": {"uz": "Plastik ustasi", "ru": "Мастер пластика", "en": "Plastic master"},
        "description": {
            "uz": "Plastik bo'limidagi barcha loyihalarni bajaring",
            "ru": "Выполните все проекты раздела «Пластик»",
            "en": "Complete every project in the Plastic section",
        },
    },
    {
        "code": "master_glass",
        "icon": "🫙",
        "name": {"uz": "Shisha ustasi", "ru": "Мастер стекла", "en": "Glass master"},
        "description": {
            "uz": "Shisha bo'limidagi barcha loyihalarni bajaring",
            "ru": "Выполните все проекты раздела «Стекло»",
            "en": "Complete every project in the Glass section",
        },
    },
    {
        "code": "master_paper",
        "icon": "📦",
        "name": {"uz": "Qog'oz ustasi", "ru": "Мастер бумаги", "en": "Paper master"},
        "description": {
            "uz": "Qog'oz va karton bo'limidagi barcha loyihalarni bajaring",
            "ru": "Выполните все проекты раздела «Бумага и картон»",
            "en": "Complete every project in the Paper and cardboard section",
        },
    },
    {
        "code": "master_textile",
        "icon": "👕",
        "name": {"uz": "Tekstil ustasi", "ru": "Мастер текстиля", "en": "Textile master"},
        "description": {
            "uz": "Tekstil bo'limidagi barcha loyihalarni bajaring",
            "ru": "Выполните все проекты раздела «Текстиль»",
            "en": "Complete every project in the Textiles section",
        },
    },
    {
        "code": "master_organic",
        "icon": "🍂",
        "name": {"uz": "Kompost ustasi", "ru": "Мастер компоста", "en": "Compost master"},
        "description": {
            "uz": "Organik bo'limidagi barcha loyihalarni bajaring",
            "ru": "Выполните все проекты раздела «Органика»",
            "en": "Complete every project in the Organic section",
        },
    },
    {
        "code": "quiz_champion",
        "icon": "🧠",
        "name": {"uz": "Viktorina chempioni", "ru": "Чемпион викторины", "en": "Quiz champion"},
        "description": {
            "uz": "50 ta savolga to'g'ri javob bering",
            "ru": "Правильно ответьте на 50 вопросов",
            "en": "Answer 50 questions correctly",
        },
    },
    {
        "code": "sorting_master",
        "icon": "♻️",
        "name": {"uz": "Saralash ustasi", "ru": "Мастер сортировки", "en": "Sorting master"},
        "description": {
            "uz": "O'yinda 100 ta buyumni to'g'ri saralang",
            "ru": "Правильно рассортируйте 100 предметов в игре",
            "en": "Sort 100 items correctly in the game",
        },
    },
]

# "category": None means a general ecology question.
DEMO_QUESTIONS = [
    {
        "category": "plastic",
        "correct_index": 0,
        "text": {
            "uz": "Plastik butilkani qayta ishlashga topshirishdan oldin nima qilish kerak?",
            "ru": "Что нужно сделать с пластиковой бутылкой перед сдачей на переработку?",
            "en": "What should you do with a plastic bottle before recycling it?",
        },
        "options": {
            "uz": [
                "Chayib, ezib qo'yish",
                "Ichida suv qoldirish",
                "Yoqib yuborish",
                "Yerga ko'mish",
            ],
            "ru": ["Ополоснуть и смять", "Оставить внутри воду", "Сжечь", "Закопать в землю"],
            "en": ["Rinse and crush it", "Leave water inside", "Burn it", "Bury it"],
        },
        "explanation": {
            "uz": "Toza va ezilgan butilka kam joy egallaydi va uni qayta ishlash osonroq.",
            "ru": "Чистая смятая бутылка занимает меньше места, и её проще переработать.",
            "en": "A clean, crushed bottle takes less space and is easier to recycle.",
        },
    },
    {
        "category": "glass",
        "correct_index": 1,
        "text": {
            "uz": "Shisha idishni necha marta qayta ishlash mumkin?",
            "ru": "Сколько раз можно перерабатывать стеклянную тару?",
            "en": "How many times can a glass container be recycled?",
        },
        "options": {
            "uz": [
                "Faqat bir marta",
                "Ko'p marta, sifati deyarli yo'qolmaydi",
                "Umuman qayta ishlanmaydi",
            ],
            "ru": [
                "Только один раз",
                "Много раз почти без потери качества",
                "Вообще не перерабатывается",
            ],
            "en": [
                "Only once",
                "Many times with almost no loss of quality",
                "It can't be recycled",
            ],
        },
        "explanation": {
            "uz": "Shisha eritilib, qayta-qayta yangi idishga aylantirilishi mumkin.",
            "ru": "Стекло можно снова и снова плавить и делать из него новую тару.",
            "en": "Glass can be melted and made into new containers again and again.",
        },
    },
    {
        "category": "paper",
        "correct_index": 2,
        "text": {
            "uz": "Qaysi qog'ozni qayta ishlashga topshirib bo'lmaydi?",
            "ru": "Какую бумагу нельзя сдать на переработку?",
            "en": "Which paper can't be recycled?",
        },
        "options": {
            "uz": ["Eski gazeta", "Karton quti", "Yog'li pitsa qutisi", "Daftar varag'i"],
            "ru": [
                "Старая газета",
                "Картонная коробка",
                "Жирная коробка от пиццы",
                "Тетрадный лист",
            ],
            "en": ["An old newspaper", "A cardboard box", "A greasy pizza box", "A notebook page"],
        },
        "explanation": {
            "uz": "Yog' va ovqat qoldiqlari qog'oz tolalarini ifloslantiradi, shuning uchun bunday qog'oz qayta ishlanmaydi.",
            "ru": "Жир и остатки еды загрязняют волокна бумаги, поэтому такая бумага не перерабатывается.",
            "en": "Grease and food spoil the paper fibres, so this paper can't be recycled.",
        },
    },
    {
        "category": "organic",
        "correct_index": 1,
        "text": {
            "uz": "Kuzda to'kilgan quruq barglarni nima qilgan ma'qul?",
            "ru": "Что лучше сделать с опавшими сухими листьями?",
            "en": "What is the best thing to do with fallen dry leaves?",
        },
        "options": {
            "uz": ["Yoqib yuborish", "Kompost qilish", "Ariqqa tashlash"],
            "ru": ["Сжечь", "Сделать компост", "Выбросить в арык"],
            "en": ["Burn them", "Compost them", "Throw them into a ditch"],
        },
        "explanation": {
            "uz": "Yoqilganda tutun havoni ifloslantiradi, kompost esa tuproqni o'g'itlaydi.",
            "ru": "Дым от сжигания загрязняет воздух, а компост удобряет почву.",
            "en": "Burning pollutes the air with smoke, while compost feeds the soil.",
        },
    },
    {
        "category": "hazardous",
        "correct_index": 1,
        "text": {
            "uz": "Ishlatilgan batareyani qayerga tashlash kerak?",
            "ru": "Куда нужно выбрасывать использованные батарейки?",
            "en": "Where should used batteries go?",
        },
        "options": {
            "uz": ["Oddiy chiqindi qutisiga", "Maxsus qabul punktiga", "Ariqqa"],
            "ru": ["В обычное мусорное ведро", "В специальный пункт приёма", "В арык"],
            "en": ["Into the regular bin", "To a special drop-off point", "Into a ditch"],
        },
        "explanation": {
            "uz": "Batareyada tuproq va suvni zaharlaydigan moddalar bor, shuning uchun ularni alohida yig'ish kerak.",
            "ru": "В батарейках есть вещества, которые отравляют почву и воду, поэтому их собирают отдельно.",
            "en": "Batteries contain substances that poison soil and water, so they are collected separately.",
        },
    },
    {
        "category": "metal",
        "correct_index": 0,
        "text": {
            "uz": "Alyumin ichimlik bankasini qayta ishlash mumkinmi?",
            "ru": "Можно ли переработать алюминиевую банку от напитка?",
            "en": "Can an aluminium drink can be recycled?",
        },
        "options": {
            "uz": ["Ha, ko'p marta", "Yo'q", "Faqat bir marta"],
            "ru": ["Да, много раз", "Нет", "Только один раз"],
            "en": ["Yes, many times", "No", "Only once"],
        },
        "explanation": {
            "uz": "Alyuminiy sifatini yo'qotmasdan qayta-qayta eritilishi mumkin.",
            "ru": "Алюминий можно переплавлять снова и снова без потери качества.",
            "en": "Aluminium can be melted down again and again without losing quality.",
        },
    },
    {
        "category": None,
        "correct_index": 2,
        "text": {
            "uz": "Plastik paket tabiatda qancha vaqtda parchalanadi?",
            "ru": "Сколько времени разлагается в природе пластиковый пакет?",
            "en": "How long does a plastic bag take to break down in nature?",
        },
        "options": {
            "uz": ["Bir haftada", "Bir yilda", "O'nlab, hatto yuzlab yillarda"],
            "ru": ["За неделю", "За год", "Десятки и даже сотни лет"],
            "en": ["A week", "A year", "Decades or even hundreds of years"],
        },
        "explanation": {
            "uz": "Plastik juda sekin parchalanadi, shuning uchun uni kamroq ishlatgan ma'qul.",
            "ru": "Пластик разлагается очень медленно, поэтому лучше использовать его меньше.",
            "en": "Plastic breaks down very slowly, so it's better to use less of it.",
        },
    },
    {
        "category": "textile",
        "correct_index": 1,
        "text": {
            "uz": "Kichik bo'lib qolgan kiyimni nima qilish mumkin?",
            "ru": "Что можно сделать с одеждой, из которой вырос?",
            "en": "What can you do with clothes you have outgrown?",
        },
        "options": {
            "uz": [
                "Faqat tashlab yuborish",
                "Boshqalarga berish yoki undan yangi buyum yasash",
                "Yoqib yuborish",
            ],
            "ru": ["Только выбросить", "Отдать другим или сделать из неё новую вещь", "Сжечь"],
            "en": ["Only throw them away", "Give them away or make something new", "Burn them"],
        },
        "explanation": {
            "uz": "Kiyimga ikkinchi hayot bering: uni sovg'a qiling yoki undan sumka, latta, o'yinchoq yasang.",
            "ru": "Дайте одежде вторую жизнь: подарите её или сшейте сумку, тряпку, игрушку.",
            "en": "Give clothes a second life: pass them on or turn them into a bag, a rag or a toy.",
        },
    },
    {
        "category": None,
        "correct_index": 0,
        "text": {
            "uz": "«Uch R» qoidasi nimani anglatadi?",
            "ru": "Что означает правило «трёх R»?",
            "en": 'What does the "three Rs" rule mean?',
        },
        "options": {
            "uz": [
                "Kamaytir, qayta foydalan, qayta ishla",
                "Yugur, sakra, dam ol",
                "O'qi, yoz, rasm chiz",
            ],
            "ru": [
                "Сокращай, используй повторно, перерабатывай",
                "Бегай, прыгай, отдыхай",
                "Читай, пиши, рисуй",
            ],
            "en": ["Reduce, reuse, recycle", "Run, jump, rest", "Read, write, draw"],
        },
        "explanation": {
            "uz": "Reduce, Reuse, Recycle: kamroq iste'mol qilish, buyumni qayta ishlatish va qayta ishlashga topshirish.",
            "ru": "Reduce, Reuse, Recycle: меньше потреблять, использовать вещи повторно и сдавать на переработку.",
            "en": "Use less, use things again, and send what's left for recycling.",
        },
    },
    {
        "category": "organic",
        "correct_index": 2,
        "text": {
            "uz": "Qaysi biri uydagi kompostga solinmaydi?",
            "ru": "Что не стоит класть в домашний компост?",
            "en": "Which of these should not go into a home compost?",
        },
        "options": {
            "uz": ["Sabzavot po'chog'i", "Quruq barg", "Go'sht qoldig'i"],
            "ru": ["Овощные очистки", "Сухие листья", "Остатки мяса"],
            "en": ["Vegetable peels", "Dry leaves", "Meat scraps"],
        },
        "explanation": {
            "uz": "Go'sht va sut mahsulotlari yomon hid chiqaradi va zararkunandalarni jalb qiladi.",
            "ru": "Мясо и молочные продукты неприятно пахнут и привлекают вредителей.",
            "en": "Meat and dairy smell bad and attract pests.",
        },
    },
    {
        "category": None,
        "correct_index": 0,
        "text": {
            "uz": "Tishni yuvayotganda jo'mrakni yopib qo'ysak nima bo'ladi?",
            "ru": "Что будет, если закрывать кран, пока чистишь зубы?",
            "en": "What happens if you turn off the tap while brushing your teeth?",
        },
        "options": {
            "uz": ["Suv tejaladi", "Hech narsa o'zgarmaydi", "Tish yaxshiroq tozalanadi"],
            "ru": ["Сэкономится вода", "Ничего не изменится", "Зубы почистятся лучше"],
            "en": ["You save water", "Nothing changes", "Your teeth get cleaner"],
        },
        "explanation": {
            "uz": "Jo'mrak ochiq qolsa, bir daqiqada bir necha litr toza suv behuda oqib ketadi.",
            "ru": "Из открытого крана за минуту зря утекает несколько литров чистой воды.",
            "en": "An open tap wastes several litres of clean water every minute.",
        },
    },
    {
        "category": "plastic",
        "correct_index": 1,
        "text": {
            "uz": "Qaysi buyumni ko'p marta ishlatish mumkin?",
            "ru": "Какую вещь можно использовать много раз?",
            "en": "Which of these can be used many times?",
        },
        "options": {
            "uz": ["Bir martalik plastik stakan", "Mato sumka", "Yupqa plastik paket"],
            "ru": [
                "Одноразовый пластиковый стаканчик",
                "Тканевая сумка",
                "Тонкий пластиковый пакет",
            ],
            "en": ["A single-use plastic cup", "A cloth bag", "A thin plastic bag"],
        },
        "explanation": {
            "uz": "Mato sumka yillar davomida xizmat qiladi va ko'plab paketlar o'rnini bosadi.",
            "ru": "Тканевая сумка служит годами и заменяет множество пакетов.",
            "en": "A cloth bag lasts for years and replaces lots of plastic bags.",
        },
    },
]

DEMO_GAME_ITEMS = [
    {
        "bin": "plastic",
        "icon": "🧴",
        "name": {"uz": "Shampun idishi", "ru": "Флакон от шампуня", "en": "Shampoo bottle"},
        "explanation": {
            "uz": "Qattiq plastik idishlar plastik qutisiga tashlanadi.",
            "ru": "Жёсткие пластиковые флаконы — в контейнер для пластика.",
            "en": "Hard plastic bottles go into the plastic bin.",
        },
    },
    {
        "bin": "plastic",
        "icon": "🥤",
        "name": {"uz": "Plastik stakan", "ru": "Пластиковый стаканчик", "en": "Plastic cup"},
        "explanation": {
            "uz": "Plastik stakan — plastik. Yaxshisi, qayta ishlatiladigan krujkadan foydalaning.",
            "ru": "Пластиковый стаканчик — это пластик. А лучше пользоваться многоразовой кружкой.",
            "en": "A plastic cup is plastic. Better still, use a reusable mug.",
        },
    },
    {
        "bin": "plastic",
        "icon": "🪣",
        "name": {
            "uz": "Singan plastik chelak",
            "ru": "Сломанное пластиковое ведро",
            "en": "Broken plastic bucket",
        },
        "explanation": {
            "uz": "Qattiq plastikdan yasalgan buyumlar plastik qutisiga tashlanadi.",
            "ru": "Вещи из жёсткого пластика — в контейнер для пластика.",
            "en": "Things made of hard plastic go into the plastic bin.",
        },
    },
    {
        "bin": "glass",
        "icon": "🫙",
        "name": {"uz": "Shisha butilka", "ru": "Стеклянная бутылка", "en": "Glass bottle"},
        "explanation": {
            "uz": "Shisha butilka shisha qutisiga. Shisha ko'p marta qayta ishlanadi.",
            "ru": "Стеклянная бутылка — в контейнер для стекла. Стекло перерабатывается много раз.",
            "en": "A glass bottle goes into the glass bin. Glass can be recycled many times.",
        },
    },
    {
        "bin": "glass",
        "icon": "🫙",
        "name": {"uz": "Shisha banka", "ru": "Стеклянная банка", "en": "Glass jar"},
        "explanation": {
            "uz": "Bo'sh shisha banka shisha qutisiga. Yoki uni uyda qayta ishlating!",
            "ru": "Пустая банка — в контейнер для стекла. Или используйте её дома ещё раз!",
            "en": "An empty jar goes into the glass bin. Or reuse it at home!",
        },
    },
    {
        "bin": "paper",
        "icon": "📦",
        "name": {"uz": "Karton quti", "ru": "Картонная коробка", "en": "Cardboard box"},
        "explanation": {
            "uz": "Kartonni yassilab, qog'oz qutisiga tashlang.",
            "ru": "Сложите коробку и положите в контейнер для бумаги.",
            "en": "Flatten the box and put it into the paper bin.",
        },
    },
    {
        "bin": "paper",
        "icon": "📰",
        "name": {"uz": "Eski gazeta", "ru": "Старая газета", "en": "Old newspaper"},
        "explanation": {
            "uz": "Gazeta — qog'oz, uni qayta ishlash mumkin.",
            "ru": "Газета — это бумага, её можно переработать.",
            "en": "A newspaper is paper and can be recycled.",
        },
    },
    {
        "bin": "paper",
        "icon": "📓",
        "name": {"uz": "Eski daftar", "ru": "Старая тетрадь", "en": "Old notebook"},
        "explanation": {
            "uz": "Daftar qog'oz qutisiga. Agar muqovasi plastik bo'lsa, uni ajratib oling.",
            "ru": "Тетрадь — в контейнер для бумаги. Пластиковую обложку снимите.",
            "en": "A notebook goes into the paper bin. Remove a plastic cover first.",
        },
    },
    {
        "bin": "organic",
        "icon": "🍌",
        "name": {"uz": "Banan po'chog'i", "ru": "Банановая кожура", "en": "Banana peel"},
        "explanation": {
            "uz": "Meva po'chog'i — organik chiqindi, undan kompost bo'ladi.",
            "ru": "Кожура фруктов — органика, из неё получится компост.",
            "en": "Fruit peel is organic waste and makes good compost.",
        },
    },
    {
        "bin": "organic",
        "icon": "🍂",
        "name": {"uz": "Quruq barglar", "ru": "Сухие листья", "en": "Dry leaves"},
        "explanation": {
            "uz": "Barglarni yoqmang — ular kompost uchun juda yaxshi.",
            "ru": "Не сжигайте листья — они отлично подходят для компоста.",
            "en": "Don't burn leaves — they are great for compost.",
        },
    },
    {
        "bin": "organic",
        "icon": "🍎",
        "name": {"uz": "Olma qoldig'i", "ru": "Огрызок яблока", "en": "Apple core"},
        "explanation": {
            "uz": "Ovqat qoldiqlari organik qutisiga yoki kompostga.",
            "ru": "Остатки еды — в контейнер для органики или в компост.",
            "en": "Food scraps go into the organic bin or the compost.",
        },
    },
    {
        "bin": "metal",
        "icon": "🥫",
        "name": {"uz": "Konserva bankasi", "ru": "Консервная банка", "en": "Tin can"},
        "explanation": {
            "uz": "Metall banka metall qutisiga. Avval uni chayib oling.",
            "ru": "Металлическая банка — в контейнер для металла. Сначала ополосните её.",
            "en": "A metal can goes into the metal bin. Rinse it first.",
        },
    },
    {
        "bin": "metal",
        "icon": "🔩",
        "name": {
            "uz": "Eski bolt va gaykalar",
            "ru": "Старые болты и гайки",
            "en": "Old bolts and nuts",
        },
        "explanation": {
            "uz": "Metall buyumlar eritilib, qayta ishlatiladi.",
            "ru": "Металлические вещи переплавляют и используют снова.",
            "en": "Metal things are melted down and used again.",
        },
    },
    {
        "bin": "metal",
        "icon": "🔑",
        "name": {"uz": "Eski kalit", "ru": "Старый ключ", "en": "Old key"},
        "explanation": {
            "uz": "Kalit metalldan yasalgan, uni metall qutisiga tashlang.",
            "ru": "Ключ сделан из металла — в контейнер для металла.",
            "en": "A key is made of metal, so it goes into the metal bin.",
        },
    },
    {
        "bin": "hazardous",
        "icon": "🔋",
        "name": {"uz": "Batareya", "ru": "Батарейка", "en": "Battery"},
        "explanation": {
            "uz": "Batareya xavfli chiqindi: uni maxsus qabul punktiga topshiring.",
            "ru": "Батарейка — опасные отходы: сдайте её в специальный пункт приёма.",
            "en": "A battery is hazardous waste: take it to a special drop-off point.",
        },
    },
    {
        "bin": "hazardous",
        "icon": "💡",
        "name": {
            "uz": "Energiya tejovchi lampa",
            "ru": "Энергосберегающая лампа",
            "en": "Energy-saving lamp",
        },
        "explanation": {
            "uz": "Bunday lampada simob bor — uni oddiy chiqindiga tashlab bo'lmaydi.",
            "ru": "В такой лампе есть ртуть — её нельзя выбрасывать с обычным мусором.",
            "en": "These lamps contain mercury and must not go in the regular bin.",
        },
    },
    {
        "bin": "hazardous",
        "icon": "💊",
        "name": {
            "uz": "Muddati o'tgan dorilar",
            "ru": "Просроченные лекарства",
            "en": "Expired medicines",
        },
        "explanation": {
            "uz": "Eski dorilarni dorixona yoki maxsus qabul punktiga topshiring.",
            "ru": "Старые лекарства сдают в аптеку или специальный пункт приёма.",
            "en": "Take old medicines to a pharmacy or a special drop-off point.",
        },
    },
]
