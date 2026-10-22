<?php
// API для мобильного приложения. Тот же кабинет, что на сайте: те же клиенты, заявки и баллы.
// Вместо cookie приложение передаёт токен в заголовке X-Auth-Token (или Authorization: Bearer).
// Действие — в параметре ?a=, данные — JSON в теле запроса. Ответ всегда JSON: {"ok": true, ...}
// или {"ok": false, "error": "код", "message": "текст для клиента"}.
require __DIR__ . '/../app/bootstrap.php';
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

// Токен перестаёт действовать, если приложением не пользовались полгода
const TOKEN_TTL_DAYS = 180;

function reply(array $data, int $code = 200): void
{
    http_response_code($code);
    echo json_encode(['ok' => $code < 400] + $data, JSON_UNESCAPED_UNICODE);
    exit;
}

function fail(string $error, string $message, int $code = 400): void
{
    reply(['error' => $error, 'message' => $message], $code);
}

function input(): array
{
    static $data;
    if ($data === null) {
        $data = $_POST;
        if (stripos($_SERVER['CONTENT_TYPE'] ?? '', 'application/json') !== false) {
            $json = json_decode((string) file_get_contents('php://input'), true);
            $data = is_array($json) ? $json : [];
        }
    }
    return $data;
}

function str_in(string $key): string
{
    $v = input()[$key] ?? '';
    return is_scalar($v) ? trim((string) $v) : '';
}

function ensure_tokens_table(): void
{
    foreach (array_filter(array_map('trim', explode(';', file_get_contents(__DIR__ . '/../app/schema.sql')))) as $sql) {
        if (stripos($sql, 'CREATE TABLE IF NOT EXISTS app_tokens') !== false) {
            db()->exec($sql);
        }
    }
}

function issue_token(int $uid): string
{
    ensure_tokens_table();
    $token = bin2hex(random_bytes(32));
    $device = mb_substr(str_in('device') ?: (string) ($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 100);
    db()->prepare('INSERT INTO app_tokens (user_id, token_hash, device, created_at, last_used_at) VALUES (?, ?, ?, ?, ?)')
        ->execute([$uid, hash('sha256', $token), $device, now(), now()]);
    return $token;
}

function request_token(): string
{
    $t = $_SERVER['HTTP_X_AUTH_TOKEN'] ?? '';
    if ($t === '') {
        $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? ($_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '');
        if (preg_match('/^Bearer\s+(\S+)$/i', $auth, $m)) {
            $t = $m[1];
        }
    }
    return preg_match('/^[a-f0-9]{64}$/', $t) ? $t : '';
}

function token_user(): ?array
{
    $token = request_token();
    if ($token === '') {
        return null;
    }
    try {
        $st = db()->prepare('SELECT t.id AS token_id, t.last_used_at, u.id, u.phone, u.name, u.created_at
            FROM app_tokens t JOIN users u ON u.id = t.user_id WHERE t.token_hash = ?');
        $st->execute([hash('sha256', $token)]);
        $row = $st->fetch();
    } catch (PDOException $e) {
        return null; // таблицы токенов ещё нет — значит, никто не входил
    }
    if (!$row) {
        return null;
    }
    if (strtotime($row['last_used_at']) < time() - TOKEN_TTL_DAYS * 86400) {
        db()->prepare('DELETE FROM app_tokens WHERE id = ?')->execute([$row['token_id']]);
        return null;
    }
    // Отметку об использовании обновляем не чаще раза в час
    if (strtotime($row['last_used_at']) < time() - 3600) {
        db()->prepare('UPDATE app_tokens SET last_used_at = ? WHERE id = ?')->execute([now(), $row['token_id']]);
    }
    return $row;
}

function require_token_user(): array
{
    $user = token_user();
    if (!$user) {
        fail('not_logged', 'Войдите в личный кабинет.', 401);
    }
    return $user;
}

function user_json(array $user): array
{
    $uid = (int) $user['id'];
    return [
        'id' => $uid,
        'name' => $user['name'],
        'phone' => $user['phone'],
        'phone_formatted' => format_phone($user['phone']),
        'balance' => balance($uid),
        'created_at' => $user['created_at'],
    ];
}

function order_json(array $o): array
{
    return [
        'id' => (int) $o['id'],
        'source' => $o['source'],
        'text' => $o['text'],
        'status' => $o['status'],
        'want_redeem' => (bool) $o['want_redeem'],
        'amount' => $o['amount'] === null ? null : (int) $o['amount'],
        'points_used' => (int) $o['points_used'],
        'cashback' => (int) $o['cashback'],
        'created_at' => $o['created_at'],
        'paid_at' => $o['paid_at'],
    ];
}

try {
    db();
} catch (Throwable $e) {
    fail('unavailable', 'Кабинет временно недоступен. Попробуйте позже.', 503);
}

$action = (string) ($_GET['a'] ?? '');
$method = $_SERVER['REQUEST_METHOD'];
$reads = ['config', 'me', 'orders', 'points'];
if (in_array($action, $reads, true) ? $method !== 'GET' : $method !== 'POST') {
    fail('method', 'Неверный метод запроса.', 405);
}

switch ($action) {
    // Правила программы — приложение не держит их у себя, а берёт с сервера
    case 'config':
        $c = config();
        reply([
            'cashback_percent' => percent_bp('cashback_percent') / 100,
            'max_redeem_percent' => percent_bp('max_redeem_percent') / 100,
            'whatsapp' => (string) $c['whatsapp'],
            'rules_url' => 'https://kttron.kz/account/rules.php',
        ]);

    case 'login':
        $raw = str_in('phone');
        $phone = normalize_phone($raw) ?? substr(preg_replace('/\D+/', '', $raw), 0, 15);
        if (too_many_attempts('user', $phone)) {
            fail('too_many', 'Слишком много попыток. Подождите 15 минут.', 429);
        }
        $st = db()->prepare('SELECT id, phone, name, created_at, password_hash FROM users WHERE phone = ?');
        $st->execute([$phone]);
        $row = $st->fetch();
        $password = (string) (input()['password'] ?? '');
        if (!$row || !password_verify($password, $row['password_hash'])) {
            record_failed_attempt('user', $phone);
            fail('bad_login', 'Неверный телефон или пароль.', 401);
        }
        clear_attempts('user', $phone);
        if (password_needs_rehash($row['password_hash'], PASSWORD_DEFAULT)) {
            db()->prepare('UPDATE users SET password_hash = ? WHERE id = ?')
                ->execute([password_hash($password, PASSWORD_DEFAULT), $row['id']]);
        }
        reply(['token' => issue_token((int) $row['id']), 'user' => user_json($row)]);

    case 'register':
        $name = str_in('name');
        $phone = normalize_phone(str_in('phone'));
        $password = (string) (input()['password'] ?? '');
        if ($name === '' || mb_strlen($name) > 100) {
            fail('name', 'Укажите имя.');
        }
        if (!$phone) {
            fail('phone', 'Укажите телефон полностью, например +7 777 123-45-67.');
        }
        if (strlen($password) < 8) {
            fail('password', 'Пароль — не короче 8 символов.');
        }
        if (empty(input()['consent'])) {
            fail('consent', 'Нужно согласие на обработку персональных данных и с правилами кэшбэка.');
        }
        // Защита от перебора номеров: после 5 попыток занять чужой номер — пауза 15 минут
        if (too_many_attempts('reg', $phone)) {
            fail('too_many', 'Слишком много попыток. Подождите 15 минут.', 429);
        }
        $st = db()->prepare('SELECT id FROM users WHERE phone = ?');
        $st->execute([$phone]);
        if ($st->fetch()) {
            record_failed_attempt('reg', $phone);
            fail('phone_taken', 'Этот номер уже зарегистрирован. Войдите или попросите менеджера сбросить пароль.', 409);
        }
        db()->prepare('INSERT INTO users (phone, name, password_hash, consent_at, created_at) VALUES (?, ?, ?, ?, ?)')
            ->execute([$phone, $name, password_hash($password, PASSWORD_DEFAULT), now(), now()]);
        $uid = (int) db()->lastInsertId();
        reply(['token' => issue_token($uid), 'user' => user_json(['id' => $uid, 'phone' => $phone, 'name' => $name, 'created_at' => now()])]);

    case 'logout':
        $user = require_token_user();
        db()->prepare('DELETE FROM app_tokens WHERE id = ?')->execute([$user['token_id']]);
        reply([]);

    case 'me':
        reply(['user' => user_json(require_token_user())]);

    case 'orders':
        $user = require_token_user();
        $st = db()->prepare('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 100');
        $st->execute([$user['id']]);
        reply(['orders' => array_map('order_json', $st->fetchAll())]);

    case 'points':
        $user = require_token_user();
        $st = db()->prepare('SELECT id, order_id, amount, kind, note, created_at FROM points WHERE user_id = ? ORDER BY id DESC LIMIT 100');
        $st->execute([$user['id']]);
        $moves = array_map(fn ($m) => [
            'id' => (int) $m['id'],
            'order_id' => $m['order_id'] === null ? null : (int) $m['order_id'],
            'amount' => (int) $m['amount'],
            'kind' => $m['kind'],
            'note' => $m['note'],
            'created_at' => $m['created_at'],
        ], $st->fetchAll());
        reply(['balance' => balance((int) $user['id']), 'points' => $moves]);

    // Заявка из приложения — те же правила, что у заявок с сайта (account/api.php)
    case 'order':
        $user = require_token_user();
        $uid = (int) $user['id'];
        $text = trim(str_replace("\r", '', str_in('text')));
        $source = str_in('source') ?: 'request';
        if (!in_array($source, ['request', 'lead', 'calc'], true) || $text === '' || mb_strlen($text) > 4000) {
            fail('bad_order', 'Заявка пустая или слишком длинная.');
        }
        $st = db()->prepare('SELECT COUNT(*) FROM orders WHERE user_id = ? AND created_at > ?');
        $st->execute([$uid, date('Y-m-d H:i:s', time() - 86400)]);
        if ((int) $st->fetchColumn() >= 30) {
            fail('limit', 'Не больше 30 заявок в сутки. Напишите менеджеру в WhatsApp.', 429);
        }
        $st = db()->prepare('SELECT id FROM orders WHERE user_id = ? AND text = ? AND created_at > ?');
        $st->execute([$uid, $text, date('Y-m-d H:i:s', time() - 600)]);
        if ($id = $st->fetchColumn()) {
            reply(['order' => (int) $id]);
        }
        $want = empty(input()['want_redeem']) ? 0 : 1;
        db()->prepare('INSERT INTO orders (user_id, source, text, want_redeem, created_at) VALUES (?, ?, ?, ?, ?)')
            ->execute([$uid, $source, $text, $want, now()]);
        reply(['order' => (int) db()->lastInsertId()]);

    case 'redeem':
        $user = require_token_user();
        $want = empty(input()['want']) ? 0 : 1;
        $st = db()->prepare("UPDATE orders SET want_redeem = ? WHERE id = ? AND user_id = ? AND status = 'new'");
        $st->execute([$want, (int) (input()['order'] ?? 0), $user['id']]);
        $st = db()->prepare("SELECT * FROM orders WHERE id = ? AND user_id = ?");
        $st->execute([(int) (input()['order'] ?? 0), $user['id']]);
        $o = $st->fetch();
        if (!$o) {
            fail('not_found', 'Заявка не найдена.', 404);
        }
        reply(['order' => order_json($o)]);

    case 'password':
        $user = require_token_user();
        $st = db()->prepare('SELECT password_hash FROM users WHERE id = ?');
        $st->execute([$user['id']]);
        $new = (string) (input()['new'] ?? '');
        if (!password_verify((string) (input()['old'] ?? ''), (string) $st->fetchColumn())) {
            fail('bad_password', 'Текущий пароль указан неверно.');
        }
        if (strlen($new) < 8) {
            fail('password', 'Новый пароль — не короче 8 символов.');
        }
        db()->prepare('UPDATE users SET password_hash = ? WHERE id = ?')
            ->execute([password_hash($new, PASSWORD_DEFAULT), $user['id']]);
        // Выходим на остальных устройствах, текущее остаётся
        db()->prepare('DELETE FROM app_tokens WHERE user_id = ? AND id <> ?')->execute([$user['id'], $user['token_id']]);
        reply([]);

    // Удаление кабинета прямо из приложения — обязательное требование App Store и Google Play.
    // Заявки и движение баллов остаются для учёта, но больше не связаны с телефоном и именем.
    case 'delete':
        $user = require_token_user();
        $st = db()->prepare('SELECT password_hash FROM users WHERE id = ?');
        $st->execute([$user['id']]);
        if (!password_verify((string) (input()['password'] ?? ''), (string) $st->fetchColumn())) {
            fail('bad_password', 'Пароль указан неверно.');
        }
        $uid = (int) $user['id'];
        db()->prepare('DELETE FROM app_tokens WHERE user_id = ?')->execute([$uid]);
        db()->prepare("UPDATE users SET phone = ?, name = 'Кабинет удалён', password_hash = ? WHERE id = ?")
            ->execute(['del' . $uid, password_hash(bin2hex(random_bytes(16)), PASSWORD_DEFAULT), $uid]);
        reply([]);

    default:
        fail('unknown', 'Неизвестное действие.', 404);
}
