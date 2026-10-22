import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'screens/account.dart';
import 'screens/calculator.dart';
import 'screens/cart.dart';
import 'screens/catalog.dart';
import 'screens/tasks.dart';
import 'state.dart';

const brandBlue = Color(0xFF0093DD);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final state = await AppState.load();
  runApp(AppScope(notifier: state, child: const KtTronApp()));
  state.refresh();
}

// Доступ к состоянию из любого экрана: AppScope.of(context)
class AppScope extends InheritedNotifier<AppState> {
  const AppScope({super.key, required super.notifier, required super.child});

  static AppState of(BuildContext context) => context.dependOnInheritedWidgetOfExactType<AppScope>()!.notifier!;
  static AppState read(BuildContext context) => context.getInheritedWidgetOfExactType<AppScope>()!.notifier!;
}

class KtTronApp extends StatelessWidget {
  const KtTronApp({super.key});

  @override
  Widget build(BuildContext context) {
    ThemeData theme(Brightness b) => ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: brandBlue, brightness: b),
          useMaterial3: true,
          inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
        );
    return MaterialApp(
      title: 'КТ ТРОН Казахстан',
      debugShowCheckedModeBanner: false,
      locale: const Locale('ru'),
      supportedLocales: const [Locale('ru')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      theme: theme(Brightness.light),
      darkTheme: theme(Brightness.dark),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  // Переключить вкладку, например из карточки товара в калькулятор
  static void openTab(BuildContext context, int index) =>
      context.findAncestorStateOfType<_HomeScreenState>()?.select(index);

  static const catalogTab = 0, tasksTab = 1, calcTab = 2, cartTab = 3, accountTab = 4;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = 0;
  final _navigators = List.generate(5, (_) => GlobalKey<NavigatorState>());

  void select(int index) {
    if (index == _index) {
      _navigators[index].currentState?.popUntil((r) => r.isFirst);
    }
    setState(() => _index = index);
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    const roots = [CatalogScreen(), TasksScreen(), CalculatorScreen(), CartScreen(), AccountScreen()];
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        final nav = _navigators[_index].currentState!;
        if (nav.canPop()) {
          nav.pop();
        } else if (_index != 0) {
          setState(() => _index = 0);
        }
      },
      child: Scaffold(
        body: IndexedStack(
          index: _index,
          children: [
            for (var i = 0; i < roots.length; i++)
              Navigator(
                key: _navigators[i],
                onGenerateRoute: (_) => MaterialPageRoute(builder: (_) => roots[i]),
              ),
          ],
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: select,
          destinations: [
            const NavigationDestination(icon: Icon(Icons.grid_view_outlined), selectedIcon: Icon(Icons.grid_view), label: 'Каталог'),
            const NavigationDestination(icon: Icon(Icons.lightbulb_outline), selectedIcon: Icon(Icons.lightbulb), label: 'Подбор'),
            const NavigationDestination(icon: Icon(Icons.calculate_outlined), selectedIcon: Icon(Icons.calculate), label: 'Расчёт'),
            NavigationDestination(
              icon: Badge(isLabelVisible: state.cartCount > 0, label: Text('${state.cartCount}'), child: const Icon(Icons.shopping_bag_outlined)),
              selectedIcon: Badge(isLabelVisible: state.cartCount > 0, label: Text('${state.cartCount}'), child: const Icon(Icons.shopping_bag)),
              label: 'Заявка',
            ),
            NavigationDestination(
              icon: const Icon(Icons.person_outline),
              selectedIcon: const Icon(Icons.person),
              label: state.logged ? '${state.user!.balance} б.' : 'Кабинет',
            ),
          ],
        ),
      ),
    );
  }
}
