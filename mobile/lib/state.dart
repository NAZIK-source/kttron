// Общее состояние приложения: каталог, заявка (корзина) и вход в кабинет.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import 'api.dart';
import 'catalog.dart';

class CartItem {
  CartItem({required this.name, this.productId, this.qty = 1, this.note = ''});
  CartItem.fromJson(Map<String, dynamic> j)
      : name = j['name'] as String,
        productId = j['productId'] as String?,
        qty = j['qty'] as int,
        note = j['note'] as String? ?? '';
  final String name;
  final String? productId;
  int qty;
  final String note; // для строк из калькулятора: что и сколько посчитано

  Map<String, dynamic> toJson() => {'name': name, 'productId': productId, 'qty': qty, 'note': note};
}

class AppState extends ChangeNotifier {
  AppState(this.catalog);

  Catalog catalog;
  final cart = <CartItem>[];
  String comment = '';
  User? user;
  double cashbackPercent = 0.1;
  double maxRedeemPercent = 30;

  final _secure = const FlutterSecureStorage();
  final api = Api(null);
  bool get logged => user != null;

  static Future<AppState> load() async {
    final state = AppState(await Catalog.loadLocal());
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('cart');
    if (saved != null) {
      try {
        state.cart.addAll([for (final i in jsonDecode(saved) as List) CartItem.fromJson(i as Map<String, dynamic>)]);
      } catch (_) {}
    }
    state.api.token = await state._secure.read(key: 'token');
    return state;
  }

  // Фоновые обновления после запуска: свежий каталог, правила кэшбэка, баланс
  Future<void> refresh() async {
    final fresh = await Catalog.fetch(catalog.version);
    if (fresh != null) {
      catalog = fresh;
      notifyListeners();
    }
    try {
      final c = await api.config();
      cashbackPercent = (c['cashback_percent'] as num).toDouble();
      maxRedeemPercent = (c['max_redeem_percent'] as num).toDouble();
    } catch (_) {}
    await refreshUser();
  }

  Future<void> refreshUser() async {
    if (api.token == null) return;
    try {
      user = await api.me();
    } on ApiException catch (e) {
      if (e.code == 'not_logged') await _forget();
    }
    notifyListeners();
  }

  String get _device => '${Platform.operatingSystem} ${Platform.operatingSystemVersion}';

  Future<void> login(String phone, String password) async {
    final (token, u) = await api.login(phone, password, _device);
    await _remember(token, u);
  }

  Future<void> register(String name, String phone, String password) async {
    final (token, u) = await api.register(name, phone, password, _device);
    await _remember(token, u);
  }

  Future<void> logout() async {
    try {
      await api.logout();
    } catch (_) {}
    await _forget();
  }

  Future<void> deleteAccount(String password) async {
    await api.deleteAccount(password);
    await _forget();
  }

  Future<void> _remember(String token, User u) async {
    api.token = token;
    user = u;
    await _secure.write(key: 'token', value: token);
    notifyListeners();
  }

  Future<void> _forget() async {
    api.token = null;
    user = null;
    await _secure.delete(key: 'token');
    notifyListeners();
  }

  // ---------- Заявка ----------

  int get cartCount => cart.fold(0, (n, i) => n + i.qty);

  void addProduct(Product p) {
    for (final i in cart) {
      if (i.productId == p.id && i.note.isEmpty) {
        i.qty++;
        _saveCart();
        return;
      }
    }
    cart.add(CartItem(name: p.name, productId: p.id));
    _saveCart();
  }

  void addCalc(String name, int qty, String note) {
    cart.add(CartItem(name: name, productId: catalog.productByName(name)?.id, qty: qty, note: note));
    _saveCart();
  }

  void setQty(CartItem item, int qty) {
    if (qty <= 0) {
      cart.remove(item);
    } else {
      item.qty = qty;
    }
    _saveCart();
  }

  void clearCart() {
    cart.clear();
    comment = '';
    _saveCart();
  }

  void _saveCart() {
    notifyListeners();
    SharedPreferences.getInstance()
        .then((p) => p.setString('cart', jsonEncode([for (final i in cart) i.toJson()])));
  }

  // Тот же формат, что у заявки с сайта
  String cartText() {
    final lines = <String>[];
    for (final (n, i) in cart.indexed) {
      final p = i.productId == null ? null : catalog.productById(i.productId!);
      final pack = p != null && p.pack.isNotEmpty ? ' (фасовка ${p.pack})' : '';
      lines.add('${n + 1}. ${i.name} × ${i.qty}$pack${i.note.isEmpty ? '' : ' — ${i.note}'}');
    }
    return [
      'Здравствуйте! Заявка из приложения КТ ТРОН',
      'Нужен расчёт / консультация по материалам:',
      ...lines,
      if (comment.trim().isNotEmpty) 'Комментарий: ${comment.trim()}',
    ].join('\n');
  }

  // Заявка сохраняется в кабинете (если клиент вошёл) и уходит менеджеру в WhatsApp.
  // Возвращает номер заявки в кабинете или null, если клиент не вошёл.
  Future<int?> sendCart({required bool wantRedeem}) async {
    final text = cartText();
    int? orderId;
    if (logged) orderId = await api.sendOrder(text, 'request', wantRedeem);
    await openWhatsApp(orderId == null ? text : '$text\nЗаявка в кабинете № $orderId');
    clearCart();
    return orderId;
  }

  Future<void> openWhatsApp([String text = '']) => openUrl(
      'https://wa.me/${catalog.whatsapp}${text.isEmpty ? '' : '?text=${Uri.encodeComponent(text)}'}');
}

Future<void> openUrl(String url) async {
  if (!await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication)) {
    debugPrint('Не открылась ссылка $url');
  }
}
