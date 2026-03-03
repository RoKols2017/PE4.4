Services
- nginx (edge): terminates TLS, проксирует на web контейнер.
- web (ассистент сайта): HTTP only внутри сети (например, :8000), наружу не торчит.
- bot (telegram): outbound only, без входящих портов (вебхуки необязательны; можно polling).
- postgres (storage): внутренняя БД для заявок и событий (`leads`, `lead_events`).
- (Опционально) certbot контейнер или внешний менеджмент сертификатов.

Networking
- Один docker network (bridge), где nginx видит web.
- bot в той же сети не обязателен, но удобно для общего .env/логики.

HTTPS strategy (выбери одно и зафиксируй)
- Вариант A (простой): Let’s Encrypt через certbot + webroot/standalone, сертификаты монтируются в nginx.
- Вариант B (инфра): сертификаты выдаёт внешний ingress (Traefik/Cloudflare), nginx только reverse proxy.

Observability
- Логи всех контейнеров в stdout.
- Корреляция: в Lead добавлять lead_id и прокидывать в логи.

Shared domain
- Единая библиотека в коде (валидации/нормализация/контракт репозитория) используется и ботом и сайтом (чтобы не разъехались правила).

ai-factory хорошо работает, когда архитектурные развилки (A/B) решены до /aif-plan full.
