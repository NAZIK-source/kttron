import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../catalog.dart';
import '../main.dart';
import '../state.dart';
import 'calculator.dart';

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  String? _category;
  String _query = '';

  // «кт трон 3», «кттрон-3» и «КТ ТРОН-3» — одно и то же
  static String _norm(String s) => s.toLowerCase().replaceAll('кттрон', 'кт трон').replaceAll(RegExp(r'[\s\-]+'), '');

  @override
  Widget build(BuildContext context) {
    final catalog = AppScope.of(context).catalog;
    final q = _norm(_query);
    final items = catalog.products
        .where((p) => _category == null || p.category == _category)
        .where((p) => q.isEmpty || _norm('${p.name} ${p.desc}').contains(q))
        .toList();
    return Scaffold(
      appBar: AppBar(
        title: const Text('КТ ТРОН Казахстан'),
        actions: [
          IconButton(
            tooltip: 'Написать в WhatsApp',
            icon: const Icon(Icons.chat_outlined),
            onPressed: () => AppScope.read(context).openWhatsApp(),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(112),
          child: Column(children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
              child: SearchBar(
                hintText: 'Поиск: КТ ТРОН-1, гидроизоляция…',
                leading: const Icon(Icons.search),
                elevation: const WidgetStatePropertyAll(0),
                onChanged: (v) => setState(() => _query = v),
              ),
            ),
            SizedBox(
              height: 48,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                children: [
                  _chip('Все', null),
                  for (final c in catalog.categories)
                    if (catalog.products.any((p) => p.category == c.id)) _chip(c.name, c.id),
                ],
              ),
            ),
          ]),
        ),
      ),
      body: items.isEmpty
          ? const Center(child: Text('Ничего не нашлось'))
          : ListView.separated(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: items.length,
              separatorBuilder: (_, _) => const Divider(height: 1, indent: 104),
              itemBuilder: (context, i) => ProductTile(product: items[i]),
            ),
    );
  }

  Widget _chip(String label, String? id) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4),
        child: ChoiceChip(label: Text(label), selected: _category == id, onSelected: (_) => setState(() => _category = id)),
      );
}

class ProductImage extends StatelessWidget {
  const ProductImage(this.url, {super.key, this.size});
  final String url;
  final double? size;

  @override
  Widget build(BuildContext context) => ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: CachedNetworkImage(
          imageUrl: url,
          width: size,
          height: size,
          fit: BoxFit.contain,
          placeholder: (_, _) => Container(width: size, height: size, color: Theme.of(context).colorScheme.surfaceContainerHighest),
          errorWidget: (_, _, _) => SizedBox(width: size, height: size, child: const Icon(Icons.inventory_2_outlined)),
        ),
      );
}

class ProductTile extends StatelessWidget {
  const ProductTile({super.key, required this.product, this.subtitle});
  final Product product;
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context).textTheme;
    return InkWell(
      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ProductScreen(product: product))),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          ProductImage(product.image, size: 72),
          const SizedBox(width: 16),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(product.name, style: t.titleMedium),
              const SizedBox(height: 2),
              Text(subtitle ?? product.desc, maxLines: 3, overflow: TextOverflow.ellipsis, style: t.bodyMedium),
              const SizedBox(height: 4),
              Text(product.priceLabel, style: t.labelLarge?.copyWith(color: Theme.of(context).colorScheme.primary)),
            ]),
          ),
        ]),
      ),
    );
  }
}

class ProductScreen extends StatelessWidget {
  const ProductScreen({super.key, required this.product});
  final Product product;

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final t = Theme.of(context).textTheme;
    final calc = state.catalog.calcById(product.calc);
    return Scaffold(
      appBar: AppBar(title: Text(product.name)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Center(child: ProductImage(product.image, size: 220)),
          const SizedBox(height: 16),
          Text(product.name, style: t.headlineSmall),
          const SizedBox(height: 8),
          Text(product.desc, style: t.bodyLarge),
          const SizedBox(height: 12),
          if (product.pack.isNotEmpty) Text('Фасовка: ${product.pack}', style: t.bodyMedium),
          Text(product.priceLabel, style: t.titleMedium?.copyWith(color: Theme.of(context).colorScheme.primary)),
          Text('Цена завода для Казахстана, без доставки. Точную цену назовёт менеджер.', style: t.bodySmall),
          const SizedBox(height: 16),
          FilledButton.icon(
            icon: const Icon(Icons.add_shopping_cart),
            label: const Text('Добавить в заявку'),
            onPressed: () {
              state.addProduct(product);
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text('${product.name} в заявке'),
                action: SnackBarAction(label: 'Открыть', onPressed: () => HomeScreen.openTab(context, HomeScreen.cartTab)),
              ));
            },
          ),
          if (calc != null) ...[
            const SizedBox(height: 8),
            OutlinedButton.icon(
              icon: const Icon(Icons.calculate_outlined),
              label: const Text('Рассчитать количество'),
              onPressed: () => Navigator.of(context)
                  .push(MaterialPageRoute(builder: (_) => CalculatorScreen(initial: calc.id))),
            ),
          ],
          const SizedBox(height: 8),
          OutlinedButton.icon(
            icon: const Icon(Icons.chat_outlined),
            label: const Text('Спросить специалиста'),
            onPressed: () => state.openWhatsApp('Здравствуйте! Вопрос по ${product.name}: '),
          ),
          if (product.specs.isNotEmpty) ...[
            const SizedBox(height: 24),
            Text('Технические характеристики', style: t.titleLarge),
            const SizedBox(height: 8),
            for (final row in product.specs)
              row.length == 1
                  ? Padding(
                      padding: const EdgeInsets.only(top: 12, bottom: 4),
                      child: Text(row[0], style: t.titleSmall),
                    )
                  : Container(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Theme.of(context).dividerColor))),
                      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Expanded(flex: 3, child: Text(row[0], style: t.bodyMedium)),
                        const SizedBox(width: 12),
                        Expanded(flex: 2, child: Text(row.sublist(1).join(' · '), style: t.bodyMedium?.copyWith(fontWeight: FontWeight.w600))),
                      ]),
                    ),
          ],
          const SizedBox(height: 16),
          TextButton.icon(
            icon: const Icon(Icons.description_outlined),
            label: const Text('Техописание и сертификаты на kttron.ru'),
            onPressed: () => openUrl(product.source),
          ),
          TextButton.icon(
            icon: const Icon(Icons.open_in_new),
            label: const Text('Страница на kttron.kz'),
            onPressed: () => openUrl(product.url),
          ),
        ],
      ),
    );
  }
}
