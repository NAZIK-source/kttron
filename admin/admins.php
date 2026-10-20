<?php
require __DIR__ . '/../app/admin.php';
start_session();
require_post_csrf();
$admin = require_admin();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = (string) ($_POST['action'] ?? '');
    if ($action === 'add') {
        $login = trim((string) ($_POST['login'] ?? ''));
        $password = (string) ($_POST['password'] ?? '');
        $st = db()->prepare('SELECT id FROM admins WHERE login = ?');
        $st->execute([$login]);
        if (!preg_match('/^[a-zA-Z0-9_.-]{3,50}$/', $login)) {
            flash('Логин: 3–50 латинских букв, цифр, «.», «-», «_».');
        } elseif (strlen($password) < 10) {
            flash('Пароль администратора — не короче 10 символов.');
        } elseif ($st->fetch()) {
            flash('Такой логин уже есть.');
        } else {
            db()->prepare('INSERT INTO admins (login, password_hash, created_at) VALUES (?, ?, ?)')
                ->execute([$login, password_hash($password, PASSWORD_DEFAULT), now()]);
            flash('Администратор ' . $login . ' добавлен.');
        }
    } elseif ($action === 'password') {
        $st = db()->prepare('SELECT password_hash FROM admins WHERE id = ?');
        $st->execute([$admin['id']]);
        $new = (string) ($_POST['new'] ?? '');
        if (!password_verify((string) ($_POST['old'] ?? ''), (string) $st->fetchColumn())) {
            flash('Текущий пароль указан неверно.');
        } elseif (strlen($new) < 10) {
            flash('Новый пароль — не короче 10 символов.');
        } else {
            db()->prepare('UPDATE admins SET password_hash = ? WHERE id = ?')->execute([password_hash($new, PASSWORD_DEFAULT), $admin['id']]);
            session_regenerate_id(true);
            flash('Пароль изменён.');
        }
    } elseif ($action === 'delete') {
        $target = (int) ($_POST['id'] ?? 0);
        if ($target === (int) $admin['id']) {
            flash('Себя удалить нельзя.');
        } else {
            db()->prepare('DELETE FROM admins WHERE id = ?')->execute([$target]);
            flash('Администратор удалён.');
        }
    }
    redirect('/admin/admins.php');
}

admin_page('Администраторы');
$admins = db()->query('SELECT id, login, created_at FROM admins ORDER BY id')->fetchAll();
?>
<h1>Администраторы</h1>
<div class="acc-grid">
  <section class="acc-card">
    <table class="acc-table">
      <thead><tr><th>Логин</th><th>С</th><th></th></tr></thead>
      <tbody>
      <?php foreach ($admins as $a): ?>
        <tr>
          <td><?= h($a['login']) ?></td>
          <td><?= h(date('d.m.Y', strtotime($a['created_at']))) ?></td>
          <td><?php if ((int) $a['id'] !== (int) $admin['id']): ?>
            <form method="post" class="acc-inline"><?= csrf_field() ?><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="<?= (int) $a['id'] ?>">
              <button class="btn btn-ghost-dark" type="submit" onclick="return confirm('Удалить администратора?')">Удалить</button></form>
          <?php endif ?></td>
        </tr>
      <?php endforeach ?>
      </tbody>
    </table>
    <h2>Добавить</h2>
    <form method="post" class="acc-form">
      <?= csrf_field() ?><input type="hidden" name="action" value="add">
      <label>Логин<input name="login" required pattern="[a-zA-Z0-9_.\-]{3,50}" autocomplete="off"></label>
      <label>Пароль (от 10 символов)<input name="password" type="password" minlength="10" required autocomplete="new-password"></label>
      <button class="btn btn-ghost-dark" type="submit">Добавить</button>
    </form>
  </section>
  <section class="acc-card">
    <h2>Мой пароль</h2>
    <form method="post" class="acc-form">
      <?= csrf_field() ?><input type="hidden" name="action" value="password">
      <label>Текущий<input name="old" type="password" required autocomplete="current-password"></label>
      <label>Новый (от 10 символов)<input name="new" type="password" minlength="10" required autocomplete="new-password"></label>
      <button class="btn btn-ghost-dark" type="submit">Сохранить</button>
    </form>
  </section>
</div>
<?php page_end();
