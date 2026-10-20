-- Таблицы личного кабинета и кэшбэка (MySQL / MariaDB)

CREATE TABLE IF NOT EXISTS users (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  phone VARCHAR(15) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  consent_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS orders (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  source VARCHAR(20) NOT NULL,
  text TEXT NOT NULL,
  status ENUM('new','paid','cancelled') NOT NULL DEFAULT 'new',
  want_redeem TINYINT(1) NOT NULL DEFAULT 0,
  amount INT UNSIGNED NULL,
  points_used INT UNSIGNED NOT NULL DEFAULT 0,
  cashback INT UNSIGNED NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  paid_at DATETIME NULL,
  paid_by INT UNSIGNED NULL,
  KEY idx_orders_user (user_id),
  KEY idx_orders_status (status, created_at),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Движение баллов: начисления (+) и списания (-). Баланс = сумма строк.
CREATE TABLE IF NOT EXISTS points (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  order_id INT UNSIGNED NULL,
  amount INT NOT NULL,
  kind ENUM('cashback','redeem','manual') NOT NULL,
  note VARCHAR(255) NOT NULL DEFAULT '',
  admin_id INT UNSIGNED NULL,
  created_at DATETIME NOT NULL,
  KEY idx_points_user (user_id),
  CONSTRAINT fk_points_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_points_order FOREIGN KEY (order_id) REFERENCES orders(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS admins (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  login VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Неудачные попытки входа: защита от подбора пароля
CREATE TABLE IF NOT EXISTS login_attempts (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  scope VARCHAR(10) NOT NULL,
  login VARCHAR(50) NOT NULL,
  ip VARCHAR(45) NOT NULL,
  created_at DATETIME NOT NULL,
  KEY idx_attempts_login (scope, login, created_at),
  KEY idx_attempts_ip (ip, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
