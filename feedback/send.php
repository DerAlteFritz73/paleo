<?php
declare(strict_types=1);

// Endpoint minimal, sans dépendance externe (pas de Composer / PHPMailer) :
// reçoit un commentaire depuis le formulaire du site et l'envoie par e-mail
// via le relais SMTP configuré dans l'environnement (voir .env.local).
// Volontairement autonome — le reste du site est un simple export statique,
// ce script est le seul point d'entrée dynamique.

header('Content-Type: application/json; charset=utf-8');
// Pas d'en-tête CORS : ce point de terminaison n'est destiné qu'à des
// appels same-origin depuis le site lui-même.

function respond(int $code, array $data): never {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    respond(405, ['ok' => false, 'error' => 'method_not_allowed']);
}

$raw = file_get_contents('php://input');
$input = json_decode($raw ?: '', true);
if (!is_array($input)) {
    $input = $_POST;
}

// Piège à robots : ce champ est masqué en CSS, un humain ne le remplit jamais.
if (trim((string)($input['website'] ?? '')) !== '') {
    respond(200, ['ok' => true]); // on répond "succès" sans rien envoyer, pour ne pas alerter le bot
}

$name    = trim((string)($input['name'] ?? ''));
$email   = trim((string)($input['email'] ?? ''));
$message = trim((string)($input['message'] ?? ''));
$lang    = trim((string)($input['lang'] ?? 'fr'));
$page    = trim((string)($input['page'] ?? ''));

$name = preg_replace('/[\r\n]+/', ' ', $name) ?? '';
$page = preg_replace('/[\r\n]+/', ' ', $page) ?? '';

if ($message === '' || strlen($message) > 8000) {
    respond(422, ['ok' => false, 'error' => 'invalid_message']);
}
if (strlen($name) > 200) {
    respond(422, ['ok' => false, 'error' => 'invalid_name']);
}
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    respond(422, ['ok' => false, 'error' => 'invalid_email']);
}

// Anti-spam très simple : une soumission par IP toutes les 20 secondes.
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$rateLimitFile = sys_get_temp_dir() . '/paleo-feedback-' . md5($ip);
if (is_file($rateLimitFile) && (time() - filemtime($rateLimitFile)) < 20) {
    respond(429, ['ok' => false, 'error' => 'rate_limited']);
}
touch($rateLimitFile);

$smtp = [
    'host' => getenv('SMTP_HOST') ?: '',
    'port' => (int)(getenv('SMTP_PORT') ?: 587),
    'user' => getenv('SMTP_USER') ?: '',
    'pass' => getenv('SMTP_PASS') ?: '',
    'from' => getenv('SMTP_FROM') ?: (getenv('SMTP_USER') ?: ''),
    'to'   => getenv('FEEDBACK_TO') ?: 'marino@kreilos.com',
];

if ($smtp['host'] === '' || $smtp['user'] === '' || $smtp['pass'] === '') {
    error_log('paleo-feedback: SMTP not configured (missing env vars)');
    respond(500, ['ok' => false, 'error' => 'mail_not_configured']);
}

$subject = 'Paléo — nouveau commentaire' . ($page !== '' ? " ($page)" : '');
$bodyLines = [
    'Nouveau commentaire reçu sur le blog Paléo.',
    '',
    'Langue      : ' . $lang,
    'Page        : ' . ($page !== '' ? $page : '(non précisée)'),
    'Nom         : ' . ($name !== '' ? $name : '(non précisé)'),
    'E-mail      : ' . ($email !== '' ? $email : '(non précisé)'),
    'Adresse IP  : ' . $ip,
    'Date        : ' . date('Y-m-d H:i:s') . ' UTC',
    '',
    '--- Message ---',
    $message,
];

$ok = smtp_send_mail($smtp, $subject, implode("\n", $bodyLines), $email !== '' ? $email : null);

if (!$ok) {
    respond(502, ['ok' => false, 'error' => 'send_failed']);
}

respond(200, ['ok' => true]);

/**
 * Client SMTP minimal (EHLO/STARTTLS/AUTH LOGIN/DATA), sans dépendance
 * externe. Pensé pour un unique envoi par requête, pas pour du volume.
 */
function smtp_send_mail(array $cfg, string $subject, string $body, ?string $replyTo): bool {
    $sock = @stream_socket_client(
        "tcp://{$cfg['host']}:{$cfg['port']}",
        $errno,
        $errstr,
        10
    );
    if (!$sock) {
        error_log("paleo-feedback: connexion SMTP échouée ($errno) $errstr");
        return false;
    }
    stream_set_timeout($sock, 10);

    $readResponse = function () use ($sock): string {
        $data = '';
        while (($line = fgets($sock, 515)) !== false) {
            $data .= $line;
            // Une ligne de continuation SMTP a un tiret en 4e position ("250-…"),
            // la dernière ligne d'une réponse a un espace ("250 …").
            if (strlen($line) < 4 || $line[3] === ' ') {
                break;
            }
        }
        return $data;
    };
    $sendCommand = function (string $cmd) use ($sock) {
        fwrite($sock, $cmd . "\r\n");
    };
    $expect = function (string $prefix) use ($readResponse): bool {
        return str_starts_with($readResponse(), $prefix);
    };

    $readResponse(); // bannière de connexion

    $sendCommand('EHLO paleo.kreilos.fr');
    $readResponse();

    $sendCommand('STARTTLS');
    if (!$expect('220')) {
        fclose($sock);
        return false;
    }
    if (!stream_socket_enable_crypto($sock, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
        error_log('paleo-feedback: échec STARTTLS');
        fclose($sock);
        return false;
    }

    $sendCommand('EHLO paleo.kreilos.fr');
    $readResponse();

    $sendCommand('AUTH LOGIN');
    if (!$expect('334')) {
        fclose($sock);
        return false;
    }
    $sendCommand(base64_encode($cfg['user']));
    if (!$expect('334')) {
        fclose($sock);
        return false;
    }
    $sendCommand(base64_encode($cfg['pass']));
    if (!$expect('235')) {
        error_log('paleo-feedback: authentification SMTP refusée');
        fclose($sock);
        return false;
    }

    $sendCommand("MAIL FROM:<{$cfg['from']}>");
    if (!$expect('250')) {
        fclose($sock);
        return false;
    }
    $sendCommand("RCPT TO:<{$cfg['to']}>");
    if (!$expect('250')) {
        fclose($sock);
        return false;
    }
    $sendCommand('DATA');
    if (!$expect('354')) {
        fclose($sock);
        return false;
    }

    $headers = [
        'From: =?UTF-8?B?' . base64_encode('Paléo') . '?= <' . $cfg['from'] . '>',
        'To: <' . $cfg['to'] . '>',
    ];
    if ($replyTo !== null) {
        $headers[] = 'Reply-To: <' . $replyTo . '>';
    }
    $headers[] = 'Subject: =?UTF-8?B?' . base64_encode($subject) . '?=';
    $headers[] = 'MIME-Version: 1.0';
    $headers[] = 'Content-Type: text/plain; charset=UTF-8';
    $headers[] = 'Content-Transfer-Encoding: 8bit';

    // Un point seul en début de ligne termine le message SMTP : on double
    // tout point de début de ligne présent dans le corps ("dot-stuffing").
    $escapedBody = preg_replace('/^\./m', '..', $body);

    $payload = implode("\r\n", $headers) . "\r\n\r\n" . $escapedBody . "\r\n.";
    $sendCommand($payload);
    $sent = $expect('250');

    $sendCommand('QUIT');
    $readResponse();
    fclose($sock);

    return $sent;
}
