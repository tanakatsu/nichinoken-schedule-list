## nichinoken-schedule-list

Extract nichinoken schedules from pdf file using OCR and publish links for Google Calendar registration

### Preparation

- Google Cloud Document AI
    - Create a GCP project and activate Cloud Document AI API
    - Create a `Document OCR` processor
    - Create service account and download credential json file
- LINE notify
    - Go to [https://notify-bot.line.me/ja](https://notify-bot.line.me/ja) and login
    - Publish token
    - Choose talk room

### Get started

1. Create python virtual environment and install packages
    ```
    $ pip install -r requirements.txt
    ```
1. Copy `config.sample.yml` to `config.yml` and edit it
    - For OCR (Document AI), you need `project_id` and `location` and `processor_id` 
    - For LINE notify, you need `token`
1. Download nichinoken's schedule file from `MY NICHINOKEN` site
    - Login MY NICHINOKEN (`https://mynichinoken.jp`)
    - Go to `教室からのお知らせ` → `月間スケジュール`
    - You can download schedule files there
    - Or, you also can take a picture of handout by yourself
1. Set environment variable
    ```
    export GOOGLE_APPLICATION_CREDENTIALS="[credentialファイルへのパス]"
    ```
1. Run script
    ```
    $ python main.py downloaded_schedule_filename[スケジュールのpdfファイル] school_year[学年]
    ```
    You'll get messages in LINE as following.
    ```
    ■ 2024-05-19（日） ★学習力育成テスト・日特
    https://www.google.com/calendar/render?action=TEMPLATE&text=%E2%98%85%E5%AD%A6%E7%BF%92%E5%8A%9B%E8%82%B2%E6%88%90%E3%83%86%E3%82%B9%E3%83%88%E3%83%BB%E6%97%A5%E7%89%B9&details=&dates=20240519/20240519&sf=true&output=xml

    ■ 2024-05-20（月） ◆後日テスト 17:00 集合
    https://www.google.com/calendar/render?action=TEMPLATE&text=%E2%97%86%E5%BE%8C%E6%97%A5%E3%83%86%E3%82%B9%E3%83%88%2017%3A00%20%E9%9B%86%E5%90%88&details=&dates=20240520/20240520&sf=true&output=xml
    ```
1. Click urls and register events in your Google Calendar
