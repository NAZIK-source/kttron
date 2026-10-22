import 'package:flutter/material.dart';

import '../api.dart';
import '../catalog.dart';
import '../main.dart';
import '../state.dart';

const rulesUrl = '$site/account/rules.php';

String _date(DateTime d) =>
    '${d.day.toString().padLeft(2, '0')}.${d.month.toString().padLeft(2, '0')}.${d.year}';

class AccountScreen extends StatelessWidget {
  const AccountScreen({super.key});

  @override
  Widget build(BuildContext context) =>
      AppScope.of(context).logged ? const _Cabinet() : const _AuthForm();
}

// ---------- Вход и регистрация ----------

class _AuthForm extends StatefulWidget {
  const _AuthForm();

  @override
  State<_AuthForm> createState() => _AuthFormState();
}

class _AuthFormState extends State<_AuthForm> {
  bool _register = false;
  bool _consent = false;
  bool _busy = false;
  String? _error;
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _password = TextEditingController();
  final _password2 = TextEditingController();

  Future<void> _submit() async {
    final state = AppScope.read(context);
    setState(() => _error = null);
    if (_register) {
      if (_name.text.trim().isEmpty) return setState(() => _error = 'Укажите имя.');
      if (_password.text.length < 8) return setState(() => _error = 'Пароль — не короче 8 символов.');
      if (_password.text != _password2.text) return setState(() => _error = 'Пароли не совпадают.');
      if (!_consent) return setState(() => _error = 'Нужно согласие на обработку персональных данных и с правилами кэшбэка.');
    }
    setState(() => _busy = true);
    try {
      if (_register) {
        await state.register(_name.text.trim(), _phone.text, _password.text);
      } else {
        await state.login(_phone.text, _password.text);
      }
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final t = Theme.of(context).textTheme;
    final percent = fmtNum(state.cashbackPercent, digits: 2);
    return Scaffold(
      appBar: AppBar(title: Text(_register ? 'Регистрация' : 'Вход в кабинет')),
      body: AutofillGroup(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Один кабинет на сайте kttron.kz и в приложении: те же заявки и баллы.', style: t.bodyLarge),
            const SizedBox(height: 4),
            Text('Кэшбэк $percent% баллами за каждую оплаченную заявку. 1 балл = 1 ₸ скидки.', style: t.bodyMedium),
            const SizedBox(height: 24),
            if (_register) ...[
              TextField(
                controller: _name,
                textCapitalization: TextCapitalization.words,
                autofillHints: const [AutofillHints.name],
                decoration: const InputDecoration(labelText: 'Имя'),
              ),
              const SizedBox(height: 16),
            ],
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              autofillHints: const [AutofillHints.telephoneNumber],
              decoration: InputDecoration(labelText: _register ? 'Телефон (как в WhatsApp)' : 'Телефон', hintText: '+7 777 123-45-67'),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _password,
              obscureText: true,
              autofillHints: [_register ? AutofillHints.newPassword : AutofillHints.password],
              decoration: const InputDecoration(labelText: 'Пароль'),
              onSubmitted: (_) => _register ? null : _submit(),
            ),
            if (_register) ...[
              const SizedBox(height: 16),
              TextField(
                controller: _password2,
                obscureText: true,
                autofillHints: const [AutofillHints.newPassword],
                decoration: const InputDecoration(labelText: 'Пароль ещё раз'),
              ),
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                value: _consent,
                onChanged: (v) => setState(() => _consent = v ?? false),
                title: const Text('Согласен на обработку персональных данных и с правилами кэшбэка'),
                subtitle: GestureDetector(
                  onTap: () => openUrl(rulesUrl),
                  child: Text('Прочитать правила', style: TextStyle(color: Theme.of(context).colorScheme.primary)),
                ),
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _busy ? null : _submit,
              child: _busy
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(_register ? 'Зарегистрироваться' : 'Войти'),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => setState(() {
                _register = !_register;
                _error = null;
              }),
              child: Text(_register ? 'Уже есть кабинет? Войти' : 'Нет кабинета? Зарегистрироваться'),
            ),
            if (!_register)
              TextButton(
                onPressed: () => state.openWhatsApp('Здравствуйте! Забыл пароль от личного кабинета.'),
                child: const Text('Забыли пароль? Напишите в WhatsApp'),
              ),
          ],
        ),
      ),
    );
  }
}

// ---------- Кабинет ----------

class _Cabinet extends StatefulWidget {
  const _Cabinet();

  @override
  State<_Cabinet> createState() => _CabinetState();
}

class _CabinetState extends State<_Cabinet> {
  List<Order>? _orders;
  List<PointMove>? _points;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final state = AppScope.read(context);
    try {
      final results = await Future.wait([state.api.orders(), state.api.points(), state.refreshUser()]);
      if (!mounted) return;
      setState(() {
        _orders = results[0] as List<Order>;
        _points = results[1] as List<PointMove>;
        _error = null;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _toggleRedeem(Order o) async {
    try {
      await AppScope.read(context).api.redeem(o.id, !o.wantRedeem);
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final user = state.user!;
    final t = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Личный кабинет'),
        actions: [
          PopupMenuButton<String>(
            onSelected: (v) => switch (v) {
              'password' => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const _PasswordScreen())),
              'rules' => openUrl(rulesUrl),
              'logout' => state.logout(),
              'delete' => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const _DeleteScreen())),
              _ => null,
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'password', child: Text('Сменить пароль')),
              PopupMenuItem(value: 'rules', child: Text('Правила кэшбэка')),
              PopupMenuItem(value: 'logout', child: Text('Выйти')),
              PopupMenuItem(value: 'delete', child: Text('Удалить кабинет')),
            ],
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(user.name, style: t.headlineSmall),
            Text(user.phone, style: t.bodyMedium),
            const SizedBox(height: 16),
            Card(
              margin: EdgeInsets.zero,
              color: scheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Баланс', style: t.labelLarge),
                  Text('${fmtNum(user.balance)} ${pointsWord(user.balance)}', style: t.headlineMedium),
                  const SizedBox(height: 4),
                  Text('1 балл = 1 ₸ скидки. Кэшбэк ${fmtNum(state.cashbackPercent, digits: 2)}% с оплаченных заявок. '
                      'Баллами можно оплатить до ${state.maxRedeemPercent.round()}% заказа.', style: t.bodySmall),
                ]),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(_error!, style: TextStyle(color: scheme.error)),
            ],
            const SizedBox(height: 24),
            Text('Мои заявки', style: t.titleLarge),
            const SizedBox(height: 8),
            if (_orders == null && _error == null)
              const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))
            else if (_orders?.isEmpty ?? true)
              const Text('Заявок пока нет. Соберите заявку в каталоге и отправьте — она появится здесь. '
                  'Кэшбэк начислим, когда менеджер отметит оплату.')
            else
              for (final o in _orders!)
                Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ExpansionTile(
                    title: Text('Заявка № ${o.id}'),
                    subtitle: Text('${_date(o.createdAt)} · ${o.statusLabel}'
                        '${o.status == 'paid' ? ' · +${o.cashback} ${pointsWord(o.cashback)}' : ''}'),
                    childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                    expandedCrossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SelectableText(o.text),
                      if (o.status == 'paid') ...[
                        const SizedBox(height: 8),
                        Text('Оплачено: ${fmtNum(o.amount ?? 0)} ₸'
                            '${o.pointsUsed > 0 ? ' · списано ${o.pointsUsed} ${pointsWord(o.pointsUsed)}' : ''}'
                            ' · начислено +${o.cashback} ${pointsWord(o.cashback)}'),
                      ],
                      if (o.status == 'new' && user.balance > 0) ...[
                        const SizedBox(height: 8),
                        if (o.wantRedeem) const Text('Вы попросили списать баллы — менеджер учтёт их при оплате.'),
                        OutlinedButton(
                          onPressed: () => _toggleRedeem(o),
                          child: Text(o.wantRedeem ? 'Не списывать' : 'Списать баллы по этой заявке'),
                        ),
                      ],
                    ],
                  ),
                ),
            const SizedBox(height: 24),
            Text('История баллов', style: t.titleLarge),
            const SizedBox(height: 8),
            if (_points?.isEmpty ?? true)
              const Text('Пока пусто.')
            else
              for (final m in _points!)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(m.label),
                  subtitle: Text(_date(m.createdAt)),
                  trailing: Text(
                    '${m.amount > 0 ? '+' : ''}${m.amount}',
                    style: t.titleMedium?.copyWith(color: m.amount < 0 ? scheme.error : Colors.green.shade700),
                  ),
                ),
          ],
        ),
      ),
    );
  }
}

String pointsWord(int n) {
  final a = n.abs() % 100, m = a % 10;
  if (a > 10 && a < 20) return 'баллов';
  if (m == 1) return 'балл';
  if (m >= 2 && m <= 4) return 'балла';
  return 'баллов';
}

class _PasswordScreen extends StatefulWidget {
  const _PasswordScreen();

  @override
  State<_PasswordScreen> createState() => _PasswordScreenState();
}

class _PasswordScreenState extends State<_PasswordScreen> {
  final _old = TextEditingController();
  final _new = TextEditingController();
  String? _error;

  Future<void> _save() async {
    if (_new.text.length < 8) return setState(() => _error = 'Новый пароль — не короче 8 символов.');
    try {
      await AppScope.read(context).api.changePassword(_old.text, _new.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Пароль изменён.')));
      Navigator.pop(context);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Сменить пароль')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          TextField(controller: _old, obscureText: true, decoration: const InputDecoration(labelText: 'Текущий пароль')),
          const SizedBox(height: 16),
          TextField(controller: _new, obscureText: true, decoration: const InputDecoration(labelText: 'Новый пароль')),
          if (_error != null) Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ),
          const SizedBox(height: 16),
          FilledButton(onPressed: _save, child: const Text('Сохранить')),
        ]),
      );
}

class _DeleteScreen extends StatefulWidget {
  const _DeleteScreen();

  @override
  State<_DeleteScreen> createState() => _DeleteScreenState();
}

class _DeleteScreenState extends State<_DeleteScreen> {
  final _password = TextEditingController();
  String? _error;

  Future<void> _delete() async {
    final state = AppScope.read(context);
    final nav = Navigator.of(context);
    try {
      await state.deleteAccount(_password.text);
      nav.popUntil((r) => r.isFirst);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Удалить кабинет')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          const Text('Кабинет удалится на сайте и в приложении. Имя и телефон будут стёрты, '
              'накопленные баллы сгорят. Отменить это нельзя.'),
          const SizedBox(height: 16),
          TextField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: 'Пароль для подтверждения')),
          if (_error != null) Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ),
          const SizedBox(height: 16),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.error),
            onPressed: _delete,
            child: const Text('Удалить навсегда'),
          ),
        ]),
      );
}
