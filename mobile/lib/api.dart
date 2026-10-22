// Связь с личным кабинетом на kttron.kz (account/app-api.php).
// Кабинет общий с сайтом: те же клиенты, заявки и баллы.
import 'dart:convert';

import 'package:http/http.dart' as http;

// Для проверки на тестовом сервере: flutter run --dart-define=SITE=https://…
const site = String.fromEnvironment('SITE', defaultValue: 'https://kttron.kz');

class ApiException implements Exception {
  ApiException(this.code, this.message);
  final String code;
  final String message;
  @override
  String toString() => message;
}

class User {
  User.fromJson(Map<String, dynamic> j)
      : id = j['id'] as int,
        name = j['name'] as String,
        phone = j['phone_formatted'] as String? ?? j['phone'] as String,
        balance = j['balance'] as int;
  final int id;
  final String name;
  final String phone;
  final int balance;
}

class Order {
  Order.fromJson(Map<String, dynamic> j)
      : id = j['id'] as int,
        text = j['text'] as String,
        status = j['status'] as String,
        wantRedeem = j['want_redeem'] as bool,
        amount = j['amount'] as int?,
        pointsUsed = j['points_used'] as int,
        cashback = j['cashback'] as int,
        createdAt = DateTime.parse(j['created_at'] as String);
  final int id;
  final String text;
  final String status; // new, paid, cancelled
  final bool wantRedeem;
  final int? amount;
  final int pointsUsed;
  final int cashback;
  final DateTime createdAt;

  String get statusLabel => const {'new': 'Новая', 'paid': 'Оплачена', 'cancelled': 'Отменена'}[status] ?? status;
}

class PointMove {
  PointMove.fromJson(Map<String, dynamic> j)
      : amount = j['amount'] as int,
        kind = j['kind'] as String,
        orderId = j['order_id'] as int?,
        note = j['note'] as String,
        createdAt = DateTime.parse(j['created_at'] as String);
  final int amount;
  final String kind;
  final int? orderId;
  final String note;
  final DateTime createdAt;

  String get label {
    final k = const {'cashback': 'Кэшбэк', 'redeem': 'Списание', 'manual': 'Корректировка'}[kind] ?? kind;
    return [k, if (orderId != null) 'заявка № $orderId', if (note.isNotEmpty) note].join(' · ');
  }
}

class Api {
  Api(this.token);
  String? token;

  Future<Map<String, dynamic>> _call(String action, {Map<String, dynamic>? body}) async {
    final uri = Uri.parse('$site/account/app-api.php?a=$action');
    final headers = {
      'Accept': 'application/json',
      'X-Auth-Token': ?token,
      if (body != null) 'Content-Type': 'application/json',
    };
    final http.Response r;
    try {
      r = body == null
          ? await http.get(uri, headers: headers).timeout(const Duration(seconds: 20))
          : await http.post(uri, headers: headers, body: jsonEncode(body)).timeout(const Duration(seconds: 20));
    } catch (_) {
      throw ApiException('network', 'Нет связи с сервером. Проверьте интернет.');
    }
    Map<String, dynamic> data;
    try {
      data = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    } catch (_) {
      throw ApiException('server', 'Сервер ответил с ошибкой. Попробуйте позже.');
    }
    if (data['ok'] != true) {
      throw ApiException(data['error'] as String? ?? 'error', data['message'] as String? ?? 'Ошибка');
    }
    return data;
  }

  Future<Map<String, dynamic>> config() => _call('config');

  Future<(String, User)> login(String phone, String password, String device) async {
    final d = await _call('login', body: {'phone': phone, 'password': password, 'device': device});
    return (d['token'] as String, User.fromJson(d['user'] as Map<String, dynamic>));
  }

  Future<(String, User)> register(String name, String phone, String password, String device) async {
    final d = await _call('register',
        body: {'name': name, 'phone': phone, 'password': password, 'consent': true, 'device': device});
    return (d['token'] as String, User.fromJson(d['user'] as Map<String, dynamic>));
  }

  Future<void> logout() => _call('logout', body: {});

  Future<User> me() async => User.fromJson((await _call('me'))['user'] as Map<String, dynamic>);

  Future<List<Order>> orders() async => [
        for (final o in (await _call('orders'))['orders'] as List) Order.fromJson(o as Map<String, dynamic>),
      ];

  Future<List<PointMove>> points() async => [
        for (final m in (await _call('points'))['points'] as List) PointMove.fromJson(m as Map<String, dynamic>),
      ];

  Future<int> sendOrder(String text, String source, bool wantRedeem) async =>
      (await _call('order', body: {'text': text, 'source': source, 'want_redeem': wantRedeem}))['order'] as int;

  Future<Order> redeem(int orderId, bool want) async =>
      Order.fromJson((await _call('redeem', body: {'order': orderId, 'want': want}))['order'] as Map<String, dynamic>);

  Future<void> changePassword(String oldPassword, String newPassword) =>
      _call('password', body: {'old': oldPassword, 'new': newPassword});

  Future<void> deleteAccount(String password) => _call('delete', body: {'password': password});
}
