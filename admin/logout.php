<?php
require __DIR__ . '/../app/bootstrap.php';
start_session();
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    require_post_csrf();
    unset($_SESSION['aid']);
    session_regenerate_id(true);
}
redirect('/admin/login.php');
