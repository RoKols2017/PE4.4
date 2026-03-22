Services
- caddy (edge): автоматически получает TLS-сертификаты, проксирует на web контейнер.
- web (ассистент сайта): HTTP only внутри сети (например, :8000), наружу не торчит.
- bot (telegram): outbound only, без входящих портов (вебхуки необязательны; можно polling).
- postgres (storage): внутренняя БД для заявок и событий (`leads`, `lead_events`).
- Caddy хранит ACME state в Docker volume (`caddy-data`) и публикует `80/443`.

Networking
- Один docker network (bridge), где caddy видит web.
- bot в той же сети не обязателен, но удобно для общего .env/логики.

HTTPS strategy
- Выбранный вариант: Caddy как edge с автоматическим Let's Encrypt для `CADDY_SITE_HOST`.
- Для первого выпуска сертификата домен должен резолвиться на VPS и порты `80/443` должны быть доступны снаружи.

Observability
- Логи всех контейнеров в stdout.
- Корреляция: в Lead добавлять lead_id и прокидывать в логи.

Shared domain
- Единая библиотека в коде (валидации/нормализация/контракт репозитория) используется и ботом и сайтом (чтобы не разъехались правила).

Runtime conversation boundary
- FSM и deterministic resolver управляют step transitions, draft mutation и persistence.
- `gpt-4o-mini` работает только через узкий JSON-контракт (`detected_intent`, `candidate_fields`, `needs_clarification`, `user_facing_message`).
- Candidate-поля от модели считаются hint'ами и проходят field-by-field validation before commit.
- При конфликте модели и валидатора источником истины остается валидатор.
- Если ответ модели пустой, битый или с недопустимым intent, используется deterministic fallback.

ai-factory хорошо работает, когда архитектурные развилки (A/B) решены до /aif-plan full.
