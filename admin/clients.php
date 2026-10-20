<?php
require __DIR__ . '/../app/admin.php';
admin_page('Клиенты');

$q = trim((string) ($_GET['q'] ?? ''));
$sql = 'SELECT u.id, u.name, u.phone, u.created_at,
          (SELECT COALESCE(SUM(p.amount), 0) FROM points p WHERE p.user_id = u.id) AS balance,
          (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id AND o.status = \'paid\') AS paid_orders
        FROM users u';
$args = [];
if ($q !== '') {
    $digits = preg_replace('/\D+/', '', $q);
    $sql .= ' WHERE u.name LIKE ? OR u.phone LIKE ?';
    $args = ['%' . $q . '%', '%' . ($digits !== '' ? $digits : $q) . '%'];
}
$st = db()->prepare($sql . ' ORDER BY u.id DESC LIMIT 200');
$st->execute($args);
$clients = $st->fetchAll();
?>
<h1>Клиенты</h1>
<form class="acc-filter" method="get">
  <input name="q" value="<?= h($q) ?>" placeholder="Имя или телефон">
  <button class="btn btn-ghost-dark" type="submit">Найти</button>
</form>
<?php if (!$clients): ?>
  <p class="muted">Клиентов нет.</p>
<?php else: ?>
<table class="acc-table">
  <thead><tr><th>Клиент</th><th>Телефон</th><th>Регистрация</th><th>Оплачено заявок</th><th>Баланс</th></tr></thead>
  <tbody>
  <?php foreach ($clients as $u): ?>
    <tr>
      <td><a href="/admin/client.php?id=<?= (int) $u['id'] ?>"><?= h($u['name']) ?></a></td>
      <td><?= h(format_phone($u['phone'])) ?></td>
      <td><?= h(date('d.m.Y', strtotime($u['created_at']))) ?></td>
      <td><?= (int) $u['paid_orders'] ?></td>
      <td><?= (int) $u['balance'] ?></td>
    </tr>
  <?php endforeach ?>
  </tbody>
</table>
<?php endif;
page_end();
