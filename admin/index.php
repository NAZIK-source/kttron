<?php
require __DIR__ . '/../app/admin.php';
admin_page('Заявки');

$status = (string) ($_GET['status'] ?? 'new');
if (!in_array($status, ['new', 'paid', 'cancelled', 'all'], true)) {
    $status = 'new';
}
$q = trim((string) ($_GET['q'] ?? ''));
$where = [];
$args = [];
if ($status !== 'all') {
    $where[] = 'o.status = ?';
    $args[] = $status;
}
if ($q !== '') {
    $digits = preg_replace('/\D+/', '', $q);
    $where[] = '(u.name LIKE ? OR u.phone LIKE ?' . (ctype_digit($q) ? ' OR o.id = ?' : '') . ')';
    $args[] = '%' . $q . '%';
    $args[] = '%' . ($digits !== '' ? $digits : $q) . '%';
    if (ctype_digit($q)) {
        $args[] = (int) $q;
    }
}
$st = db()->prepare('SELECT o.*, u.name, u.phone FROM orders o JOIN users u ON u.id = o.user_id'
    . ($where ? ' WHERE ' . implode(' AND ', $where) : '') . ' ORDER BY o.id DESC LIMIT 200');
$st->execute($args);
$orders = $st->fetchAll();
$tabs = ['new' => 'Новые', 'paid' => 'Оплаченные', 'cancelled' => 'Отменённые', 'all' => 'Все'];
?>
<h1>Заявки</h1>
<form class="acc-filter" method="get">
  <?php foreach ($tabs as $k => $label): ?>
    <a class="<?= $k === $status ? 'is-active' : '' ?>" href="?status=<?= $k ?>"><?= $label ?></a>
  <?php endforeach ?>
  <input type="hidden" name="status" value="<?= h($status) ?>">
  <input name="q" value="<?= h($q) ?>" placeholder="Имя, телефон или № заявки">
  <button class="btn btn-ghost-dark" type="submit">Найти</button>
</form>
<?php if (!$orders): ?>
  <p class="muted">Заявок нет.</p>
<?php else: ?>
<table class="acc-table">
  <thead><tr><th>№</th><th>Дата</th><th>Клиент</th><th>Заявка</th><th>Статус</th></tr></thead>
  <tbody>
  <?php foreach ($orders as $o): ?>
    <tr>
      <td><a href="/admin/order.php?id=<?= (int) $o['id'] ?>"><?= (int) $o['id'] ?></a></td>
      <td><?= h(date('d.m H:i', strtotime($o['created_at']))) ?></td>
      <td><a href="/admin/client.php?id=<?= (int) $o['user_id'] ?>"><?= h($o['name']) ?></a><br><small><?= h(format_phone($o['phone'])) ?></small></td>
      <td><a href="/admin/order.php?id=<?= (int) $o['id'] ?>"><?= h(mb_strimwidth(preg_replace('/\s+/u', ' ', $o['text']), 0, 90, '…')) ?></a>
        <?php if ($o['want_redeem'] && $o['status'] === 'new'): ?><br><span class="acc-badge acc-warn">Хочет списать баллы</span><?php endif ?></td>
      <td><?= h(order_status_label($o['status'])) ?><?= $o['status'] === 'paid' ? '<br><small>' . money((int) $o['amount']) . '</small>' : '' ?></td>
    </tr>
  <?php endforeach ?>
  </tbody>
</table>
<?php endif;
page_end();
