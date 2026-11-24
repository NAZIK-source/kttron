<?php
// Заявка с сайта (окно «Заявка на техническое решение», assets/kt-lead.js) → письмо на info@kttron.kz с файлами.
// Заявки нигде не хранятся: только письмо. Ответ — JSON {ok, error}.
declare(strict_types=1);

const LEAD_TO = 'info@kttron.kz';
const LEAD_FROM = 'info@kttron.kz';
const MAX_FILES = 5;
const MAX_TOTAL = 15 * 1024 * 1024; // письмо с вложениями должно пройти лимит почтового сервера (~25 МБ)
const ALLOWED = ['jpg', 'jpeg', 'png', 'webp', 'heic', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'dwg', 'zip'];
const MIME = ['jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'png' => 'image/png', 'webp' => 'image/webp', 'pdf' => 'application/pdf'];
const RATE_LIMIT = 5;      // заявок с одного IP
const RATE_WINDOW = 3600;  // за час

header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex');

function out(bool $ok, string $error = ''): void
{
    if (!$ok) {
        http_response_code(400);
    }
    echo json_encode(['ok' => $ok, 'error' => $error], JSON_UNESCAPED_UNICODE);
    exit;
}

function field(string $name, int $max): string
{
    $v = trim((string) ($_POST[$name] ?? ''));
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v) ?? '';
    return mb_substr($v, 0, $max);
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    out(false, 'method');
}

// Файлы больше post_max_size: PHP отдаёт пустой $_POST
if (empty($_POST) && (int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {
    out(false, 'too_big');
}

// Ловушки для ботов: скрытое поле и слишком быстрая отправка (форма открыта меньше 3 секунд)
if (field('website', 200) !== '') {
    out(true);
}
$opened = (int) ($_POST['t'] ?? 0);
if ($opened > 0 && time() - intdiv($opened, 1000) < 3) {
    out(true);
}

// Не больше RATE_LIMIT заявок с одного IP за RATE_WINDOW
$ip = (string) ($_SERVER['REMOTE_ADDR'] ?? '');
$rateFile = sys_get_temp_dir() . '/kt-lead-' . hash('sha256', $ip . __FILE__);
$hits = array_filter(
    is_file($rateFile) ? array_map('intval', explode(',', (string) file_get_contents($rateFile))) : [],
    static fn (int $t): bool => $t > time() - RATE_WINDOW
);
if (count($hits) >= RATE_LIMIT) {
    out(false, 'rate');
}

$name = field('name', 100);
$phone = field('phone', 30);
$city = field('city', 100);
$message = field('message', 3000);
$page = field('page', 300);
$lang = field('lang', 5);
$digits = preg_replace('/\D+/', '', $phone) ?? '';

if (mb_strlen($name) < 2) {
    out(false, 'name');
}
if (strlen($digits) < 10 || strlen($digits) > 15) {
    out(false, 'phone');
}
if (($_POST['consent'] ?? '') !== '1') {
    out(false, 'consent');
}

// Файлы
$files = [];
$total = 0;
if (!empty($_FILES['files']) && is_array($_FILES['files']['name'])) {
    foreach ($_FILES['files']['name'] as $i => $orig) {
        $err = $_FILES['files']['error'][$i];
        if ($err === UPLOAD_ERR_NO_FILE) {
            continue;
        }
        if ($err === UPLOAD_ERR_INI_SIZE || $err === UPLOAD_ERR_FORM_SIZE) {
            out(false, 'too_big');
        }
        if ($err !== UPLOAD_ERR_OK || !is_uploaded_file($_FILES['files']['tmp_name'][$i])) {
            out(false, 'file');
        }
        $ext = strtolower(pathinfo((string) $orig, PATHINFO_EXTENSION));
        if (!in_array($ext, ALLOWED, true)) {
            out(false, 'file_type');
        }
        $size = (int) $_FILES['files']['size'][$i];
        $total += $size;
        if (count($files) >= MAX_FILES) {
            out(false, 'file_count');
        }
        if ($total > MAX_TOTAL) {
            out(false, 'too_big');
        }
        $safe = preg_replace('/[^\p{L}\p{N}._ -]+/u', '_', basename((string) $orig)) ?: ('file.' . $ext);
        $files[] = ['name' => mb_substr($safe, 0, 120), 'path' => $_FILES['files']['tmp_name'][$i],
            'type' => MIME[$ext] ?? 'application/octet-stream'];
    }
}

// Письмо
$when = (new DateTime('now', new DateTimeZone('Asia/Almaty')))->format('d.m.Y H:i');
$lines = [
    'Заявка на техническое решение с сайта kttron.kz',
    '',
    'Имя: ' . $name,
    'Телефон: ' . $phone,
    'WhatsApp: https://wa.me/' . $digits,
    'Город: ' . ($city !== '' ? $city : '—'),
    '',
    'Описание объекта:',
    $message !== '' ? $message : '—',
    '',
    'Файлы: ' . ($files ? implode(', ', array_column($files, 'name')) : 'нет'),
    '',
    'Страница: ' . ($page !== '' ? $page : '—') . ($lang !== '' ? ' (' . $lang . ')' : ''),
    'Время: ' . $when . ' (Алматы)',
    'IP: ' . $ip,
];
$text = implode("\r\n", $lines);

$enc = static fn (string $s): string => '=?UTF-8?B?' . base64_encode($s) . '?=';
$subject = $enc('Заявка на техническое решение — ' . $name . ', ' . $phone);
$boundary = 'kt' . bin2hex(random_bytes(12));
$headers = [
    'From: ' . $enc('Сайт КТ ТРОН') . ' <' . LEAD_FROM . '>',
    'MIME-Version: 1.0',
    'Content-Type: multipart/mixed; boundary="' . $boundary . '"',
];
$body = "--$boundary\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n"
    . chunk_split(base64_encode($text)) . "\r\n";
foreach ($files as $f) {
    $data = (string) file_get_contents($f['path']);
    $body .= "--$boundary\r\nContent-Type: " . $f['type'] . "; name=\"" . $enc($f['name']) . "\"\r\n"
        . "Content-Transfer-Encoding: base64\r\nContent-Disposition: attachment; filename=\"" . $enc($f['name']) . "\"\r\n\r\n"
        . chunk_split(base64_encode($data)) . "\r\n";
}
$body .= "--$boundary--\r\n";

if (!mail(LEAD_TO, $subject, $body, implode("\r\n", $headers), '-f' . LEAD_FROM)) {
    error_log('kttron zayavka: mail() failed for ' . $phone);
    out(false, 'send');
}

$hits[] = time();
@file_put_contents($rateFile, implode(',', $hits), LOCK_EX);
out(true);
