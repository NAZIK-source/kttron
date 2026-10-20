<?php
require __DIR__ . '/../app/admin.php';
start_session();
require_post_csrf();
$admin = require_admin();
$id = (int) ($_GET['id'] ?? 0);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = (string) ($_POST['action'] ?? '');
    if ($action === 'adjust') {
        $amount = (int) ($_POST['amount'] ?? 0);
        $note = trim((string) ($_POST['note'] ?? ''));
        if ($amount === 0 || $note === '') {
            flash('Укажите количество баллов (со знаком минус для списания) и причину.');
        } else {
            db()->prepare('INSERT INTO points (user_id, amount, kind, note, admin_id, created_at) VALUES (?, ?, ?, ?, ?, ?)')
                ->execute([$id, $amount, 'manual', mb_substr($note, 0, 255), (int) $admin['id'], now()]);
            flash('Баланс изменён на ' . ($amount > 0 ? '+' : '') . $amount . '.');
        }
    } elseif ($action === 'reset') {
        // Временный пароль показываем один раз; клиент меняет его в кабинете
        $alphabet = 'abcdefghjkmnpqrstuvwxyz23456789';
        $temp = '';
        for ($i = 0; $i < 10; $i++) {
            $temp .= $alphabet[random_int(0, strlen($alphabet) - 1)];
        }
        db()->prepare('UPDATE users SET password_hash = ? WHERE id = ?')
            ->execute([password_hash($temp, PASSWORD_DEFAULT), $id]);
        flash('Новый временный пароль: ' . $temp . ' — отправьте клиенту и попросите сменить его в кабинете.');
    }
    redirect('/admin/client.php?id=' . $id);
}

$st = db()->prepare('SELECT * FROM users WHERE id = ?');
$st->execute([$id]);
$u = $st->fetch();
admin_page($u ? $u['name'] : 'Клиент');
if (!$u) {
    echo '<p>Клиент не найден.</p>';
    page_end();
    exit;
}
$balance = balance($id);
$st = db()->prepare('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 100');
$st->execute([$id]);
$orders = $st->fetchAll();
$st = db()->prepare('SELECT p.*, a.login FROM points p LEFT JOIN admins a ON a.id = p.admin_id WHERE p.user_id = ? ORDER BY p.id DESC LIMIT 200');
$st->execute([$id]);
$moves = $st->fetchAll();
$kinds = ['cashback' => 'Кэшбэк', 'redeem' => 'Списание', 'manual' => 'Вручную'];
?>
<h1><?= h($u['name']) ?></h1>
<p><?= h(format_phone($u['phone'])) ?> · <a href="https://wa.me/<?= h($u['phone']) ?>" target="_blank" rel="noopener">WhatsApp</a>
  · с <?= h(date('d.m.Y', strtotime($u['created_at']))) ?> · баланс <b><?= $balance ?> <?= points_word($balance) ?></b></p>

<div class="acc-grid">
  <section class="acc-card">
    <h2>Заявки</h2>
    <?php if (!$orders): ?><p class="muted">Нет.</p><?php else: ?>
    <table class="acc-table">
      <thead><tr><th>№</th><th>Дата</th><th>Статус</th><th>Сумма</th><th>Кэшбэк</th></tr></thead>
      <tbody>
      <?php foreach ($orders as $o): ?>
        <tr>
          <td><a href="/admin/order.php?id=<?= (int) $o['id'] ?>"><?= (int) $o['id'] ?></a></td>
          <td><?= h(date('d.m.Y', strtotime($o['created_at']))) ?></td>
          <td><?= h(order_status_label($o['status'])) ?></td>
          <td><?= $o['amount'] !== null ? money((int) $o['amount']) : '—' ?></td>
          <td><?= $o['cashback'] ? '+' . (int) $o['cashback'] : '—' ?></td>
        </tr>
      <?php endforeach ?>
      </tbody>
    </table>
    <?php endif ?>
  </section>

  <section class="acc-card">
    <h2>Изменить баланс вручную</h2>
    <form method="post" class="acc-form">
      <?= csrf_field() ?><input type="hidden" name="action" value="adjust">
      <label>Баллы (минус — списать)<input name="amount" type="number" step="1" required></label>
      <label>Причина (видна клиенту)<input name="note" maxlength="255" required placeholder="Например: возврат товара по заявке № 12"></label>
      <button class="btn btn-ghost-dark" type="submit">Применить</button>
    </form>
    <h2>Пароль</h2>
    <form method="post" class="acc-inline">
      <?= csrf_field() ?><input type="hidden" name="action" value="reset">
      <button class="btn btn-ghost-dark" type="submit" onclick="return confirm('Выдать клиенту новый временный пароль?')">Сбросить пароль</button>
    </form>
  </section>
</div>

<section class="acc-card">
  <h2>История баллов</h2>
  <?php if (!$moves): ?><p class="muted">Пусто.</p><?php else: ?>
  <table class="acc-table">
    <thead><tr><th>Дата</th><th>Операция</th><th>Баллы</th><th>Кто</th></tr></thead>
    <tbody>
    <?php foreach ($moves as $m): ?>
      <tr>
        <td><?= h(date('d.m.Y H:i', strtotime($m['created_at']))) ?></td>
        <td><?= h($kinds[$m['kind']]) ?><?= $m['order_id'] ? ' · № ' . (int) $m['order_id'] : '' ?><?= $m['note'] !== '' ? ' · ' . h($m['note']) : '' ?></td>
        <td class="<?= $m['amount'] < 0 ? 'acc-minus' : 'acc-plus' ?>"><?= $m['amount'] > 0 ? '+' : '' ?><?= (int) $m['amount'] ?></td>
        <td><?= h($m['login'] ?? '') ?></td>
      </tr>
    <?php endforeach ?>
    </tbody>
  </table>
  <?php endif ?>
</section>
<?php page_end();
