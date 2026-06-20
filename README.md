# Facebook Ads → Telegram күнделікті есеп боты

Бұл бот күн сайын Facebook Ads Manager-ден статистиканы алып, Telegram
тобыңызға автоматты жібереді. Хостинг (сервер) керек емес — GitHub Actions
тегін есебінде жұмыс істейді.

## 1-қадам: Telegram бот жасау

1. Telegram-да **@BotFather**-ге жазыңыз.
2. `/newbot` командасын жіберіп, ботқа атау беріңіз.
3. BotFather сізге **бот токенін** береді (мысалы:
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`). Сақтап қойыңыз.
4. Сол ботты статистика жіберілетін Telegram тобыңызға қосыңыз.
5. Топта ботқа **админ құқығын** беріңіз (хабарлама жіберу үшін).
6. Топтың `chat_id`-ін табу үшін:
   - Топта кез келген хабарлама жазыңыз (мысалы "сәлем").
   - Браузерде мына сілтемені ашыңыз (TOKEN орнына өз токеніңізді қойыңыз):
     `https://api.telegram.org/botTOKEN/getUpdates`
   - Жауаптан `"chat":{"id": -1001234567890, ...}` дегенді табасыз.
     Бұл теріс сан — сіздің `TELEGRAM_CHAT_ID`-іңіз.

## 2-қадам: Facebook Marketing API баптау

1. [developers.facebook.com](https://developers.facebook.com) сайтында
   жаңа App жасаңыз (түрі — **Business**).
2. App-қа **Marketing API** өнімін қосыңыз.
3. [business.facebook.com](https://business.facebook.com) → **Business
   Settings → Users → System Users** бөлімінде жаңа System User жасаңыз.
4. Сол System User-ге **Ad Accounts** бөлімінен өз Ad Account-ыңызды
   қосып, рұқсат беріңіз (кем дегенде **ads_read**).
5. Сол жерден **Generate New Token** басып, App-ыңызды таңдап,
   `ads_read` рұқсатын белгілеп, токен жасаңыз. Бұл — `FB_ACCESS_TOKEN`.
   (System User токені әдетте мерзімсіз, қолмен өшіргенше жұмыс істейді.)
6. Ads Manager-ден **Ad Account ID**-ні көшіріп алыңыз, алдына `act_`
   қосыңыз (мысалы: `act_1234567890`). Бұл — `FB_AD_ACCOUNT_ID`.

## 3-қадам: GitHub репозиторий жасау

1. [github.com](https://github.com) тіркелгіңіз болмаса, тегін тіркеліңіз.
2. Жаңа **private** репозиторий жасаңыз (мысалы `fb-telegram-report`).
3. Осы папкадағы файлдарды (fb_telegram_report.py, requirements.txt,
   .github/workflows/daily_report.yml) сол репозиторийге жүктеңіз.
4. Репозиторийде **Settings → Secrets and variables → Actions →
   New repository secret** бөліміне барып, мына 4 secret-ті қосыңыз:
   - `FB_ACCESS_TOKEN`
   - `FB_AD_ACCOUNT_ID`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

   (Бұл деректер репозиторийде жасырын сақталады, ешкім көрмейді.)

## 4-қадам: Тестілеу

1. Репозиторийдің **Actions** бөліміне өтіңіз.
2. "Daily Facebook Ads Report" workflow-ын ашып, **Run workflow**
   батырмасын басыңыз — бұл скриптті қазір қолмен іске қосады.
3. Telegram тобыңызға хабарлама келуі керек. Қате болса, Actions
   логында (run-ды ашып) себебін көресіз.

Бәрі дұрыс болса, скрипт енді **әр күні таңғы 09:00-де (Алматы/Ақтау
уақыты бойынша)** автоматты іске қосылады. Уақытты өзгерту үшін
`.github/workflows/daily_report.yml` ішіндегі `cron` жолын өзгертіңіз.

## Маңызды ескерту: "Лид" саны туралы

Facebook кампанияңыздың мақсатына (objective) байланысты "лид" әртүрлі
есептеледі:

- Егер кампания **Messenger/WhatsApp-та хабарласу** үшін болса —
  скрипт дұрыс жұмыс істейді (`messaging_conversation_started_7d`).
- Егер кампания **Lead Forms (Instant Forms)** арқылы болса — скрипт
  те қамтиды (`lead`, `leadgen.other`).
- Егер сан дұрыс шықпаса, `fb_telegram_report.py` файлындағы
  `LEAD_ACTION_TYPES` тізіміне нақты action_type атауын қосу керек
  болуы мүмкін — ол үшін Ads Manager-де "Breakdown → Conversion" арқылы
  нақты атауды тексеруге болады, немесе маған хабарласыңыз, бірге
  тексеріп көрейік.

## Бір реттік тест (локальді компьютерде, GitHub-сыз)

```bash
pip install -r requirements.txt

export FB_ACCESS_TOKEN="..."
export FB_AD_ACCOUNT_ID="act_..."
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."

python fb_telegram_report.py
```
