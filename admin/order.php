<?php
require __DIR__ . '/../app/admin.php';
start_session();
require_post_csrf();
$admin = require_admin();
$id = (int) ($_GET['id'] ?? 0);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = (string) ($_POST['action'] ?? '');
    $error = null;
    if ($action === 'paid') {
        $error = mark_paid($id, (int) ($_POST['amount'] ?? 0), (int) ($_POST['points'] ?? 0), (int) $admin['id']);
        $ok = 'Оплата отмечена, кэшбэк начислен.';
    } elseif ($action === 'unpay') {
        $error = unmark_paid($id, (int) $admin['id']);
        $ok = 'Оплата отменена, баллы пересчитаны.';
    } elseif ($action === 'cancel' || $action === 'reopen') {
        db()->prepare('UPDATE orders SET status = ? WHERE id = ? AND status = ?')
            ->execute($action === 'cancel' ? ['cancelled', $id, 'new'] : ['new', $id, 'cancelled']);
        $ok = $action === 'cancel' ? 'Заявка отменена.' : 'Заявка снова в работе.';
    }
    flash($error ?? ($ok ?? null));
    redirect('/admin/order.php?id=' . $id);
}

$st = db()->prepare('SELECT o.*, u.name, u.phone FROM orders o JOIN users u ON u.id = o.user_id WHERE o.id = ?');
$st->execute([$id]);
$o = $st->fetch();
admin_page('Заявка № ' . $id);
if (!$o) {
    echo '<p>Заявка не найдена.</p>';
    page_end();
    exit;
}
$balance = balance((int) $o['user_id']);
$c = config();
?>
<h1>Заявка № <?= (int) $o['id'] ?> <span class="acc-badge"><?= h(order_status_label($o['status'])) ?></span></h1>
<div class="acc-grid">
  <section class="acc-card">
    <p><b><a href="/admin/client.php?id=<?= (int) $o['user_id'] ?>"><?= h($o['name']) ?></a></b> · <?= h(format_phone($o['phone'])) ?>
      · <a href="https://wa.me/<?= h($o['phone']) ?>" target="_blank" rel="noopener">WhatsApp</a></p>
    <p class="muted">Создана <?= h(date('d.m.Y H:i', strtotime($o['created_at']))) ?> · источник: <?= h(['request' => 'корзина заявки', 'lead' => 'форма «Написать специалисту»', 'calc' => 'калькулятор'][$o['source']] ?? $o['source']) ?></p>
    <pre><?= h($o['text']) ?></pre>
    <p>Баланс клиента: <b><?= $balance ?> <?= points_word($balance) ?></b></p>
  </section>

  <section class="acc-card">
  <?php if ($o['status'] === 'new'): ?>
    <h2>Отметить оплату</h2>
    <?php if ($o['want_redeem']): ?><p class="acc-badge acc-warn">Клиент просит списать баллы</p><?php endif ?>
    <form method="post" class="acc-form" id="payForm" data-balance="<?= $balance ?>" data-max="<?= percent_bp('max_redeem_percent') ?>" data-pct="<?= percent_bp('cashback_percent') ?>">
      <?= csrf_field() ?><input type="hidden" name="action" value="paid">
      <label>Сумма заказа, ₸<input name="amount" type="number" min="1" step="1" required></label>
      <label>Списать баллов (до <?= percent_label('max_redeem_percent') ?>% суммы, на балансе <?= $balance ?>)<input name="points" type="number" min="0" step="1" value="0"></label>
      <p class="muted" id="payHint"></p>
      <button class="btn btn-solid btn-lg" type="submit">Оплачено — начислить кэшбэк</button>
    </form>
    <form method="post" class="acc-inline"><?= csrf_field() ?><input type="hidden" name="action" value="cancel">
      <button class="btn btn-ghost-dark" type="submit" onclick="return confirm('Отменить заявку?')">Отменить заявку</button></form>
    <script>
      (function () {
        var f = document.getElementById('payForm'), hint = document.getElementById('payHint');
        var bal = +f.dataset.balance, max = +f.dataset.max, pct = +f.dataset.pct;
        function upd() {
          var a = Math.floor(+f.amount.value || 0), lim = Math.max(0, Math.min(bal, Math.floor(a * max / 10000)));
          f.points.max = lim;
          var p = Math.min(+f.points.value || 0, lim);
          hint.textContent = a ? 'Можно списать до ' + lim + '. К оплате деньгами: ' + (a - p).toLocaleString('ru-RU') + ' ₸. Кэшбэк: +' + Math.floor((a - p) * pct / 10000) + '.' : '';
        }
        f.addEventListener('input', upd);
      })();
    </script>
  <?php elseif ($o['status'] === 'paid'): ?>
    <h2>Оплачена</h2>
    <p><?= h(date('d.m.Y H:i', strtotime($o['paid_at']))) ?></p>
    <p>Сумма: <b><?= money((int) $o['amount']) ?></b><br>Списано баллов: <?= (int) $o['points_used'] ?><br>Начислено кэшбэка: <b>+<?= (int) $o['cashback'] ?></b></p>
    <form method="post" class="acc-inline"><?= csrf_field() ?><input type="hidden" name="action" value="unpay">
      <button class="btn btn-ghost-dark" type="submit" onclick="return confirm('Отменить оплату? Начисленный кэшбэк будет списан, списанные баллы вернутся.')">Отменить оплату (ошибка)</button></form>
  <?php else: ?>
    <h2>Отменена</h2>
    <form method="post" class="acc-inline"><?= csrf_field() ?><input type="hidden" name="action" value="reopen">
      <button class="btn btn-ghost-dark" type="submit">Вернуть в работу</button></form>
  <?php endif ?>
  </section>
</div>
<?php page_end();
