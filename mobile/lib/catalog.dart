// Каталог, цены, калькулятор и подбор — из app-data.json на kttron.kz
// (собирает tools/build_app_data.py). В приложение вшита копия на случай,
// если при первом запуске нет интернета.
import 'dart:convert';
import 'dart:math';

import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'api.dart';

class Category {
  Category(this.id, this.name);
  final String id;
  final String name;
}

class Product {
  Product.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        name = j['name'] as String,
        category = j['category'] as String,
        desc = j['desc'] as String,
        pack = j['pack'] as String,
        image = j['image'] as String,
        url = j['url'] as String,
        source = j['source'] as String,
        price = (j['price'] as num?)?.toDouble(),
        unit = j['unit'] as String?,
        specs = [for (final r in j['specs'] as List) List<String>.from(r as List)],
        calc = j['calc'] as String?;
  final String id;
  final String name;
  final String category;
  final String desc;
  final String pack;
  final String image;
  final String url;
  final String source;
  final double? price;
  final String? unit;
  final List<List<String>> specs;
  final String? calc;

  String get priceLabel => price == null ? 'Цена по запросу' : 'от ${fmtNum(price!)} ₸ за 1 $unit';
}

class CalcMaterial {
  CalcMaterial.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        name = j['name'] as String,
        group = j['group'] as String,
        pack = (j['pack'] as num).toDouble(),
        kit = (j['kit'] as num?)?.toDouble(),
        mode = j['mode'] as String,
        min = (j['min'] as num).toDouble(),
        max = (j['max'] as num).toDouble(),
        thick = (j['thick'] as num?)?.toDouble(),
        minThick = (j['minThick'] as num?)?.toDouble(),
        maxThick = (j['maxThick'] as num?)?.toDouble(),
        note = j['note'] as String;
  final String id;
  final String name;
  final String group;
  final double pack;
  final double? kit; // двухкомпонентные продаются комплектом
  final String mode; // area — кг/м², mm — кг/м² на 1 мм, m3 — кг на 1 м³, seam — шов
  final double min;
  final double max;
  final double? thick;
  final double? minThick;
  final double? maxThick;
  final String note;

  bool get isSeam => mode == 'seam';
  bool get needsThickness => mode != 'area';
}

class CalcResult {
  CalcResult(this.kgMin, this.kgMax, this.packsMin, this.packsMax, this.sumMin, this.sumMax);
  final double kgMin;
  final double kgMax;
  final int packsMin;
  final int packsMax;
  final int? sumMin;
  final int? sumMax;
}

// Тот же расчёт, что в calculator/index.html на сайте
CalcResult calculate(CalcMaterial m, double area, double thick, double? pricePerKg) {
  final t = m.needsThickness ? thick : 1.0;
  final factor = switch (m.mode) {
    'm3' => area * t / 1000,
    'seam' => area * (t / 1000) * (t / 1000),
    _ => area * t,
  };
  final kgMin = factor * m.min;
  final kgMax = factor * m.max;
  final packsMin = (kgMin / m.pack).ceil();
  final packsMax = (kgMax / m.pack).ceil();
  int? sumMin, sumMax;
  if (pricePerKg != null) {
    // Считаем по целым мешкам: покупают их, а не килограммы
    final unitKg = m.kit ?? m.pack;
    sumMin = (packsMin * unitKg * pricePerKg).round();
    sumMax = (packsMax * unitKg * pricePerKg).round();
  }
  return CalcResult(kgMin, kgMax, packsMin, packsMax, sumMin, sumMax);
}

class Task {
  Task.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        url = j['url'] as String,
        title = j['title'] as String,
        group = j['group'] as String,
        image = j['image'] as String,
        lead = j['lead'] as String,
        materials = [for (final m in j['materials'] as List) ((m as Map)['name'] as String, m['why'] as String)],
        steps = List<String>.from(j['steps'] as List),
        faq = [for (final f in j['faq'] as List) ((f as Map)['q'] as String, f['a'] as String)];
  final String id;
  final String url;
  final String title;
  final String group;
  final String image;
  final String lead;
  final List<(String, String)> materials;
  final List<String> steps;
  final List<(String, String)> faq;
}

class Catalog {
  Catalog.fromJson(Map<String, dynamic> j)
      : version = j['version'] as String,
        whatsapp = j['whatsapp'] as String,
        categories = [for (final c in j['categories'] as List) Category(c['id'] as String, c['name'] as String)],
        products = [for (final p in j['products'] as List) Product.fromJson(p as Map<String, dynamic>)],
        calc = [for (final c in j['calc'] as List) CalcMaterial.fromJson(c as Map<String, dynamic>)],
        tasks = [for (final t in j['tasks'] as List) Task.fromJson(t as Map<String, dynamic>)],
        _prices = {
          for (final e in (j['prices'] as Map).entries)
            e.key as String: ((e.value['price'] as num).toDouble(), e.value['unit'] as String),
        };
  final String version;
  final String whatsapp;
  final List<Category> categories;
  final List<Product> products;
  final List<CalcMaterial> calc;
  final List<Task> tasks;
  final Map<String, (double, String)> _prices;

  double? pricePerKg(String name) {
    final p = _prices[name];
    return p != null && p.$2 == 'кг' ? p.$1 : null;
  }

  Product? productByName(String name) {
    for (final p in products) {
      if (p.name == name) return p;
    }
    return null;
  }

  Product? productById(String id) {
    for (final p in products) {
      if (p.id == id) return p;
    }
    return null;
  }

  CalcMaterial? calcById(String? id) {
    for (final c in calc) {
      if (c.id == id) return c;
    }
    return null;
  }

  static const _cacheKey = 'app-data';

  // Сначала — сохранённая копия (или вшитая), чтобы приложение открылось мгновенно
  static Future<Catalog> loadLocal() async {
    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getString(_cacheKey);
    if (cached != null) {
      try {
        return Catalog.fromJson(jsonDecode(cached) as Map<String, dynamic>);
      } catch (_) {
        await prefs.remove(_cacheKey);
      }
    }
    return Catalog.fromJson(jsonDecode(await rootBundle.loadString('assets/app-data.json')) as Map<String, dynamic>);
  }

  // Потом — свежие данные с сайта. null, если обновлять нечего или нет связи.
  static Future<Catalog?> fetch(String currentVersion) async {
    try {
      final r = await http.get(Uri.parse('$site/app-data.json')).timeout(const Duration(seconds: 20));
      if (r.statusCode != 200) return null;
      final body = utf8.decode(r.bodyBytes);
      final catalog = Catalog.fromJson(jsonDecode(body) as Map<String, dynamic>);
      if (catalog.version == currentVersion) return null;
      await (await SharedPreferences.getInstance()).setString(_cacheKey, body);
      return catalog;
    } catch (_) {
      return null;
    }
  }
}

// 1250 → «1 250» (неразрывный пробел, чтобы число не переносилось), 2.5 → «2,5»
String fmtNum(num n, {int digits = 1}) {
  final p = pow(10, digits);
  final rounded = (n * p).round() / p;
  final whole = rounded.truncate();
  final s = whole.abs().toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => '\u00a0');
  final frac = ((rounded - whole).abs() * p).round();
  return '${rounded < 0 ? '-' : ''}$s${frac == 0 ? '' : ',${frac.toString().padLeft(digits, '0').replaceAll(RegExp(r'0+$'), '')}'}';
}
