<?php
require __DIR__ . '/../app/bootstrap.php';
start_session();
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    require_post_csrf();
    unset($_SESSION['uid']);
    session_regenerate_id(true);
}
redirect('/account/login.php');
