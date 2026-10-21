<?php
require __DIR__ . '/../app/bootstrap.php';
start_session();
require_post_csrf();
if (current_user()) {
    redirect('/account/');
}

$errors = [];
$name = trim((string) ($_POST['name'] ?? ''));
$phoneRaw = trim((string) ($_POST['phone'] ?? ''));

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $phone = normalize_phone($phoneRaw);
    $password = (string) ($_POST['password'] ?? '');
    if ($name === '' || mb_strlen($name) > 100) {
        $errors[] = 'Укажите имя.';
    }
    if (!$phone) {
        $errors[] = 'Укажите телефон полностью, например +7 777 123-45-67.';
    }
    if (strlen($password) < 8) {
        $errors[] = 'Пароль — не короче 8 символов.';
    } elseif ($password !== (string) ($_POST['password2'] ?? '')) {
        $errors[] = 'Пароли не совпадают.';
    }
    if (empty($_POST['consent'])) {
        $errors[] = 'Нужно согласие на обработку персональных данных и с правилами кэшбэка.';
    }
    if (!$errors) {
        $st = db()->prepare('SELECT id FROM users WHERE phone = ?');
        $st->execute([$phone]);
        if ($st->fetch()) {
            $errors[] = 'Этот номер уже зарегистрирован. Войдите или попросите менеджера сбросить пароль.';
        }
    }
    if (!$errors) {
        db()->prepare('INSERT INTO users (phone, name, password_hash, consent_at, created_at) VALUES (?, ?, ?, ?, ?)')
            ->execute([$phone, $name, password_hash($password, PASSWORD_DEFAULT), now(), now()]);
        login_session('uid', (int) db()->lastInsertId());
        flash('Готово! Теперь заявки с сайта сохраняются в кабинете, а за оплаченные начисляется кэшбэк.');
        redirect('/account/');
    }
}

page_start('Регистрация');
?>
<section class="acc-card acc-narrow">
  <p class="eyebrow">Личный кабинет</p>
  <h1>Регистрация</h1>
  <p class="muted">Кэшбэк <?= percent_label('cashback_percent') ?>% баллами за каждую оплаченную заявку с сайта. 1 балл = 1 ₸ скидки.</p>
  <?php foreach ($errors as $e): ?><p class="acc-error"><?= h($e) ?></p><?php endforeach ?>
  <form method="post" class="acc-form" autocomplete="on">
    <?= csrf_field() ?>
    <label>Имя<input name="name" value="<?= h($name) ?>" maxlength="100" required autocomplete="name"></label>
    <label>Телефон (как в WhatsApp)<input name="phone" type="tel" value="<?= h($phoneRaw) ?>" placeholder="+7 777 123-45-67" required autocomplete="tel"></label>
    <label>Пароль<input name="password" type="password" minlength="8" required autocomplete="new-password"></label>
    <label>Пароль ещё раз<input name="password2" type="password" minlength="8" required autocomplete="new-password"></label>
    <label class="acc-check"><input type="checkbox" name="consent" value="1" required>
      <span>Согласен на обработку персональных данных и с <a href="/account/rules.php" target="_blank">правилами кэшбэка</a></span></label>
    <button class="btn btn-solid btn-lg" type="submit">Зарегистрироваться</button>
  </form>
  <p class="muted">Уже есть кабинет? <a href="/account/login.php">Войти</a></p>
</section>
<?php page_end();
