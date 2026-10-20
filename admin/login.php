<?php
require __DIR__ . '/../app/bootstrap.php';
start_session();
require_post_csrf();
if (current_admin()) {
    redirect('/admin/');
}

$error = '';
$login = trim((string) ($_POST['login'] ?? ''));
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $key = substr($login, 0, 50);
    if (too_many_attempts('admin', $key)) {
        $error = 'Слишком много попыток. Подождите 15 минут.';
    } else {
        $st = db()->prepare('SELECT id, password_hash FROM admins WHERE login = ?');
        $st->execute([$key]);
        $row = $st->fetch();
        if ($row && password_verify((string) ($_POST['password'] ?? ''), $row['password_hash'])) {
            clear_attempts('admin', $key);
            login_session('aid', (int) $row['id']);
            redirect('/admin/');
        }
        record_failed_attempt('admin', $key);
        $error = 'Неверный логин или пароль.';
    }
}

page_start('Вход в админку', 'admin');
?>
<section class="acc-card acc-narrow">
  <h1>Вход в админку</h1>
  <?php if ($error): ?><p class="acc-error"><?= h($error) ?></p><?php endif ?>
  <form method="post" class="acc-form">
    <?= csrf_field() ?>
    <label>Логин<input name="login" value="<?= h($login) ?>" required autocomplete="username"></label>
    <label>Пароль<input name="password" type="password" required autocomplete="current-password"></label>
    <button class="btn btn-solid btn-lg" type="submit">Войти</button>
  </form>
</section>
<?php page_end();
