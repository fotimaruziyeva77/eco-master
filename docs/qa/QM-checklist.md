# Qabul qilish mezonlari: tekshiruv ro'yxati (TZ 15)

Har bir mezon (QM-01 — QM-21) uchun quyida uchta narsa yozilgan:

- **Avtomatik** — qaysi test buni tekshiradi. Testlar har push'da GitHub Actions'da ishlaydi
  (`.github/workflows/ci.yml`), lokal ishga tushirish pastda.
- **Qo'lda** — haqiqiy telefon, haqiqiy bot yoki server kerak bo'lgan tekshiruvlar.
  ⚠️ belgisi bor qadamlarni testlar almashtira olmaydi: ular faqat qo'lda tekshiriladi.
- **Natija** — qabul paytida to'ldiriladi: o'tdi / o'tmadi, sana, kim tekshirdi.

Qo'lda tekshiruvlar sinov muhitida (staging) yoki ishga tushirishdan oldin production'da,
haqiqiy bot bilan bajariladi. Test foydalanuvchisi yaratilgandan keyin uni
«Ma'lumotlarimni o'chirish» orqali tozalash mumkin (QM-17).

## Avtomatik tekshiruvlarni ishga tushirish

```bash
cd backend && .venv/Scripts/python -m pytest && .venv/Scripts/ruff check .
cd frontend && npm run typecheck && npm test && npm run build && npm run size
```

Oxirgi to'liq ishga tushirish (2026-10-10): backend — 340 test, frontend — 51 test, hammasi
o'tdi; boshlang'ich JS — 125 KB (gzip), chegara 250 KB. Production stek (Docker Compose)
lokal smoke testdan o'tdi: migratsiyalar, xavfsizlik sarlavhalari, zaxira nusxa va tiklash.

Backend testlari `backend/tests/` papkasida, frontend testlari `frontend/src/**/*.test.ts`.
Yarim tun atrofidagi holatlar `test_midnight.py` da soatni almashtirib tekshiriladi
(TZ 13: «kun almashuvi, yarim tun atrofidagi holatlar»).

## Mezonlar

### QM-01. Onboarding 1 daqiqadan kam; tanishtiruvni o'tkazib yuborish; qayta ko'rsatilmaydi (8.1)

- **Avtomatik:** `test_onboarding_api.py` — `test_full_onboarding_flow`,
  `test_progress_is_resumed_and_never_goes_back`, `test_complete_requires_path_and_nickname`;
  `test_auth_api.py::test_second_login_returns_same_user_and_keeps_chosen_language`.
- **Qo'lda:** ⚠️ yangi hisob bilan (yoki ma'lumotlarni o'chirgandan keyin) sekundomer bilan:
  ochish → til → tanishtiruv («O'tkazib yuborish») → yo'l → taxallus → bosh sahifa.
  60 soniyadan kam bo'lishi kerak. Ilovani yopib qayta ochish → to'g'ri bosh sahifaga tushadi.
- **Natija:**

### QM-02. Telegram tili uz/ru/en bo'lsa — shu til, boshqasida — o'zbek tili (6)

- **Avtomatik:** `frontend/src/i18n/i18n.test.ts` — «pickLanguage (QM-02)» (uz, ru, en,
  ru-RU, en_US, kk, de, til yo'q); `test_auth_api.py` —
  `test_login_creates_user_with_telegram_language`, `test_unknown_telegram_language_defaults_to_uzbek`.
- **Qo'lda:** Telegram ilovasi rus tilida → Ekoustoz rus tilida ochiladi; Telegram nemis
  tilida → o'zbek tilida.
- **Natija:**

### QM-03. Band, odobsiz, qoidaga mos kelmaydigan taxallus qabul qilinmaydi (8.1)

- **Avtomatik:** `test_rules.py` — `test_invalid_nicknames`, `test_banned_nicknames`;
  `test_onboarding_api.py` — `test_bad_nicknames_are_rejected`,
  `test_nickname_is_unique_ignoring_case`; `test_admin_moderation.py::test_word_lists_apply_to_new_nicknames`
  (admin qo'shgan taqiqlangan so'zlar). Xato matnlari uch tilda (`onboarding.nicknameErrors.*`).
- **Qo'lda:** band taxallus, «admin», juda qisqa va taqiqlangan so'z bilan urinib ko'rish —
  xato xabari foydalanuvchi tilida va tushunarli.
- **Natija:**

### QM-04. Til almashtirilganda hamma matn yangi tilda; tarjima kaliti ko'rinmaydi (6)

- **Avtomatik:** `frontend/src/i18n/i18n.test.ts` — «locale files (QM-04)»: uch tilda kalitlar
  bir xil, bo'sh matn yo'q, ko'plik shakllari to'liq va **koddagi har bir `t("…")` kaliti
  fayllarda bor**; `test_i18n.py::test_every_bot_text_exists_in_all_languages` (bot matnlari);
  `test_content_v1.py::test_everything_in_three_languages` (kontent); uch tilsiz kontent
  nashr qilinmaydi (QM-14).
- **Qo'lda:** Profil → «Til / Language» → rus, keyin ingliz tili: barcha ekranlarni ko'zdan
  kechirish (bosh sahifa, o'rganish, loyiha, viktorina, o'yin, reyting, profil, o'qituvchilar).
- **Natija:**

### QM-05. initData'siz, soxta yoki eskirgan initData rad etiladi — 401 (11.1)

- **Avtomatik:** `test_security.py` — `test_tampered_user_is_rejected`,
  `test_other_bot_token_is_rejected`, `test_missing_hash_is_rejected`,
  `test_expired_init_data_is_rejected`, `test_future_auth_date_is_rejected`, sessiya tokeni
  testlari; `test_auth_api.py` — `test_forged_init_data_is_rejected`,
  `test_me_requires_a_valid_token`, `test_dev_login_helper_is_not_mounted_outside_dev`.
- **Qo'lda (server):** `curl -i https://<DOMAIN>/api/me` → `401`;
  `curl -i -X POST https://<DOMAIN>/api/auth/telegram -H "Content-Type: application/json" -d "{\"init_data\":\"x\"}"` → `401`.
- **Natija:**

### QM-06. «Bajardim» ikkinchi marta ball bermaydi; takroriy so'rov ham bir marta yoziladi (8.3, 11.1)

- **Avtomatik:** `test_content_api.py::test_project_done_awards_points_once` (bir xil
  `client_event_id` bilan qayta yuborish va yangi so'rov); `test_phase4_api.py::test_daily_task_once_per_day`;
  `frontend/src/outbox.test.ts` (qayta yuborishda o'sha ID ishlatiladi).
- **Qo'lda:** «Bajardim»ni tez-tez ikki marta bosish → ball bir marta qo'shiladi.
- **Natija:**

### QM-07. Viktorinada takroriy to'g'ri javob ball bermaydi; har javobdan keyin tushuntirish (8.4)

- **Avtomatik:** `test_games_api.py` — `test_quiz_points_only_for_first_correct_answer`,
  `test_wrong_quiz_answer`, `test_cannot_change_answer_after_seeing_it`,
  `test_quiz_round_does_not_leak_answers`; `test_content_v1.py::test_question_template`
  (har savolda uch tilda tushuntirish).
- **Qo'lda:** viktorinani ikki marta o'ynash — ikkinchi marta o'sha savollar uchun ball yo'q;
  har javobdan keyin tushuntirish chiqadi.
- **Natija:**

### QM-08. O'yindan kuniga 40 balldan ortiq yo'q; surish ilovani yopmaydi (8.4)

- **Avtomatik:** `test_games_api.py::test_game_daily_cap`,
  `test_midnight.py::test_game_limit_starts_again_at_midnight`. O'yinda sudrash yo'q — chiqindi
  bosish bilan tanlanadi; `frontend/src/telegram.ts` pastga surishni o'chiradi
  (`disableVerticalSwipes`, Telegram 7.7+).
- **Qo'lda:** ⚠️ Android va iOS'da o'yin paytida barmoq bilan pastga surish → ilova yopilmaydi.
- **Natija:**

### QM-09. Kunlik topshiriq Toshkent vaqti 00:00 da almashadi; 23:59 dagi bajarish shu kunga (8.5)

- **Avtomatik:** `test_midnight.py::test_task_done_at_23_59_counts_for_that_day` (23:59:30 da
  bajarilgan topshiriq yakshanbaga, 00:00 dan keyin — dushanbaning yangi topshirig'i);
  `test_rules.py::test_tashkent_day_boundary`.
- **Qo'lda:** shart emas.
- **Natija:**

### QM-10. 7 kun ketma-ket — 50 bonus ball va nishon; kun o'tkazilsa streak 0 (8.5, 8.6)

- **Avtomatik:** `test_phase4_api.py` — `test_seventh_day_gives_bonus_and_badge`,
  `test_missed_day_resets_streak`; `test_midnight.py::test_missed_day_resets_the_streak_at_midnight`.
- **Qo'lda:** shart emas.
- **Natija:**

### QM-11. Eslatma o'chirilgan yoki topshiriq bajarilgan bo'lsa yuborilmaydi; bloklaganga qayta yuborilmaydi (8.5)

- **Avtomatik:** `test_phase5.py` — `test_reminder_is_sent_once_after_the_chosen_time`,
  `test_reminder_is_skipped`, `test_no_reminders_in_quiet_hours`,
  `test_blocked_bot_turns_reminders_off`, `test_one_blocked_chat_does_not_stop_the_others`.
- **Qo'lda:** ⚠️ haqiqiy bot bilan: eslatma vaqtini bir necha daqiqa keyinga qo'yish → bitta
  xabar keladi; topshiriqni bajarib qo'yish → o'sha kuni eslatma kelmaydi; botni bloklash →
  `docker compose logs bot` da xatolar takrorlanmaydi.
- **Natija:**

### QM-12. Haftalik reyting dushanba 00:00 da noldan; top-100 dan tashqarida ham o'z o'rni; teng ballda avval yetgan yuqorida (8.7)

- **Avtomatik:** `test_phase4_api.py` — `test_leaderboard_order_and_ties`,
  `test_weekly_board_only_counts_this_week`, `test_own_rank_shown_outside_top_100`;
  `test_midnight.py::test_weekly_board_starts_from_zero_on_monday`.
- **Qo'lda:** shart emas.
- **Natija:**

### QM-13. Admin yashirgan yoki bloklagan foydalanuvchi reytingdan 5 daqiqa ichida yo'qoladi (8.7, 8.12)

- **Avtomatik:** `test_phase4_api.py::test_hidden_and_blocked_users_are_not_listed`;
  `test_admin_moderation.py` — `test_blocked_user_leaves_the_rating_at_once`,
  `test_hide_and_force_nickname_change`. Reyting keshlanmaydi — o'zgarish darhol ko'rinadi.
- **Qo'lda:** admin panelda test foydalanuvchini yashirish → ilovada reytingni yangilash.
- **Natija:**

### QM-14. Uch tilning birida matn bo'lmasa nashr qilinmaydi; 🟡/🔴 loyiha xavfsizlik matni va «amalda sinab ko'rildi» belgisisiz nashr qilinmaydi (8.12)

- **Avtomatik:** `test_admin_content.py` — `test_publish_needs_three_languages_safety_text_and_testing`,
  `test_published_item_stays_valid_and_keeps_its_slug`, `test_field_validation`;
  `test_content_v1.py::test_drafts_pass_the_publish_checks`.
- **Qo'lda:** admin panelda rus matni bo'sh qoralamani nashr qilishga urinish → rad etiladi
  va sababi ko'rsatiladi.
- **Natija:**

### QM-15. «PDF'ni chatga yuborish» — bot PDF'ni foydalanuvchi tilida 10 soniyada yuboradi (8.9)

- **Avtomatik:** `test_phase5.py` — `test_lesson_pdf_in_every_language`, `test_send_pdf_to_chat`,
  `test_send_pdf_without_bot`, `test_send_pdf_when_user_never_started_bot`.
- **Qo'lda:** ⚠️ haqiqiy bot bilan, uch tilda: tugmani bosish → 10 soniya ichida PDF chatga
  keladi; PDF ochiladi, kirill harflari va oʻ, gʻ to'g'ri ko'rinadi.
- **Natija:**

### QM-16. Ulashish tayyor xabar bilan chat tanlash oynasini ochadi; xabarda ilovani ochish tugmasi (8.11)

- **Avtomatik:** `test_phase5.py` — `test_share_prepares_telegram_message`,
  `test_inline_share_for_older_clients`, `test_inline_share_for_strangers`,
  `test_no_inline_query_without_inline_mode`, `test_share_texts`,
  `test_progress_share_never_brags_about_zeros`.
- **Qo'lda:** ⚠️ Android, iOS va Desktop'da: «Ulashish» → chat tanlash oynasi → yuborilgan
  xabarda tugma bor → tugma Ekoustoz'ni ochadi. Eski Telegram versiyalari uchun BotFather'da
  `/setinline` yoqilgan bo'lishi kerak.
- **Natija:**

### QM-17. «Ma'lumotlarimni o'chirish»dan keyin reytingda yo'q; qayta kirsa onboarding (8.8)

- **Avtomatik:** `test_phase4_api.py::test_delete_account`.
- **Qo'lda:** Profil → «Ma'lumotlarimni o'chirish» → «Ha, o'chirish» → ilovani qayta ochish →
  onboarding boshidan; reytingda eski taxallus yo'q.
- **Natija:**

### QM-18. Internet uzilganda tushunarli xabar; aloqa tiklangach harakat saqlanadi, ball bir marta (13)

- **Avtomatik:** `frontend/src/outbox.test.ts` — navbat saqlanadi, aloqa tiklanganda o'sha ID
  bilan qayta yuboriladi, yakuniy xatolarda (400/403/404/409/422) navbatdan olib tashlanadi,
  tarmoq xatosi, 401 va 5xx da qoladi; serverda takroriy so'rov ball bermaydi (QM-06).
- **Qo'lda:** ⚠️ telefonda samolyot rejimi → tepada «Internet yo'q…» xabari → loyihada
  «Bajardim» → «Saqlandi! Internet qaytganda ball qo'shiladi.» → samolyot rejimini o'chirish →
  «Aloqa tiklandi — saqlangan ishlaringiz yuborildi.», ball bir marta qo'shilgan. Xuddi shuni
  server to'xtatilganda ham tekshirish (`docker compose stop api`, keyin `start`).
- **Ma'lum cheklov:** oflayn saqlangan kunlik topshiriq yarim tundan keyin yetib borsa, server
  qabul qilgan kunga yoziladi.
- **Natija:**

### QM-19. Tezlik: birinchi ochilish 4G'da 3 s dan, 3G'da 5 s dan kam (13)

- **Avtomatik:** `npm run size` — boshlang'ich JS 250 KB (gzip) dan oshsa, CI va Docker yig'ish
  to'xtaydi (hozir 125 KB). Ekranlar va ru/en tarjimalari kerak bo'lganda yuklanadi; Caddy
  zstd/gzip bilan siqadi, `/assets/*` bir yilga keshlanadi.
- **Qo'lda:** ⚠️ production domenida: Chrome DevTools → Network → «Fast 4G» / «3G», keshsiz
  ochish → bosh sahifa ishlatishga tayyor bo'lguncha vaqt; takroriy ochish (keshdan) 1,5 s dan
  kam. Arzon Android telefonda (2–3 GB RAM) Telegram ichida ham o'lchash. API: so'rovlarning
  95% i 500 ms dan tez (TZ 13) — ishga tushgandan keyin bir hafta kuzatiladi.
- **Natija:** 4G: … s, 3G: … s, takroriy: … s

### QM-20. Barcha sinov qurilmalarida, yorug' va qorong'i mavzuda kritik xatosiz; kontrast WCAG AA (12, 13)

- **Avtomatik:** `frontend/src/theme.test.ts` — matn/fon juftliklari ikkala mavzuda kamida
  4.5:1 (WCAG AA). Ilovadagi xatolar `error` hodisasi sifatida yig'iladi (TZ 14) va admin
  panel statistikasida ko'rinadi.
- **Qo'lda:** ⚠️ quyidagi jadval bo'yicha asosiy ssenariy: onboarding → loyiha → «Bajardim» →
  viktorina → o'yin → kunlik topshiriq → reyting → profil → o'qituvchilar bo'limi.
- **Natija:** jadvalda.

| Qurilma (TZ 13) | Telegram versiyasi | Yorug' | Qorong'i | Izoh |
| --- | --- | --- | --- | --- |
| Android — eng yangi Telegram | | | | |
| Android — oldingi Telegram versiyasi | | | | |
| Android, 2–3 GB RAM (arzon telefon) | | | | |
| iOS — eng yangi versiya | | | | |
| iOS — oldingi versiya | | | | |
| Telegram Desktop (Windows) | | | | |
| Telegram Desktop (macOS) | | | | |
| Telegram Web (web.telegram.org) | | | | |

### QM-21. Oddiy brauzerda «Telegram'da ochish» sahifasi (5)

- **Avtomatik:** — (ilova initData bo'lmasa `OpenInTelegramScreen` ni ko'rsatadi).
- **Qo'lda:** `https://<DOMAIN>` ni Chrome'da ochish → «Ilovani Telegram'da oching» sahifasi;
  «Telegram'da ochish» tugmasi `t.me/<bot>/<app>` ga olib boradi.
- **Natija:**

## Bozor (9-faza, TZ'ga qo'shimcha)

TZ v0.2 da rasm yuklash va bozor 1-versiyaga kirmagan edi (11.3, 16-bo'limlar). Loyiha rahbari
2026-10-10 da qo'shishga qaror qildi: bozor TZ v0.3 ning 8.13-bo'limida yozilgan, quyidagi
mezonlar uning 15-bo'limiga kiritilgan. Rasm yuklash yurist tekshiruviga (11.4) kiritiladi.

### QM-22. E'lon moderator tasdiqlamaguncha hech kimga ko'rinmaydi

- **Avtomatik:** `test_market.py::test_new_listing_waits_for_a_moderator` (begona foydalanuvchi
  ko'rmaydi, bozor bo'sh, tasdiqlanmagan e'lonning rasmi ochiq havola bilan ham ochilmaydi);
  `test_changes_go_back_to_review`; `test_market_admin.py::test_editor_reviews_listings`.
- **Qo'lda:** ikki telefon: birida e'lon berish, ikkinchisida bozorda ko'rinmasligini tekshirish;
  admin tasdiqlagach paydo bo'lishi va muallifga bot xabari kelishi.
- **Natija:**

### QM-23. Rasmlarda joylashuv (GPS) va kamera ma'lumotlari saqlanmaydi

- **Avtomatik:** `test_market.py::test_photo_keeps_only_pixels`, `test_only_real_photos_are_accepted`,
  `test_photo_links_are_signed_and_expire`.
- **Qo'lda:** ⚠️ joylashuv yoqilgan telefonda suratga olib yuklash; admin panelda rasmni yuklab
  olib, EXIF ko'ruvchida GPS yo'qligini tekshirish.
- **Natija:**

### QM-24. Bolalar kontakt almashmaydi; buyum faqat topshirish joyida kod bilan beriladi

- **Avtomatik:** `test_market.py::test_contacts_and_rude_words_are_refused`,
  `test_handover_through_the_point` (ikki xil kod, noto'g'ri kod rad etiladi),
  `test_market_admin.py::test_codes_work_only_at_their_point`,
  `test_point_staff_see_only_their_desk`.
- **Qo'lda:** ⚠️ haqiqiy topshirish joyida xodim bilan to'liq aylanish: e'lon → «Olmoqchiman» →
  rozilik → egasi kod bilan olib keladi → oluvchi kod bilan olib ketadi; bot xabarlari keladi.
- **Natija:**

### QM-25. Shikoyat va moderator qarori

- **Avtomatik:** `test_market.py::test_reports_take_a_listing_down` (3 xil foydalanuvchi →
  yashiriladi), `test_market_admin.py::test_hiding_calls_off_a_handover`.
- **Qo'lda:** admin panelda qaytarish sababini tanlab, bolaga uning tilida tushunarli xabar
  borishini tekshirish.
- **Natija:**

### QM-26. Hisob o'chirilsa, e'lonlar va rasmlar o'chadi; boshlangan topshirish yakunlanadi

- **Avtomatik:** `test_market.py::test_deleting_the_account`, `test_handovers_expire`,
  `test_item_left_at_the_point_goes_to_the_next_one`, `test_loose_photos_are_removed`.
- **Qo'lda:** shart emas.
- **Natija:**

## Ishga tushirishdan oldin server tekshiruvlari

- [ ] `https://<DOMAIN>/api/health` → `{"status":"ok"}`; uptime monitoring shu manzilga ulangan.
- [ ] HTTPS sertifikati to'g'ri, `http://` → `https://` ga yo'naltiriladi.
- [ ] `curl -I https://<DOMAIN>/` da `Content-Security-Policy`, `Strict-Transport-Security`
      sarlavhalari bor; `/admin/` da `frame-ancestors 'none'`.
- [ ] `/api/docs` va `/api/dev/init-data` → 404 (production'da yopiq).
- [ ] Zaxira nusxa: `docker compose exec backup sh /usr/local/bin/backup.sh now`, keyin
      `sh deploy/restore-test.sh` → «Restore check passed».
- [ ] `deploy/backups` boshqa joyga ham nusxalanadi.
- [ ] Birinchi administrator yaratilgan, ikki bosqichli kirish (parol + kod) ishlaydi.
- [ ] Kontent (`seed --content`) jamoa tomonidan ko'rib chiqildi va admin panelda nashr qilindi
      (`docs/content/README.md`).
- [ ] BotFather: `/newapp` URL `https://<DOMAIN>`, `/setinline` yoqilgan.
- [ ] Bozor: kamida bitta topshirish joyi nashr qilingan, uning xodimiga «Topshirish joyi xodimi»
      hisobi ochilgan; moderatorlar navbati kuzatib boriladi.
- [ ] Loglarda shaxsiy ma'lumot yo'q: `docker compose logs api bot` da faqat ichki ID'lar.
