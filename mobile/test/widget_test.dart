import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:kttron/catalog.dart';
import 'package:kttron/state.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  SharedPreferences.setMockInitialValues({});
  final catalog = Catalog.fromJson(jsonDecode(File('assets/app-data.json').readAsStringSync()) as Map<String, dynamic>);

  test('каталог читается целиком', () {
    expect(catalog.products, hasLength(50));
    expect(catalog.calc, isNotEmpty);
    expect(catalog.tasks, isNotEmpty);
    for (final p in catalog.products) {
      expect(catalog.categories.map((c) => c.id), contains(p.category));
    }
  });

  // Те же числа, что даёт калькулятор на kttron.kz/calculator/
  test('расчёт как на сайте', () {
    final kt1 = catalog.calcById('kt-tron-1')!;
    final r1 = calculate(kt1, 100, 1, 1000);
    expect(r1.kgMin, closeTo(80, 1e-9));
    expect(r1.kgMax, closeTo(120, 1e-9));
    expect((r1.packsMin, r1.packsMax), (4, 5));
    expect((r1.sumMin, r1.sumMax), (100000, 125000));

    final kt3 = catalog.calcById('kt-tron-3')!; // 1800 кг на м³
    final r3 = calculate(kt3, 10, 10, null);
    expect(r3.kgMin, closeTo(180, 1e-9));
    expect(r3.packsMin, 8);
    expect(r3.sumMin, isNull);

    final seam = catalog.calcById('kt-tron-2')!; // шов 20×20 мм — 0,7 кг на метр
    expect(calculate(seam, 1, 20, null).kgMin, closeTo(0.7, 1e-9));

    final kit = catalog.calcById('kt-tron-10-2k')!; // комплект 33,5 кг
    expect(calculate(kit, 10, 2, 100).sumMin, (2 * 33.5 * 100).round());
  });

  test('числа по-русски', () {
    expect(fmtNum(1250), '1\u00a0250');
    expect(fmtNum(2.5), '2,5');
    expect(fmtNum(0.1, digits: 2), '0,1');
    expect(fmtNum(1234567.89), '1\u00a0234\u00a0567,9');
  });

  test('текст заявки как на сайте', () {
    final state = AppState(catalog);
    state.addProduct(catalog.productByName('КТ ТРОН-1')!);
    state.addProduct(catalog.productByName('КТ ТРОН-1')!);
    state.addCalc('КТ ТРОН-3', 8, 'расчёт: 10 м², толщина 10 мм, 180 кг');
    state.comment = 'Доставка в Алматы';
    final text = state.cartText();
    expect(text, contains('1. КТ ТРОН-1 × 2 (фасовка'));
    expect(text, contains('2. КТ ТРОН-3 × 8'));
    expect(text, endsWith('Комментарий: Доставка в Алматы'));
    expect(state.cartCount, 10);
  });
}
