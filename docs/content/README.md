# 1-versiya kontenti: qoralama (TZ 9)

Bu papka kontent jamoasi uchun. Qoralama matnlar kodda turadi
(`backend/app/seed_data_v1.py`) va admin panelga **«Tekshiruvda»** holatida yuklanadi.
Jamoa tekshirib, tuzatib, nashr qilmaguncha ilovada hech narsa ko'rinmaydi.

```bash
cd backend && .venv/Scripts/python -m app.seed --content
```

Buyruqni qayta ishga tushirsangiz, takror qo'shmaydi va admin panelda tahrirlangan
matnlarga tegmaydi.

## Hajm (TZ 9.1: minimal ishga tushirish to'plami)

| Tur | Namuna (nashr qilingan) | Yangi qoralama | Jami | TZ minimumi |
|---|---|---|---|---|
| Loyihalar (video darslar) | 3 | 5 | 8 | 8 |
| Viktorina savollari | 12 | 48 | 60 | 60 |
| O'yin buyumlari | 17 | 25 | 42 | 40 |
| Kunlik topshiriqlar | 10 | 20 | 30 | 30 |
| Kunlik maslahatlar | 5 | 25 | 30 | 30 |
| Bilim kartochkalari | 2 | 2 | 4 | 3–4 |
| O'qituvchi darslari | 3 | — | 3 | 3 |
| Foydalanish shartlari | — | 1 (ilovada) | 1 | 1 |

Savollar har bir chiqindi turi va umumiy ekologiya bo'yicha (har biriga kamida 6 ta),
o'yin buyumlari 6 ta quti bo'yicha teng (har biriga 7 ta) taqsimlangan. Uzunlik va
format TZ 9.2 bo'yicha avtomatik test bilan tekshiriladi (`backend/tests/test_content_v1.py`).

## Tekshirish tartibi (TZ 9.3)

Admin panel → kerakli bo'lim → **«Tekshiruvda»** yorlig'i. Har bir element uchun:

1. **Mutaxassis (ekolog yoki biologiya o'qituvchisi):** faktlar to'g'riligi va xavfsizlik.
   Pastdagi ro'yxatdagi raqam va da'volarni alohida tekshiring.
2. **Tarjima tekshiruvi:** rus va ingliz matnlari (oldindan ko'rishda tilni almashtiring).
3. **Loyihalar:** jamoa a'zosi loyihani amalda bajarib ko'radi, «Kim sinab ko'rdi» va
   «Qachon» maydonlarini to'ldiradi. Usiz loyiha nashr qilinmaydi.
4. **Video:** loyiha qadamlari — suratga olish ssenariysi (pastdagi talablar).
5. **Nashr qilish.** Xato bo'lsa, admin panel nashrga ruxsat bermaydi va sababini ko'rsatadi.

## Mutaxassis tekshirishi kerak bo'lgan faktlar

| Da'vo | Qayerda |
|---|---|
| Alyuminiyni qayta ishlash rudadan olishga nisbatan ~95% energiya tejaydi | Savol (metall) |
| Qog'ozni taxminan 5–7 marta qayta ishlash mumkin | Savol (qog'oz) |
| Bitta paxta futbolka uchun minglab litr suv sarflanadi (WWF: ~2700 l) | Savol (tekstil) |
| Mikroplastik — 5 mm dan kichik zarrachalar | Savol (plastik) |
| O'zbekistonda elektrning katta qismi tabiiy gazdan olinadi | Savol (umumiy) |
| Shisha va metallni cheksiz qayta ishlash mumkin | Maslahat, o'yin buyumlari |
| Ba'zi batareyalarda simob, kadmiy, qo'rg'oshin bor; litiy akkumulyator yonishi mumkin | Savol, kartochka |
| Lyuminessent lampada simob bor | Savol |
| Kassa cheklari odatda qayta ishlanmaydi | Savol (qog'oz) |
| Ko'zgu va deraza oynasi butilka shishasi bilan birga qabul qilinmaydi | Savol (shisha) |
| Chiqindixonada ovqat qoldiqlari metan chiqaradi | Savol (organik) |
| Barg tutunida mayda zarrachalar va is gazi bor | Kartochka |

**Mahalliy moslik:** ko'p matnlar «qabul punktiga topshiring» deydi. Hududlarda batareya,
lampa, elektron chiqindi va makulatura qayerda qabul qilinishini aniqlab, kerak bo'lsa
matnga aniq joy yoki boshqa amaliy yo'l qo'shing.

## Fayl talablari (TZ 9.2)

| Element | Talab |
|---|---|
| Video | MP4 (H.264), 1080×1920, 30–90 soniya, 20 MB gacha; ovozsiz, ekranda matnsiz |
| Video muqovasi | JPG yoki WebP, 1080×1920, 150 KB gacha |
| Loyiha / o'yin buyumi rasmi | WebP yoki PNG, 512×512, o'yin uchun shaffof fon, 100 KB gacha |

Hozircha o'yin buyumlarida emoji turadi; rasm tayyor bo'lsa, admin panelda «Rasm havolasi»
maydoniga qo'yiladi.

## Yurist tekshiruvi (TZ 11.4)

Maxfiylik siyosati va foydalanish shartlari ilovada «Qoralama» belgisi bilan turibdi
(`frontend/src/i18n/locales/*.json`, `privacy` va `terms` bo'limlari). Yurist tasdiqlagan
matn shu joylarga qo'yiladi va «Qoralama» belgisi olib tashlanadi.
