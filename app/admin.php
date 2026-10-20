<?php
// Общие функции админки
require __DIR__ . '/bootstrap.php';

function admin_page(string $title): array
{
    start_session();
    require_post_csrf();
    $admin = require_admin();
    page_start($title, 'admin');
    echo '<nav class="acc-nav">'
        . '<a href="/admin/">Заявки</a><a href="/admin/clients.php">Клиенты</a><a href="/admin/admins.php">Администраторы</a>'
        . '<form method="post" action="/admin/logout.php">' . csrf_field()
        . '<button type="submit">Выйти (' . h($admin['login']) . ')</button></form></nav>';
    return $admin;
}

function order_status_label(string $s): string
{
    return ['new' => 'Новая', 'paid' => 'Оплачена', 'cancelled' => 'Отменена'][$s] ?? $s;
}

function max_redeem(int $amount, int $balance): int
{
    return max(0, min($balance, intdiv($amount * (int) config()['max_redeem_percent'], 100)));
}

// Отметить заявку оплаченной: списать баллы и начислить кэшбэк. Возвращает текст ошибки или null.
function mark_paid(int $orderId, int $amount, int $pointsUsed, int $adminId): ?string
{
    if ($amount <= 0) {
        return 'Укажите сумму оплаты.';
    }
    if ($pointsUsed < 0) {
        return 'Баллы к списанию не могут быть отрицательными.';
    }
    $pdo = db();
    $pdo->beginTransaction();
    try {
        $st = $pdo->prepare("SELECT * FROM orders WHERE id = ? FOR UPDATE");
        $st->execute([$orderId]);
        $order = $st->fetch();
        if (!$order || $order['status'] !== 'new') {
            $pdo->rollBack();
            return 'Заявка уже обработана.';
        }
        $uid = (int) $order['user_id'];
        $pdo->prepare('SELECT id FROM users WHERE id = ? FOR UPDATE')->execute([$uid]);
        $limit = max_redeem($amount, balance($uid));
        if ($pointsUsed > $limit) {
            $pdo->rollBack();
            return 'Можно списать не больше ' . $limit . ' ' . points_word($limit) . '.';
        }
        $cashback = intdiv(($amount - $pointsUsed) * (int) config()['cashback_percent'], 100);
        $pdo->prepare("UPDATE orders SET status = 'paid', amount = ?, points_used = ?, cashback = ?, paid_at = ?, paid_by = ? WHERE id = ?")
            ->execute([$amount, $pointsUsed, $cashback, now(), $adminId, $orderId]);
        $ins = $pdo->prepare('INSERT INTO points (user_id, order_id, amount, kind, note, admin_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)');
        if ($pointsUsed > 0) {
            $ins->execute([$uid, $orderId, -$pointsUsed, 'redeem', '', $adminId, now()]);
        }
        if ($cashback > 0) {
            $ins->execute([$uid, $orderId, $cashback, 'cashback', '', $adminId, now()]);
        }
        $pdo->commit();
        return null;
    } catch (Throwable $e) {
        $pdo->rollBack();
        throw $e;
    }
}

// Отменить ошибочно отмеченную оплату: вернуть списанные баллы, забрать начисленные
function unmark_paid(int $orderId, int $adminId): ?string
{
    $pdo = db();
    $pdo->beginTransaction();
    try {
        $st = $pdo->prepare("SELECT * FROM orders WHERE id = ? FOR UPDATE");
        $st->execute([$orderId]);
        $order = $st->fetch();
        if (!$order || $order['status'] !== 'paid') {
            $pdo->rollBack();
            return 'Заявка не в статусе «Оплачена».';
        }
        $uid = (int) $order['user_id'];
        $delta = (int) $order['points_used'] - (int) $order['cashback'];
        if ($delta !== 0) {
            $pdo->prepare('INSERT INTO points (user_id, order_id, amount, kind, note, admin_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)')
                ->execute([$uid, $orderId, $delta, 'manual', 'Отмена оплаты', $adminId, now()]);
        }
        $pdo->prepare("UPDATE orders SET status = 'new', amount = NULL, points_used = 0, cashback = 0, paid_at = NULL, paid_by = NULL WHERE id = ?")
            ->execute([$orderId]);
        $pdo->commit();
        return null;
    } catch (Throwable $e) {
        $pdo->rollBack();
        throw $e;
    }
}
