import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../catalog.dart';
import '../main.dart';
import 'catalog.dart';

class CalculatorScreen extends StatefulWidget {
  const CalculatorScreen({super.key, this.initial});
  final String? initial; // id материала, если открыли из карточки товара

  @override
  State<CalculatorScreen> createState() => _CalculatorScreenState();
}

class _CalculatorScreenState extends State<CalculatorScreen> {
  String? _id;
  final _area = TextEditingController(text: '10');
  final _thick = TextEditingController();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_id == null) {
      final calc = AppScope.read(context).catalog.calc;
      _pick(calc.firstWhere((m) => m.id == widget.initial, orElse: () => calc.first));
    }
  }

  void _pick(CalcMaterial m) {
    _id = m.id;
    _thick.text = m.thick == null ? '' : fmtNum(m.thick!);
  }

  double? _num(TextEditingController c) => double.tryParse(c.text.replaceAll(',', '.').replaceAll(' ', ''));

  Future<void> _choose(List<CalcMaterial> all) async {
    final picked = await showModalBottomSheet<CalcMaterial>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        final groups = <String, List<CalcMaterial>>{};
        for (final m in all) {
          groups.putIfAbsent(m.group, () => []).add(m);
        }
        return DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.75,
          builder: (context, scroll) => ListView(controller: scroll, children: [
            for (final g in groups.entries) ...[
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
                child: Text(g.key, style: Theme.of(context).textTheme.titleSmall),
              ),
              for (final m in g.value)
                ListTile(
                  title: Text(m.name),
                  selected: m.id == _id,
                  onTap: () => Navigator.pop(context, m),
                ),
            ],
          ]),
        );
      },
    );
    if (picked != null) setState(() => _pick(picked));
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final catalog = state.catalog;
    final m = catalog.calcById(_id) ?? catalog.calc.first;
    final t = Theme.of(context).textTheme;
    final area = _num(_area);
    final thick = _num(_thick) ?? m.thick ?? 1;
    final price = catalog.pricePerKg(m.name);
    final r = area != null && area > 0 && thick > 0 ? calculate(m, area, thick, price) : null;
    final product = catalog.productByName(m.name);

    String kg(CalcResult r) => r.kgMin == r.kgMax ? '${fmtNum(r.kgMin)} кг' : '${fmtNum(r.kgMin)}–${fmtNum(r.kgMax)} кг';
    String packs(CalcResult r) => r.packsMin == r.packsMax ? '${r.packsMin}' : '${r.packsMin}–${r.packsMax}';
    String? sum(CalcResult r) => r.sumMin == null
        ? null
        : 'от ${fmtNum(r.sumMin!)}${r.sumMax! > r.sumMin! ? '–${fmtNum(r.sumMax!)}' : ''} ₸';
    String detail() => m.mode == 'area'
        ? '${fmtNum(area!)} м²'
        : m.isSeam
            ? 'шов ${fmtNum(area!)} м, сечение ${fmtNum(thick)}×${fmtNum(thick)} мм'
            : '${fmtNum(area!)} м², толщина ${fmtNum(thick)} мм';

    return Scaffold(
      appBar: AppBar(title: const Text('Калькулятор расхода')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            margin: EdgeInsets.zero,
            child: ListTile(
              title: Text(m.name, style: t.titleMedium),
              subtitle: Text(m.group),
              trailing: const Icon(Icons.expand_more),
              onTap: () => _choose(catalog.calc),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _area,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[\d.,]'))],
            decoration: InputDecoration(labelText: m.isSeam ? 'Длина шва, м' : 'Площадь, м²'),
            onChanged: (_) => setState(() {}),
          ),
          if (m.needsThickness) ...[
            const SizedBox(height: 16),
            TextField(
              controller: _thick,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[\d.,]'))],
              decoration: InputDecoration(
                labelText: m.isSeam ? 'Сечение шва, мм (ширина = глубина)' : 'Толщина, мм',
                helperText: m.minThick != null && m.maxThick != null
                    ? 'Рекомендуется ${fmtNum(m.minThick!)}–${fmtNum(m.maxThick!)} мм'
                    : null,
              ),
              onChanged: (_) => setState(() {}),
            ),
          ],
          const SizedBox(height: 12),
          Text(m.note + (price != null ? ' Цена от ${fmtNum(price)} ₸ за 1 кг.' : ' Цена по запросу.'), style: t.bodySmall),
          const SizedBox(height: 16),
          Card(
            color: Theme.of(context).colorScheme.primaryContainer,
            margin: EdgeInsets.zero,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: r == null
                  ? Text(m.isSeam ? 'Укажите длину шва.' : 'Укажите площадь.')
                  : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('Понадобится', style: t.labelLarge),
                      Text(kg(r), style: t.headlineMedium),
                      Text('${packs(r)} ${m.kit != null ? 'компл. по ${fmtNum(m.kit!)} кг' : 'меш. по ${fmtNum(m.pack)} кг'}', style: t.titleMedium),
                      if (sum(r) != null) ...[
                        const SizedBox(height: 8),
                        Text('Ориентировочно ${sum(r)} без доставки. Точную цену назовёт менеджер.', style: t.bodyMedium),
                      ],
                    ]),
            ),
          ),
          const SizedBox(height: 16),
          if (r != null) ...[
            FilledButton.icon(
              icon: const Icon(Icons.add_shopping_cart),
              label: const Text('Добавить в заявку'),
              onPressed: () {
                state.addCalc(m.name, r.packsMax, 'расчёт: ${detail()}, ${kg(r)}');
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                  content: Text('${m.name} × ${r.packsMax} в заявке'),
                  action: SnackBarAction(label: 'Открыть', onPressed: () => HomeScreen.openTab(context, HomeScreen.cartTab)),
                ));
              },
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              icon: const Icon(Icons.chat_outlined),
              label: const Text('Отправить расчёт в WhatsApp'),
              onPressed: () => state.openWhatsApp('Здравствуйте! Нужен ${m.name}. ${detail()}. Ориентир: ${kg(r)}, '
                  '${packs(r)} меш. по ${fmtNum(m.pack)} кг${sum(r) != null ? '. Цена ориентировочно ${sum(r)} без доставки.' : '. Цена по запросу.'}'),
            ),
          ],
          if (product != null) ...[
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ProductScreen(product: product))),
              child: const Text('Карточка материала'),
            ),
          ],
          const SizedBox(height: 8),
          Text('Расчёт по нормам завода, без учёта потерь и неровностей основания.', style: t.bodySmall),
        ],
      ),
    );
  }
}
