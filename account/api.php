<?php
// Запросы со страниц сайта: кто вошёл и сохранение заявки в кабинет
require __DIR__ . '/../app/bootstrap.php';
start_session();
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function reply(array $data, int $code = 200): void
{
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

// Без настроенной базы отвечаем ошибкой: скрипт сайта тогда спрячет кнопки кабинета
try {
    db();
} catch (Throwable $e) {
    reply(['ok' => false], 503);
}
$user = current_user();

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (!$user) {
        reply(['logged' => false]);
    }
    reply(['logged' => true, 'name' => $user['name'], 'balance' => balance((int) $user['id'])]);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !same_origin()) {
    reply(['ok' => false], 403);
}
if (!$user) {
    reply(['ok' => false, 'reason' => 'not_logged'], 401);
}

$text = trim(str_replace("\r", '', (string) ($_POST['text'] ?? '')));
$source = (string) ($_POST['source'] ?? '');
if (!in_array($source, ['request', 'lead', 'calc'], true) || $text === '' || mb_strlen($text) > 4000) {
    reply(['ok' => false], 400);
}
$uid = (int) $user['id'];

// Не больше 30 заявок в сутки и без дублей одной и той же заявки подряд
$st = db()->prepare('SELECT COUNT(*) FROM orders WHERE user_id = ? AND created_at > ?');
$st->execute([$uid, date('Y-m-d H:i:s', time() - 86400)]);
if ((int) $st->fetchColumn() >= 30) {
    reply(['ok' => false, 'reason' => 'limit'], 429);
}
$st = db()->prepare('SELECT id FROM orders WHERE user_id = ? AND text = ? AND created_at > ?');
$st->execute([$uid, $text, date('Y-m-d H:i:s', time() - 600)]);
if ($id = $st->fetchColumn()) {
    reply(['ok' => true, 'order' => (int) $id]);
}

db()->prepare('INSERT INTO orders (user_id, source, text, created_at) VALUES (?, ?, ?, ?)')
    ->execute([$uid, $source, $text, now()]);
reply(['ok' => true, 'order' => (int) db()->lastInsertId()]);
