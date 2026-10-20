<?php
// Общее ядро личного кабинета и админки: настройки, база, сессии, защита.
declare(strict_types=1);

date_default_timezone_set('Asia/Almaty');

function config(): array
{
    static $config;
    if ($config === null) {
        $file = __DIR__ . '/config.php';
        if (!is_file($file)) {
            http_response_code(500);
            exit('Кабинет не настроен: нет файла app/config.php (см. app/config.example.php).');
        }
        $config = require $file;
    }
    return $config;
}

function db(): PDO
{
    static $pdo;
    if ($pdo === null) {
        $c = config();
        $pdo = new PDO(
            'mysql:host=' . $c['db_host'] . ';dbname=' . $c['db_name'] . ';charset=utf8mb4',
            $c['db_user'],
            $c['db_pass'],
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]
        );
        $pdo->exec("SET time_zone = '+05:00'");
    }
    return $pdo;
}

function now(): string
{
    return date('Y-m-d H:i:s');
}

function h(?string $s): string
{
    return htmlspecialchars((string) $s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function redirect(string $path): void
{
    header('Location: ' . $path, true, 303);
    exit;
}

// ---------- Сессия и защита форм ----------

function start_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    $https = ($_SERVER['HTTPS'] ?? '') !== '' && $_SERVER['HTTPS'] !== 'off';
    session_name('KTSESS');
    session_set_cookie_params([
        'lifetime' => 60 * 60 * 24 * 30,
        'path' => '/',
        'secure' => $https,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    ini_set('session.use_strict_mode', '1');
    ini_set('session.gc_maxlifetime', (string) (60 * 60 * 24 * 30));
    session_start();
}

function csrf_token(): string
{
    start_session();
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

function csrf_field(): string
{
    return '<input type="hidden" name="_csrf" value="' . h(csrf_token()) . '">';
}

// Все POST-формы проверяют токен: чужой сайт не сможет отправить форму от имени клиента
function require_post_csrf(): void
{
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        return;
    }
    $token = $_POST['_csrf'] ?? '';
    if (!is_string($token) || !hash_equals(csrf_token(), $token)) {
        http_response_code(400);
        exit('Форма устарела. Обновите страницу и попробуйте ещё раз.');
    }
}

// Для запросов из скриптов сайта: принимаем только со своего домена
function same_origin(): bool
{
    $host = $_SERVER['HTTP_HOST'] ?? '';
    $origin = $_SERVER['HTTP_ORIGIN'] ?? ($_SERVER['HTTP_REFERER'] ?? '');
    return $host !== '' && parse_url($origin, PHP_URL_HOST) === parse_url('//' . $host, PHP_URL_HOST);
}

function client_ip(): string
{
    return substr($_SERVER['REMOTE_ADDR'] ?? '', 0, 45);
}

// ---------- Защита от подбора пароля ----------

function too_many_attempts(string $scope, string $login): bool
{
    $since = date('Y-m-d H:i:s', time() - 15 * 60);
    $st = db()->prepare('SELECT COUNT(*) FROM login_attempts WHERE scope = ? AND login = ? AND created_at > ?');
    $st->execute([$scope, $login, $since]);
    if ((int) $st->fetchColumn() >= 5) {
        return true;
    }
    $st = db()->prepare('SELECT COUNT(*) FROM login_attempts WHERE ip = ? AND created_at > ?');
    $st->execute([client_ip(), $since]);
    return (int) $st->fetchColumn() >= 30;
}

function record_failed_attempt(string $scope, string $login): void
{
    db()->prepare('INSERT INTO login_attempts (scope, login, ip, created_at) VALUES (?, ?, ?, ?)')
        ->execute([$scope, $login, client_ip(), now()]);
    db()->exec("DELETE FROM login_attempts WHERE created_at < '" . date('Y-m-d H:i:s', time() - 86400) . "'");
}

function clear_attempts(string $scope, string $login): void
{
    db()->prepare('DELETE FROM login_attempts WHERE scope = ? AND login = ?')->execute([$scope, $login]);
}

// ---------- Телефоны, деньги ----------

// Храним только цифры с кодом страны: 77751810595
function normalize_phone(string $raw): ?string
{
    $d = preg_replace('/\D+/', '', $raw);
    if (strlen($d) === 11 && $d[0] === '8') {
        $d = '7' . substr($d, 1);
    } elseif (strlen($d) === 10 && $d[0] === '7') {
        $d = '7' . $d;
    }
    return preg_match('/^\d{10,15}$/', $d) ? $d : null;
}

function format_phone(string $d): string
{
    if (strlen($d) === 11 && $d[0] === '7') {
        return sprintf('+7 %s %s-%s-%s', substr($d, 1, 3), substr($d, 4, 3), substr($d, 7, 2), substr($d, 9, 2));
    }
    return '+' . $d;
}

function money(int $n): string
{
    return number_format($n, 0, ',', ' ') . ' ₸';
}

function points_word(int $n): string
{
    $n = abs($n) % 100;
    $m = $n % 10;
    if ($n > 10 && $n < 20) return 'баллов';
    if ($m === 1) return 'балл';
    if ($m >= 2 && $m <= 4) return 'балла';
    return 'баллов';
}

// ---------- Клиенты и администраторы ----------

function current_user(): ?array
{
    start_session();
    if (empty($_SESSION['uid'])) {
        return null;
    }
    $st = db()->prepare('SELECT id, phone, name, created_at FROM users WHERE id = ?');
    $st->execute([$_SESSION['uid']]);
    return $st->fetch() ?: null;
}

function require_user(): array
{
    $user = current_user();
    if (!$user) {
        redirect('/account/login.php');
    }
    return $user;
}

function current_admin(): ?array
{
    start_session();
    if (empty($_SESSION['aid'])) {
        return null;
    }
    $st = db()->prepare('SELECT id, login FROM admins WHERE id = ?');
    $st->execute([$_SESSION['aid']]);
    return $st->fetch() ?: null;
}

function require_admin(): array
{
    $admin = current_admin();
    if (!$admin) {
        redirect('/admin/login.php');
    }
    return $admin;
}

function login_session(string $key, int $id): void
{
    start_session();
    session_regenerate_id(true);
    $_SESSION[$key] = $id;
}

function balance(int $userId): int
{
    $st = db()->prepare('SELECT COALESCE(SUM(amount), 0) FROM points WHERE user_id = ?');
    $st->execute([$userId]);
    return (int) $st->fetchColumn();
}

function flash(?string $message = null): ?string
{
    start_session();
    if ($message !== null) {
        $_SESSION['flash'] = $message;
        return null;
    }
    $m = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);
    return $m;
}

// ---------- Оформление страниц ----------

function page_start(string $title, string $area = 'account'): void
{
    header('Content-Type: text/html; charset=utf-8');
    header('X-Frame-Options: DENY');
    header('Referrer-Policy: same-origin');
    header('Cache-Control: no-store');
    $home = $area === 'admin' ? '/admin/' : '/account/';
    $label = $area === 'admin' ? 'Админка' : 'Личный кабинет';
    $msg = flash();
    echo '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        . '<meta name="viewport" content="width=device-width, initial-scale=1">'
        . '<meta name="robots" content="noindex, nofollow">'
        . '<title>' . h($title) . ' — КТ ТРОН Казахстан</title>'
        . '<link rel="icon" href="/favicon.ico" sizes="48x48">'
        . '<link rel="stylesheet" href="/assets/main-BRCBiG-u.css">'
        . '<link rel="stylesheet" href="/assets/material.css">'
        . '<link rel="stylesheet" href="/assets/account.css">'
        . '</head><body class="acc">'
        . '<header class="acc-top"><div class="shell acc-top-in">'
        . '<a class="acc-brand" href="/">КТ ТРОН <span>Казахстан</span></a>'
        . '<a class="acc-area" href="' . $home . '">' . $label . '</a>'
        . '</div></header><main class="shell acc-main">';
    if ($msg) {
        echo '<p class="acc-flash" role="status">' . h($msg) . '</p>';
    }
}

function page_end(): void
{
    echo '</main><footer class="acc-foot"><div class="shell">'
        . '<a href="/">На сайт</a> · <a href="/account/rules.php">Правила кэшбэка</a>'
        . '</div></footer></body></html>';
}
