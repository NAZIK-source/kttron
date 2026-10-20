<?php
require __DIR__ . '/../app/bootstrap.php';
start_session();
require_post_csrf();
if (current_user()) {
    redirect('/account/');
}

$error = '';
$phoneRaw = trim((string) ($_POST['phone'] ?? ''));

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $phone = normalize_phone($phoneRaw) ?? substr(preg_replace('/\D+/', '', $phoneRaw), 0, 15);
    if (too_many_attempts('user', $phone)) {
        $error = 'Слишком много попыток. Подождите 15 минут.';
    } else {
        $st = db()->prepare('SELECT id, password_hash FROM users WHERE phone = ?');
        $st->execute([$phone]);
        $row = $st->fetch();
        if ($row && password_verify((string) ($_POST['password'] ?? ''), $row['password_hash'])) {
            clear_attempts('user', $phone);
            if (password_needs_rehash($row['password_hash'], PASSWORD_DEFAULT)) {
                db()->prepare('UPDATE users SET password_hash = ? WHERE id = ?')
                    ->execute([password_hash((string) $_POST['password'], PASSWORD_DEFAULT), $row['id']]);
            }
            login_session('uid', (int) $row['id']);
            redirect('/account/');
        }
        record_failed_attempt('user', $phone);
        $error = 'Неверный телефон или пароль.';
    }
}

page_start('Вход');
?>
<section class="acc-card acc-narrow">
  <p class="eyebrow">Личный кабинет</p>
  <h1>Вход</h1>
  <?php if ($error): ?><p class="acc-error"><?= h($error) ?></p><?php endif ?>
  <form method="post" class="acc-form">
    <?= csrf_field() ?>
    <label>Телефон<input name="phone" type="tel" value="<?= h($phoneRaw) ?>" placeholder="+7 777 123-45-67" required autocomplete="tel"></label>
    <label>Пароль<input name="password" type="password" required autocomplete="current-password"></label>
    <button class="btn btn-solid btn-lg" type="submit">Войти</button>
  </form>
  <p class="muted">Нет кабинета? <a href="/account/register.php">Зарегистрироваться</a></p>
  <p class="muted">Забыли пароль? Напишите в <a href="https://wa.me/<?= h(config()['whatsapp']) ?>" target="_blank" rel="noopener">WhatsApp</a> с номера, на который зарегистрирован кабинет, — менеджер выдаст новый.</p>
</section>
<?php page_end();
