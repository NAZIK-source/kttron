import 'package:flutter/material.dart';

import '../api.dart';
import '../main.dart';

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});

  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  late final _comment = TextEditingController(text: AppScope.read(context).comment);
  bool _redeem = false;
  bool _sending = false;

  Future<void> _send() async {
    final state = AppScope.read(context);
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _sending = true);
    try {
      final id = await state.sendCart(wantRedeem: _redeem);
      _comment.clear();
      messenger.showSnackBar(SnackBar(
        content: Text(id == null
            ? 'Заявка открыта в WhatsApp. Войдите в кабинет, чтобы получать кэшбэк.'
            : 'Заявка № $id сохранена в кабинете. Кэшбэк начислим после оплаты.'),
      ));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final t = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Заявка'),
        actions: [
          if (state.cart.isNotEmpty)
            IconButton(
              tooltip: 'Очистить',
              icon: const Icon(Icons.delete_outline),
              onPressed: () {
                state.clearCart();
                _comment.clear();
              },
            ),
        ],
      ),
      body: state.cart.isEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  const Icon(Icons.shopping_bag_outlined, size: 64),
                  const SizedBox(height: 16),
                  Text('Заявка пуста', style: t.titleLarge),
                  const SizedBox(height: 8),
                  const Text('Добавьте материалы из каталога или из калькулятора. Менеджер посчитает точную цену и доставку.',
                      textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: () => HomeScreen.openTab(context, HomeScreen.catalogTab),
                    child: const Text('Открыть каталог'),
                  ),
                ]),
              ),
            )
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                for (final item in state.cart)
                  Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
                      child: Row(children: [
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(item.name, style: t.titleMedium),
                            if (item.note.isNotEmpty) Text(item.note, style: t.bodySmall),
                          ]),
                        ),
                        IconButton(icon: const Icon(Icons.remove), onPressed: () => state.setQty(item, item.qty - 1)),
                        Text('${item.qty}', style: t.titleMedium),
                        IconButton(icon: const Icon(Icons.add), onPressed: () => state.setQty(item, item.qty + 1)),
                      ]),
                    ),
                  ),
                const SizedBox(height: 8),
                TextField(
                  controller: _comment,
                  minLines: 2,
                  maxLines: 5,
                  decoration: const InputDecoration(labelText: 'Комментарий', hintText: 'Объект, сроки, адрес доставки'),
                  onChanged: (v) => state.comment = v,
                ),
                const SizedBox(height: 16),
                if (state.logged && state.user!.balance > 0)
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text('Списать баллы (на балансе ${state.user!.balance})'),
                    subtitle: Text('Баллами можно оплатить до ${state.maxRedeemPercent.round()}% заказа. Сумму списания поставит менеджер.'),
                    value: _redeem,
                    onChanged: (v) => setState(() => _redeem = v),
                  ),
                if (!state.logged)
                  Card(
                    color: Theme.of(context).colorScheme.secondaryContainer,
                    margin: const EdgeInsets.only(bottom: 16),
                    child: ListTile(
                      leading: const Icon(Icons.savings_outlined),
                      title: const Text('Получайте кэшбэк'),
                      subtitle: Text('Войдите в кабинет: за оплаченные заявки начислим ${state.cashbackPercent.toString().replaceAll('.', ',')}% баллами.'),
                      onTap: () => HomeScreen.openTab(context, HomeScreen.accountTab),
                    ),
                  ),
                FilledButton.icon(
                  icon: _sending
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.send),
                  label: const Text('Отправить в WhatsApp'),
                  onPressed: _sending ? null : _send,
                ),
                const SizedBox(height: 8),
                Text('Менеджер ответит в WhatsApp, уточнит цену с доставкой и способ оплаты.', style: t.bodySmall, textAlign: TextAlign.center),
              ],
            ),
    );
  }
}
