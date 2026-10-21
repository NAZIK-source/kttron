<?php
// Первая настройка: создаёт таблицы и первого администратора.
// Работает, только пока нет ни одного администратора и в config.php задан setup_key.
require __DIR__ . '/../app/bootstrap.php';
start_session();
require_post_csrf();

$key = (string) (config()['setup_key'] ?? '');
$hasAdmin = false;
$dbError = '';
try {
    db();
    try {
        $hasAdmin = (int) db()->query('SELECT COUNT(*) FROM admins')->fetchColumn() > 0;
    } catch (PDOException $e) {
        // таблиц ещё нет
    }
} catch (PDOException $e) {
    // Причину показываем только после правильного ключа настройки
    $dbError = $e->getMessage();
}
if ($hasAdmin || strlen($key) < 16) {
    http_response_code(404);
    exit('Не найдено');
}

$error = '';
$login = trim((string) ($_POST['login'] ?? ''));
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $password = (string) ($_POST['password'] ?? '');
    if (!hash_equals($key, (string) ($_POST['key'] ?? ''))) {
        $error = 'Неверный ключ настройки.';
    } elseif ($dbError !== '') {
        $error = 'Нет подключения к базе. Проверьте db_name, db_user и db_pass в app/config.php. Ответ сервера: ' . $dbError;
    } elseif (!preg_match('/^[a-zA-Z0-9_.-]{3,50}$/', $login)) {
        $error = 'Логин: 3–50 латинских букв, цифр, «.», «-», «_».';
    } elseif (strlen($password) < 10) {
        $error = 'Пароль администратора — не короче 10 символов.';
    } else {
        foreach (array_filter(array_map('trim', explode(';', file_get_contents(__DIR__ . '/../app/schema.sql')))) as $sql) {
            if (preg_match('/^\s*(--[^\n]*\n\s*)*CREATE/i', $sql)) {
                db()->exec($sql);
            }
        }
        db()->prepare('INSERT INTO admins (login, password_hash, created_at) VALUES (?, ?, ?)')
            ->execute([$login, password_hash($password, PASSWORD_DEFAULT), now()]);
        login_session('aid', (int) db()->lastInsertId());
        flash('Таблицы созданы, администратор добавлен. Удалите setup_key из app/config.php.');
        redirect('/admin/');
    }
}

page_start('Первая настройка', 'admin');
?>
<section class="acc-card acc-narrow">
  <h1>Первая настройка</h1>
  <p class="muted">Создаст таблицы в базе и первого администратора.</p>
  <?php if ($error): ?><p class="acc-error"><?= h($error) ?></p><?php endif ?>
  <form method="post" class="acc-form">
    <?= csrf_field() ?>
    <label>Ключ настройки (setup_key из app/config.php)<input name="key" type="password" required></label>
    <label>Логин администратора<input name="login" value="<?= h($login) ?>" required pattern="[a-zA-Z0-9_.\-]{3,50}" autocomplete="username"></label>
    <label>Пароль (от 10 символов)<input name="password" type="password" minlength="10" required autocomplete="new-password"></label>
    <button class="btn btn-solid btn-lg" type="submit">Создать</button>
  </form>
</section>
<?php page_end();
