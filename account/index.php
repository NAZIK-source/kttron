<?php
require __DIR__ . '/../app/bootstrap.php';
start_session();
require_post_csrf();
$user = require_user();
$uid = (int) $user['id'];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = (string) ($_POST['action'] ?? '');
    if ($action === 'redeem') {
        // Клиент просит списать баллы по своей новой заявке; сумму списания ставит менеджер
        $want = empty($_POST['want']) ? 0 : 1;
        db()->prepare("UPDATE orders SET want_redeem = ? WHERE id = ? AND user_id = ? AND status = 'new'")
            ->execute([$want, (int) ($_POST['order'] ?? 0), $uid]);
        flash($want ? 'Менеджер увидит, что по этой заявке вы хотите списать баллы.' : 'Списание баллов отменено.');
    } elseif ($action === 'password') {
        $st = db()->prepare('SELECT password_hash FROM users WHERE id = ?');
        $st->execute([$uid]);
        $new = (string) ($_POST['new'] ?? '');
        if (!password_verify((string) ($_POST['old'] ?? ''), (string) $st->fetchColumn())) {
            flash('Текущий пароль указан неверно.');
        } elseif (strlen($new) < 8) {
            flash('Новый пароль — не короче 8 символов.');
        } else {
            db()->prepare('UPDATE users SET password_hash = ? WHERE id = ?')
                ->execute([password_hash($new, PASSWORD_DEFAULT), $uid]);
            session_regenerate_id(true);
            flash('Пароль изменён.');
        }
    }
    redirect('/account/');
}

$balance = balance($uid);
$st = db()->prepare('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 50');
$st->execute([$uid]);
$orders = $st->fetchAll();
$st = db()->prepare('SELECT * FROM points WHERE user_id = ? ORDER BY id DESC LIMIT 50');
$st->execute([$uid]);
$moves = $st->fetchAll();
$status = ['new' => 'Новая', 'paid' => 'Оплачена', 'cancelled' => 'Отменена'];
$kinds = ['cashback' => 'Кэшбэк', 'redeem' => 'Списание', 'manual' => 'Корректировка'];

page_start('Личный кабинет');
?>
<section class="acc-head">
  <div>
    <p class="eyebrow">Личный кабинет</p>
    <h1><?= h($user['name']) ?></h1>
    <p class="muted"><?= h(format_phone($user['phone'])) ?></p>
  </div>
  <div class="acc-balance">
    <span>Баланс</span>
    <b><?= number_format($balance, 0, ',', ' ') ?> <?= points_word($balance) ?></b>
    <small>1 балл = 1 ₸ скидки. Кэшбэк <?= (int) config()['cashback_percent'] ?>% с оплаченных заявок.</small>
  </div>
</section>

<section class="acc-card">
  <h2>Мои заявки</h2>
  <?php if (!$orders): ?>
    <p class="muted">Заявок пока нет. Соберите заявку в <a href="/#catalog">каталоге</a> и нажмите «Отправить в WhatsApp» — она появится здесь. Кэшбэк начислим, когда менеджер отметит оплату.</p>
  <?php else: ?>
    <div class="acc-orders">
    <?php foreach ($orders as $o): ?>
      <article class="acc-order acc-<?= h($o['status']) ?>">
        <header>
          <b>Заявка № <?= (int) $o['id'] ?></b>
          <span class="acc-badge"><?= h($status[$o['status']]) ?></span>
          <time><?= h(date('d.m.Y H:i', strtotime($o['created_at']))) ?></time>
        </header>
        <pre><?= h($o['text']) ?></pre>
        <?php if ($o['status'] === 'paid'): ?>
          <p class="acc-sum">Оплачено: <?= money((int) $o['amount']) ?>
            <?php if ($o['points_used']): ?> · списано <?= (int) $o['points_used'] ?> <?= points_word((int) $o['points_used']) ?><?php endif ?>
            · начислено <b>+<?= (int) $o['cashback'] ?></b> <?= points_word((int) $o['cashback']) ?></p>
        <?php elseif ($o['status'] === 'new' && $balance > 0): ?>
          <form method="post" class="acc-inline">
            <?= csrf_field() ?><input type="hidden" name="action" value="redeem"><input type="hidden" name="order" value="<?= (int) $o['id'] ?>">
            <?php if ($o['want_redeem']): ?>
              <span class="acc-note">Вы попросили списать баллы — менеджер учтёт их при оплате.</span>
              <button class="btn btn-ghost-dark" type="submit">Не списывать</button>
            <?php else: ?>
              <input type="hidden" name="want" value="1">
              <button class="btn btn-ghost-dark" type="submit">Списать баллы по этой заявке</button>
            <?php endif ?>
          </form>
        <?php endif ?>
      </article>
    <?php endforeach ?>
    </div>
  <?php endif ?>
</section>

<section class="acc-card">
  <h2>История баллов</h2>
  <?php if (!$moves): ?>
    <p class="muted">Пока пусто.</p>
  <?php else: ?>
    <table class="acc-table">
      <thead><tr><th>Дата</th><th>Операция</th><th>Баллы</th></tr></thead>
      <tbody>
      <?php foreach ($moves as $m): ?>
        <tr>
          <td><?= h(date('d.m.Y', strtotime($m['created_at']))) ?></td>
          <td><?= h($kinds[$m['kind']]) ?><?= $m['order_id'] ? ' · заявка № ' . (int) $m['order_id'] : '' ?><?= $m['note'] !== '' ? ' · ' . h($m['note']) : '' ?></td>
          <td class="<?= $m['amount'] < 0 ? 'acc-minus' : 'acc-plus' ?>"><?= $m['amount'] > 0 ? '+' : '' ?><?= (int) $m['amount'] ?></td>
        </tr>
      <?php endforeach ?>
      </tbody>
    </table>
  <?php endif ?>
</section>

<section class="acc-card acc-narrow">
  <h2>Сменить пароль</h2>
  <form method="post" class="acc-form">
    <?= csrf_field() ?><input type="hidden" name="action" value="password">
    <label>Текущий пароль<input name="old" type="password" required autocomplete="current-password"></label>
    <label>Новый пароль<input name="new" type="password" minlength="8" required autocomplete="new-password"></label>
    <button class="btn btn-ghost-dark" type="submit">Сохранить</button>
  </form>
  <form method="post" action="/account/logout.php" class="acc-logout">
    <?= csrf_field() ?><button class="btn btn-ghost-dark" type="submit">Выйти</button>
  </form>
</section>
<?php page_end();
